import tempfile
import unittest
from pathlib import Path

from database.database import Database
from database.schema import create_tables
from models.flashcard import Flashcard
from repositories.flashcard_repository import FlashcardRepository
from repositories.study_progress_repository import StudyProgressRepository
from repositories.study_set_repository import StudySetRepository
from services.study_progress_service import StudyProgressService
from services.study_set_service import StudySetService


class StudyProgressTest(unittest.TestCase):

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

        self.study_set = self.study_set_service.create_study_set(
            "TOEIC",
            "Vocabulary",
        )
        self.card = self.flashcard_repository.create(
            Flashcard(
                id=None,
                set_id=self.study_set.id,
                term="purchase",
                definition="mua",
            )
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_summary_counts_missing_progress_as_new(self) -> None:
        summary = self.progress_service.get_summary_for_set(
            self.study_set.id
        )

        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["new"], 1)
        self.assertEqual(summary["learning"], 0)
        self.assertEqual(summary["mastered"], 0)
        self.assertEqual(summary["mastered_percent"], 0.0)

    def test_get_or_create_is_idempotent(self) -> None:
        first = self.progress_service.get_or_create_for_flashcard(
            self.card.id
        )
        second = self.progress_service.get_or_create_for_flashcard(
            self.card.id
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.flashcard_id, self.card.id)

    def test_record_answer_updates_counts_and_status(self) -> None:
        progress = self.progress_service.record_answer(
            self.card.id,
            correct=False,
        )

        self.assertEqual(progress.review_count, 1)
        self.assertEqual(progress.correct_count, 0)
        self.assertEqual(progress.wrong_count, 1)
        self.assertEqual(progress.status, "LEARNING")
        self.assertIsNotNone(progress.last_review)

    def test_progress_is_deleted_with_flashcard(self) -> None:
        self.progress_service.get_or_create_for_flashcard(
            self.card.id
        )

        self.flashcard_repository.delete(self.card.id)

        progress = self.progress_repository.get_by_flashcard_id(
            self.card.id
        )
        self.assertIsNone(progress)


if __name__ == "__main__":
    unittest.main()
