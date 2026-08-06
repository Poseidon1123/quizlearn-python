import random

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QMessageBox, QSizePolicy, QProgressBar,
)

from models.study_progress import (
    RATING_AGAIN, RATING_EASY, RATING_GOOD, RATING_HARD,
)
from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService
from services.study_progress_service import StudyProgressService
from services.pronunciation_service import PronunciationService


class FlashcardWidget(QFrame):
    flipped = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Flashcard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(340)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.term = ""
        self.definition = ""
        self.showing_definition = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(55, 45, 55, 45)
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
        self.term, self.definition = term, definition
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
        self.show_front() if self.showing_definition else self.show_back()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.flip()
        super().mousePressEvent(event)


class FlashcardPage(QWidget):
    back_requested = Signal()

    def __init__(
        self,
        study_set_service: StudySetService,
        flashcard_service: FlashcardService,
        study_progress_service: StudyProgressService,
        pronunciation_service: PronunciationService,
        parent=None,
    ):
        super().__init__(parent)
        self.study_set_service = study_set_service
        self.flashcard_service = flashcard_service
        self.study_progress_service = study_progress_service
        self.pronunciation_service = pronunciation_service
        self.current_set_id = None
        self.cards = []
        self.current_index = 0
        self.reviewed_card_ids = set()
        self.rating_counts = {
            RATING_AGAIN: 0, RATING_HARD: 0,
            RATING_GOOD: 0, RATING_EASY: 0,
        }
        self.session_complete_shown = False
        self._setup_ui()
        self._show_empty_state()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setSpacing(14)

        header = QHBoxLayout()
        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("SecondaryButton")
        self.back_button.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_button)
        self.title_label = QLabel("Flashcards")
        self.title_label.setObjectName("PageTitle")
        header.addWidget(self.title_label)
        header.addStretch()
        self.speak_button = QPushButton("🔊  Pronounce")
        self.speak_button.setObjectName("PronounceButton")
        self.speak_button.clicked.connect(self._speak_current_term)
        header.addWidget(self.speak_button)
        self.shuffle_button = QPushButton("Shuffle")
        self.shuffle_button.setObjectName("SecondaryButton")
        self.shuffle_button.clicked.connect(self._shuffle)
        header.addWidget(self.shuffle_button)
        layout.addLayout(header)

        self.description_label = QLabel("")
        self.description_label.setObjectName("SecondaryText")
        layout.addWidget(self.description_label)

        progress_header = QHBoxLayout()
        self.counter_label = QLabel("0 / 0")
        self.counter_label.setObjectName("FlashcardCounter")
        progress_header.addWidget(self.counter_label)
        progress_header.addStretch()
        self.progress_text_label = QLabel("0 reviewed")
        self.progress_text_label.setObjectName("SecondaryText")
        progress_header.addWidget(self.progress_text_label)
        layout.addLayout(progress_header)

        self.session_progress = QProgressBar()
        self.session_progress.setTextVisible(False)
        self.session_progress.setFixedHeight(10)
        layout.addWidget(self.session_progress)

        self.flashcard = FlashcardWidget()
        self.flashcard.flipped.connect(self._on_card_flipped)
        layout.addWidget(self.flashcard, 1)

        self.empty_label = QLabel("This study set does not contain any flashcards.")
        self.empty_label.setObjectName("EmptyMessage")
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)

        self.card_status_label = QLabel("Flip the card, then rate your recall.")
        self.card_status_label.setObjectName("SecondaryText")
        self.card_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.card_status_label)

        rating_layout = QHBoxLayout()
        rating_layout.addStretch()
        self.rating_buttons = []
        for text, name, rating in (
            ("1  Again", "AgainButton", RATING_AGAIN),
            ("2  Hard", "HardButton", RATING_HARD),
            ("3  Good", "GoodButton", RATING_GOOD),
            ("4  Easy", "EasyButton", RATING_EASY),
        ):
            button = QPushButton(text)
            button.setObjectName(name)
            button.setMinimumSize(130, 50)
            button.clicked.connect(
                lambda checked=False, value=rating: self.rate_current_card(value)
            )
            self.rating_buttons.append(button)
            rating_layout.addWidget(button)
        rating_layout.addStretch()
        layout.addLayout(rating_layout)

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
        layout.addLayout(navigation)

        self.keyboard_hint = QLabel(
            "Space: Flip    P: Pronounce    1: Again    2: Hard    3: Good    4: Easy"
        )
        self.keyboard_hint.setObjectName("SecondaryText")
        self.keyboard_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.keyboard_hint)
        self._set_rating_enabled(False)

    def load_study_set(self, set_id: int) -> None:
        try:
            study_set = self.study_set_service.get_study_set(set_id)
            self.cards = list(self.flashcard_service.get_flashcards_by_set(set_id))
        except Exception as error:
            QMessageBox.critical(self, "Flashcards", str(error))
            return

        self.current_set_id = set_id
        self.current_index = 0
        self.reviewed_card_ids.clear()
        for key in self.rating_counts:
            self.rating_counts[key] = 0
        self.session_complete_shown = False
        self.title_label.setText(study_set.title)
        self.description_label.setText(study_set.description or "")
        self.description_label.setVisible(bool(study_set.description))
        self._update_session_progress()
        self._show_card() if self.cards else self._show_empty_state()

    def _show_card(self) -> None:
        card = self.cards[self.current_index]
        self.flashcard.set_card(card.term, card.definition)
        self.counter_label.setText(f"{self.current_index + 1} / {len(self.cards)}")
        self.flashcard.setVisible(True)
        self.empty_label.setVisible(False)
        self.speak_button.setEnabled(True)
        self.card_status_label.setText("Flip the card, then rate your recall.")
        self._set_rating_enabled(False)
        self._update_navigation()

    def _show_empty_state(self) -> None:
        self.flashcard.setVisible(False)
        self.empty_label.setVisible(True)
        self.speak_button.setEnabled(False)
        self.counter_label.setText("0 / 0")
        self._set_rating_enabled(False)
        self._update_navigation()

    def _speak_current_term(self) -> None:
        if self.cards:
            self.pronunciation_service.speak(self.cards[self.current_index].term)

    def _on_card_flipped(self, showing_definition: bool) -> None:
        self._set_rating_enabled(showing_definition and bool(self.cards))
        self.card_status_label.setText(
            "How well did you remember this card?"
            if showing_definition else "Flip the card before rating."
        )

    def rate_current_card(self, rating: str) -> None:
        if not self.cards or not self.flashcard.showing_definition:
            return
        card = self.cards[self.current_index]
        if card.id is None:
            return
        try:
            progress = self.study_progress_service.review_flashcard(card.id, rating)
        except Exception as error:
            QMessageBox.critical(self, "Study Progress", str(error))
            return
        self.reviewed_card_ids.add(card.id)
        self.rating_counts[rating] += 1
        self._update_session_progress()
        self.card_status_label.setText(
            f"{rating.title()} · next review in {progress.interval_days} day(s)"
        )
        if len(self.reviewed_card_ids) >= len(self.cards):
            self._show_session_complete()
            return
        for offset in range(1, len(self.cards) + 1):
            index = (self.current_index + offset) % len(self.cards)
            if self.cards[index].id not in self.reviewed_card_ids:
                self.current_index = index
                self._show_card()
                break

    def _update_session_progress(self) -> None:
        total = len(self.cards)
        reviewed = len(self.reviewed_card_ids)
        self.session_progress.setRange(0, max(total, 1))
        self.session_progress.setValue(reviewed)
        self.progress_text_label.setText(f"{reviewed} / {total} reviewed")

    def _show_session_complete(self) -> None:
        if self.session_complete_shown:
            return
        self.session_complete_shown = True
        QMessageBox.information(
            self, "Flashcard Session Complete",
            f"Reviewed: {len(self.reviewed_card_ids)} / {len(self.cards)}\n\n"
            f"Again: {self.rating_counts[RATING_AGAIN]}\n"
            f"Hard: {self.rating_counts[RATING_HARD]}\n"
            f"Good: {self.rating_counts[RATING_GOOD]}\n"
            f"Easy: {self.rating_counts[RATING_EASY]}",
        )

    def _set_rating_enabled(self, enabled: bool) -> None:
        for button in getattr(self, "rating_buttons", []):
            button.setEnabled(enabled)

    def _update_navigation(self) -> None:
        has_cards = bool(self.cards)
        self.previous_button.setEnabled(has_cards and self.current_index > 0)
        self.next_button.setEnabled(has_cards and self.current_index < len(self.cards) - 1)
        self.flip_button.setEnabled(has_cards)
        self.shuffle_button.setEnabled(has_cards)

    def previous_card(self) -> None:
        if self.current_index > 0:
            self.current_index -= 1
            self._show_card()

    def next_card(self) -> None:
        if self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self._show_card()

    def _shuffle(self) -> None:
        if self.cards:
            random.shuffle(self.cards)
            self.current_index = 0
            self._show_card()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Space:
            self.flashcard.flip()
        elif event.key() == Qt.Key_P:
            self._speak_current_term()
        elif event.key() in (Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4):
            ratings = {
                Qt.Key_1: RATING_AGAIN, Qt.Key_2: RATING_HARD,
                Qt.Key_3: RATING_GOOD, Qt.Key_4: RATING_EASY,
            }
            self.rate_current_card(ratings[event.key()])
        else:
            super().keyPressEvent(event)
