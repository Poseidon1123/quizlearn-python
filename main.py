import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from database.database import Database
from database.schema import create_tables

from repositories.flashcard_repository import FlashcardRepository
from repositories.study_set_repository import StudySetRepository

from services.flashcard_service import FlashcardService
from services.study_set_service import StudySetService

from ui.main_window import MainWindow


# ============================================================
# BASE PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# LOAD STYLESHEET
# ============================================================

def load_stylesheet(app: QApplication) -> None:

    style_path = (
        BASE_DIR
        / "styles"
        / "dark.qss"
    )

    if not style_path.exists():

        print(
            f"[WARNING] Không tìm thấy stylesheet: "
            f"{style_path}"
        )

        return

    with open(
        style_path,
        "r",
        encoding="utf-8"
    ) as file:

        app.setStyleSheet(
            file.read()
        )


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database() -> Database:
    """
    Khởi tạo database SQLite và tạo các bảng nếu chưa tồn tại.
    """

    database_path = (
        BASE_DIR
        / "data"
        / "quizlet.db"
    )

    # Đảm bảo thư mục data tồn tại
    database_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    database = Database(
        database_path
    )

    create_tables(
        database
    )

    return database


# ============================================================
# CREATE REPOSITORIES
# ============================================================

def create_repositories(
    database: Database
):

    study_set_repository = (
        StudySetRepository(
            database
        )
    )

    flashcard_repository = (
        FlashcardRepository(
            database
        )
    )

    return {
        "study_set": study_set_repository,
        "flashcard": flashcard_repository,
    }


# ============================================================
# CREATE SERVICES
# ============================================================

def create_services(
    repositories
):

    study_set_service = StudySetService(
        repositories["study_set"]
    )

    flashcard_service = FlashcardService(
        repositories["flashcard"],
        repositories["study_set"]
    )

    return {
        "study_set": study_set_service,
        "flashcard": flashcard_service,
    }


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    # --------------------------------------------------------
    # QApplication
    # --------------------------------------------------------

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Quizlet Python"
    )

    app.setOrganizationName(
        "QuizletPython"
    )

    # --------------------------------------------------------
    # Stylesheet
    # --------------------------------------------------------

    load_stylesheet(
        app
    )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    database = (
        create_database()
    )

    # --------------------------------------------------------
    # Repository
    # --------------------------------------------------------

    repositories = (
        create_repositories(
            database
        )
    )

    # --------------------------------------------------------
    # Services
    # --------------------------------------------------------

    services = (
        create_services(
            repositories
        )
    )

    # --------------------------------------------------------
    # Main Window
    # --------------------------------------------------------

    window = MainWindow(
        study_set_service=services[
            "study_set"
        ],
        flashcard_service=services[
            "flashcard"
        ]
    )

    window.show()

    # --------------------------------------------------------
    # Run app
    # --------------------------------------------------------

    return app.exec()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
