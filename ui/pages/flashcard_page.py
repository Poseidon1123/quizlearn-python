import random

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
    QSizePolicy
)

from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService


# ============================================================
# FLASHCARD WIDGET
# ============================================================

class FlashcardWidget(QFrame):
    """
    Widget hiển thị một flashcard.

    Click vào card để chuyển giữa:
        Term <-> Definition
    """

    flipped = Signal(bool)

    def __init__(
        self,
        parent=None
    ):
        super().__init__(parent)

        self.setObjectName(
            "Flashcard"
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setMinimumHeight(
            320
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.term = ""
        self.definition = ""

        self.showing_definition = False

        self._setup_ui()

    # ========================================================
    # SETUP UI
    # ========================================================

    def _setup_ui(
        self
    ) -> None:

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            50,
            50,
            50,
            50
        )

        layout.addStretch()

        # ----------------------------------------------------
        # SIDE LABEL
        # ----------------------------------------------------

        self.side_label = QLabel(
            "TERM"
        )

        self.side_label.setObjectName(
            "FlashcardSide"
        )

        self.side_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.side_label
        )

        layout.addSpacing(
            20
        )

        # ----------------------------------------------------
        # CARD TEXT
        # ----------------------------------------------------

        self.text_label = QLabel(
            ""
        )

        self.text_label.setObjectName(
            "FlashcardText"
        )

        self.text_label.setAlignment(
            Qt.AlignCenter
        )

        self.text_label.setWordWrap(
            True
        )

        self.text_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        layout.addWidget(
            self.text_label
        )

        layout.addStretch()

        # ----------------------------------------------------
        # HINT
        # ----------------------------------------------------

        self.hint_label = QLabel(
            "Click the card to flip"
        )

        self.hint_label.setObjectName(
            "FlashcardHint"
        )

        self.hint_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.hint_label
        )

    # ========================================================
    # SET CARD
    # ========================================================

    def set_card(
        self,
        term: str,
        definition: str
    ) -> None:

        self.term = term
        self.definition = definition

        self.show_front()

    # ========================================================
    # SHOW FRONT
    # ========================================================

    def show_front(
        self
    ) -> None:

        self.showing_definition = False

        self.side_label.setText(
            "TERM"
        )

        self.text_label.setText(
            self.term
        )

        self.flipped.emit(
            False
        )

    # ========================================================
    # SHOW BACK
    # ========================================================

    def show_back(
        self
    ) -> None:

        self.showing_definition = True

        self.side_label.setText(
            "DEFINITION"
        )

        self.text_label.setText(
            self.definition
        )

        self.flipped.emit(
            True
        )

    # ========================================================
    # FLIP
    # ========================================================

    def flip(
        self
    ) -> None:

        if self.showing_definition:

            self.show_front()

        else:

            self.show_back()

    # ========================================================
    # MOUSE CLICK
    # ========================================================

    def mousePressEvent(
        self,
        event
    ) -> None:

        if event.button() == Qt.LeftButton:

            self.flip()

        super().mousePressEvent(
            event
        )


# ============================================================
# FLASHCARD PAGE
# ============================================================

class FlashcardPage(QWidget):
    """
    Trang học flashcard.
    """

    back_requested = Signal()

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

        # Study Set hiện tại
        self.current_set_id = None

        # Danh sách flashcard
        self.cards = []

        # Vị trí hiện tại
        self.current_index = 0

        # Trạng thái shuffle
        self.is_shuffled = False

        self._setup_ui()

        self._show_empty_state()

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
            40,
            30,
            40,
            30
        )

        main_layout.setSpacing(
            20
        )

        # ====================================================
        # HEADER
        # ====================================================

        header_layout = QHBoxLayout()

        # ----------------------------------------------------
        # BACK
        # ----------------------------------------------------

        self.back_button = QPushButton(
            "← Back"
        )

        self.back_button.setObjectName(
            "SecondaryButton"
        )

        self.back_button.setCursor(
            Qt.PointingHandCursor
        )

        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        header_layout.addWidget(
            self.back_button
        )

        header_layout.addSpacing(
            15
        )

        # ----------------------------------------------------
        # STUDY SET TITLE
        # ----------------------------------------------------

        self.title_label = QLabel(
            "Flashcards"
        )

        self.title_label.setObjectName(
            "PageTitle"
        )

        header_layout.addWidget(
            self.title_label
        )

        header_layout.addStretch()

        # ----------------------------------------------------
        # SHUFFLE
        # ----------------------------------------------------

        self.shuffle_button = QPushButton(
            "Shuffle"
        )

        self.shuffle_button.setObjectName(
            "SecondaryButton"
        )

        self.shuffle_button.setCheckable(
            True
        )

        self.shuffle_button.setCursor(
            Qt.PointingHandCursor
        )

        self.shuffle_button.clicked.connect(
            self._toggle_shuffle
        )

        header_layout.addWidget(
            self.shuffle_button
        )

        main_layout.addLayout(
            header_layout
        )

        # ====================================================
        # DESCRIPTION
        # ====================================================

        self.description_label = QLabel(
            ""
        )

        self.description_label.setObjectName(
            "SecondaryText"
        )

        self.description_label.setWordWrap(
            True
        )

        main_layout.addWidget(
            self.description_label
        )

        # ====================================================
        # CARD COUNTER
        # ====================================================

        self.counter_label = QLabel(
            "0 / 0"
        )

        self.counter_label.setObjectName(
            "FlashcardCounter"
        )

        self.counter_label.setAlignment(
            Qt.AlignCenter
        )

        main_layout.addWidget(
            self.counter_label
        )

        # ====================================================
        # FLASHCARD
        # ====================================================

        self.flashcard = FlashcardWidget()

        main_layout.addWidget(
            self.flashcard,
            1
        )

        # ====================================================
        # EMPTY MESSAGE
        # ====================================================

        self.empty_label = QLabel(
            "This study set does not contain any flashcards."
        )

        self.empty_label.setObjectName(
            "EmptyMessage"
        )

        self.empty_label.setAlignment(
            Qt.AlignCenter
        )

        self.empty_label.setWordWrap(
            True
        )

        main_layout.addWidget(
            self.empty_label
        )

        # ====================================================
        # NAVIGATION
        # ====================================================

        navigation_layout = QHBoxLayout()

        navigation_layout.addStretch()

        # ----------------------------------------------------
        # PREVIOUS
        # ----------------------------------------------------

        self.previous_button = QPushButton(
            "← Previous"
        )

        self.previous_button.setObjectName(
            "SecondaryButton"
        )

        self.previous_button.setMinimumWidth(
            130
        )

        self.previous_button.setMinimumHeight(
            44
        )

        self.previous_button.setCursor(
            Qt.PointingHandCursor
        )

        self.previous_button.clicked.connect(
            self.previous_card
        )

        navigation_layout.addWidget(
            self.previous_button
        )

        # ----------------------------------------------------
        # FLIP
        # ----------------------------------------------------

        self.flip_button = QPushButton(
            "Flip"
        )

        self.flip_button.setObjectName(
            "PrimaryButton"
        )

        self.flip_button.setMinimumWidth(
            130
        )

        self.flip_button.setMinimumHeight(
            44
        )

        self.flip_button.setCursor(
            Qt.PointingHandCursor
        )

        self.flip_button.clicked.connect(
            self.flashcard.flip
        )

        navigation_layout.addWidget(
            self.flip_button
        )

        # ----------------------------------------------------
        # NEXT
        # ----------------------------------------------------

        self.next_button = QPushButton(
            "Next →"
        )

        self.next_button.setObjectName(
            "SecondaryButton"
        )

        self.next_button.setMinimumWidth(
            130
        )

        self.next_button.setMinimumHeight(
            44
        )

        self.next_button.setCursor(
            Qt.PointingHandCursor
        )

        self.next_button.clicked.connect(
            self.next_card
        )

        navigation_layout.addWidget(
            self.next_button
        )

        navigation_layout.addStretch()

        main_layout.addLayout(
            navigation_layout
        )

        # ====================================================
        # KEYBOARD HINT
        # ====================================================

        self.keyboard_hint = QLabel(
            "← Previous     Space: Flip     Next →"
        )

        self.keyboard_hint.setObjectName(
            "SecondaryText"
        )

        self.keyboard_hint.setAlignment(
            Qt.AlignCenter
        )

        main_layout.addWidget(
            self.keyboard_hint
        )

    # ========================================================
    # LOAD STUDY SET
    # ========================================================

    def load_study_set(
        self,
        set_id: int
    ) -> None:
        """
        Load StudySet và toàn bộ flashcard của bộ đó.
        """

        try:

            study_set = (
                self.study_set_service
                .get_study_set(
                    set_id
                )
            )

            cards = (
                self.flashcard_service
                .get_flashcards_by_set(
                    set_id
                )
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Study Set",
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
        # SAVE CURRENT SET
        # ----------------------------------------------------

        self.current_set_id = set_id

        self.cards = list(
            cards
        )

        self.current_index = 0

        self.is_shuffled = False

        self.shuffle_button.setChecked(
            False
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        self.title_label.setText(
            study_set.title
        )

        self.description_label.setText(
            study_set.description
        )

        self.description_label.setVisible(
            bool(study_set.description)
        )

        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        if not self.cards:

            self._show_empty_state()

            return

        self._show_card()

    # ========================================================
    # SHOW CARD
    # ========================================================

    def _show_card(
        self
    ) -> None:

        if not self.cards:

            self._show_empty_state()

            return

        # ----------------------------------------------------
        # CHECK INDEX
        # ----------------------------------------------------

        if self.current_index < 0:

            self.current_index = 0

        if self.current_index >= len(
            self.cards
        ):

            self.current_index = (
                len(self.cards) - 1
            )

        # ----------------------------------------------------
        # CURRENT CARD
        # ----------------------------------------------------

        card = self.cards[
            self.current_index
        ]

        self.flashcard.set_card(
            term=card.term,
            definition=card.definition
        )

        # ----------------------------------------------------
        # COUNTER
        # ----------------------------------------------------

        self.counter_label.setText(
            (
                f"{self.current_index + 1}"
                f" / "
                f"{len(self.cards)}"
            )
        )

        # ----------------------------------------------------
        # VISIBILITY
        # ----------------------------------------------------

        self.flashcard.setVisible(
            True
        )

        self.empty_label.setVisible(
            False
        )

        self.flip_button.setEnabled(
            True
        )

        # ----------------------------------------------------
        # NAVIGATION STATE
        # ----------------------------------------------------

        self._update_navigation_buttons()

    # ========================================================
    # EMPTY STATE
    # ========================================================

    def _show_empty_state(
        self
    ) -> None:

        self.flashcard.setVisible(
            False
        )

        self.empty_label.setVisible(
            True
        )

        self.counter_label.setText(
            "0 / 0"
        )

        self.previous_button.setEnabled(
            False
        )

        self.next_button.setEnabled(
            False
        )

        self.flip_button.setEnabled(
            False
        )

        self.shuffle_button.setEnabled(
            False
        )

    # ========================================================
    # UPDATE NAVIGATION
    # ========================================================

    def _update_navigation_buttons(
        self
    ) -> None:

        has_cards = bool(
            self.cards
        )

        self.shuffle_button.setEnabled(
            has_cards
        )

        if not has_cards:

            self.previous_button.setEnabled(
                False
            )

            self.next_button.setEnabled(
                False
            )

            return

        self.previous_button.setEnabled(
            self.current_index > 0
        )

        self.next_button.setEnabled(
            self.current_index
            < len(self.cards) - 1
        )

    # ========================================================
    # PREVIOUS
    # ========================================================

    def previous_card(
        self
    ) -> None:

        if not self.cards:
            return

        if self.current_index <= 0:
            return

        self.current_index -= 1

        self._show_card()

    # ========================================================
    # NEXT
    # ========================================================

    def next_card(
        self
    ) -> None:

        if not self.cards:
            return

        if self.current_index >= (
            len(self.cards) - 1
        ):
            return

        self.current_index += 1

        self._show_card()

    # ========================================================
    # SHUFFLE
    # ========================================================

    def _toggle_shuffle(
        self
    ) -> None:

        if not self.cards:
            return

        self.is_shuffled = (
            self.shuffle_button.isChecked()
        )

        # ----------------------------------------------------
        # SHUFFLE ON
        # ----------------------------------------------------

        if self.is_shuffled:

            random.shuffle(
                self.cards
            )

        # ----------------------------------------------------
        # SHUFFLE OFF
        # ----------------------------------------------------

        else:

            try:

                self.cards = (
                    self.flashcard_service
                    .get_flashcards_by_set(
                        self.current_set_id
                    )
                )

            except Exception as error:

                QMessageBox.warning(
                    self,
                    "Shuffle",
                    str(error)
                )

                return

        self.current_index = 0

        self._show_card()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(
        self
    ) -> None:
        """
        Load lại StudySet hiện tại.
        """

        if self.current_set_id is None:
            return

        self.load_study_set(
            self.current_set_id
        )

    # ========================================================
    # KEYBOARD CONTROL
    # ========================================================

    def keyPressEvent(
        self,
        event
    ) -> None:

        # ----------------------------------------------------
        # LEFT
        # ----------------------------------------------------

        if event.key() == Qt.Key_Left:

            self.previous_card()

            return

        # ----------------------------------------------------
        # RIGHT
        # ----------------------------------------------------

        if event.key() == Qt.Key_Right:

            self.next_card()

            return

        # ----------------------------------------------------
        # SPACE
        # ----------------------------------------------------

        if event.key() == Qt.Key_Space:

            if self.cards:

                self.flashcard.flip()

            return

        super().keyPressEvent(
            event
        )