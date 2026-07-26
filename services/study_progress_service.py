from datetime import datetime

from models.study_progress import (
    STATUS_LEARNING,
    STATUS_MASTERED,
    STATUS_NEW,
    STATUS_REVIEW,
    VALID_PROGRESS_STATUSES,
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
        flashcard = self.flashcard_repository.get_by_id(
            flashcard_id
        )
        if flashcard is None:
            raise ValueError("Không tìm thấy flashcard.")

        progress = self.repository.get_by_flashcard_id(
            flashcard_id
        )
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

        summary = self.repository.get_summary_by_set_id(
            set_id
        )

        total = summary["total"]
        mastered = summary["mastered"]
        percent = (
            round(mastered * 100 / total, 1)
            if total > 0
            else 0.0
        )

        return {
            **summary,
            "mastered_percent": percent,
        }

    def record_answer(
        self,
        flashcard_id: int,
        correct: bool,
    ) -> StudyProgress:
        """
        Ghi nhận một câu trả lời đúng/sai.

        Đây là cơ chế progress cơ bản cho Learn/Test. Spaced repetition
        chi tiết với Again/Hard/Good/Easy sẽ được xây trên cùng model sau.
        """
        progress = self.get_or_create_for_flashcard(
            flashcard_id
        )

        progress.review_count += 1
        progress.last_review = datetime.now()

        if correct:
            progress.correct_count += 1
        else:
            progress.wrong_count += 1

        progress.status = self._calculate_status(
            progress
        )

        return self.repository.update(
            progress
        )

    def update_schedule(
        self,
        flashcard_id: int,
        *,
        status: str,
        ease_factor: float,
        interval_days: int,
        next_review: datetime | None,
    ) -> StudyProgress:
        """API nền để Flashcard/Spaced Repetition cập nhật lịch ôn sau này."""
        if status not in VALID_PROGRESS_STATUSES:
            raise ValueError("Trạng thái học tập không hợp lệ.")

        if ease_factor < 1.3:
            raise ValueError("ease_factor phải lớn hơn hoặc bằng 1.3.")

        if interval_days < 0:
            raise ValueError("interval_days không được âm.")

        progress = self.get_or_create_for_flashcard(
            flashcard_id
        )
        progress.status = status
        progress.ease_factor = ease_factor
        progress.interval_days = interval_days
        progress.next_review = next_review

        return self.repository.update(progress)

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
