import random

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QProgressBar, QFrame, QComboBox

from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService
from services.learning_service import DIRECTION_DEFINITION_TO_TERM, DIRECTION_TERM_TO_DEFINITION, LearningService
from services.pronunciation_service import PronunciationService

MODE_TERM_TO_DEFINITION = "term_to_definition"
MODE_DEFINITION_TO_TERM = "definition_to_term"
MODE_MIXED = "mixed"


class LearnPage(QWidget):
    back_requested = Signal()

    def __init__(self, study_set_service: StudySetService, flashcard_service: FlashcardService, learning_service: LearningService, pronunciation_service: PronunciationService, parent=None):
        super().__init__(parent)
        self.study_set_service = study_set_service
        self.flashcard_service = flashcard_service
        self.learning_service = learning_service
        self.pronunciation_service = pronunciation_service
        self.current_set_id = None
        self.all_cards = []
        self.queue = []
        self.current_card = None
        self.current_direction = DIRECTION_TERM_TO_DEFINITION
        self.total_initial = self.correct_count = self.wrong_count = self.answered_count = 0
        self.awaiting_next = False
        self._setup_ui()
        self._show_empty_state()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(18)
        header = QHBoxLayout()
        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("SecondaryButton")
        self.back_button.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_button)
        self.title_label = QLabel("Learn")
        self.title_label.setObjectName("PageTitle")
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.setMinimumWidth(220)
        self.mode_combo.addItem("Term → Definition", MODE_TERM_TO_DEFINITION)
        self.mode_combo.addItem("Definition → Term", MODE_DEFINITION_TO_TERM)
        self.mode_combo.addItem("Mixed", MODE_MIXED)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        header.addWidget(self.mode_combo)
        layout.addLayout(header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setMinimumHeight(26)
        layout.addWidget(self.progress_bar)

        self.question_frame = QFrame()
        self.question_frame.setObjectName("LearnQuestionCard")
        ql = QVBoxLayout(self.question_frame)
        ql.setContentsMargins(35, 35, 35, 35)
        self.prompt_label = QLabel("")
        self.prompt_label.setObjectName("SecondaryText")
        self.prompt_label.setAlignment(Qt.AlignCenter)
        ql.addWidget(self.prompt_label)
        self.question_label = QLabel("")
        self.question_label.setObjectName("LearnTerm")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setWordWrap(True)
        ql.addWidget(self.question_label)
        self.speak_button = QPushButton("🔊  Pronounce English")
        self.speak_button.setObjectName("PronounceButton")
        self.speak_button.clicked.connect(self._speak_english)
        ql.addWidget(self.speak_button, alignment=Qt.AlignCenter)
        layout.addWidget(self.question_frame, 1)

        self.answer_input = QLineEdit()
        self.answer_input.setObjectName("MainInput")
        self.answer_input.setMinimumHeight(54)
        self.answer_input.returnPressed.connect(self._submit_or_next)
        layout.addWidget(self.answer_input)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("LearnFeedback")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.feedback_label)
        self.correct_answer_label = QLabel("")
        self.correct_answer_label.setObjectName("SecondaryText")
        self.correct_answer_label.setAlignment(Qt.AlignCenter)
        self.correct_answer_label.setWordWrap(True)
        self.correct_answer_label.setVisible(False)
        layout.addWidget(self.correct_answer_label)

        actions = QHBoxLayout()
        actions.addStretch()
        self.submit_button = QPushButton("Check")
        self.submit_button.setObjectName("PrimaryButton")
        self.submit_button.setMinimumSize(170, 50)
        self.submit_button.clicked.connect(self._submit_or_next)
        actions.addWidget(self.submit_button)
        actions.addStretch()
        layout.addLayout(actions)

        self.stats_label = QLabel("Correct: 0    Incorrect: 0")
        self.stats_label.setObjectName("SecondaryText")
        self.stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_label)
        self.empty_label = QLabel("This study set does not contain any flashcards.")
        self.empty_label.setObjectName("EmptyMessage")
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)
        self.keyboard_hint = QLabel("Enter: Check / Continue    P: Pronounce English")
        self.keyboard_hint.setObjectName("SecondaryText")
        self.keyboard_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.keyboard_hint)

    def load_study_set(self, set_id: int) -> bool:
        try:
            study_set = self.study_set_service.get_study_set(set_id)
            self.all_cards = list(self.flashcard_service.get_flashcards_by_set(set_id))
        except Exception as error:
            QMessageBox.critical(self, "Learn", str(error))
            return False
        self.current_set_id = set_id
        self.title_label.setText(f"Learn · {study_set.title}")
        if not self.all_cards:
            self._show_empty_state()
            return True
        self._show_study_state()
        self._restart_session()
        return True

    def _show_study_state(self):
        for widget in (self.question_frame, self.answer_input, self.submit_button, self.feedback_label, self.stats_label, self.keyboard_hint):
            widget.setVisible(True)
        self.empty_label.setVisible(False)
        self.mode_combo.setEnabled(True)

    def _restart_session(self):
        self.queue = [(card, self._choose_direction()) for card in self.all_cards]
        random.shuffle(self.queue)
        self.total_initial = len(self.queue)
        self.correct_count = self.wrong_count = self.answered_count = 0
        self.stats_label.setText("Correct: 0    Incorrect: 0")
        self._show_next_card()

    def _choose_direction(self):
        mode = self.mode_combo.currentData() or MODE_TERM_TO_DEFINITION
        if mode == MODE_DEFINITION_TO_TERM:
            return DIRECTION_DEFINITION_TO_TERM
        if mode == MODE_MIXED:
            return random.choice([DIRECTION_TERM_TO_DEFINITION, DIRECTION_DEFINITION_TO_TERM])
        return DIRECTION_TERM_TO_DEFINITION

    def _on_mode_changed(self):
        if self.all_cards:
            self._restart_session()

    def _show_next_card(self):
        if not self.queue:
            self._finish_session()
            return
        self.current_card, self.current_direction = self.queue.pop(0)
        prompt, displayed, hint = self.learning_service.get_prompt_and_answer_hint(self.current_card, self.current_direction)
        self.prompt_label.setText(prompt)
        self.question_label.setText(displayed)
        self.answer_input.setPlaceholderText(hint)
        self.answer_input.clear()
        self.answer_input.setEnabled(True)
        self.answer_input.setFocus()
        self.feedback_label.clear()
        self.correct_answer_label.clear()
        self.correct_answer_label.setVisible(False)
        self.submit_button.setText("Check")
        self.awaiting_next = False
        self._update_progress()

    def _speak_english(self):
        if self.current_card is not None:
            self.pronunciation_service.speak(self.current_card.term)

    def _submit_or_next(self):
        if self.current_card is None:
            return
        if self.awaiting_next:
            self._show_next_card()
            return
        try:
            result = self.learning_service.submit_answer(self.current_card, self.answer_input.text(), direction=self.current_direction)
        except ValueError as error:
            QMessageBox.information(self, "Learn", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "Learn", str(error))
            return
        self.answered_count += 1
        self.answer_input.setEnabled(False)
        if result.is_correct:
            self.correct_count += 1
            self.feedback_label.setText("✓ Correct — minor typo accepted" if result.accepted_with_typo else "✓ Correct")
            if result.accepted_with_typo:
                self.correct_answer_label.setText(f"Expected answer: {result.canonical_answer}")
                self.correct_answer_label.setVisible(True)
        else:
            self.wrong_count += 1
            self.feedback_label.setText("✗ Incorrect")
            self.correct_answer_label.setText(f"Correct answer: {result.canonical_answer}")
            self.correct_answer_label.setVisible(True)
            self.queue.append((self.current_card, self.current_direction))
        self.stats_label.setText(f"Correct: {self.correct_count}    Incorrect: {self.wrong_count}")
        self.submit_button.setText("Continue")
        self.awaiting_next = True
        self._update_progress()

    def _update_progress(self):
        if not self.total_initial:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0 / 0")
            return
        completed = self.total_initial - len(self.queue) - (0 if self.awaiting_next else 1)
        if self.awaiting_next and self.feedback_label.text().startswith("✓"):
            completed += 1
        completed = max(0, min(completed, self.total_initial))
        self.progress_bar.setValue(round(completed * 100 / self.total_initial))
        self.progress_bar.setFormat(f"{completed} / {self.total_initial} mastered")

    def _finish_session(self):
        self.current_card = None
        QMessageBox.information(self, "Learn Session Complete", f"Correct attempts: {self.correct_count}\nIncorrect attempts: {self.wrong_count}\nTotal attempts: {self.answered_count}")
        self.back_requested.emit()

    def _show_empty_state(self):
        self.current_card = None
        for widget in (self.question_frame, self.answer_input, self.submit_button, self.feedback_label, self.correct_answer_label, self.stats_label, self.keyboard_hint):
            widget.setVisible(False)
        self.empty_label.setVisible(True)
        self.mode_combo.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0 / 0")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_P:
            self._speak_english()
        else:
            super().keyPressEvent(event)
