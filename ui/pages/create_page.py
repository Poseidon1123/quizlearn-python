from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QScrollArea,
    QMessageBox,
)

from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService
from ui.widgets.flashcard_editor_row import FlashcardEditorRow


class CreatePage(QWidget):
    """Trang tạo StudySet và nhiều Flashcard."""

    study_set_created = Signal(int)
    cancel_requested = Signal()

    def __init__(
        self,
        study_set_service: StudySetService,
        flashcard_service: FlashcardService,
        parent=None,
    ):
        super().__init__(parent)

        self.study_set_service = study_set_service
        self.flashcard_service = flashcard_service
        self.card_rows: list[FlashcardEditorRow] = []

        self._setup_ui()
        self.reset_form()

    # ========================================================
    # UI
    # ========================================================

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(18)

        header = QHBoxLayout()

        title = QLabel("Create Study Set")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("SecondaryButton")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(
            self.cancel_requested.emit
        )
        header.addWidget(self.cancel_button)
        main_layout.addLayout(header)

        title_label = QLabel("Title")
        title_label.setObjectName("FieldLabel")
        main_layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setObjectName("MainInput")
        self.title_input.setPlaceholderText(
            "Ví dụ: TOEIC Vocabulary"
        )
        self.title_input.setMinimumHeight(46)
        main_layout.addWidget(self.title_input)

        description_label = QLabel("Description")
        description_label.setObjectName("FieldLabel")
        main_layout.addWidget(description_label)

        self.description_input = QTextEdit()
        self.description_input.setObjectName("DescriptionInput")
        self.description_input.setPlaceholderText(
            "Mô tả ngắn về bộ học..."
        )
        self.description_input.setFixedHeight(90)
        main_layout.addWidget(self.description_input)

        cards_header = QHBoxLayout()

        cards_title = QLabel("Flashcards")
        cards_title.setObjectName("SectionTitle")
        cards_header.addWidget(cards_title)
        cards_header.addStretch()

        self.card_count_label = QLabel("0 cards")
        self.card_count_label.setObjectName("SecondaryText")
        cards_header.addWidget(self.card_count_label)
        main_layout.addLayout(cards_header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("CardScrollArea")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll_area, 1)

        self.add_card_button = QPushButton("+ Add Card")
        self.add_card_button.setObjectName("SecondaryButton")
        self.add_card_button.setMinimumHeight(44)
        self.add_card_button.setCursor(Qt.PointingHandCursor)
        self.add_card_button.clicked.connect(
            lambda: self.add_card_row()
        )
        main_layout.addWidget(self.add_card_button)

        self.create_button = QPushButton("Create Study Set")
        self.create_button.setObjectName("PrimaryButton")
        self.create_button.setMinimumHeight(48)
        self.create_button.setCursor(Qt.PointingHandCursor)
        self.create_button.clicked.connect(
            self._create_study_set
        )
        main_layout.addWidget(self.create_button)

    # ========================================================
    # ROW MANAGEMENT
    # ========================================================

    def add_card_row(
        self,
        term: str = "",
        definition: str = "",
    ) -> None:
        row = FlashcardEditorRow(
            index=len(self.card_rows) + 1,
            term=term,
            definition=definition,
        )

        row.delete_requested.connect(
            self.remove_card_row
        )

        self.card_rows.append(row)

        insert_position = self.cards_layout.count() - 1
        self.cards_layout.insertWidget(
            insert_position,
            row,
        )

        self._update_card_count()
        row.term_input.setFocus()

    def remove_card_row(
        self,
        row: FlashcardEditorRow,
    ) -> None:
        if row not in self.card_rows:
            return

        if len(self.card_rows) <= 1:
            row.clear()
            return

        self.card_rows.remove(row)
        self.cards_layout.removeWidget(row)
        row.deleteLater()

        self._renumber_rows()
        self._update_card_count()

    def _clear_rows(self) -> None:
        for row in self.card_rows:
            self.cards_layout.removeWidget(row)
            row.deleteLater()

        self.card_rows.clear()

    def _renumber_rows(self) -> None:
        for index, row in enumerate(
            self.card_rows,
            start=1,
        ):
            row.set_index(index)

    def _update_card_count(self) -> None:
        total = len(self.card_rows)

        self.card_count_label.setText(
            f"{total} card"
            if total == 1
            else f"{total} cards"
        )

    # ========================================================
    # DATA / VALIDATION
    # ========================================================

    def _get_flashcard_data(
        self,
    ) -> list[tuple[str, str]]:
        cards: list[tuple[str, str]] = []

        for row in self.card_rows:
            term, definition = row.get_content()

            if not term and not definition:
                continue

            if not term:
                raise ValueError(
                    f"Flashcard số {row.index}: "
                    "Term / Question đang để trống."
                )

            if not definition:
                raise ValueError(
                    f"Flashcard số {row.index}: "
                    "Definition / Answer đang để trống."
                )

            cards.append((term, definition))

        return cards

    # ========================================================
    # CREATE
    # ========================================================

    def _create_study_set(self) -> None:
        title = self.title_input.text().strip()
        description = (
            self.description_input
            .toPlainText()
            .strip()
        )

        try:
            cards = self._get_flashcard_data()
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Flashcard",
                str(error),
            )
            return

        if not cards:
            QMessageBox.warning(
                self,
                "No Flashcards",
                "Hãy nhập ít nhất một flashcard.",
            )
            return

        self.create_button.setEnabled(False)

        try:
            study_set = self.study_set_service.create_study_set(
                title=title,
                description=description,
            )

            self.flashcard_service.create_many_flashcards(
                set_id=study_set.id,
                cards=cards,
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Study Set",
                str(error),
            )
            return

        except Exception as error:
            # Create flow vẫn giữ cơ chế cleanup cũ. Một bước sau có thể
            # chuyển use case này sang transaction tương tự Edit.
            if "study_set" in locals() and study_set.id is not None:
                try:
                    self.study_set_service.delete_study_set(
                        study_set.id
                    )
                except Exception:
                    pass

            QMessageBox.critical(
                self,
                "Create Error",
                str(error),
            )
            return

        finally:
            self.create_button.setEnabled(True)

        QMessageBox.information(
            self,
            "Success",
            (
                f'Đã tạo bộ "{study_set.title}" '
                f"với {len(cards)} flashcard."
            ),
        )

        created_set_id = study_set.id
        self.reset_form()
        self.study_set_created.emit(created_set_id)

    # ========================================================
    # RESET
    # ========================================================

    def reset_form(self) -> None:
        self.title_input.clear()
        self.description_input.clear()
        self._clear_rows()

        for _ in range(3):
            self.add_card_row()

        self.title_input.setFocus()
