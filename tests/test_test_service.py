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
from services.test_service import (
    QUESTION_MULTIPLE_CHOICE,
    QUESTION_WRITTEN,
    TestQuestion,
    TestService,
)


class TestServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db = Database(Path(self.temp_dir.name) / "test.db")
        create_tables(db)
        self.study_set_repo = StudySetRepository(db)
        self.flashcard_repo = FlashcardRepository(db)
        self.progress_repo = StudyProgressRepository(db)
        self.study_set_service = StudySetService(self.study_set_repo, self.flashcard_repo)
        self.progress_service = StudyProgressService(self.progress_repo, self.flashcard_repo, self.study_set_repo)
        self.learning_service = LearningService(self.progress_service)
        self.test_service = TestService(self.learning_service, self.progress_service)

        study_set = self.study_set_service.create_study_set("TOEIC", "Test")
        self.cards = [
            self.flashcard_repo.create(Flashcard(None, study_set.id, "purchase", "mua")),
            self.flashcard_repo.create(Flashcard(None, study_set.id, "equipment", "thiết bị")),
            self.flashcard_repo.create(Flashcard(None, study_set.id, "available", "có sẵn")),
            self.flashcard_repo.create(Flashcard(None, study_set.id, "contract", "hợp đồng")),
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_test_contains_mcq_and_written(self):
        questions = self.test_service.build_test(self.cards)
        self.assertEqual(len(questions), 4)
        types = {q.question_type for q in questions}
        self.assertIn(QUESTION_MULTIPLE_CHOICE, types)
        self.assertIn(QUESTION_WRITTEN, types)

    def test_multiple_choice_has_correct_answer(self):
        questions = self.test_service.build_test(self.cards)
        mcq = next(q for q in questions if q.question_type == QUESTION_MULTIPLE_CHOICE)
        self.assertIn(mcq.correct_answer, mcq.options)
        self.assertLessEqual(len(mcq.options), 4)

    def test_grade_multiple_choice_records_progress(self):
        card = self.cards[0]
        q = TestQuestion(card, QUESTION_MULTIPLE_CHOICE, "term_to_definition", card.term, card.definition, [card.definition])
        self.assertTrue(self.test_service.grade_multiple_choice(q, card.definition))
        progress = self.progress_repo.get_by_flashcard_id(card.id)
        self.assertEqual(progress.correct_count, 1)
        self.assertEqual(progress.review_count, 1)

    def test_grade_written_reuses_learning_typo_support(self):
        card = self.cards[0]
        q = TestQuestion(card, QUESTION_WRITTEN, "definition_to_term", card.definition, card.term, [])
        correct, expected, typo = self.test_service.grade_written(q, "purchse")
        self.assertTrue(correct)
        self.assertEqual(expected, "purchase")
        self.assertTrue(typo)


if __name__ == "__main__":
    unittest.main()
