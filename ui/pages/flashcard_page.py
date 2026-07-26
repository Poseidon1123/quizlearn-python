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
    QSizePolicy,
    QProgressBar,
)

from models.study_progress import (
    RATING_AGAIN,
    RATING_EASY,
    RATING_GOOD,
    RATING_HARD,
)
from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService
from services.study_progress_service import StudyProgressService


class FlashcardWidget(QFrame):
    """Flashcard có thể lật giữa Term và Definition."""

    flipped = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Flashcard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(300)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.term = ""
        self.definition = ""
        self.showing_definition = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 45, 50, 45)
        layout.addStretch()

        self.side_label = QLabel("TERM")
        self.side_label.setObjectName("FlashcardSide")
        self.side_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.side_label)
        layout.addSpacing(18)

        self.text_label = QLabel("")
        self.text_label.setObjectName("FlashcardText")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.text_label)

        layout.addStretch()

        self.hint_label = QLabel("Click the card or press Space to flip")
        self.hint_label.setObjectName("FlashcardHint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint_label)

    def set_card(self, term: str, definition: str) -> None:
        self.term = term
        self.definition = definition
        self.show_front()

    def show_front(self) -> None:
        self.showing_definition = False
        self.side_label.setText("TERM")
        self.text_label.setText(self.term)
        self.flipped.emit(False)

    def show_back(self) -> None:
        self.showing_definition = True
        self.side_label.setText("DEFINITION")
        self.text_label.setText(self.definition)
        self.flipped.emit(True)

    def flip(self) -> None:
        if self.showing_definition:
            self.show_front()
        else:
            self.show_back()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.flip()
        super().mousePressEvent(event)


class FlashcardPage(QWidget):
    """
    Flashcard study mode.

    Sau khi xem đáp án, người học tự đánh giá bằng Again / Hard / Good /
    Easy. Mỗi đánh giá được ghi vào StudyProgress và tạo lịch ôn tiếp.
    """

    back_requested = Signal()

    def __init__(
        self,
        study_set_service: StudySetService,
        flashcard_service: FlashcardService,
        study_progress_service: StudyProgressService,
        parent=None,
    ):
        super().__init__(parent)

        self.study_set_service = study_set_service
        self.flashcard_service = flashcard_service
        self.study_progress_service = study_progress_service

        self.current_set_id: int | None = None
        self.cards = []
        self.current_index = 0
        self.is_shuffled = False

        self.reviewed_card_ids: set[int] = set()
        self.rating_counts = {
            RATING_AGAIN: 0,
            RATING_HARD: 0,
            RATING_GOOD: 0,
            RATING_EASY: 0,
        }
        self.session_complete_shown = False

        self._setup_ui()
        self._show_empty_state()

    # ========================================================
    # UI
    # ========================================================

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 25, 40, 25)
        main_layout.setSpacing(14)

        header = QHBoxLayout()

        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("SecondaryButton")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_button)

        header.addSpacing(15)

        self.title_label = QLabel("Flashcards")
        self.title_label.setObjectName("PageTitle")
        header.addWidget(self.title_label)
        header.addStretch()

        self.shuffle_button = QPushButton("Shuffle")
        self.shuffle_button.setObjectName("SecondaryButton")
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.setCursor(Qt.PointingHandCursor)
        self.shuffle_button.clicked.connect(self._toggle_shuffle)
        header.addWidget(self.shuffle_button)

        main_layout.addLayout(header)

        self.description_label = QLabel("")
        self.description_label.setObjectName("SecondaryText")
        self.description_label.setWordWrap(True)
        main_layout.addWidget(self.description_label)

        # Session progress.
        progress_header = QHBoxLayout()

        self.counter_label = QLabel("0 / 0")
        self.counter_label.setObjectName("FlashcardCounter")
        progress_header.addWidget(self.counter_label)

        progress_header.addStretch()

        self.progress_text_label = QLabel("0 reviewed")
        self.progress_text_label.setObjectName("SecondaryText")
        progress_header.addWidget(self.progress_text_label)

        main_layout.addLayout(progress_header)

        self.session_progress = QProgressBar()
        self.session_progress.setObjectName("StudyProgressBar")
        self.session_progress.setRange(0, 1)
        self.session_progress.setValue(0)
        self.session_progress.setTextVisible(False)
        self.session_progress.setFixedHeight(8)
        main_layout.addWidget(self.session_progress)

        # Card.
        self.flashcard = FlashcardWidget()
        self.flashcard.flipped.connect(self._on_card_flipped)
        main_layout.addWidget(self.flashcard, 1)

        self.empty_label = QLabel(
            "This study set does not contain any flashcards."
        )
        self.empty_label.setObjectName("EmptyMessage")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        main_layout.addWidget(self.empty_label)

        # Current progress / schedule information.
        self.card_status_label = QLabel(
            "Flip the card, then rate how well you remembered it."
        )
        self.card_status_label.setObjectName("SecondaryText")
        self.card_status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.card_status_label)

        # Rating buttons.
        rating_layout = QHBoxLayout()
        rating_layout.addStretch()

        self.again_button = self._create_rating_button(
            "1  Again",
            "AgainButton",
            RATING_AGAIN,
        )
        self.hard_button = self._create_rating_button(
            "2  Hard",
            "HardButton",
            RATING_HARD,
        )
        self.good_button = self._create_rating_button(
            "3  Good",
            "GoodButton",
            RATING_GOOD,
        )
        self.easy_button = self._create_rating_button(
            "4  Easy",
            "EasyButton",
            RATING_EASY,
        )

        self.rating_buttons = [
            self.again_button,
            self.hard_button,
            self.good_button,
            self.easy_button,
        ]

        for button in self.rating_buttons:
            rating_layout.addWidget(button)

        rating_layout.addStretch()
        main_layout.addLayout(rating_layout)

        # Navigation remains available for free review, but rating advances
        # automatically to the next unreviewed card.
        navigation = QHBoxLayout()
        navigation.addStretch()

        self.previous_button = QPushButton("← Previous")
        self.previous_button.setObjectName("SecondaryButton")
        self.previous_button.clicked.connect(self.previous_card)
        navigation.addWidget(self.previous_button)

        self.flip_button = QPushButton("Flip")
        self.flip_button.setObjectName("PrimaryButton")
        self.flip_button.clicked.connect(self.flashcard.flip)
        navigation.addWidget(self.flip_button)

        self.next_button = QPushButton("Next →")
        self.next_button.setObjectName("SecondaryButton")
        self.next_button.clicked.connect(self.next_card)
        navigation.addWidget(self.next_button)

        navigation.addStretch()
        main_layout.addLayout(navigation)

        self.keyboard_hint = QLabel(
            "Space: Flip    1: Again    2: Hard    3: Good    4: Easy"
        )
        self.keyboard_hint.setObjectName("SecondaryText")
        self.keyboard_hint.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.keyboard_hint)

        self._set_rating_enabled(False)

    def _create_rating_button(
        self,
        text: str,
        object_name: str,
        rating: str,
    ) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setMinimumWidth(125)
        button.setMinimumHeight(46)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(
            lambda checked=False, value=rating: self.rate_current_card(value)
        )
        return button

    # ========================================================
    # LOAD / DISPLAY
    # ========================================================

    def load_study_set(self, set_id: int) -> None:
        try:
            study_set = self.study_set_service.get_study_set(set_id)
            cards = self.flashcard_service.get_flashcards_by_set(set_id)
        except ValueError as error:
            QMessageBox.warning(self, "Study Set", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "Database Error", str(error))
            return

        self.current_set_id = set_id
        self.cards = list(cards)
        self.current_index = 0
        self.is_shuffled = False
        self.shuffle_button.setChecked(False)

        self.reviewed_card_ids.clear()
        for rating in self.rating_counts:
            self.rating_counts[rating] = 0
        self.session_complete_shown = False

        self.title_label.setText(study_set.title)
        self.description_label.setText(study_set.description or "")
        self.description_label.setVisible(bool(study_set.description))

        self._update_session_progress()

        if not self.cards:
            self._show_empty_state()
            return

        self._show_card()

    def _show_card(self) -> None:
        if not self.cards:
            self._show_empty_state()
            return

        self.current_index = max(
            0,
            min(self.current_index, len(self.cards) - 1),
        )
        card = self.cards[self.current_index]

        self.flashcard.set_card(
            term=card.term,
            definition=card.definition,
        )

        self.counter_label.setText(
            f"{self.current_index + 1} / {len(self.cards)}"
        )

        self.flashcard.setVisible(True)
        self.empty_label.setVisible(False)
        self.flip_button.setEnabled(True)
        self.shuffle_button.setEnabled(True)

        self.card_status_label.setText(
            "Flip the card, then rate how well you remembered it."
        )
        self._set_rating_enabled(False)
        self._update_navigation_buttons()

    def _show_empty_state(self) -> None:
        self.flashcard.setVisible(False)
        self.empty_label.setVisible(True)
        self.counter_label.setText("0 / 0")
        self.progress_text_label.setText("0 reviewed")
        self.session_progress.setRange(0, 1)
        self.session_progress.setValue(0)

        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.flip_button.setEnabled(False)
        self.shuffle_button.setEnabled(False)
        self._set_rating_enabled(False)

    def _on_card_flipped(self, showing_definition: bool) -> None:
        self._set_rating_enabled(
            bool(self.cards) and showing_definition
        )

        if showing_definition:
            self.card_status_label.setText(
                "How well did you remember this card?"
            )
        else:
            self.card_status_label.setText(
                "Flip the card before rating your recall."
            )

    # ========================================================
    # RATING / STUDY PROGRESS
    # ========================================================

    def rate_current_card(self, rating: str) -> None:
        if not self.cards or not self.flashcard.showing_definition:
            return

        card = self.cards[self.current_index]
        if card.id is None:
            QMessageBox.warning(
                self,
                "Flashcard",
                "Flashcard chưa có ID hợp lệ.",
            )
            return

        self._set_rating_enabled(False)

        try:
            progress = self.study_progress_service.review_flashcard(
                flashcard_id=card.id,
                rating=rating,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Study Progress", str(error))
            self._set_rating_enabled(True)
            return
        except Exception as error:
            QMessageBox.critical(self, "Database Error", str(error))
            self._set_rating_enabled(True)
            return

        self.reviewed_card_ids.add(card.id)
        self.rating_counts[rating] += 1
        self._update_session_progress()

        schedule_text = self._format_schedule(progress)
        self.card_status_label.setText(
            f"{rating.title()} · {schedule_text} · {progress.status.title()}"
        )

        if len(self.reviewed_card_ids) >= len(self.cards):
            self._show_session_complete()
            return

        next_index = self._find_next_unreviewed_index()
        if next_index is not None:
            self.current_index = next_index
            self._show_card()

    def _find_next_unreviewed_index(self) -> int | None:
        if not self.cards:
            return None

        total = len(self.cards)
        for offset in range(1, total + 1):
            index = (self.current_index + offset) % total
            card_id = self.cards[index].id
            if card_id is not None and card_id not in self.reviewed_card_ids:
                return index

        return None

    def _update_session_progress(self) -> None:
        total = len(self.cards)
        reviewed = len(self.reviewed_card_ids)

        self.session_progress.setRange(0, max(total, 1))
        self.session_progress.setValue(reviewed)
        self.progress_text_label.setText(
            f"{reviewed} / {total} reviewed"
        )

    @staticmethod
    def _format_schedule(progress) -> str:
        if progress.interval_days == 0:
            return "review again in about 10 min"
        if progress.interval_days == 1:
            return "next review in 1 day"
        return f"next review in {progress.interval_days} days"

    def _show_session_complete(self) -> None:
        if self.session_complete_shown:
            return

        self.session_complete_shown = True
        self._set_rating_enabled(False)
        self.card_status_label.setText("Session complete")

        QMessageBox.information(
            self,
            "Flashcard Session Complete",
            (
                f"Reviewed: {len(self.reviewed_card_ids)} / {len(self.cards)}\n\n"
                f"Again: {self.rating_counts[RATING_AGAIN]}\n"
                f"Hard: {self.rating_counts[RATING_HARD]}\n"
                f"Good: {self.rating_counts[RATING_GOOD]}\n"
                f"Easy: {self.rating_counts[RATING_EASY]}"
            ),
        )

    def _set_rating_enabled(self, enabled: bool) -> None:
        if not hasattr(self, "rating_buttons"):
            return
        for button in self.rating_buttons:
            button.setEnabled(enabled)

    # ========================================================
    # NAVIGATION
    # ========================================================

    def _update_navigation_buttons(self) -> None:
        has_cards = bool(self.cards)
        self.previous_button.setEnabled(
            has_cards and self.current_index > 0
        )
        self.next_button.setEnabled(
            has_cards and self.current_index < len(self.cards) - 1
        )
        self.shuffle_button.setEnabled(has_cards)

    def previous_card(self) -> None:
        if self.cards and self.current_index > 0:
            self.current_index -= 1
            self._show_card()

    def next_card(self) -> None:
        if self.cards and self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self._show_card()

    def _toggle_shuffle(self) -> None:
        if not self.cards:
            return

        self.is_shuffled = self.shuffle_button.isChecked()

        if self.is_shuffled:
            random.shuffle(self.cards)
        else:
            try:
                self.cards = list(
                    self.flashcard_service.get_flashcards_by_set(
                        self.current_set_id
                    )
                )
            except Exception as error:
                QMessageBox.warning(self, "Shuffle", str(error))
                return

        self.current_index = 0
        self._show_card()

    def refresh(self) -> None:
        if self.current_set_id is not None:
            self.load_study_set(self.current_set_id)

    # ========================================================
    # KEYBOARD
    # ========================================================

    def keyPressEvent(self, event) -> None:
        key = event.key()

        if key == Qt.Key_Left:
            self.previous_card()
            return

        if key == Qt.Key_Right:
            self.next_card()
            return

        if key == Qt.Key_Space:
            if self.cards:
                self.flashcard.flip()
            return

        if self.flashcard.showing_definition:
            if key == Qt.Key_1:
                self.rate_current_card(RATING_AGAIN)
                return
            if key == Qt.Key_2:
                self.rate_current_card(RATING_HARD)
                return
            if key == Qt.Key_3:
                self.rate_current_card(RATING_GOOD)
                return
            if key == Qt.Key_4:
                self.rate_current_card(RATING_EASY)
                return

        super().keyPressEvent(event)
