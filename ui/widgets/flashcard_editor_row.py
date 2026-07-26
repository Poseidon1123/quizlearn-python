from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class FlashcardEditorRow(QFrame):
    """
    Widget dùng chung cho CreatePage và EditStudySetPage.

    card_id:
        None -> flashcard mới
        int  -> flashcard đã tồn tại trong database
    """

    delete_requested = Signal(object)

    def __init__(
        self,
        index: int,
        card_id: int | None = None,
        term: str = "",
        definition: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self.index = index
        self.card_id = card_id

        self.setObjectName("FlashcardRow")

        self._setup_ui()
        self.set_data(
            term=term,
            definition=definition,
        )

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.number_label = QLabel(str(self.index))
        self.number_label.setObjectName("CardNumber")
        self.number_label.setFixedWidth(32)
        self.number_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.number_label)

        self.term_input = QLineEdit()
        self.term_input.setObjectName("CardInput")
        self.term_input.setPlaceholderText("Term / Question")
        self.term_input.setMinimumHeight(44)
        layout.addWidget(self.term_input, 1)

        self.definition_input = QLineEdit()
        self.definition_input.setObjectName("CardInput")
        self.definition_input.setPlaceholderText("Definition / Answer")
        self.definition_input.setMinimumHeight(44)
        layout.addWidget(self.definition_input, 1)

        self.delete_button = QPushButton("×")
        self.delete_button.setObjectName("DeleteCardButton")
        self.delete_button.setFixedSize(40, 40)
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.clicked.connect(
            lambda: self.delete_requested.emit(self)
        )
        layout.addWidget(self.delete_button)

    def set_index(self, index: int) -> None:
        self.index = index
        self.number_label.setText(str(index))

    def set_data(
        self,
        term: str,
        definition: str,
    ) -> None:
        self.term_input.setText(term)
        self.definition_input.setText(definition)

    def clear(self) -> None:
        self.term_input.clear()
        self.definition_input.clear()

    def get_content(self) -> tuple[str, str]:
        """Trả về nội dung card, không kèm ID."""
        return (
            self.term_input.text().strip(),
            self.definition_input.text().strip(),
        )

    def get_data(self) -> tuple[int | None, str, str]:
        """Trả về card_id + nội dung, phù hợp cho luồng Edit/Save."""
        term, definition = self.get_content()
        return (
            self.card_id,
            term,
            definition,
        )

    @property
    def is_new(self) -> bool:
        return self.card_id is None

    @property
    def is_empty(self) -> bool:
        term, definition = self.get_content()
        return not term and not definition
