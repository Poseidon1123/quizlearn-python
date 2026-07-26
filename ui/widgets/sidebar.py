from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)


class Sidebar(QWidget):
    """Thanh điều hướng chính của ứng dụng."""

    home_clicked = Signal()
    create_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Sidebar")
        self.setFixedWidth(220)

        self._setup_ui()

    # ========================================================
    # UI
    # ========================================================

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(10)

        title = QLabel("QuizLearn")
        title.setObjectName("SidebarTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        self.home_button = self._create_button("Home")
        self.home_button.clicked.connect(
            self.home_clicked.emit
        )
        layout.addWidget(self.home_button)

        self.create_button = self._create_button("Create")
        self.create_button.clicked.connect(
            self.create_clicked.emit
        )
        layout.addWidget(self.create_button)

        layout.addStretch()

    def _create_button(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("SidebarButton")
        button.setMinimumHeight(44)
        button.setCursor(Qt.PointingHandCursor)
        button.setCheckable(True)
        return button

    # ========================================================
    # ACTIVE STATE
    # ========================================================

    def set_active(self, page_name: str | None) -> None:
        """
        Đánh dấu mục điều hướng cấp cao đang mở.

        Các trang con như StudySetDetail / Edit / Flashcards có thể truyền
        ``None`` để không làm người dùng hiểu nhầm rằng đang ở Home/Create.
        """
        buttons = {
            "home": self.home_button,
            "create": self.create_button,
        }

        for name, button in buttons.items():
            button.setChecked(
                name == page_name
            )
