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
    QFrame,
    QMessageBox
)

from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService


# ============================================================
# EDIT FLASHCARD ROW
# ============================================================

class EditFlashcardRow(QFrame):
    """
    Một dòng flashcard trong trang Edit.

    card_id = None  -> card mới
    card_id = int   -> card đã tồn tại trong database
    """

    delete_requested = Signal(object)

    def __init__(
        self,
        index: int,
        card_id: int | None = None,
        term: str = "",
        definition: str = "",
        parent=None
    ):
        super().__init__(parent)

        self.index = index
        self.card_id = card_id

        self.setObjectName(
            "FlashcardRow"
        )

        self._setup_ui(
            term,
            definition
        )

    def _setup_ui(
        self,
        term: str,
        definition: str
    ) -> None:

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        layout.setSpacing(
            10
        )

        self.number_label = QLabel(
            str(self.index)
        )

        self.number_label.setObjectName(
            "CardNumber"
        )

        self.number_label.setFixedWidth(
            32
        )

        self.number_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.number_label
        )

        self.term_input = QLineEdit()
        self.term_input.setObjectName(
            "CardInput"
        )
        self.term_input.setPlaceholderText(
            "Term / Question"
        )
        self.term_input.setMinimumHeight(
            44
        )
        self.term_input.setText(
            term
        )

        layout.addWidget(
            self.term_input,
            1
        )

        self.definition_input = QLineEdit()
        self.definition_input.setObjectName(
            "CardInput"
        )
        self.definition_input.setPlaceholderText(
            "Definition / Answer"
        )
        self.definition_input.setMinimumHeight(
            44
        )
        self.definition_input.setText(
            definition
        )

        layout.addWidget(
            self.definition_input,
            1
        )

        self.delete_button = QPushButton(
            "×"
        )

        self.delete_button.setObjectName(
            "DeleteCardButton"
        )

        self.delete_button.setFixedSize(
            40,
            40
        )

        self.delete_button.setCursor(
            Qt.PointingHandCursor
        )

        self.delete_button.clicked.connect(
            lambda: self.delete_requested.emit(self)
        )

        layout.addWidget(
            self.delete_button
        )

    def get_data(
        self
    ) -> tuple[int | None, str, str]:
        """
        Trả dữ liệu thô cho Service xử lý/validate.
        UI không quyết định CREATE hay UPDATE.
        """
        return (
            self.card_id,
            self.term_input.text(),
            self.definition_input.text()
        )

    def set_index(
        self,
        index: int
    ) -> None:
        self.index = index
        self.number_label.setText(
            str(index)
        )


# ============================================================
# EDIT STUDY SET PAGE
# ============================================================

class EditStudySetPage(QWidget):
    """
    Trang chỉnh sửa StudySet.

    Trách nhiệm của UI chỉ còn:
    - hiển thị dữ liệu;
    - thu thập dữ liệu người dùng;
    - phát yêu cầu Save;
    - hiển thị kết quả/lỗi.

    Quyết định CREATE / UPDATE / DELETE card, validation nghiệp vụ và
    transaction được xử lý trong StudySetService.
    """

    saved = Signal(int)
    cancel_requested = Signal()

    def __init__(
        self,
        study_set_service: StudySetService,
        flashcard_service: FlashcardService,
        parent=None
    ):
        super().__init__(parent)

        self.study_set_service = study_set_service

        # FlashcardService hiện chỉ dùng cho thao tác đọc danh sách card.
        # Toàn bộ workflow ghi dữ liệu đã chuyển sang StudySetService.
        self.flashcard_service = flashcard_service

        self.current_set_id: int | None = None
        self.card_rows: list[EditFlashcardRow] = []
        self.deleted_card_ids: set[int] = set()

        self._setup_ui()

    # ========================================================
    # SETUP UI
    # ========================================================

    def _setup_ui(
        self
    ) -> None:

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        main_layout.setSpacing(
            16
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            "Edit Study Set"
        )
        title.setObjectName(
            "PageTitle"
        )

        header.addWidget(
            title
        )
        header.addStretch()

        self.cancel_button = QPushButton(
            "Cancel"
        )
        self.cancel_button.setObjectName(
            "SecondaryButton"
        )
        self.cancel_button.setCursor(
            Qt.PointingHandCursor
        )
        self.cancel_button.clicked.connect(
            self.cancel_requested.emit
        )

        header.addWidget(
            self.cancel_button
        )

        main_layout.addLayout(
            header
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title_label = QLabel(
            "Title"
        )
        title_label.setObjectName(
            "FieldLabel"
        )

        main_layout.addWidget(
            title_label
        )

        self.title_input = QLineEdit()
        self.title_input.setObjectName(
            "MainInput"
        )
        self.title_input.setMinimumHeight(
            46
        )
        self.title_input.setPlaceholderText(
            "Study Set title"
        )

        main_layout.addWidget(
            self.title_input
        )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        description_label = QLabel(
            "Description"
        )
        description_label.setObjectName(
            "FieldLabel"
        )

        main_layout.addWidget(
            description_label
        )

        self.description_input = QTextEdit()
        self.description_input.setObjectName(
            "DescriptionInput"
        )
        self.description_input.setPlaceholderText(
            "Mô tả bộ học..."
        )
        self.description_input.setFixedHeight(
            90
        )

        main_layout.addWidget(
            self.description_input
        )

        # ----------------------------------------------------
        # FLASHCARDS HEADER
        # ----------------------------------------------------

        card_header = QHBoxLayout()

        cards_title = QLabel(
            "Flashcards"
        )
        cards_title.setObjectName(
            "SectionTitle"
        )

        card_header.addWidget(
            cards_title
        )
        card_header.addStretch()

        self.card_count_label = QLabel(
            "0 cards"
        )
        self.card_count_label.setObjectName(
            "SecondaryText"
        )

        card_header.addWidget(
            self.card_count_label
        )

        main_layout.addLayout(
            card_header
        )

        # ----------------------------------------------------
        # CARD SCROLL AREA
        # ----------------------------------------------------

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(
            True
        )
        self.scroll_area.setObjectName(
            "CardScrollArea"
        )

        self.cards_container = QWidget()

        self.cards_layout = QVBoxLayout(
            self.cards_container
        )
        self.cards_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        self.cards_layout.setSpacing(
            10
        )
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(
            self.cards_container
        )

        main_layout.addWidget(
            self.scroll_area,
            1
        )

        # ----------------------------------------------------
        # ADD CARD
        # ----------------------------------------------------

        self.add_card_button = QPushButton(
            "+ Add Card"
        )
        self.add_card_button.setObjectName(
            "SecondaryButton"
        )
        self.add_card_button.setMinimumHeight(
            44
        )
        self.add_card_button.setCursor(
            Qt.PointingHandCursor
        )
        self.add_card_button.clicked.connect(
            lambda: self.add_card_row()
        )

        main_layout.addWidget(
            self.add_card_button
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        self.save_button = QPushButton(
            "Save Changes"
        )
        self.save_button.setObjectName(
            "PrimaryButton"
        )
        self.save_button.setMinimumHeight(
            48
        )
        self.save_button.setCursor(
            Qt.PointingHandCursor
        )
        self.save_button.clicked.connect(
            self._save
        )

        main_layout.addWidget(
            self.save_button
        )

    # ========================================================
    # LOAD
    # ========================================================

    def load_study_set(
        self,
        set_id: int
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
                str(error)
            )
            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                str(error)
            )
            return

        self.current_set_id = set_id
        self.deleted_card_ids.clear()

        self.title_input.setText(
            study_set.title
        )

        self.description_input.setPlainText(
            study_set.description or ""
        )

        self._clear_rows()

        for card in flashcards:
            self.add_card_row(
                card_id=card.id,
                term=card.term,
                definition=card.definition
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
        definition: str = ""
    ) -> None:

        row = EditFlashcardRow(
            index=len(self.card_rows) + 1,
            card_id=card_id,
            term=term,
            definition=definition
        )

        row.delete_requested.connect(
            self.remove_card_row
        )

        self.card_rows.append(
            row
        )

        insert_position = (
            self.cards_layout.count() - 1
        )

        self.cards_layout.insertWidget(
            insert_position,
            row
        )

        self._update_card_count()

        if card_id is None:
            row.term_input.setFocus()

    def remove_card_row(
        self,
        row: EditFlashcardRow
    ) -> None:

        if row not in self.card_rows:
            return

        if row.card_id is not None:
            answer = QMessageBox.question(
                self,
                "Delete Flashcard",
                "Bạn có chắc muốn xóa flashcard này không?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if answer != QMessageBox.Yes:
                return

            # Chỉ ghi nhận ý định xóa. Database chưa bị thay đổi cho đến
            # khi người dùng bấm Save Changes.
            self.deleted_card_ids.add(
                row.card_id
            )

        self.card_rows.remove(
            row
        )

        self.cards_layout.removeWidget(
            row
        )

        row.deleteLater()

        self._renumber_rows()
        self._update_card_count()

        if not self.card_rows:
            self.add_card_row()

    def _clear_rows(
        self
    ) -> None:

        for row in self.card_rows:
            self.cards_layout.removeWidget(
                row
            )
            row.deleteLater()

        self.card_rows.clear()

    def _renumber_rows(
        self
    ) -> None:

        for index, row in enumerate(
            self.card_rows,
            start=1
        ):
            row.set_index(
                index
            )

    def _update_card_count(
        self
    ) -> None:

        total = len(
            self.card_rows
        )

        self.card_count_label.setText(
            f"{total} card"
            if total == 1
            else f"{total} cards"
        )

    # ========================================================
    # SAVE
    # ========================================================

    def _save(
        self
    ) -> None:
        """
        Thu thập dữ liệu UI và giao toàn bộ nghiệp vụ Save cho Service.

        Không UPDATE/INSERT/DELETE database trực tiếp tại Page này.
        """
        if self.current_set_id is None:
            QMessageBox.warning(
                self,
                "Error",
                "Chưa có Study Set nào được chọn."
            )
            return

        cards = [
            row.get_data()
            for row in self.card_rows
        ]

        self.save_button.setEnabled(
            False
        )

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
                    deleted_card_ids=self.deleted_card_ids
                )
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Save Error",
                str(error)
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
                )
            )
            return

        finally:
            self.save_button.setEnabled(
                True
            )

        self.deleted_card_ids.clear()

        QMessageBox.information(
            self,
            "Success",
            "Đã cập nhật Study Set và flashcards."
        )

        self.saved.emit(
            updated_set.id
        )
