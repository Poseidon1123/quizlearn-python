from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox
)

from services.study_set_service import StudySetService


class HomePage(QWidget):
    """
    Trang Home hiển thị các bộ học StudySet.
    """
    study_set_edit_requested = Signal(int)
    # Khi người dùng muốn mở một StudySet
    study_set_opened = Signal(int)

    # Khi người dùng muốn tạo StudySet mới
    create_requested = Signal()

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        study_set_service: StudySetService,
        parent=None
    ):
        super().__init__(parent)

        self.study_set_service = (
            study_set_service
        )

        self._setup_ui()

        self.refresh()

    # ========================================================
    # SETUP UI
    # ========================================================

    def _setup_ui(self) -> None:

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        layout.setSpacing(
            20
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header_layout = QHBoxLayout()

        title = QLabel(
            "Your Study Sets"
        )

        title.setObjectName(
            "PageTitle"
        )

        header_layout.addWidget(
            title
        )

        header_layout.addStretch()

        self.create_button = QPushButton(
            "+ Create Study Set"
        )

        self.create_button.setObjectName(
            "PrimaryButton"
        )

        self.create_button.setCursor(
            Qt.PointingHandCursor
        )

        self.create_button.clicked.connect(
            self.create_requested.emit
        )

        header_layout.addWidget(
            self.create_button
        )

        layout.addLayout(
            header_layout
        )

        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        self.total_sets_label = QLabel(
            "0 study sets"
        )

        self.total_sets_label.setObjectName(
            "SecondaryText"
        )

        layout.addWidget(
            self.total_sets_label
        )

        # ----------------------------------------------------
        # EMPTY MESSAGE
        # ----------------------------------------------------

        self.empty_label = QLabel(
            "Bạn chưa có bộ học nào.\n"
            "Hãy tạo Study Set đầu tiên."
        )

        self.empty_label.setAlignment(
            Qt.AlignCenter
        )

        self.empty_label.setObjectName(
            "EmptyMessage"
        )

        self.empty_label.setMinimumHeight(
            120
        )

        layout.addWidget(
            self.empty_label
        )

        # ----------------------------------------------------
        # STUDY SET LIST
        # ----------------------------------------------------

        self.study_set_list = QListWidget()

        self.study_set_list.setObjectName(
            "StudySetList"
        )

        self.study_set_list.setSpacing(
            8
        )

        self.study_set_list.itemDoubleClicked.connect(
            self._open_selected_set
        )

        layout.addWidget(
            self.study_set_list
        )

        # ----------------------------------------------------
        # ACTION BUTTONS
        # ----------------------------------------------------

        buttons_layout = QHBoxLayout()

        self.open_button = QPushButton(
            "Open"
        )
        self.edit_button = QPushButton(
            "Edit"
        )

        self.edit_button.setObjectName(
            "SecondaryButton"
        )

        self.edit_button.clicked.connect(
            self._edit_selected_set
        )

        buttons_layout.addWidget(
            self.edit_button
        )
        self.open_button.setObjectName(
            "PrimaryButton"
        )

        self.open_button.clicked.connect(
            self._open_selected_set
        )

        buttons_layout.addWidget(
            self.open_button
        )

        self.delete_button = QPushButton(
            "Delete"
        )

        self.delete_button.setObjectName(
            "DangerButton"
        )

        self.delete_button.clicked.connect(
            self._delete_selected_set
        )

        buttons_layout.addWidget(
            self.delete_button
        )

        buttons_layout.addStretch()

        layout.addLayout(
            buttons_layout
        )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(self) -> None:
        """
        Đọc lại danh sách StudySet từ service.
        """

        try:

            study_sets = (
                self.study_set_service
                .get_all_study_sets()
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Database Error",
                str(error)
            )

            return

        self.study_set_list.clear()

        # ----------------------------------------------------
        # ADD ITEMS
        # ----------------------------------------------------

        for study_set in study_sets:

            description = (
                study_set.description
                if study_set.description
                else "Không có mô tả"
            )

            text = (
                f"{study_set.title}\n"
                f"{description}"
            )

            item = QListWidgetItem(
                text
            )

            # Lưu id của StudySet vào item
            item.setData(
                Qt.UserRole,
                study_set.id
            )

            item.setToolTip(
                "Double click để mở bộ học"
            )

            self.study_set_list.addItem(
                item
            )

        # ----------------------------------------------------
        # COUNT
        # ----------------------------------------------------

        total = len(
            study_sets
        )

        self.total_sets_label.setText(
            f"{total} study set"
            if total == 1
            else f"{total} study sets"
        )

        # ----------------------------------------------------
        # EMPTY STATE
        # ----------------------------------------------------

        has_sets = total > 0

        self.empty_label.setVisible(
            not has_sets
        )

        self.study_set_list.setVisible(
            has_sets
        )

        self.open_button.setEnabled(
            has_sets
        )

        self.delete_button.setEnabled(
            has_sets
        )
        self.edit_button.setEnabled(
            has_sets
        )

    # ========================================================
    # GET SELECTED SET ID
    # ========================================================

    def _get_selected_set_id(
        self
    ) -> int | None:

        item = (
            self.study_set_list
            .currentItem()
        )

        if item is None:
            return None

        return item.data(
            Qt.UserRole
        )

    # ========================================================
    # OPEN SELECTED SET
    # ========================================================

    def _open_selected_set(
        self,
        *args
    ) -> None:

        set_id = (
            self._get_selected_set_id()
        )

        if set_id is None:

            QMessageBox.information(
                self,
                "Open Study Set",
                "Hãy chọn một bộ học trước."
            )

            return

        self.study_set_opened.emit(
            set_id
        )

    # ========================================================
    # DELETE SELECTED SET
    # ========================================================

    def _delete_selected_set(
        self
    ) -> None:

        set_id = (
            self._get_selected_set_id()
        )

        if set_id is None:

            QMessageBox.information(
                self,
                "Delete Study Set",
                "Hãy chọn một bộ học trước."
            )

            return

        # ----------------------------------------------------
        # LOAD SET
        # ----------------------------------------------------

        try:

            study_set = (
                self.study_set_service
                .get_study_set(
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

        # ----------------------------------------------------
        # CONFIRM
        # ----------------------------------------------------

        answer = QMessageBox.question(
            self,
            "Delete Study Set",
            (
                f'Bạn có chắc muốn xóa '
                f'"{study_set.title}" không?\n\n'
                f'Tất cả flashcard trong bộ này '
                f'cũng sẽ bị xóa.'
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        # ----------------------------------------------------
        # DELETE
        # ----------------------------------------------------

        try:

            self.study_set_service.delete_study_set(
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

        # ----------------------------------------------------
        # REFRESH UI
        # ----------------------------------------------------

        self.refresh()
        # ----------------------------------------------------
        # edit_selected_set
        # ---
    def _edit_selected_set(
        self
    ) -> None:

        set_id = (
            self._get_selected_set_id()
        )

        if set_id is None:

            QMessageBox.information(
                self,
                "Edit Study Set",
                "Hãy chọn một bộ học trước."
            )

            return

        self.study_set_edit_requested.emit(
            set_id
        )