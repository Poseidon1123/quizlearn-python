from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QProgressBar, QFrame, QRadioButton, QButtonGroup
from services.study_set_service import StudySetService
from services.flashcard_service import FlashcardService
from services.test_service import QUESTION_MULTIPLE_CHOICE, TestQuestion, TestService


class TestPage(QWidget):
    back_requested = Signal()

    def __init__(self, study_set_service: StudySetService, flashcard_service: FlashcardService, test_service: TestService, parent=None):
        super().__init__(parent)
        self.study_set_service = study_set_service
        self.flashcard_service = flashcard_service
        self.test_service = test_service
        self.current_set_id = None
        self.questions: list[TestQuestion] = []
        self.current_index = 0
        self.correct_count = 0
        self.answered = False
        self._setup_ui()
        self._show_empty_state()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(18)
        header = QHBoxLayout()
        self.back_button = QPushButton('← Back')
        self.back_button.setObjectName('SecondaryButton')
        self.back_button.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_button)
        self.title_label = QLabel('Test')
        self.title_label.setObjectName('PageTitle')
        header.addWidget(self.title_label)
        header.addStretch()
        self.score_label = QLabel('Score: 0 / 0')
        self.score_label.setObjectName('SecondaryText')
        header.addWidget(self.score_label)
        layout.addLayout(header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setMinimumHeight(24)
        layout.addWidget(self.progress_bar)

        self.question_frame = QFrame()
        self.question_frame.setObjectName('LearnQuestionCard')
        ql = QVBoxLayout(self.question_frame)
        self.type_label = QLabel('')
        self.type_label.setObjectName('SecondaryText')
        self.type_label.setAlignment(Qt.AlignCenter)
        ql.addWidget(self.type_label)
        self.prompt_label = QLabel('')
        self.prompt_label.setObjectName('LearnTerm')
        self.prompt_label.setAlignment(Qt.AlignCenter)
        self.prompt_label.setWordWrap(True)
        ql.addWidget(self.prompt_label)
        layout.addWidget(self.question_frame)

        self.choice_frame = QFrame()
        self.choice_frame.setObjectName('FlashcardRow')
        choices = QVBoxLayout(self.choice_frame)
        self.choice_group = QButtonGroup(self)
        self.choice_buttons = []
        for _ in range(4):
            button = QRadioButton('')
            button.setMinimumHeight(38)
            self.choice_group.addButton(button)
            self.choice_buttons.append(button)
            choices.addWidget(button)
        layout.addWidget(self.choice_frame)

        self.answer_input = QLineEdit()
        self.answer_input.setObjectName('MainInput')
        self.answer_input.setMinimumHeight(48)
        self.answer_input.returnPressed.connect(self._submit_or_next)
        layout.addWidget(self.answer_input)

        self.feedback_label = QLabel('')
        self.feedback_label.setObjectName('LearnFeedback')
        self.feedback_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.feedback_label)
        self.correct_answer_label = QLabel('')
        self.correct_answer_label.setObjectName('SecondaryText')
        self.correct_answer_label.setAlignment(Qt.AlignCenter)
        self.correct_answer_label.setWordWrap(True)
        layout.addWidget(self.correct_answer_label)

        actions = QHBoxLayout()
        actions.addStretch()
        self.submit_button = QPushButton('Submit')
        self.submit_button.setObjectName('PrimaryButton')
        self.submit_button.setMinimumWidth(160)
        self.submit_button.clicked.connect(self._submit_or_next)
        actions.addWidget(self.submit_button)
        actions.addStretch()
        layout.addLayout(actions)

        self.empty_label = QLabel('This study set does not contain any flashcards.')
        self.empty_label.setObjectName('EmptyMessage')
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)
        self.keyboard_hint = QLabel('Enter: Submit / Continue')
        self.keyboard_hint.setObjectName('SecondaryText')
        self.keyboard_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.keyboard_hint)
        layout.addStretch()

    def load_study_set(self, set_id: int) -> bool:
        try:
            study_set = self.study_set_service.get_study_set(set_id)
            cards = self.flashcard_service.get_flashcards_by_set(set_id)
            self.questions = self.test_service.build_test(cards)
        except Exception as error:
            QMessageBox.critical(self, 'Test Error', str(error))
            return False
        self.current_set_id = set_id
        self.title_label.setText(f'Test · {study_set.title}')
        self.current_index = 0
        self.correct_count = 0
        self.answered = False
        if not self.questions:
            self._show_empty_state()
            return True
        self._show_test_state()
        self._show_question()
        return True

    def _show_question(self):
        if self.current_index >= len(self.questions):
            self._finish_test()
            return
        q = self.questions[self.current_index]
        self.answered = False
        self.feedback_label.clear()
        self.correct_answer_label.clear()
        self.correct_answer_label.setVisible(False)
        self.submit_button.setText('Submit')
        direction_text = 'Term → Definition' if q.direction == 'term_to_definition' else 'Definition → Term'
        type_text = 'Multiple choice' if q.question_type == QUESTION_MULTIPLE_CHOICE else 'Written answer'
        self.type_label.setText(f'{type_text} · {direction_text}')
        self.prompt_label.setText(q.prompt)

        if q.question_type == QUESTION_MULTIPLE_CHOICE:
            self.choice_frame.setVisible(True)
            self.answer_input.setVisible(False)
            self.choice_group.setExclusive(False)
            for b in self.choice_buttons:
                b.setChecked(False)
            self.choice_group.setExclusive(True)
            for i, b in enumerate(self.choice_buttons):
                if i < len(q.options):
                    b.setText(q.options[i])
                    b.setVisible(True)
                    b.setEnabled(True)
                else:
                    b.setVisible(False)
        else:
            self.choice_frame.setVisible(False)
            self.answer_input.setVisible(True)
            self.answer_input.clear()
            self.answer_input.setEnabled(True)
            self.answer_input.setPlaceholderText('Nhập Definition...' if q.direction == 'term_to_definition' else 'Nhập Term...')
            self.answer_input.setFocus()
        self._update_progress(False)

    def _submit_or_next(self):
        if not self.questions:
            return
        if self.answered:
            self.current_index += 1
            self._show_question()
            return
        q = self.questions[self.current_index]
        try:
            if q.question_type == QUESTION_MULTIPLE_CHOICE:
                checked = self.choice_group.checkedButton()
                if checked is None:
                    raise ValueError('Hãy chọn một đáp án.')
                is_correct = self.test_service.grade_multiple_choice(q, checked.text())
                correct_answer = q.correct_answer
                typo = False
            else:
                is_correct, correct_answer, typo = self.test_service.grade_written(q, self.answer_input.text())
        except ValueError as error:
            QMessageBox.information(self, 'Test', str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, 'Test Error', str(error))
            return

        self.answered = True
        if is_correct:
            self.correct_count += 1
            self.feedback_label.setText('✓ Correct — minor typo accepted' if typo else '✓ Correct')
            if typo:
                self.correct_answer_label.setText(f'Expected answer: {correct_answer}')
                self.correct_answer_label.setVisible(True)
        else:
            self.feedback_label.setText('✗ Incorrect')
            self.correct_answer_label.setText(f'Correct answer: {correct_answer}')
            self.correct_answer_label.setVisible(True)

        if q.question_type == QUESTION_MULTIPLE_CHOICE:
            for b in self.choice_buttons:
                b.setEnabled(False)
        else:
            self.answer_input.setEnabled(False)
        self.submit_button.setText('Finish' if self.current_index == len(self.questions) - 1 else 'Continue')
        self._update_progress(True)

    def _update_progress(self, answered_current: bool):
        total = len(self.questions)
        completed = self.current_index + (1 if answered_current else 0)
        if total:
            self.progress_bar.setValue(round(completed * 100 / total))
            self.progress_bar.setFormat(f'{completed} / {total}')
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat('0 / 0')
        self.score_label.setText(f'Score: {self.correct_count} / {completed if completed else total}')

    def _finish_test(self):
        total = len(self.questions)
        percent = round(self.correct_count * 100 / total) if total else 0
        QMessageBox.information(self, 'Test Complete', f'Bạn đã hoàn thành bài kiểm tra.\n\nCorrect: {self.correct_count}\nIncorrect: {total - self.correct_count}\nScore: {percent}%')
        self.back_requested.emit()

    def _show_test_state(self):
        self.empty_label.setVisible(False)
        self.question_frame.setVisible(True)
        self.submit_button.setVisible(True)
        self.feedback_label.setVisible(True)
        self.keyboard_hint.setVisible(True)

    def _show_empty_state(self):
        self.question_frame.setVisible(False)
        self.choice_frame.setVisible(False)
        self.answer_input.setVisible(False)
        self.submit_button.setVisible(False)
        self.feedback_label.setVisible(False)
        self.correct_answer_label.setVisible(False)
        self.empty_label.setVisible(True)
        self.keyboard_hint.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('0 / 0')
