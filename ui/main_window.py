from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
    QMessageBox
)

from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService

from ui.widgets.sidebar import Sidebar

from ui.pages.home_page import HomePage
from ui.pages.create_page import CreatePage
from ui.pages.flashcard_page import FlashcardPage
from ui.pages.edit_study_set_page import EditStudySetPage


class MainWindow(QMainWindow):
    """
    Cửa sổ chính của ứng dụng QuizLearn.

    MainWindow chịu trách nhiệm:

    - chứa Sidebar;
    - chứa các Page;
    - chuyển trang;
    - kết nối Signal giữa các Page;
    - điều phối dữ liệu giữa các trang.
    """

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        study_set_service: StudySetService,
        flashcard_service: FlashcardService,
        parent=None
    ):
        super().__init__(parent)

        # ----------------------------------------------------
        # SERVICES
        # ----------------------------------------------------

        self.study_set_service = (
            study_set_service
        )

        self.flashcard_service = (
            flashcard_service
        )

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.setWindowTitle(
            "QuizLearn"
        )

        self.resize(
            1200,
            760
        )

        self.setMinimumSize(
            900,
            600
        )

        # ----------------------------------------------------
        # SETUP
        # ----------------------------------------------------

        self._setup_ui()

        self._connect_signals()

        # ----------------------------------------------------
        # DEFAULT PAGE
        # ----------------------------------------------------

        self.show_home_page()

    # ========================================================
    # SETUP UI
    # ========================================================

    def _setup_ui(
        self
    ) -> None:

        # ====================================================
        # CENTRAL WIDGET
        # ====================================================

        central_widget = QWidget()

        central_widget.setObjectName(
            "CentralWidget"
        )

        self.setCentralWidget(
            central_widget
        )

        # ====================================================
        # MAIN LAYOUT
        # ====================================================

        main_layout = QHBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            0
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar = Sidebar()

        main_layout.addWidget(
            self.sidebar
        )

        # ====================================================
        # PAGE STACK
        # ====================================================

        self.pages = QStackedWidget()

        self.pages.setObjectName(
            "PageStack"
        )

        main_layout.addWidget(
            self.pages,
            1
        )

        # ====================================================
        # HOME PAGE
        # ====================================================

        self.home_page = HomePage(
            study_set_service=(
                self.study_set_service
            )
        )

        self.pages.addWidget(
            self.home_page
        )

        # ====================================================
        # CREATE PAGE
        # ====================================================

        self.create_page = CreatePage(
            study_set_service=(
                self.study_set_service
            ),
            flashcard_service=(
                self.flashcard_service
            )
        )

        self.pages.addWidget(
            self.create_page
        )

        # ====================================================
        # EDIT STUDY SET PAGE
        # ====================================================

        self.edit_study_set_page = (
            EditStudySetPage(
                study_set_service=(
                    self.study_set_service
                ),
                flashcard_service=(
                    self.flashcard_service
                )
            )
        )

        self.pages.addWidget(
            self.edit_study_set_page
        )

        # ====================================================
        # FLASHCARD PAGE
        # ====================================================

        self.flashcard_page = FlashcardPage(
            study_set_service=(
                self.study_set_service
            ),
            flashcard_service=(
                self.flashcard_service
            )
        )

        self.pages.addWidget(
            self.flashcard_page
        )

    # ========================================================
    # CONNECT SIGNALS
    # ========================================================

    def _connect_signals(
        self
    ) -> None:

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar.home_clicked.connect(
            self.show_home_page
        )

        self.sidebar.library_clicked.connect(
            self.show_home_page
        )

        self.sidebar.create_clicked.connect(
            self.show_create_page
        )

        self.sidebar.flashcards_clicked.connect(
            self.show_flashcard_page
        )

        # ====================================================
        # HOME PAGE
        # ====================================================

        self.home_page.create_requested.connect(
            self.show_create_page
        )

        self.home_page.study_set_opened.connect(
            self.open_study_set
        )

        self.home_page.study_set_edit_requested.connect(
            self.open_edit_study_set
        )

        # ====================================================
        # CREATE PAGE
        # ====================================================

        self.create_page.cancel_requested.connect(
            self.show_home_page
        )

        self.create_page.study_set_created.connect(
            self._on_study_set_created
        )

        # ====================================================
        # EDIT STUDY SET PAGE
        # ====================================================

        self.edit_study_set_page.cancel_requested.connect(
            self._cancel_edit
        )

        self.edit_study_set_page.saved.connect(
            self._on_study_set_updated
        )

        # ====================================================
        # FLASHCARD PAGE
        # ====================================================

        self.flashcard_page.back_requested.connect(
            self.show_home_page
        )

    # ========================================================
    # SHOW HOME
    # ========================================================

    def show_home_page(
        self
    ) -> None:
        """
        Hiển thị trang Home.
        """

        try:

            self.home_page.refresh()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                (
                    "Không thể tải danh sách "
                    f"Study Set.\n\n{error}"
                )
            )

        self.pages.setCurrentWidget(
            self.home_page
        )

        self.sidebar.set_active(
            "home"
        )

    # ========================================================
    # SHOW CREATE PAGE
    # ========================================================

    def show_create_page(
        self
    ) -> None:
        """
        Hiển thị trang tạo Study Set.
        """

        self.pages.setCurrentWidget(
            self.create_page
        )

        self.sidebar.set_active(
            "create"
        )

        self.create_page.title_input.setFocus()

    # ========================================================
    # SHOW FLASHCARD PAGE
    # ========================================================

    def show_flashcard_page(
        self
    ) -> None:
        """
        Mở FlashcardPage.

        Nếu đã có StudySet đang học:
            mở lại StudySet đó.

        Nếu chưa có:
            mở StudySet đầu tiên.

        Nếu chưa có StudySet nào:
            chuyển sang Create.
        """

        # ----------------------------------------------------
        # ĐÃ CÓ STUDY SET ĐANG HỌC
        # ----------------------------------------------------

        if (
            self.flashcard_page.current_set_id
            is not None
        ):

            try:

                self.flashcard_page.refresh()

            except Exception as error:

                QMessageBox.warning(
                    self,
                    "Flashcards",
                    str(error)
                )

                return

            self.pages.setCurrentWidget(
                self.flashcard_page
            )

            self.sidebar.set_active(
                "flashcards"
            )

            self.flashcard_page.setFocus()

            return

        # ----------------------------------------------------
        # CHƯA CÓ STUDY SET ĐANG HỌC
        # ----------------------------------------------------

        try:

            study_sets = (
                self.study_set_service
                .get_all_study_sets()
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Database Error",
                str(error)
            )

            return

        # ----------------------------------------------------
        # DATABASE CHƯA CÓ STUDY SET
        # ----------------------------------------------------

        if not study_sets:

            QMessageBox.information(
                self,
                "Flashcards",
                (
                    "Bạn chưa có Study Set nào.\n"
                    "Hãy tạo một bộ học trước."
                )
            )

            self.show_create_page()

            return

        # ----------------------------------------------------
        # MỞ STUDY SET ĐẦU TIÊN
        # ----------------------------------------------------

        self.open_study_set(
            study_sets[0].id
        )

    # ========================================================
    # OPEN STUDY SET
    # ========================================================

    def open_study_set(
        self,
        set_id: int
    ) -> None:
        """
        Mở StudySet trong FlashcardPage.
        """

        try:

            self.flashcard_page.load_study_set(
                set_id
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Flashcards",
                (
                    "Không thể mở Study Set.\n\n"
                    f"{error}"
                )
            )

            return

        self.pages.setCurrentWidget(
            self.flashcard_page
        )

        self.sidebar.set_active(
            "flashcards"
        )

        self.flashcard_page.setFocus()

    # ========================================================
    # OPEN EDIT STUDY SET
    # ========================================================

    def open_edit_study_set(
        self,
        set_id: int
    ) -> None:
        """
        Mở trang chỉnh sửa Study Set.

        Trang Edit có thể sửa:
        - Title
        - Description
        - Term
        - Definition
        - thêm Flashcard
        - xóa Flashcard
        """

        try:

            self.edit_study_set_page.load_study_set(
                set_id
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Edit Study Set",
                (
                    "Không thể mở Study Set "
                    "để chỉnh sửa.\n\n"
                    f"{error}"
                )
            )

            return

        self.pages.setCurrentWidget(
            self.edit_study_set_page
        )

        # Edit đang thuộc khu vực Library/Home
        self.sidebar.set_active(
            "home"
        )

        self.edit_study_set_page.title_input.setFocus()

    # ========================================================
    # CREATE SUCCESS
    # ========================================================

    def _on_study_set_created(
        self,
        set_id: int
    ) -> None:
        """
        Sau khi tạo StudySet:

        1. refresh Home;
        2. mở ngay StudySet vừa tạo.
        """

        try:

            self.home_page.refresh()

        except Exception:
            pass

        self.open_study_set(
            set_id
        )

    # ========================================================
    # EDIT SUCCESS
    # ========================================================

    def _on_study_set_updated(
        self,
        set_id: int
    ) -> None:
        """
        Sau khi sửa StudySet:

        - refresh Home;
        - refresh FlashcardPage;
        - đảm bảo các card vừa sửa được load lại;
        - quay về Home.
        """

        # ----------------------------------------------------
        # REFRESH HOME
        # ----------------------------------------------------

        try:

            self.home_page.refresh()

        except Exception as error:

            print(
                "[WARNING] "
                "Không thể refresh Home:",
                error
            )

        # ----------------------------------------------------
        # REFRESH FLASHCARD PAGE
        # ----------------------------------------------------

        if (
            self.flashcard_page.current_set_id
            == set_id
        ):

            try:

                self.flashcard_page.load_study_set(
                    set_id
                )

            except Exception as error:

                print(
                    "[WARNING] "
                    "Không thể refresh FlashcardPage:",
                    error
                )

        # ----------------------------------------------------
        # HOME
        # ----------------------------------------------------

        self.show_home_page()

    # ========================================================
    # CANCEL EDIT
    # ========================================================

    def _cancel_edit(
        self
    ) -> None:
        """
        Hủy chỉnh sửa.

        Vì EditStudySetPage chỉ ghi database khi Save,
        nên Cancel chỉ cần quay về Home.
        """

        self.show_home_page()