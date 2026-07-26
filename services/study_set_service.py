from models.study_set import StudySet
from repositories.study_set_repository import StudySetRepository


class StudySetService:
    """
    Xử lý logic nghiệp vụ liên quan đến StudySet.
    """

    def __init__(
        self,
        repository: StudySetRepository
    ):
        self.repository = repository

    # ========================================================
    # CREATE
    # ========================================================

    def create_study_set(
        self,
        title: str,
        description: str = ""
    ) -> StudySet:
        """
        Tạo một StudySet mới.
        """

        title = title.strip()
        description = description.strip()

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        if not title:
            raise ValueError(
                "Tên bộ học không được để trống."
            )

        if len(title) > 100:
            raise ValueError(
                "Tên bộ học không được vượt quá 100 ký tự."
            )

        # ----------------------------------------------------
        # Create model
        # ----------------------------------------------------

        study_set = StudySet(
            id=None,
            title=title,
            description=description
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        return self.repository.create(
            study_set
        )

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_study_set(
        self,
        set_id: int
    ) -> StudySet:
        """
        Lấy StudySet theo ID.
        """

        study_set = self.repository.get_by_id(
            set_id
        )

        if study_set is None:
            raise ValueError(
                "Không tìm thấy bộ học."
            )

        return study_set

    # ========================================================
    # GET ALL
    # ========================================================

    def get_all_study_sets(
        self
    ) -> list[StudySet]:
        """
        Lấy toàn bộ StudySet.
        """

        return self.repository.get_all()

    # ========================================================
    # UPDATE
    # ========================================================

    def update_study_set(
        self,
        set_id: int,
        title: str,
        description: str = ""
    ) -> StudySet:
        """
        Cập nhật một StudySet.
        """

        title = title.strip()
        description = description.strip()

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        if not title:
            raise ValueError(
                "Tên bộ học không được để trống."
            )

        if len(title) > 100:
            raise ValueError(
                "Tên bộ học không được vượt quá 100 ký tự."
            )

        # ----------------------------------------------------
        # Check existing
        # ----------------------------------------------------

        existing_set = (
            self.repository.get_by_id(
                set_id
            )
        )

        if existing_set is None:
            raise ValueError(
                "Không tìm thấy bộ học cần cập nhật."
            )

        # ----------------------------------------------------
        # Update model
        # ----------------------------------------------------

        existing_set.title = title
        existing_set.description = description

        updated_set = self.repository.update(
            existing_set
        )

        if updated_set is None:
            raise RuntimeError(
                "Không thể cập nhật bộ học."
            )

        return updated_set

    # ========================================================
    # DELETE
    # ========================================================

    def delete_study_set(
        self,
        set_id: int
    ) -> None:
        """
        Xóa StudySet.
        """

        if not self.repository.exists(
            set_id
        ):
            raise ValueError(
                "Không tìm thấy bộ học cần xóa."
            )

        self.repository.delete(
            set_id
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def search_study_sets(
        self,
        keyword: str
    ) -> list[StudySet]:
        """
        Tìm StudySet theo tên.
        """

        keyword = keyword.strip()

        if not keyword:

            return self.get_all_study_sets()

        return self.repository.search_by_title(
            keyword
        )

    # ========================================================
    # COUNT
    # ========================================================

    def count_study_sets(
        self
    ) -> int:
        """
        Đếm tổng số StudySet.
        """

        return self.repository.count()

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        set_id: int
    ) -> bool:
        """
        Kiểm tra StudySet có tồn tại không.
        """

        return self.repository.exists(
            set_id
        )