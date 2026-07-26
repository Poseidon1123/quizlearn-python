import random
from dataclasses import dataclass

from models.flashcard import Flashcard
from services.learning_service import (
    DIRECTION_DEFINITION_TO_TERM,
    DIRECTION_TERM_TO_DEFINITION,
    LearningService,
)
from services.study_progress_service import StudyProgressService


QUESTION_MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
QUESTION_WRITTEN = "WRITTEN"


@dataclass
class TestQuestion:
    """Một câu hỏi trong Test Mode."""

    flashcard: Flashcard
    question_type: str
    direction: str
    prompt: str
    correct_answer: str
    options: list[str]


class TestService:
    """Tạo và chấm Test Mode, đồng thời ghi kết quả vào StudyProgress."""

    def __init__(
        self,
        learning_service: LearningService,
        study_progress_service: StudyProgressService,
    ):
        self.learning_service = learning_service
        self.study_progress_service = study_progress_service

    def build_test(
        self,
        cards: list[Flashcard],
        *,
        max_questions: int | None = None,
    ) -> list[TestQuestion]:
        if not cards:
            return []

        selected = list(cards)
        random.shuffle(selected)

        if max_questions is not None:
            if max_questions <= 0:
                raise ValueError("Số câu hỏi phải lớn hơn 0.")
            selected = selected[:max_questions]

        questions: list[TestQuestion] = []
        can_build_mcq = len(cards) >= 2

        for index, card in enumerate(selected):
            direction = random.choice(
                [
                    DIRECTION_TERM_TO_DEFINITION,
                    DIRECTION_DEFINITION_TO_TERM,
                ]
            )

            question_type = (
                QUESTION_MULTIPLE_CHOICE
                if can_build_mcq and index % 2 == 0
                else QUESTION_WRITTEN
            )

            questions.append(
                self._build_question(
                    card=card,
                    all_cards=cards,
                    question_type=question_type,
                    direction=direction,
                )
            )

        random.shuffle(questions)
        return questions

    def grade_multiple_choice(
        self,
        question: TestQuestion,
        selected_answer: str,
    ) -> bool:
        if question.question_type != QUESTION_MULTIPLE_CHOICE:
            raise ValueError("Đây không phải câu hỏi trắc nghiệm.")
        if not selected_answer.strip():
            raise ValueError("Hãy chọn một đáp án.")

        correct = selected_answer == question.correct_answer
        self._record(question.flashcard, correct)
        return correct

    def grade_written(
        self,
        question: TestQuestion,
        user_answer: str,
    ) -> tuple[bool, str, bool]:
        if question.question_type != QUESTION_WRITTEN:
            raise ValueError("Đây không phải câu hỏi tự nhập.")

        result = self.learning_service.check_answer(
            question.flashcard,
            user_answer,
            direction=question.direction,
        )
        self._record(question.flashcard, result.is_correct)

        return (
            result.is_correct,
            result.canonical_answer,
            result.accepted_with_typo,
        )

    def _build_question(
        self,
        *,
        card: Flashcard,
        all_cards: list[Flashcard],
        question_type: str,
        direction: str,
    ) -> TestQuestion:
        if direction == DIRECTION_TERM_TO_DEFINITION:
            prompt = card.term
            correct_answer = card.definition.strip()
        else:
            prompt = card.definition
            correct_answer = card.term.strip()

        options: list[str] = []
        if question_type == QUESTION_MULTIPLE_CHOICE:
            distractors = []
            for other in all_cards:
                if other.id == card.id:
                    continue

                value = (
                    other.definition.strip()
                    if direction == DIRECTION_TERM_TO_DEFINITION
                    else other.term.strip()
                )
                if value and value != correct_answer and value not in distractors:
                    distractors.append(value)

            random.shuffle(distractors)
            options = [correct_answer, *distractors[:3]]
            random.shuffle(options)

        return TestQuestion(
            flashcard=card,
            question_type=question_type,
            direction=direction,
            prompt=prompt,
            correct_answer=correct_answer,
            options=options,
        )

    def _record(self, flashcard: Flashcard, correct: bool) -> None:
        if flashcard.id is None:
            raise ValueError("Flashcard chưa có ID hợp lệ.")

        self.study_progress_service.record_answer(
            flashcard.id,
            correct=correct,
        )
