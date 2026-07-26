from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
)

from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService


class StudyModeCard(QFrame):
    """Khối lựa chọn một chế độ học trong StudySetDetailPage."""

    clicked = Signal()

    def __init__(
        self,
        title: str,
        description: str,
        button_text: str,
        enabled: bool = True,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("FlashcardRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(20)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        text_layout.addWidget(title_label)

        description_label = QLabel(description)
        description_label.setObjectName("SecondaryText")
        description_label.setWordWrap(True)
        text_layout.addWidget(description_label)

        layout.addLayout(text_layout, 1)

        self.action_button = QPushButton(button_text)
        self.action_button.setObjectName(
            "PrimaryButton" if enabled else "SecondaryButton"
        )
        self.action_button.setMinimumWidth(150)
        self.action_button.setMinimumHeight(44)
        self.action_button.setCursor(Qt.PointingHandCursor)
        self.action_button.setEnabled(enabled)
        self.action_button.clicked.connect(self.clicked.emit)
        layout.addWidget(self.action_button)


class StudySetDetailPage(QWidget):
    """
    Trang trung gian của một Study Set.

    Đây là nơi người dùng chọn cách học thay vì từ Home nhảy thẳng
    vào FlashcardPage.
    """

    back_requested = Signal()
    flashcards_requested = Signal(int)
    learn_requested = Signal(int)
    test_requested = Signal(int)
    edit_requested = Signal(int)

    def __init__(
        self,
        study_set_service: StudySetService,
        flashcard_service: FlashcardService,
        parent=None,
    ):
        super().__init__(parent)

        self.study_set_service = study_set_service
        self.flashcard_service = flashcard_service
        self.current_set_id: int | None = None

        self._setup_ui()
        self._show_empty_state()

    # ========================================================
    # UI
    # ========================================================

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        header = QHBoxLayout()

        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("SecondaryButton")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_button)

        header.addStretch()

        self.edit_button = QPushButton("Edit Study Set")
        self.edit_button.setObjectName("SecondaryButton")
        self.edit_button.setCursor(Qt.PointingHandCursor)
        self.edit_button.clicked.connect(self._request_edit)
        header.addWidget(self.edit_button)

        layout.addLayout(header)

        self.title_label = QLabel("Study Set")
        self.title_label.setObjectName("PageTitle")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.description_label = QLabel("")
        self.description_label.setObjectName("SecondaryText")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        self.card_count_label = QLabel("0 cards")
        self.card_count_label.setObjectName("SecondaryText")
        layout.addWidget(self.card_count_label)

        layout.addSpacing(10)

        section_title = QLabel("Study modes")
        section_title.setObjectName("SectionTitle")
        layout.addWidget(section_title)

        self.flashcards_mode = StudyModeCard(
            title="Flashcards",
            description=(
                "Ôn từng thẻ bằng cách lật Term và Definition, có thể "
                "shuffle và di chuyển Previous / Next."
            ),
            button_text="Start Flashcards",
        )
        self.flashcards_mode.clicked.connect(
            self._request_flashcards
        )
        layout.addWidget(self.flashcards_mode)

        self.learn_mode = StudyModeCard(
            title="Learn",
            description=(
                "Trả lời câu hỏi và tập trung nhiều hơn vào những thẻ "
                "bạn chưa nhớ tốt."
            ),
            button_text="Coming soon",
            enabled=False,
        )
        self.learn_mode.clicked.connect(self._request_learn)
        layout.addWidget(self.learn_mode)

        self.test_mode = StudyModeCard(
            title="Test",
            description=(
                "Kiểm tra kiến thức bằng câu hỏi trắc nghiệm và câu trả lời "
                "tự nhập."
            ),
            button_text="Coming soon",
            enabled=False,
        )
        self.test_mode.clicked.connect(self._request_test)
        layout.addWidget(self.test_mode)

        layout.addStretch()

    # ========================================================
    # LOAD
    # ========================================================

    def load_study_set(self, set_id: int) -> bool:
        """Load Study Set. Trả về True khi load thành công."""
        try:
            study_set = self.study_set_service.get_study_set(set_id)
            flashcards = self.flashcard_service.get_flashcards_by_set(
                set_id
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Study Set",
                str(error),
            )
            return False
        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                str(error),
            )
            return False

        self.current_set_id = set_id
        self.title_label.setText(study_set.title)

        description = (study_set.description or "").strip()
        self.description_label.setText(description)
        self.description_label.setVisible(bool(description))

        total_cards = len(flashcards)
        self.card_count_label.setText(
            f"{total_cards} card"
            if total_cards == 1
            else f"{total_cards} cards"
        )

        has_cards = total_cards > 0
        self.flashcards_mode.action_button.setEnabled(has_cards)

        return True

    def refresh(self) -> bool:
        if self.current_set_id is None:
            return False

        return self.load_study_set(
            self.current_set_id
        )

    def _show_empty_state(self) -> None:
        self.title_label.setText("Study Set")
        self.description_label.clear()
        self.description_label.setVisible(False)
        self.card_count_label.setText("0 cards")
        self.flashcards_mode.action_button.setEnabled(False)

    # ========================================================
    # REQUESTS
    # ========================================================

    def _request_flashcards(self) -> None:
        if self.current_set_id is not None:
            self.flashcards_requested.emit(
                self.current_set_id
            )

    def _request_learn(self) -> None:
        if self.current_set_id is not None:
            self.learn_requested.emit(
                self.current_set_id
            )

    def _request_test(self) -> None:
        if self.current_set_id is not None:
            self.test_requested.emit(
                self.current_set_id
            )

    def _request_edit(self) -> None:
        if self.current_set_id is not None:
            self.edit_requested.emit(
                self.current_set_id
            )
