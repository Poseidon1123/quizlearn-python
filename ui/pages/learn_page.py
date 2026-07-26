import random

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QFrame,
)

from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService
from services.learning_service import LearningService


class LearnPage(QWidget):
    """Learn Mode: hiển thị Term và yêu cầu người dùng nhập Definition."""

    back_requested = Signal()

    def __init__(
        self,
        study_set_service: StudySetService,
        flashcard_service: FlashcardService,
        learning_service: LearningService,
        parent=None,
    ):
        super().__init__(parent)

        self.study_set_service = study_set_service
        self.flashcard_service = flashcard_service
        self.learning_service = learning_service

        self.current_set_id: int | None = None
        self.queue = []
        self.current_card = None
        self.total_initial = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.answered_count = 0
        self.awaiting_next = False

        self._setup_ui()
        self._show_empty_state()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(18)

        header = QHBoxLayout()

        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("SecondaryButton")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_button)

        header.addSpacing(16)

        self.title_label = QLabel("Learn")
        self.title_label.setObjectName("PageTitle")
        header.addWidget(self.title_label)
        header.addStretch()

        layout.addLayout(header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0 / 0")
        self.progress_bar.setMinimumHeight(24)
        layout.addWidget(self.progress_bar)

        self.question_frame = QFrame()
        self.question_frame.setObjectName("LearnQuestionCard")
        question_layout = QVBoxLayout(self.question_frame)
        question_layout.setContentsMargins(32, 30, 32, 30)
        question_layout.setSpacing(14)

        prompt = QLabel("What is the definition of:")
        prompt.setObjectName("SecondaryText")
        prompt.setAlignment(Qt.AlignCenter)
        question_layout.addWidget(prompt)

        self.term_label = QLabel("")
        self.term_label.setObjectName("LearnTerm")
        self.term_label.setAlignment(Qt.AlignCenter)
        self.term_label.setWordWrap(True)
        question_layout.addWidget(self.term_label)

        layout.addWidget(self.question_frame, 1)

        self.answer_input = QLineEdit()
        self.answer_input.setObjectName("MainInput")
        self.answer_input.setPlaceholderText("Nhập Definition...")
        self.answer_input.setMinimumHeight(48)
        self.answer_input.returnPressed.connect(self._submit_or_next)
        layout.addWidget(self.answer_input)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("LearnFeedback")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setWordWrap(True)
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
        self.submit_button.setMinimumWidth(160)
        self.submit_button.setMinimumHeight(46)
        self.submit_button.clicked.connect(self._submit_or_next)
        actions.addWidget(self.submit_button)

        actions.addStretch()
        layout.addLayout(actions)

        self.stats_label = QLabel("Correct: 0    Incorrect: 0")
        self.stats_label.setObjectName("SecondaryText")
        self.stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_label)

        self.empty_label = QLabel(
            "This study set does not contain any flashcards."
        )
        self.empty_label.setObjectName("EmptyMessage")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)

        self.keyboard_hint = QLabel("Enter: Check / Continue")
        self.keyboard_hint.setObjectName("SecondaryText")
        self.keyboard_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.keyboard_hint)

    def load_study_set(self, set_id: int) -> bool:
        try:
            study_set = self.study_set_service.get_study_set(set_id)
            cards = self.flashcard_service.get_flashcards_by_set(set_id)
        except ValueError as error:
            QMessageBox.warning(self, "Learn", str(error))
            return False
        except Exception as error:
            QMessageBox.critical(self, "Database Error", str(error))
            return False

        self.current_set_id = set_id
        self.title_label.setText(f"Learn · {study_set.title}")

        self.queue = list(cards)
        random.shuffle(self.queue)
        self.total_initial = len(self.queue)
        self.correct_count = 0
        self.wrong_count = 0
        self.answered_count = 0
        self.awaiting_next = False

        if not self.queue:
            self._show_empty_state()
            return True

        self.empty_label.setVisible(False)
        self.question_frame.setVisible(True)
        self.answer_input.setVisible(True)
        self.submit_button.setVisible(True)
        self.feedback_label.setVisible(True)
        self.stats_label.setVisible(True)
        self.keyboard_hint.setVisible(True)

        self._show_next_card()
        return True

    def _show_next_card(self) -> None:
        if not self.queue:
            self._finish_session()
            return

        self.current_card = self.queue.pop(0)
        self.term_label.setText(self.current_card.term)

        self.answer_input.clear()
        self.answer_input.setEnabled(True)
        self.answer_input.setFocus()

        self.feedback_label.clear()
        self.correct_answer_label.clear()
        self.correct_answer_label.setVisible(False)

        self.submit_button.setText("Check")
        self.awaiting_next = False
        self._update_progress()

    def _submit_or_next(self) -> None:
        if self.current_card is None:
            return

        if self.awaiting_next:
            self._show_next_card()
            return

        try:
            is_correct, correct_answer = self.learning_service.submit_answer(
                self.current_card,
                self.answer_input.text(),
            )
        except ValueError as error:
            QMessageBox.information(self, "Learn", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "Learn Error", str(error))
            return

        self.answered_count += 1
        self.answer_input.setEnabled(False)

        if is_correct:
            self.correct_count += 1
            self.feedback_label.setText("✓ Correct")
        else:
            self.wrong_count += 1
            self.feedback_label.setText("✗ Incorrect")
            self.correct_answer_label.setText(
                f"Correct answer: {correct_answer}"
            )
            self.correct_answer_label.setVisible(True)

            # Câu sai được đưa về cuối hàng đợi để học lại.
            self.queue.append(self.current_card)

        self.stats_label.setText(
            f"Correct: {self.correct_count}    Incorrect: {self.wrong_count}"
        )

        self.submit_button.setText("Continue")
        self.awaiting_next = True
        self._update_progress()

    def _update_progress(self) -> None:
        if self.total_initial <= 0:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0 / 0")
            return

        # Số card gốc đã vượt qua ít nhất một lần đúng.
        completed = max(
            0,
            self.total_initial - len(self.queue) - (1 if self.current_card else 0),
        )

        if self.awaiting_next and self.feedback_label.text().startswith("✓"):
            completed += 1

        completed = min(completed, self.total_initial)
        percent = round(completed * 100 / self.total_initial)
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(
            f"{completed} / {self.total_initial} mastered this session"
        )

    def _finish_session(self) -> None:
        self.current_card = None
        self.progress_bar.setValue(100 if self.total_initial else 0)
        self.progress_bar.setFormat(
            f"{self.total_initial} / {self.total_initial} completed"
            if self.total_initial
            else "0 / 0"
        )

        QMessageBox.information(
            self,
            "Learn Session Complete",
            (
                "Bạn đã hoàn thành Learn Mode.\n\n"
                f"Correct attempts: {self.correct_count}\n"
                f"Incorrect attempts: {self.wrong_count}\n"
                f"Total attempts: {self.answered_count}"
            ),
        )

        self.back_requested.emit()

    def _show_empty_state(self) -> None:
        self.current_card = None
        self.question_frame.setVisible(False)
        self.answer_input.setVisible(False)
        self.submit_button.setVisible(False)
        self.feedback_label.setVisible(False)
        self.correct_answer_label.setVisible(False)
        self.stats_label.setVisible(False)
        self.empty_label.setVisible(True)
        self.keyboard_hint.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0 / 0")
