from datetime import datetime, timedelta

from models.study_progress import (
    RATING_AGAIN,
    RATING_EASY,
    RATING_GOOD,
    RATING_HARD,
    STATUS_LEARNING,
    STATUS_MASTERED,
    STATUS_NEW,
    STATUS_REVIEW,
    VALID_PROGRESS_STATUSES,
    VALID_REVIEW_RATINGS,
    StudyProgress,
)
from repositories.flashcard_repository import FlashcardRepository
from repositories.study_progress_repository import StudyProgressRepository
from repositories.study_set_repository import StudySetRepository


class StudyProgressService:
    """Nghiệp vụ theo dõi tiến độ học của từng flashcard."""

    def __init__(
        self,
        repository: StudyProgressRepository,
        flashcard_repository: FlashcardRepository,
        study_set_repository: StudySetRepository,
    ):
        self.repository = repository
        self.flashcard_repository = flashcard_repository
        self.study_set_repository = study_set_repository
        self.database = repository.database

    def get_or_create_for_flashcard(
        self,
        flashcard_id: int,
    ) -> StudyProgress:
        flashcard = self.flashcard_repository.get_by_id(flashcard_id)
        if flashcard is None:
            raise ValueError("Không tìm thấy flashcard.")

        progress = self.repository.get_by_flashcard_id(flashcard_id)
        if progress is not None:
            return progress

        return self.repository.create(
            StudyProgress(
                id=None,
                flashcard_id=flashcard_id,
            )
        )

    def get_progress_for_set(
        self,
        set_id: int,
    ) -> list[StudyProgress]:
        if not self.study_set_repository.exists(set_id):
            raise ValueError("Không tìm thấy bộ học.")

        return self.repository.get_by_set_id(set_id)

    def get_summary_for_set(
        self,
        set_id: int,
    ) -> dict[str, int | float]:
        if not self.study_set_repository.exists(set_id):
            raise ValueError("Không tìm thấy bộ học.")

        summary = self.repository.get_summary_by_set_id(set_id)
        total = summary["total"]
        mastered = summary["mastered"]
        percent = round(mastered * 100 / total, 1) if total > 0 else 0.0

        return {
            **summary,
            "mastered_percent": percent,
        }

    def record_answer(
        self,
        flashcard_id: int,
        correct: bool,
    ) -> StudyProgress:
        """Ghi nhận kết quả đúng/sai cho Learn/Test Mode."""
        progress = self.get_or_create_for_flashcard(flashcard_id)
        progress.review_count += 1
        progress.last_review = datetime.now()

        if correct:
            progress.correct_count += 1
        else:
            progress.wrong_count += 1

        progress.status = self._calculate_status(progress)
        return self.repository.update(progress)

    def review_flashcard(
        self,
        flashcard_id: int,
        rating: str,
    ) -> StudyProgress:
        """
        Ghi nhận đánh giá Again / Hard / Good / Easy và lên lịch ôn tiếp.

        Quy tắc hiện tại là một biến thể spaced repetition đơn giản:
        - Again: quay về LEARNING, ôn lại ngay trong ngày.
        - Hard: khoảng cách ngắn, giảm ease factor.
        - Good: tăng khoảng cách theo ease factor.
        - Easy: tăng khoảng cách mạnh hơn và tăng ease factor.

        Thuật toán được tách trong service để UI không chứa logic học tập.
        """
        rating = rating.strip().upper()
        if rating not in VALID_REVIEW_RATINGS:
            raise ValueError("Mức đánh giá flashcard không hợp lệ.")

        now = datetime.now()

        with self.database.transaction():
            progress = self.get_or_create_for_flashcard(flashcard_id)

            previous_interval = progress.interval_days
            progress.review_count += 1
            progress.last_review = now

            if rating == RATING_AGAIN:
                progress.wrong_count += 1
                progress.status = STATUS_LEARNING
                progress.ease_factor = max(1.3, progress.ease_factor - 0.20)
                progress.interval_days = 0
                progress.next_review = now + timedelta(minutes=10)

            elif rating == RATING_HARD:
                progress.correct_count += 1
                progress.ease_factor = max(1.3, progress.ease_factor - 0.15)
                progress.interval_days = max(
                    1,
                    round(previous_interval * 1.2) if previous_interval else 1,
                )
                progress.status = STATUS_REVIEW
                progress.next_review = now + timedelta(
                    days=progress.interval_days
                )

            elif rating == RATING_GOOD:
                progress.correct_count += 1
                progress.interval_days = (
                    max(1, round(previous_interval * progress.ease_factor))
                    if previous_interval
                    else 1
                )
                progress.status = self._status_after_success(progress)
                progress.next_review = now + timedelta(
                    days=progress.interval_days
                )

            elif rating == RATING_EASY:
                progress.correct_count += 1
                progress.ease_factor = min(3.5, progress.ease_factor + 0.15)
                progress.interval_days = (
                    max(
                        previous_interval + 1,
                        round(previous_interval * progress.ease_factor * 1.3),
                    )
                    if previous_interval
                    else 4
                )
                progress.status = self._status_after_success(
                    progress,
                    easy=True,
                )
                progress.next_review = now + timedelta(
                    days=progress.interval_days
                )

            return self.repository.update(progress)

    def update_schedule(
        self,
        flashcard_id: int,
        *,
        status: str,
        ease_factor: float,
        interval_days: int,
        next_review: datetime | None,
    ) -> StudyProgress:
        """API nền để cập nhật lịch ôn thủ công khi cần."""
        if status not in VALID_PROGRESS_STATUSES:
            raise ValueError("Trạng thái học tập không hợp lệ.")
        if ease_factor < 1.3:
            raise ValueError("ease_factor phải lớn hơn hoặc bằng 1.3.")
        if interval_days < 0:
            raise ValueError("interval_days không được âm.")

        progress = self.get_or_create_for_flashcard(flashcard_id)
        progress.status = status
        progress.ease_factor = ease_factor
        progress.interval_days = interval_days
        progress.next_review = next_review
        return self.repository.update(progress)

    @staticmethod
    def _status_after_success(
        progress: StudyProgress,
        *,
        easy: bool = False,
    ) -> str:
        accuracy = (
            progress.correct_count / progress.review_count
            if progress.review_count
            else 0.0
        )

        if (
            (progress.interval_days >= 21 and accuracy >= 0.8)
            or (easy and progress.review_count >= 4 and accuracy >= 0.85)
        ):
            return STATUS_MASTERED

        return STATUS_REVIEW

    @staticmethod
    def _calculate_status(
        progress: StudyProgress,
    ) -> str:
        if progress.review_count == 0:
            return STATUS_NEW

        if progress.wrong_count > 0 and progress.review_count <= 2:
            return STATUS_LEARNING

        accuracy = (
            progress.correct_count / progress.review_count
            if progress.review_count
            else 0.0
        )

        if progress.review_count >= 5 and accuracy >= 0.85:
            return STATUS_MASTERED

        if accuracy >= 0.6:
            return STATUS_REVIEW

        return STATUS_LEARNING
