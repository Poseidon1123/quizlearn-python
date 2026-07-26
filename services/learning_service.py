import re
import unicodedata

from models.flashcard import Flashcard
from services.study_progress_service import StudyProgressService


class LearningService:
    """Nghiệp vụ kiểm tra câu trả lời trong Learn Mode."""

    def __init__(
        self,
        study_progress_service: StudyProgressService,
    ):
        self.study_progress_service = study_progress_service

    def check_answer(
        self,
        flashcard: Flashcard,
        user_answer: str,
    ) -> tuple[bool, str]:
        """
        So sánh câu trả lời của người dùng với Definition.

        Quy tắc hiện tại:
        - bỏ khoảng trắng thừa;
        - không phân biệt hoa/thường;
        - chuẩn hóa Unicode;
        - bỏ dấu câu nhẹ ở đầu/cuối;
        - Definition có thể chứa nhiều đáp án ngăn bởi dấu phẩy,
          chấm phẩy, |, / hoặc xuống dòng.

        Trả về (is_correct, canonical_answer).
        """
        answer = user_answer.strip()
        if not answer:
            raise ValueError("Hãy nhập câu trả lời trước khi kiểm tra.")

        accepted_answers = self._split_accepted_answers(
            flashcard.definition
        )

        normalized_user = self._normalize(answer)
        is_correct = any(
            normalized_user == self._normalize(candidate)
            for candidate in accepted_answers
        )

        return is_correct, flashcard.definition.strip()

    def submit_answer(
        self,
        flashcard: Flashcard,
        user_answer: str,
    ) -> tuple[bool, str]:
        """Kiểm tra đáp án và ghi kết quả vào StudyProgress."""
        if flashcard.id is None:
            raise ValueError("Flashcard chưa có ID hợp lệ.")

        is_correct, canonical_answer = self.check_answer(
            flashcard,
            user_answer,
        )

        self.study_progress_service.record_answer(
            flashcard.id,
            correct=is_correct,
        )

        return is_correct, canonical_answer

    @staticmethod
    def _split_accepted_answers(definition: str) -> list[str]:
        parts = re.split(r"[,;|/\n]+", definition)
        answers = [part.strip() for part in parts if part.strip()]
        return answers or [definition.strip()]

    @staticmethod
    def _normalize(value: str) -> str:
        value = unicodedata.normalize("NFKC", value)
        value = value.casefold().strip()
        value = re.sub(r"\s+", " ", value)
        value = value.strip(".,;:!?。！？")
        return value
