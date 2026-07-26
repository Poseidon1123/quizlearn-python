import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database.database import Database
from database.schema import create_tables
from models.flashcard import Flashcard
from repositories.flashcard_repository import FlashcardRepository
from repositories.study_set_repository import StudySetRepository
from services.study_set_service import StudySetService


class StudySetTransactionTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test.db"

        self.database = Database(database_path)
        create_tables(self.database)

        self.study_set_repository = StudySetRepository(
            self.database
        )
        self.flashcard_repository = FlashcardRepository(
            self.database
        )

        self.service = StudySetService(
            self.study_set_repository,
            self.flashcard_repository
        )

        self.study_set = self.service.create_study_set(
            "Original title",
            "Original description"
        )

        self.card_1 = self.flashcard_repository.create(
            Flashcard(
                id=None,
                set_id=self.study_set.id,
                term="purchase",
                definition="mua"
            )
        )

        self.card_2 = self.flashcard_repository.create(
            Flashcard(
                id=None,
                set_id=self.study_set.id,
                term="equipment",
                definition="thiết bị"
            )
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # ========================================================
    # CREATE TRANSACTION
    # ========================================================

    def test_create_study_set_with_flashcards_commits_all_changes(self) -> None:
        created = self.service.create_study_set_with_flashcards(
            title="TOEIC Vocabulary",
            description="Vocabulary set",
            cards=[
                ("available", "có sẵn"),
                ("contract", "hợp đồng"),
                ("", ""),
            ]
        )

        self.assertIsNotNone(created.id)
        self.assertEqual(
            created.title,
            "TOEIC Vocabulary"
        )

        cards = self.flashcard_repository.get_by_set_id(
            created.id
        )

        self.assertEqual(
            len(cards),
            2
        )

        card_values = {
            card.term: card.definition
            for card in cards
        }

        self.assertEqual(
            card_values["available"],
            "có sẵn"
        )
        self.assertEqual(
            card_values["contract"],
            "hợp đồng"
        )

    def test_create_rolls_back_study_set_when_flashcard_insert_fails(self) -> None:
        set_count_before = self.study_set_repository.count()
        original_create = self.flashcard_repository.create
        call_count = 0

        def failing_create(flashcard: Flashcard):
            nonlocal call_count
            call_count += 1

            if call_count == 2:
                raise RuntimeError(
                    "Simulated flashcard insert failure"
                )

            return original_create(flashcard)

        with patch.object(
            self.flashcard_repository,
            "create",
            side_effect=failing_create,
        ):
            with self.assertRaises(RuntimeError):
                self.service.create_study_set_with_flashcards(
                    title="Must rollback",
                    description="Must rollback too",
                    cards=[
                        ("first", "one"),
                        ("second", "two"),
                    ]
                )

        self.assertEqual(
            self.study_set_repository.count(),
            set_count_before
        )

        matches = self.study_set_repository.search_by_title(
            "Must rollback"
        )

        self.assertEqual(
            matches,
            []
        )

    # ========================================================
    # UPDATE TRANSACTION
    # ========================================================

    def test_save_study_set_with_flashcards_commits_all_changes(self) -> None:
        updated = self.service.save_study_set_with_flashcards(
            set_id=self.study_set.id,
            title="Updated title",
            description="Updated description",
            cards=[
                (
                    self.card_1.id,
                    "purchase",
                    "mua, mua sắm"
                ),
                (
                    None,
                    "available",
                    "có sẵn"
                )
            ],
            deleted_card_ids={self.card_2.id}
        )

        self.assertEqual(
            updated.title,
            "Updated title"
        )

        cards = self.flashcard_repository.get_by_set_id(
            self.study_set.id
        )

        self.assertEqual(
            len(cards),
            2
        )

        card_values = {
            card.term: card.definition
            for card in cards
        }

        self.assertEqual(
            card_values["purchase"],
            "mua, mua sắm"
        )
        self.assertEqual(
            card_values["available"],
            "có sẵn"
        )

    def test_save_rolls_back_everything_when_one_operation_fails(self) -> None:
        invalid_card_id = 999999

        with self.assertRaises(ValueError):
            self.service.save_study_set_with_flashcards(
                set_id=self.study_set.id,
                title="This title must rollback",
                description="This description must rollback",
                cards=[
                    (
                        self.card_1.id,
                        "purchase changed",
                        "changed definition"
                    ),
                    (
                        invalid_card_id,
                        "ghost",
                        "ghost definition"
                    ),
                    (
                        self.card_2.id,
                        "equipment",
                        "thiết bị"
                    )
                ]
            )

        study_set_after_error = self.study_set_repository.get_by_id(
            self.study_set.id
        )
        card_after_error = self.flashcard_repository.get_by_id(
            self.card_1.id
        )

        self.assertEqual(
            study_set_after_error.title,
            "Original title"
        )
        self.assertEqual(
            study_set_after_error.description,
            "Original description"
        )
        self.assertEqual(
            card_after_error.term,
            "purchase"
        )
        self.assertEqual(
            card_after_error.definition,
            "mua"
        )


if __name__ == "__main__":
    unittest.main()
