import tempfile
import unittest
from pathlib import Path

from database.database import Database
from database.schema import create_tables
from models.flashcard import Flashcard
from repositories.flashcard_repository import FlashcardRepository
from repositories.study_progress_repository import StudyProgressRepository
from repositories.study_set_repository import StudySetRepository
from services.learning_service import (
    DIRECTION_DEFINITION_TO_TERM,
    DIRECTION_TERM_TO_DEFINITION,
    LearningService,
)
from services.study_progress_service import StudyProgressService
from services.study_set_service import StudySetService


class LearningServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test.db"

        self.database = Database(database_path)
        create_tables(self.database)

        self.study_set_repository = StudySetRepository(self.database)
        self.flashcard_repository = FlashcardRepository(self.database)
        self.progress_repository = StudyProgressRepository(self.database)

        self.study_set_service = StudySetService(
            self.study_set_repository,
            self.flashcard_repository,
        )
        self.progress_service = StudyProgressService(
            self.progress_repository,
            self.flashcard_repository,
            self.study_set_repository,
        )
        self.learning_service = LearningService(
            self.progress_service
        )

        self.study_set = self.study_set_service.create_study_set(
            "TOEIC",
            "Vocabulary",
        )
        self.card = self.flashcard_repository.create(
            Flashcard(
                id=None,
                set_id=self.study_set.id,
                term="purchase",
                definition="mua; mua sắm",
            )
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_term_to_definition_ignores_case_and_spaces(self) -> None:
        result = self.learning_service.check_answer(
            self.card,
            "  MUA  ",
            direction=DIRECTION_TERM_TO_DEFINITION,
        )
        self.assertTrue(result.is_correct)
        self.assertFalse(result.accepted_with_typo)

    def test_term_to_definition_accepts_alternative(self) -> None:
        result = self.learning_service.check_answer(
            self.card,
            "mua sắm",
            direction=DIRECTION_TERM_TO_DEFINITION,
        )
        self.assertTrue(result.is_correct)

    def test_definition_to_term_accepts_term(self) -> None:
        result = self.learning_service.check_answer(
            self.card,
            "PURCHASE",
            direction=DIRECTION_DEFINITION_TO_TERM,
        )
        self.assertTrue(result.is_correct)
        self.assertEqual(result.canonical_answer, "purchase")

    def test_minor_typo_is_accepted_for_long_word(self) -> None:
        result = self.learning_service.check_answer(
            self.card,
            "purchse",
            direction=DIRECTION_DEFINITION_TO_TERM,
        )
        self.assertTrue(result.is_correct)
        self.assertTrue(result.accepted_with_typo)

    def test_short_answer_is_not_fuzzy_matched(self) -> None:
        result = self.learning_service.check_answer(
            self.card,
            "ban",
            direction=DIRECTION_TERM_TO_DEFINITION,
        )
        self.assertFalse(result.is_correct)

    def test_wrong_answer_is_rejected(self) -> None:
        result = self.learning_service.check_answer(
            self.card,
            "sell",
            direction=DIRECTION_DEFINITION_TO_TERM,
        )
        self.assertFalse(result.is_correct)

    def test_empty_answer_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.learning_service.check_answer(
                self.card,
                "   ",
            )

    def test_invalid_direction_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.learning_service.check_answer(
                self.card,
                "mua",
                direction="invalid",
            )

    def test_submit_answer_records_progress(self) -> None:
        result = self.learning_service.submit_answer(
            self.card,
            "mua",
            direction=DIRECTION_TERM_TO_DEFINITION,
        )
        self.assertTrue(result.is_correct)

        progress = self.progress_repository.get_by_flashcard_id(
            self.card.id
        )
        self.assertIsNotNone(progress)
        self.assertEqual(progress.review_count, 1)
        self.assertEqual(progress.correct_count, 1)
        self.assertEqual(progress.wrong_count, 0)


if __name__ == "__main__":
    unittest.main()
