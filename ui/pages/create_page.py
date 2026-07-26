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


class FlashcardRow(QFrame):
    """
    Một dòng nhập flashcard gồm:
    Term | Definition | Delete
    """

    delete_requested = Signal(object)

    def __init__(
        self,
        index: int,
        parent=None
    ):
        super().__init__(parent)

        self.setObjectName(
            "FlashcardRow"
        )

        self.index = index

        self._setup_ui()

    # ========================================================
    # SETUP UI
    # ========================================================

    def _setup_ui(self) -> None:

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
            30
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

        self.term_input.setPlaceholderText(
            "Term / Question"
        )

        self.term_input.setObjectName(
            "CardInput"
        )

        self.term_input.setMinimumHeight(
            42
        )

        layout.addWidget(
            self.term_input,
            1
        )

        # ----------------------------------------------------
        # DEFINITION
        # ----------------------------------------------------

        self.definition_input = QLineEdit()

        self.definition_input.setPlaceholderText(
            "Definition / Answer"
        )

        self.definition_input.setObjectName(
            "CardInput"
        )

        self.definition_input.setMinimumHeight(
            42
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
    # DATA
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

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:

        self.term_input.clear()

        self.definition_input.clear()


class CreatePage(QWidget):
    """
    Trang tạo StudySet và nhiều Flashcard.
    """

    study_set_created = Signal(int)

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

        self.card_rows = []

        self._setup_ui()

        self.reset_form()

    # ========================================================
    # SETUP UI
    # ========================================================

    def _setup_ui(self) -> None:

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
            18
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            "Create Study Set"
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
        # TITLE LABEL
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

        # ----------------------------------------------------
        # STUDY SET TITLE
        # ----------------------------------------------------

        self.title_input = QLineEdit()

        self.title_input.setObjectName(
            "MainInput"
        )

        self.title_input.setPlaceholderText(
            "Ví dụ: TOEIC Vocabulary"
        )

        self.title_input.setMinimumHeight(
            46
        )

        main_layout.addWidget(
            self.title_input
        )

        # ----------------------------------------------------
        # DESCRIPTION LABEL
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

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        self.description_input = QTextEdit()

        self.description_input.setObjectName(
            "DescriptionInput"
        )

        self.description_input.setPlaceholderText(
            "Mô tả ngắn về bộ học..."
        )

        self.description_input.setFixedHeight(
            90
        )

        main_layout.addWidget(
            self.description_input
        )

        # ----------------------------------------------------
        # FLASHCARD HEADER
        # ----------------------------------------------------

        cards_header = QHBoxLayout()

        cards_title = QLabel(
            "Flashcards"
        )

        cards_title.setObjectName(
            "SectionTitle"
        )

        cards_header.addWidget(
            cards_title
        )

        cards_header.addStretch()

        self.card_count_label = QLabel(
            "0 cards"
        )

        self.card_count_label.setObjectName(
            "SecondaryText"
        )

        cards_header.addWidget(
            self.card_count_label
        )

        main_layout.addLayout(
            cards_header
        )

        # ----------------------------------------------------
        # SCROLL AREA
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
            self.add_card_row
        )

        main_layout.addWidget(
            self.add_card_button
        )

        # ----------------------------------------------------
        # CREATE
        # ----------------------------------------------------

        self.create_button = QPushButton(
            "Create Study Set"
        )

        self.create_button.setObjectName(
            "PrimaryButton"
        )

        self.create_button.setMinimumHeight(
            48
        )

        self.create_button.setCursor(
            Qt.PointingHandCursor
        )

        self.create_button.clicked.connect(
            self._create_study_set
        )

        main_layout.addWidget(
            self.create_button
        )

    # ========================================================
    # ADD CARD ROW
    # ========================================================

    def add_card_row(
        self
    ) -> None:

        row = FlashcardRow(
            index=len(self.card_rows) + 1
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

        row.term_input.setFocus()

    # ========================================================
    # REMOVE CARD ROW
    # ========================================================

    def remove_card_row(
        self,
        row: FlashcardRow
    ) -> None:

        if row not in self.card_rows:
            return

        # Không để form hoàn toàn không có dòng nhập
        if len(self.card_rows) <= 1:

            row.clear()

            return

        self.card_rows.remove(
            row
        )

        self.cards_layout.removeWidget(
            row
        )

        row.deleteLater()

        self._renumber_rows()

        self._update_card_count()

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
    # GET FLASHCARD DATA
    # ========================================================

    def _get_flashcard_data(
        self
    ) -> list[tuple[str, str]]:

        cards = []

        for row in self.card_rows:

            term, definition = (
                row.get_data()
            )

            # ------------------------------------------------
            # Dòng hoàn toàn trống thì bỏ qua
            # ------------------------------------------------

            if not term and not definition:
                continue

            # ------------------------------------------------
            # Chỉ nhập một phía thì báo lỗi
            # ------------------------------------------------

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

            cards.append(
                (
                    term,
                    definition
                )
            )

        return cards

    # ========================================================
    # CREATE STUDY SET
    # ========================================================

    def _create_study_set(
        self
    ) -> None:

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
        # VALIDATE CARDS BEFORE WRITING DATABASE
        # ----------------------------------------------------

        try:

            cards = (
                self._get_flashcard_data()
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Invalid Flashcard",
                str(error)
            )

            return

        if not cards:

            QMessageBox.warning(
                self,
                "No Flashcards",
                "Hãy nhập ít nhất một flashcard."
            )

            return

        # ----------------------------------------------------
        # CREATE STUDY SET
        # ----------------------------------------------------

        try:

            study_set = (
                self.study_set_service
                .create_study_set(
                    title=title,
                    description=description
                )
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Invalid Study Set",
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
        # CREATE FLASHCARDS
        # ----------------------------------------------------

        try:

            self.flashcard_service.create_many_flashcards(
                set_id=study_set.id,
                cards=cards
            )

        except Exception as error:

            # Nếu tạo flashcard thất bại,
            # xóa StudySet vừa tạo để tránh bộ rỗng.
            try:

                self.study_set_service.delete_study_set(
                    study_set.id
                )

            except Exception:
                pass

            QMessageBox.critical(
                self,
                "Create Error",
                (
                    "Không thể tạo flashcard.\n\n"
                    f"{error}"
                )
            )

            return

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        QMessageBox.information(
            self,
            "Success",
            (
                f'Đã tạo bộ "{study_set.title}" '
                f'với {len(cards)} flashcard.'
            )
        )

        created_set_id = (
            study_set.id
        )

        self.reset_form()

        self.study_set_created.emit(
            created_set_id
        )

    # ========================================================
    # RESET FORM
    # ========================================================

    def reset_form(
        self
    ) -> None:

        self.title_input.clear()

        self.description_input.clear()

        # ----------------------------------------------------
        # REMOVE OLD ROWS
        # ----------------------------------------------------

        for row in self.card_rows:

            self.cards_layout.removeWidget(
                row
            )

            row.deleteLater()

        self.card_rows.clear()

        # ----------------------------------------------------
        # START WITH THREE CARDS
        # ----------------------------------------------------

        for _ in range(3):

            self.add_card_row()

        self.title_input.setFocus()