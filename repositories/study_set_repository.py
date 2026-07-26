from datetime import datetime

from database.database import Database
from models.study_set import StudySet


class StudySetRepository:
    """
    Repository quản lý dữ liệu StudySet trong SQLite.
    """

    def __init__(self, database: Database):
        self.database = database

    # ========================================================
    # CREATE
    # ========================================================

    def create(
        self,
        study_set: StudySet
    ) -> StudySet:
        """
        Thêm một StudySet mới vào database.
        """

        query = """
        INSERT INTO study_sets (
            title,
            description
        )
        VALUES (?, ?)
        """

        new_id = self.database.execute(
            query,
            (
                study_set.title,
                study_set.description
            )
        )

        return self.get_by_id(new_id)

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_by_id(
        self,
        set_id: int
    ) -> StudySet | None:
        """
        Lấy StudySet theo ID.
        """

        query = """
        SELECT
            id,
            title,
            description,
            created_at,
            updated_at
        FROM study_sets
        WHERE id = ?
        """

        row = self.database.fetch_one(
            query,
            (set_id,)
        )

        if row is None:
            return None

        return self._row_to_model(row)

    # ========================================================
    # GET ALL
    # ========================================================

    def get_all(self) -> list[StudySet]:
        """
        Lấy toàn bộ StudySet.
        """

        query = """
        SELECT
            id,
            title,
            description,
            created_at,
            updated_at
        FROM study_sets
        ORDER BY created_at DESC
        """

        rows = self.database.fetch_all(
            query
        )

        return [
            self._row_to_model(row)
            for row in rows
        ]

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        study_set: StudySet
    ) -> StudySet | None:
        """
        Cập nhật title và description.
        """

        if study_set.id is None:
            raise ValueError(
                "Không thể update StudySet chưa có ID."
            )

        query = """
        UPDATE study_sets

        SET
            title = ?,
            description = ?,
            updated_at = CURRENT_TIMESTAMP

        WHERE id = ?
        """

        self.database.execute(
            query,
            (
                study_set.title,
                study_set.description,
                study_set.id
            )
        )

        return self.get_by_id(
            study_set.id
        )

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        set_id: int
    ) -> None:
        """
        Xóa StudySet theo ID.

        Flashcard thuộc StudySet này sẽ tự bị xóa
        nhờ ON DELETE CASCADE.
        """

        query = """
        DELETE FROM study_sets
        WHERE id = ?
        """

        self.database.execute(
            query,
            (set_id,)
        )

    # ========================================================
    # COUNT
    # ========================================================

    def count(self) -> int:
        """
        Đếm tổng số StudySet.
        """

        row = self.database.fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM study_sets
            """
        )

        if row is None:
            return 0

        return row["total"]

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        set_id: int
    ) -> bool:
        """
        Kiểm tra StudySet có tồn tại hay không.
        """

        row = self.database.fetch_one(
            """
            SELECT 1
            FROM study_sets
            WHERE id = ?
            LIMIT 1
            """,
            (set_id,)
        )

        return row is not None

    # ========================================================
    # SEARCH BY TITLE
    # ========================================================

    def search_by_title(
        self,
        keyword: str
    ) -> list[StudySet]:
        """
        Tìm StudySet theo title.
        """

        query = """
        SELECT
            id,
            title,
            description,
            created_at,
            updated_at

        FROM study_sets

        WHERE title LIKE ?

        ORDER BY created_at DESC
        """

        rows = self.database.fetch_all(
            query,
            (
                f"%{keyword}%",
            )
        )

        return [
            self._row_to_model(row)
            for row in rows
        ]

    # ========================================================
    # PRIVATE - ROW TO MODEL
    # ========================================================

    def _row_to_model(
        self,
        row
    ) -> StudySet:
        """
        Chuyển sqlite3.Row thành StudySet.
        """

        created_at = None
        updated_at = None

        if row["created_at"]:
            created_at = datetime.fromisoformat(
                row["created_at"]
            )

        if row["updated_at"]:
            updated_at = datetime.fromisoformat(
                row["updated_at"]
            )

        return StudySet(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            created_at=created_at,
            updated_at=updated_at
        )