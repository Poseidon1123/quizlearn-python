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


class EditStudySetPage(QWidget):
    """
    Chỉnh sửa toàn bộ StudySet:

    - Title
    - Description
    - sửa Flashcard
    - thêm Flashcard
    - xóa Flashcard
    """

    saved = Signal(int)
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

        self.current_set_id: int | None = None
        self.card_rows: list[FlashcardEditorRow] = []
        self.deleted_card_ids: set[int] = set()

        self._setup_ui()

    # ========================================================
    # UI
    # ========================================================

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(16)

        header = QHBoxLayout()

        title = QLabel("Edit Study Set")
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
        self.title_input.setMinimumHeight(46)
        self.title_input.setPlaceholderText("Study Set title")
        main_layout.addWidget(self.title_input)

        description_label = QLabel("Description")
        description_label.setObjectName("FieldLabel")
        main_layout.addWidget(description_label)

        self.description_input = QTextEdit()
        self.description_input.setObjectName("DescriptionInput")
        self.description_input.setPlaceholderText(
            "Mô tả bộ học..."
        )
        self.description_input.setFixedHeight(90)
        main_layout.addWidget(self.description_input)

        card_header = QHBoxLayout()

        cards_title = QLabel("Flashcards")
        cards_title.setObjectName("SectionTitle")
        card_header.addWidget(cards_title)
        card_header.addStretch()

        self.card_count_label = QLabel("0 cards")
        self.card_count_label.setObjectName("SecondaryText")
        card_header.addWidget(self.card_count_label)
        main_layout.addLayout(card_header)

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

        self.save_button = QPushButton("Save Changes")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.setMinimumHeight(48)
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self._save)
        main_layout.addWidget(self.save_button)

    # ========================================================
    # LOAD
    # ========================================================

    def load_study_set(
        self,
        set_id: int,
    ) -> None:
        try:
            study_set = self.study_set_service.get_study_set(
                set_id
            )
            flashcards = self.flashcard_service.get_flashcards_by_set(
                set_id
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Error",
                str(error),
            )
            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                str(error),
            )
            return

        self.current_set_id = set_id
        self.deleted_card_ids.clear()

        self.title_input.setText(study_set.title)
        self.description_input.setPlainText(
            study_set.description or ""
        )

        self._clear_rows()

        for card in flashcards:
            self.add_card_row(
                card_id=card.id,
                term=card.term,
                definition=card.definition,
            )

        if not self.card_rows:
            self.add_card_row()

        self._update_card_count()
        self.title_input.setFocus()

    # ========================================================
    # ROW MANAGEMENT
    # ========================================================

    def add_card_row(
        self,
        card_id: int | None = None,
        term: str = "",
        definition: str = "",
    ) -> None:
        row = FlashcardEditorRow(
            index=len(self.card_rows) + 1,
            card_id=card_id,
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

        if row.is_new:
            row.term_input.setFocus()

    def remove_card_row(
        self,
        row: FlashcardEditorRow,
    ) -> None:
        if row not in self.card_rows:
            return

        if not row.is_new:
            answer = QMessageBox.question(
                self,
                "Delete Flashcard",
                "Bạn có chắc muốn xóa flashcard này không?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if answer != QMessageBox.Yes:
                return

            if row.card_id is not None:
                self.deleted_card_ids.add(row.card_id)

        self.card_rows.remove(row)
        self.cards_layout.removeWidget(row)
        row.deleteLater()

        self._renumber_rows()
        self._update_card_count()

        if not self.card_rows:
            self.add_card_row()

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
    # SAVE
    # ========================================================

    def _save(self) -> None:
        """
        UI chỉ thu thập dữ liệu và giao toàn bộ nghiệp vụ cho Service.
        """
        if self.current_set_id is None:
            QMessageBox.warning(
                self,
                "Error",
                "Chưa có Study Set nào được chọn.",
            )
            return

        cards = [
            row.get_data()
            for row in self.card_rows
        ]

        self.save_button.setEnabled(False)

        try:
            updated_set = (
                self.study_set_service
                .save_study_set_with_flashcards(
                    set_id=self.current_set_id,
                    title=self.title_input.text(),
                    description=(
                        self.description_input.toPlainText()
                    ),
                    cards=cards,
                    deleted_card_ids=self.deleted_card_ids,
                )
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Save Error",
                str(error),
            )
            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                (
                    "Không thể lưu Study Set. "
                    "Mọi thay đổi trong lần Save này đã được rollback.\n\n"
                    f"{error}"
                ),
            )
            return

        finally:
            self.save_button.setEnabled(True)

        self.deleted_card_ids.clear()

        QMessageBox.information(
            self,
            "Success",
            "Đã cập nhật Study Set và flashcards.",
        )

        self.saved.emit(updated_set.id)
