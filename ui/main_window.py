from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
    QMessageBox,
)

from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService

from ui.widgets.sidebar import Sidebar
from ui.pages.home_page import HomePage
from ui.pages.create_page import CreatePage
from ui.pages.edit_study_set_page import EditStudySetPage
from ui.pages.study_set_detail_page import StudySetDetailPage
from ui.pages.flashcard_page import FlashcardPage


class MainWindow(QMainWindow):
    """
    Cửa sổ chính của QuizLearn.

    MainWindow chỉ điều phối navigation giữa các page. Nghiệp vụ dữ liệu
    được giữ trong Service, còn mỗi Page tự quản lý UI của chính nó.
    """

    def __init__(
        self,
        study_set_service: StudySetService,
        flashcard_service: FlashcardService,
        parent=None,
    ):
        super().__init__(parent)

        self.study_set_service = study_set_service
        self.flashcard_service = flashcard_service

        self.setWindowTitle("QuizLearn")
        self.resize(1200, 760)
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._connect_signals()

        self.show_home_page()

    # ========================================================
    # UI
    # ========================================================

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

        self.home_page = HomePage(
            study_set_service=self.study_set_service
        )
        self.pages.addWidget(self.home_page)

        self.create_page = CreatePage(
            study_set_service=self.study_set_service,
            flashcard_service=self.flashcard_service,
        )
        self.pages.addWidget(self.create_page)

        self.study_set_detail_page = StudySetDetailPage(
            study_set_service=self.study_set_service,
            flashcard_service=self.flashcard_service,
        )
        self.pages.addWidget(self.study_set_detail_page)

        self.edit_study_set_page = EditStudySetPage(
            study_set_service=self.study_set_service,
            flashcard_service=self.flashcard_service,
        )
        self.pages.addWidget(self.edit_study_set_page)

        self.flashcard_page = FlashcardPage(
            study_set_service=self.study_set_service,
            flashcard_service=self.flashcard_service,
        )
        self.pages.addWidget(self.flashcard_page)

    # ========================================================
    # SIGNALS
    # ========================================================

    def _connect_signals(self) -> None:
        # Sidebar - chỉ giữ navigation cấp cao.
        self.sidebar.home_clicked.connect(
            self.show_home_page
        )
        self.sidebar.create_clicked.connect(
            self.show_create_page
        )

        # Home.
        self.home_page.create_requested.connect(
            self.show_create_page
        )
        self.home_page.study_set_opened.connect(
            self.open_study_set_detail
        )
        self.home_page.study_set_edit_requested.connect(
            self.open_edit_study_set
        )

        # Create.
        self.create_page.cancel_requested.connect(
            self.show_home_page
        )
        self.create_page.study_set_created.connect(
            self._on_study_set_created
        )

        # Study Set Detail.
        self.study_set_detail_page.back_requested.connect(
            self.show_home_page
        )
        self.study_set_detail_page.flashcards_requested.connect(
            self.open_flashcards
        )
        self.study_set_detail_page.learn_requested.connect(
            self.open_learn_mode
        )
        self.study_set_detail_page.test_requested.connect(
            self.open_test_mode
        )
        self.study_set_detail_page.edit_requested.connect(
            self.open_edit_study_set
        )

        # Edit.
        self.edit_study_set_page.cancel_requested.connect(
            self._cancel_edit
        )
        self.edit_study_set_page.saved.connect(
            self._on_study_set_updated
        )

        # Flashcards.
        self.flashcard_page.back_requested.connect(
            self._back_from_flashcards
        )

    # ========================================================
    # TOP-LEVEL NAVIGATION
    # ========================================================

    def show_home_page(self) -> None:
        self.home_page.refresh()
        self.pages.setCurrentWidget(
            self.home_page
        )
        self.sidebar.set_active("home")

    def show_create_page(self) -> None:
        self.pages.setCurrentWidget(
            self.create_page
        )
        self.sidebar.set_active("create")
        self.create_page.title_input.setFocus()

    # ========================================================
    # STUDY SET DETAIL
    # ========================================================

    def open_study_set_detail(
        self,
        set_id: int,
    ) -> None:
        """Mở dashboard của một Study Set."""
        loaded = self.study_set_detail_page.load_study_set(
            set_id
        )

        if not loaded:
            return

        self.pages.setCurrentWidget(
            self.study_set_detail_page
        )
        self.sidebar.set_active(None)

    # ========================================================
    # FLASHCARDS
    # ========================================================

    def open_flashcards(
        self,
        set_id: int,
    ) -> None:
        self.flashcard_page.load_study_set(
            set_id
        )

        # FlashcardPage tự hiển thị dialog nếu load thất bại. Chỉ route
        # sau khi current_set_id đã trùng với set được yêu cầu.
        if self.flashcard_page.current_set_id != set_id:
            return

        self.pages.setCurrentWidget(
            self.flashcard_page
        )
        self.sidebar.set_active(None)
        self.flashcard_page.setFocus()

    def _back_from_flashcards(self) -> None:
        set_id = self.flashcard_page.current_set_id

        if set_id is None:
            self.show_home_page()
            return

        self.open_study_set_detail(
            set_id
        )

    # ========================================================
    # EDIT
    # ========================================================

    def open_edit_study_set(
        self,
        set_id: int,
    ) -> None:
        self.edit_study_set_page.load_study_set(
            set_id
        )

        if self.edit_study_set_page.current_set_id != set_id:
            return

        self.pages.setCurrentWidget(
            self.edit_study_set_page
        )
        self.sidebar.set_active(None)
        self.edit_study_set_page.title_input.setFocus()

    def _cancel_edit(self) -> None:
        set_id = self.edit_study_set_page.current_set_id

        if set_id is None:
            self.show_home_page()
            return

        self.open_study_set_detail(
            set_id
        )

    # ========================================================
    # FUTURE STUDY MODES
    # ========================================================

    def open_learn_mode(
        self,
        set_id: int,
    ) -> None:
        QMessageBox.information(
            self,
            "Learn Mode",
            "Learn Mode sẽ được triển khai ở bước tiếp theo.",
        )

    def open_test_mode(
        self,
        set_id: int,
    ) -> None:
        QMessageBox.information(
            self,
            "Test Mode",
            "Test Mode sẽ được triển khai sau Learn Mode.",
        )

    # ========================================================
    # CREATE / UPDATE CALLBACKS
    # ========================================================

    def _on_study_set_created(
        self,
        set_id: int,
    ) -> None:
        """Sau Create, đưa người dùng vào StudySetDetailPage."""
        self.home_page.refresh()
        self.open_study_set_detail(
            set_id
        )

    def _on_study_set_updated(
        self,
        set_id: int,
    ) -> None:
        """Refresh các view liên quan rồi quay về StudySetDetailPage."""
        self.home_page.refresh()

        if self.flashcard_page.current_set_id == set_id:
            self.flashcard_page.load_study_set(
                set_id
            )

        self.open_study_set_detail(
            set_id
        )
