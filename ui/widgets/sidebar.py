from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel
)


class Sidebar(QWidget):
    """
    Thanh điều hướng bên trái của ứng dụng.
    """

    # ========================================================
    # SIGNALS
    # ========================================================

    home_clicked = Signal()
    library_clicked = Signal()
    create_clicked = Signal()
    flashcards_clicked = Signal()

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName(
            "Sidebar"
        )

        self.setFixedWidth(
            220
        )

        self._setup_ui()

    # ========================================================
    # SETUP UI
    # ========================================================

    def _setup_ui(self) -> None:

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            16,
            20,
            16,
            20
        )

        layout.setSpacing(
            10
        )

        # ----------------------------------------------------
        # APP TITLE
        # ----------------------------------------------------

        title = QLabel(
            "QuizLearn"
        )

        title.setObjectName(
            "SidebarTitle"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            title
        )

        layout.addSpacing(
            20
        )

        # ----------------------------------------------------
        # HOME BUTTON
        # ----------------------------------------------------

        self.home_button = self._create_button(
            "Home"
        )

        self.home_button.clicked.connect(
            self.home_clicked.emit
        )

        layout.addWidget(
            self.home_button
        )

        # ----------------------------------------------------
        # LIBRARY BUTTON
        # ----------------------------------------------------

        # ----------------------------------------------------
        # CREATE BUTTON
        # ----------------------------------------------------

        self.create_button = self._create_button(
            "Create"
        )

        self.create_button.clicked.connect(
            self.create_clicked.emit
        )

        layout.addWidget(
            self.create_button
        )

        # ----------------------------------------------------
        # FLASHCARDS BUTTON
        # ----------------------------------------------------

        self.flashcards_button = self._create_button(
            "Flashcards"
        )

        self.flashcards_button.clicked.connect(
            self.flashcards_clicked.emit
        )

        layout.addWidget(
            self.flashcards_button
        )

        layout.addStretch()

    # ========================================================
    # CREATE BUTTON
    # ========================================================

    def _create_button(
        self,
        text: str
    ) -> QPushButton:

        button = QPushButton(
            text
        )

        button.setObjectName(
            "SidebarButton"
        )

        button.setMinimumHeight(
            44
        )

        button.setCursor(
            Qt.PointingHandCursor
        )

        button.setCheckable(
            True
        )

        return button

    # ========================================================
    # SET ACTIVE BUTTON
    # ========================================================

    def set_active(
        self,
        page_name: str
    ) -> None:
        """
        Đánh dấu nút tương ứng với trang đang mở.
        """

        buttons = {
            "home": self.home_button,
            "create": self.create_button,
            "flashcards": self.flashcards_button,
        }

        for name, button in buttons.items():

            button.setChecked(
                name == page_name
            )