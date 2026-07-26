import re
import unicodedata
from dataclasses import dataclass

from models.flashcard import Flashcard
from services.study_progress_service import StudyProgressService


DIRECTION_TERM_TO_DEFINITION = "term_to_definition"
DIRECTION_DEFINITION_TO_TERM = "definition_to_term"
VALID_LEARNING_DIRECTIONS = {
    DIRECTION_TERM_TO_DEFINITION,
    DIRECTION_DEFINITION_TO_TERM,
}


@dataclass(frozen=True)
class AnswerResult:
    """Kết quả kiểm tra một câu trả lời trong Learn Mode."""

    is_correct: bool
    canonical_answer: str
    accepted_with_typo: bool = False


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
        direction: str = DIRECTION_TERM_TO_DEFINITION,
    ) -> AnswerResult:
        """
        Kiểm tra đáp án theo một trong hai chiều học.

        term_to_definition:
            hiển thị Term, người dùng nhập Definition.

        definition_to_term:
            hiển thị Definition, người dùng nhập Term.

        Hệ thống chuẩn hóa Unicode, hoa/thường, khoảng trắng, dấu câu nhẹ
        và chấp nhận lỗi chính tả nhỏ dựa trên khoảng cách Levenshtein.
        """
        if direction not in VALID_LEARNING_DIRECTIONS:
            raise ValueError("Chiều học không hợp lệ.")

        answer = user_answer.strip()
        if not answer:
            raise ValueError("Hãy nhập câu trả lời trước khi kiểm tra.")

        if direction == DIRECTION_TERM_TO_DEFINITION:
            canonical_answer = flashcard.definition.strip()
        else:
            canonical_answer = flashcard.term.strip()

        accepted_answers = self._split_accepted_answers(
            canonical_answer
        )
        normalized_user = self._normalize(answer)

        # Ưu tiên khớp chính xác sau chuẩn hóa.
        for candidate in accepted_answers:
            if normalized_user == self._normalize(candidate):
                return AnswerResult(
                    is_correct=True,
                    canonical_answer=canonical_answer,
                    accepted_with_typo=False,
                )

        # Sau đó mới thử chấp nhận lỗi chính tả nhẹ.
        for candidate in accepted_answers:
            if self._is_minor_typo(
                normalized_user,
                self._normalize(candidate),
            ):
                return AnswerResult(
                    is_correct=True,
                    canonical_answer=canonical_answer,
                    accepted_with_typo=True,
                )

        return AnswerResult(
            is_correct=False,
            canonical_answer=canonical_answer,
            accepted_with_typo=False,
        )

    def submit_answer(
        self,
        flashcard: Flashcard,
        user_answer: str,
        direction: str = DIRECTION_TERM_TO_DEFINITION,
    ) -> AnswerResult:
        """Kiểm tra đáp án và ghi kết quả vào StudyProgress."""
        if flashcard.id is None:
            raise ValueError("Flashcard chưa có ID hợp lệ.")

        result = self.check_answer(
            flashcard,
            user_answer,
            direction=direction,
        )

        self.study_progress_service.record_answer(
            flashcard.id,
            correct=result.is_correct,
        )

        return result

    @staticmethod
    def get_prompt_and_answer_hint(
        flashcard: Flashcard,
        direction: str,
    ) -> tuple[str, str, str]:
        """Trả về (prompt, displayed_value, input_hint) cho UI."""
        if direction == DIRECTION_TERM_TO_DEFINITION:
            return (
                "What is the definition of:",
                flashcard.term,
                "Nhập Definition...",
            )

        if direction == DIRECTION_DEFINITION_TO_TERM:
            return (
                "What term matches this definition:",
                flashcard.definition,
                "Nhập Term...",
            )

        raise ValueError("Chiều học không hợp lệ.")

    @staticmethod
    def _split_accepted_answers(value: str) -> list[str]:
        parts = re.split(r"[,;|/\n]+", value)
        answers = [part.strip() for part in parts if part.strip()]
        return answers or [value.strip()]

    @staticmethod
    def _normalize(value: str) -> str:
        value = unicodedata.normalize("NFKC", value)
        value = value.casefold().strip()
        value = re.sub(r"\s+", " ", value)
        value = value.strip(".,;:!?。！？")
        return value

    @classmethod
    def _is_minor_typo(
        cls,
        user_value: str,
        expected_value: str,
    ) -> bool:
        """
        Chấp nhận typo nhỏ nhưng tránh làm matcher quá dễ dãi.

        - từ <= 3 ký tự: phải đúng hoàn toàn;
        - 4..7 ký tự: tối đa 1 phép sửa;
        - >= 8 ký tự: tối đa 2 phép sửa và similarity >= 80%.
        """
        if not user_value or not expected_value:
            return False

        max_length = max(
            len(user_value),
            len(expected_value),
        )

        if max_length <= 3:
            return False

        distance = cls._levenshtein_distance(
            user_value,
            expected_value,
        )

        if 4 <= max_length <= 7:
            return distance <= 1

        similarity = 1 - (distance / max_length)
        return distance <= 2 and similarity >= 0.80

    @staticmethod
    def _levenshtein_distance(
        left: str,
        right: str,
    ) -> int:
        """Tính khoảng cách Levenshtein với bộ nhớ O(min(m, n))."""
        if left == right:
            return 0

        if not left:
            return len(right)
        if not right:
            return len(left)

        if len(left) < len(right):
            left, right = right, left

        previous = list(range(len(right) + 1))

        for i, left_char in enumerate(left, start=1):
            current = [i]

            for j, right_char in enumerate(right, start=1):
                insert_cost = current[j - 1] + 1
                delete_cost = previous[j] + 1
                replace_cost = previous[j - 1] + (
                    0 if left_char == right_char else 1
                )

                current.append(
                    min(
                        insert_cost,
                        delete_cost,
                        replace_cost,
                    )
                )

            previous = current

        return previous[-1]
