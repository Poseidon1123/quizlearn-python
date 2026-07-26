import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from database.database import Database
from database.schema import create_tables

from repositories.flashcard_repository import FlashcardRepository
from repositories.study_set_repository import StudySetRepository
from repositories.study_progress_repository import StudyProgressRepository

from services.flashcard_service import FlashcardService
from services.study_set_service import StudySetService
from services.study_progress_service import StudyProgressService
from services.learning_service import LearningService
from services.test_service import TestService

from ui.main_window import MainWindow


BASE_DIR = Path(__file__).resolve().parent


def load_stylesheet(app: QApplication) -> None:
    style_path = BASE_DIR / "styles" / "dark.qss"

    if not style_path.exists():
        print(
            f"[WARNING] Không tìm thấy stylesheet: {style_path}"
        )
        return

    with open(
        style_path,
        "r",
        encoding="utf-8",
    ) as file:
        app.setStyleSheet(file.read())


def create_database() -> Database:
    database_path = BASE_DIR / "data" / "quizlet.db"
    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    database = Database(database_path)
    create_tables(database)
    return database


def create_repositories(
    database: Database,
):
    study_set_repository = StudySetRepository(database)
    flashcard_repository = FlashcardRepository(database)
    study_progress_repository = StudyProgressRepository(database)

    return {
        "study_set": study_set_repository,
        "flashcard": flashcard_repository,
        "study_progress": study_progress_repository,
    }


def create_services(repositories):
    study_set_service = StudySetService(
        repositories["study_set"],
        repositories["flashcard"],
    )

    flashcard_service = FlashcardService(
        repositories["flashcard"],
        repositories["study_set"],
    )

    study_progress_service = StudyProgressService(
        repositories["study_progress"],
        repositories["flashcard"],
        repositories["study_set"],
    )

    learning_service = LearningService(
        study_progress_service
    )

    test_service = TestService(
        learning_service,
        study_progress_service,
    )

    return {
        "study_set": study_set_service,
        "flashcard": flashcard_service,
        "study_progress": study_progress_service,
        "learning": learning_service,
        "test": test_service,
    }


def main() -> int:
    app = QApplication(sys.argv)

    app.setApplicationName("Quizlet Python")
    app.setOrganizationName("QuizletPython")

    load_stylesheet(app)

    database = create_database()
    repositories = create_repositories(database)
    services = create_services(repositories)

    window = MainWindow(
        study_set_service=services["study_set"],
        flashcard_service=services["flashcard"],
        study_progress_service=services["study_progress"],
        learning_service=services["learning"],
        test_service=services["test"],
    )

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
