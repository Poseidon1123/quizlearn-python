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
    Một dòng Flashcard trong trang Edit.

    card_id:
        None  -> Flashcard mới
        int   -> Flashcard đã tồn tại trong database
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

    # ========================================================
    # SETUP UI
    # ========================================================

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

        # ----------------------------------------------------
        # NUMBER
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # TERM
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DEFINITION
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DELETE
        # ----------------------------------------------------

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
            lambda:
            self.delete_requested.emit(
                self
            )
        )

        layout.addWidget(
            self.delete_button
        )

    # ========================================================
    # GET DATA
    # ========================================================

    def get_data(
        self
    ) -> tuple[str, str]:

        return (
            self.term_input.text().strip(),
            self.definition_input.text().strip()
        )

    # ========================================================
    # SET INDEX
    # ========================================================

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
    Chỉnh sửa toàn bộ StudySet:

    - Title
    - Description
    - sửa Flashcard
    - thêm Flashcard
    - xóa Flashcard
    """

    saved = Signal(int)

    cancel_requested = Signal()

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

        self.study_set_service = (
            study_set_service
        )

        self.flashcard_service = (
            flashcard_service
        )

        self.current_set_id = None

        self.card_rows = []

        # Những card đã tồn tại nhưng người dùng yêu cầu xóa
        self.deleted_card_ids = set()

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

        # ====================================================
        # HEADER
        # ====================================================

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

        # ====================================================
        # TITLE
        # ====================================================

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

        # ====================================================
        # DESCRIPTION
        # ====================================================

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

        # ====================================================
        # FLASHCARD HEADER
        # ====================================================

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

        # ====================================================
        # SCROLL AREA
        # ====================================================

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

        # ====================================================
        # ADD CARD
        # ====================================================

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

        # ====================================================
        # SAVE
        # ====================================================

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
    # LOAD STUDY SET
    # ========================================================

    def load_study_set(
        self,
        set_id: int
    ) -> None:

        try:

            study_set = (
                self.study_set_service
                .get_study_set(
                    set_id
                )
            )

            flashcards = (
                self.flashcard_service
                .get_flashcards_by_set(
                    set_id
                )
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

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        self.title_input.setText(
            study_set.title
        )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        self.description_input.setPlainText(
            study_set.description or ""
        )

        # ----------------------------------------------------
        # CLEAR OLD ROWS
        # ----------------------------------------------------

        self._clear_rows()

        # ----------------------------------------------------
        # LOAD CARDS
        # ----------------------------------------------------

        for card in flashcards:

            self.add_card_row(
                card_id=card.id,
                term=card.term,
                definition=card.definition
            )

        # Nếu StudySet đang rỗng thì vẫn cho một dòng nhập
        if not self.card_rows:

            self.add_card_row()

        self._update_card_count()

        self.title_input.setFocus()

    # ========================================================
    # ADD CARD ROW
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

    # ========================================================
    # REMOVE CARD
    # ========================================================

    def remove_card_row(
        self,
        row: EditFlashcardRow
    ) -> None:

        if row not in self.card_rows:
            return

        # ----------------------------------------------------
        # EXISTING DATABASE CARD
        # ----------------------------------------------------

        if row.card_id is not None:

            answer = QMessageBox.question(
                self,
                "Delete Flashcard",
                "Bạn có chắc muốn xóa flashcard này không?",
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.No
            )

            if answer != QMessageBox.Yes:
                return

            # Chưa xóa database ngay.
            # Chỉ ghi nhận để xóa khi Save.
            self.deleted_card_ids.add(
                row.card_id
            )

        # ----------------------------------------------------
        # REMOVE UI ROW
        # ----------------------------------------------------

        self.card_rows.remove(
            row
        )

        self.cards_layout.removeWidget(
            row
        )

        row.deleteLater()

        self._renumber_rows()

        self._update_card_count()

        # Luôn để ít nhất một dòng nhập
        if not self.card_rows:

            self.add_card_row()

    # ========================================================
    # CLEAR ROWS
    # ========================================================

    def _clear_rows(
        self
    ) -> None:

        for row in self.card_rows:

            self.cards_layout.removeWidget(
                row
            )

            row.deleteLater()

        self.card_rows.clear()

    # ========================================================
    # RENUMBER
    # ========================================================

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

    # ========================================================
    # UPDATE COUNT
    # ========================================================

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
    # VALIDATE
    # ========================================================

    def _validate_rows(
        self
    ) -> None:

        valid_card_count = 0

        for row in self.card_rows:

            term, definition = (
                row.get_data()
            )

            # Dòng mới hoàn toàn trống được phép bỏ qua
            if (
                row.card_id is None
                and not term
                and not definition
            ):
                continue

            if not term:

                raise ValueError(
                    f"Flashcard số {row.index}: "
                    "Term / Question không được để trống."
                )

            if not definition:

                raise ValueError(
                    f"Flashcard số {row.index}: "
                    "Definition / Answer không được để trống."
                )

            valid_card_count += 1

        if valid_card_count == 0:

            raise ValueError(
                "Study Set phải có ít nhất một flashcard."
            )

    # ========================================================
    # SAVE
    # ========================================================

    def _save(
        self
    ) -> None:

        if self.current_set_id is None:

            QMessageBox.warning(
                self,
                "Error",
                "Chưa có Study Set nào được chọn."
            )

            return

        title = (
            self.title_input
            .text()
            .strip()
        )

        description = (
            self.description_input
            .toPlainText()
            .strip()
        )

        # ----------------------------------------------------
        # VALIDATE CARD DATA
        # ----------------------------------------------------

        try:

            self._validate_rows()

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Invalid Data",
                str(error)
            )

            return

        try:

            # =================================================
            # UPDATE STUDY SET
            # =================================================

            self.study_set_service.update_study_set(
                set_id=self.current_set_id,
                title=title,
                description=description
            )

            # =================================================
            # DELETE CARDS
            # =================================================

            for card_id in self.deleted_card_ids:

                self.flashcard_service.delete_flashcard(
                    card_id
                )

            # =================================================
            # CREATE / UPDATE CARDS
            # =================================================

            for row in self.card_rows:

                term, definition = (
                    row.get_data()
                )

                # ---------------------------------------------
                # NEW EMPTY ROW
                # ---------------------------------------------

                if (
                    row.card_id is None
                    and not term
                    and not definition
                ):
                    continue

                # ---------------------------------------------
                # NEW CARD
                # ---------------------------------------------

                if row.card_id is None:

                    self.flashcard_service.create_flashcard(
                        set_id=self.current_set_id,
                        term=term,
                        definition=definition
                    )

                # ---------------------------------------------
                # EXISTING CARD
                # ---------------------------------------------

                else:

                    self.flashcard_service.update_flashcard(
                        card_id=row.card_id,
                        term=term,
                        definition=definition
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
                str(error)
            )

            return

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        set_id = self.current_set_id

        QMessageBox.information(
            self,
            "Success",
            "Đã cập nhật Study Set."
        )

        self.saved.emit(
            set_id
        )