from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
    QMessageBox,
)

from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService
from services.study_progress_service import StudyProgressService
from services.learning_service import LearningService
from services.test_service import TestService
from services.pronunciation_service import PronunciationService

from ui.widgets.sidebar import Sidebar
from ui.pages.home_page import HomePage
from ui.pages.create_page import CreatePage
from ui.pages.edit_study_set_page import EditStudySetPage
from ui.pages.study_set_detail_page import StudySetDetailPage
from ui.pages.flashcard_page import FlashcardPage
from ui.pages.learn_page import LearnPage
from ui.pages.test_page import TestPage


class MainWindow(QMainWindow):
    """Cửa sổ chính của QuizLearn và router giữa các page."""

    def __init__(
        self,
        study_set_service: StudySetService,
        flashcard_service: FlashcardService,
        study_progress_service: StudyProgressService,
        learning_service: LearningService,
        test_service: TestService,
        pronunciation_service: PronunciationService,
        parent=None,
    ):
        super().__init__(parent)

        self.study_set_service = study_set_service
        self.flashcard_service = flashcard_service
        self.study_progress_service = study_progress_service
        self.learning_service = learning_service
        self.test_service = test_service
        self.pronunciation_service = pronunciation_service

        self.setWindowTitle("QuizLearn")
        self.resize(1200, 760)
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._connect_signals()
        self.show_home_page()

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        self.pages.setObjectName("PageStack")
        main_layout.addWidget(self.pages, 1)

        self.home_page = HomePage(self.study_set_service)
        self.pages.addWidget(self.home_page)

        self.create_page = CreatePage(
            self.study_set_service,
            self.flashcard_service,
        )
        self.pages.addWidget(self.create_page)

        self.study_set_detail_page = StudySetDetailPage(
            self.study_set_service,
            self.flashcard_service,
            self.study_progress_service,
        )
        self.pages.addWidget(self.study_set_detail_page)

        self.edit_study_set_page = EditStudySetPage(
            self.study_set_service,
            self.flashcard_service,
        )
        self.pages.addWidget(self.edit_study_set_page)

        self.flashcard_page = FlashcardPage(
            self.study_set_service,
            self.flashcard_service,
            self.study_progress_service,
            self.pronunciation_service,
        )
        self.pages.addWidget(self.flashcard_page)

        self.learn_page = LearnPage(
            self.study_set_service,
            self.flashcard_service,
            self.learning_service,
            self.pronunciation_service,
        )
        self.pages.addWidget(self.learn_page)

        self.test_page = TestPage(
            self.study_set_service,
            self.flashcard_service,
            self.test_service,
            self.pronunciation_service,
        )
        self.pages.addWidget(self.test_page)

    def _connect_signals(self) -> None:
        self.sidebar.home_clicked.connect(self.show_home_page)
        self.sidebar.create_clicked.connect(self.show_create_page)
        self.home_page.create_requested.connect(self.show_create_page)
        self.home_page.study_set_opened.connect(self.open_study_set_detail)
        self.home_page.study_set_edit_requested.connect(self.open_edit_study_set)
        self.create_page.cancel_requested.connect(self.show_home_page)
        self.create_page.study_set_created.connect(self._on_study_set_created)
        self.study_set_detail_page.back_requested.connect(self.show_home_page)
        self.study_set_detail_page.flashcards_requested.connect(self.open_flashcards)
        self.study_set_detail_page.learn_requested.connect(self.open_learn_mode)
        self.study_set_detail_page.test_requested.connect(self.open_test_mode)
        self.study_set_detail_page.edit_requested.connect(self.open_edit_study_set)
        self.edit_study_set_page.cancel_requested.connect(self._cancel_edit)
        self.edit_study_set_page.saved.connect(self._on_study_set_updated)
        self.flashcard_page.back_requested.connect(self._back_from_flashcards)
        self.learn_page.back_requested.connect(self._back_from_learn)
        self.test_page.back_requested.connect(self._back_from_test)

        self.pronunciation_service.finished.connect(
            self.pronunciation_service.play_downloaded_file
        )
        self.pronunciation_service.failed.connect(
            self._show_pronunciation_error
        )

    def _show_pronunciation_error(self, message: str) -> None:
        QMessageBox.warning(self, "Pronunciation", message)

    def show_home_page(self) -> None:
        self.home_page.refresh()
        self.pages.setCurrentWidget(self.home_page)
        self.sidebar.set_active("home")

    def show_create_page(self) -> None:
        self.pages.setCurrentWidget(self.create_page)
        self.sidebar.set_active("create")
        self.create_page.title_input.setFocus()

    def open_study_set_detail(self, set_id: int) -> None:
        if self.study_set_detail_page.load_study_set(set_id):
            self.pages.setCurrentWidget(self.study_set_detail_page)
            self.sidebar.set_active(None)

    def open_flashcards(self, set_id: int) -> None:
        self.flashcard_page.load_study_set(set_id)
        if self.flashcard_page.current_set_id == set_id:
            self.pages.setCurrentWidget(self.flashcard_page)
            self.sidebar.set_active(None)
            self.flashcard_page.setFocus()

    def _back_from_flashcards(self) -> None:
        self._return_to_detail(self.flashcard_page.current_set_id)

    def open_learn_mode(self, set_id: int) -> None:
        if self.learn_page.load_study_set(set_id):
            self.pages.setCurrentWidget(self.learn_page)
            self.sidebar.set_active(None)
            self.learn_page.answer_input.setFocus()

    def _back_from_learn(self) -> None:
        self._return_to_detail(self.learn_page.current_set_id)

    def open_test_mode(self, set_id: int) -> None:
        if self.test_page.load_study_set(set_id):
            self.pages.setCurrentWidget(self.test_page)
            self.sidebar.set_active(None)

    def _back_from_test(self) -> None:
        self._return_to_detail(self.test_page.current_set_id)

    def _return_to_detail(self, set_id: int | None) -> None:
        if set_id is None:
            self.show_home_page()
        else:
            self.open_study_set_detail(set_id)

    def open_edit_study_set(self, set_id: int) -> None:
        self.edit_study_set_page.load_study_set(set_id)
        if self.edit_study_set_page.current_set_id == set_id:
            self.pages.setCurrentWidget(self.edit_study_set_page)
            self.sidebar.set_active(None)
            self.edit_study_set_page.title_input.setFocus()

    def _cancel_edit(self) -> None:
        self._return_to_detail(self.edit_study_set_page.current_set_id)

    def _on_study_set_created(self, set_id: int) -> None:
        self.home_page.refresh()
        self.open_study_set_detail(set_id)

    def _on_study_set_updated(self, set_id: int) -> None:
        self.home_page.refresh()
        if self.flashcard_page.current_set_id == set_id:
            self.flashcard_page.load_study_set(set_id)
        self.open_study_set_detail(set_id)
