import tempfile
import unittest
from pathlib import Path

from database.database import Database
from database.schema import create_tables
from models.flashcard import Flashcard
from repositories.flashcard_repository import FlashcardRepository
from repositories.study_progress_repository import StudyProgressRepository
from repositories.study_set_repository import StudySetRepository
from services.learning_service import LearningService
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

    def test_check_answer_ignores_case_and_spaces(self) -> None:
        correct, _ = self.learning_service.check_answer(
            self.card,
            "  MUA  ",
        )
        self.assertTrue(correct)

    def test_check_answer_accepts_definition_alternative(self) -> None:
        correct, _ = self.learning_service.check_answer(
            self.card,
            "mua sắm",
        )
        self.assertTrue(correct)

    def test_wrong_answer_is_rejected(self) -> None:
        correct, _ = self.learning_service.check_answer(
            self.card,
            "bán",
        )
        self.assertFalse(correct)

    def test_empty_answer_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.learning_service.check_answer(
                self.card,
                "   ",
            )

    def test_submit_answer_records_progress(self) -> None:
        correct, _ = self.learning_service.submit_answer(
            self.card,
            "mua",
        )
        self.assertTrue(correct)

        progress = self.progress_repository.get_by_flashcard_id(
            self.card.id
        )
        self.assertIsNotNone(progress)
        self.assertEqual(progress.review_count, 1)
        self.assertEqual(progress.correct_count, 1)
        self.assertEqual(progress.wrong_count, 0)


if __name__ == "__main__":
    unittest.main()
