from datetime import datetime

from database.database import Database
from models.flashcard import Flashcard


class FlashcardRepository:
    """
    Repository quản lý dữ liệu Flashcard trong SQLite.
    """

    def __init__(self, database: Database):
        self.database = database

    # ========================================================
    # CREATE
    # ========================================================

    def create(
        self,
        flashcard: Flashcard
    ) -> Flashcard:
        """
        Thêm một flashcard mới vào database.
        """

        query = """
        INSERT INTO flashcards (
            set_id,
            term,
            definition
        )
        VALUES (?, ?, ?)
        """

        new_id = self.database.execute(
            query,
            (
                flashcard.set_id,
                flashcard.term,
                flashcard.definition
            )
        )

        return self.get_by_id(new_id)

    # ========================================================
    # CREATE MANY
    # ========================================================

    def create_many(
        self,
        flashcards: list[Flashcard]
    ) -> None:
        """
        Thêm nhiều flashcard cùng lúc.
        """

        if not flashcards:
            return

        query = """
        INSERT INTO flashcards (
            set_id,
            term,
            definition
        )
        VALUES (?, ?, ?)
        """

        parameters = [
            (
                card.set_id,
                card.term,
                card.definition
            )
            for card in flashcards
        ]

        self.database.execute_many(
            query,
            parameters
        )

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_by_id(
        self,
        card_id: int
    ) -> Flashcard | None:
        """
        Lấy flashcard theo ID.
        """

        query = """
        SELECT
            id,
            set_id,
            term,
            definition,
            created_at,
            updated_at

        FROM flashcards

        WHERE id = ?
        """

        row = self.database.fetch_one(
            query,
            (card_id,)
        )

        if row is None:
            return None

        return self._row_to_model(
            row
        )

    # ========================================================
    # GET ALL
    # ========================================================

    def get_all(self) -> list[Flashcard]:
        """
        Lấy toàn bộ flashcard trong database.
        """

        query = """
        SELECT
            id,
            set_id,
            term,
            definition,
            created_at,
            updated_at

        FROM flashcards

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
    # GET BY STUDY SET
    # ========================================================

    def get_by_set_id(
        self,
        set_id: int
    ) -> list[Flashcard]:
        """
        Lấy toàn bộ flashcard thuộc một StudySet.
        """

        query = """
        SELECT
            id,
            set_id,
            term,
            definition,
            created_at,
            updated_at

        FROM flashcards

        WHERE set_id = ?

        ORDER BY id ASC
        """

        rows = self.database.fetch_all(
            query,
            (set_id,)
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
        flashcard: Flashcard
    ) -> Flashcard | None:
        """
        Cập nhật flashcard.
        """

        if flashcard.id is None:
            raise ValueError(
                "Không thể update Flashcard chưa có ID."
            )

        query = """
        UPDATE flashcards

        SET
            set_id = ?,
            term = ?,
            definition = ?,
            updated_at = CURRENT_TIMESTAMP

        WHERE id = ?
        """

        self.database.execute(
            query,
            (
                flashcard.set_id,
                flashcard.term,
                flashcard.definition,
                flashcard.id
            )
        )

        return self.get_by_id(
            flashcard.id
        )

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        card_id: int
    ) -> None:
        """
        Xóa một flashcard theo ID.
        """

        query = """
        DELETE FROM flashcards
        WHERE id = ?
        """

        self.database.execute(
            query,
            (card_id,)
        )

    # ========================================================
    # DELETE BY SET
    # ========================================================

    def delete_by_set_id(
        self,
        set_id: int
    ) -> None:
        """
        Xóa toàn bộ flashcard thuộc một StudySet.

        Bình thường không bắt buộc phải gọi hàm này khi xóa
        StudySet vì schema đã có ON DELETE CASCADE.
        """

        query = """
        DELETE FROM flashcards
        WHERE set_id = ?
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
        Đếm tổng số flashcard.
        """

        row = self.database.fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM flashcards
            """
        )

        if row is None:
            return 0

        return row["total"]

    # ========================================================
    # COUNT BY SET
    # ========================================================

    def count_by_set_id(
        self,
        set_id: int
    ) -> int:
        """
        Đếm số flashcard thuộc một StudySet.
        """

        row = self.database.fetch_one(
            """
            SELECT COUNT(*) AS total

            FROM flashcards

            WHERE set_id = ?
            """,
            (set_id,)
        )

        if row is None:
            return 0

        return row["total"]

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        card_id: int
    ) -> bool:
        """
        Kiểm tra flashcard có tồn tại hay không.
        """

        row = self.database.fetch_one(
            """
            SELECT 1

            FROM flashcards

            WHERE id = ?

            LIMIT 1
            """,
            (card_id,)
        )

        return row is not None

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self,
        set_id: int,
        keyword: str
    ) -> list[Flashcard]:
        """
        Tìm flashcard trong một StudySet theo term
        hoặc definition.
        """

        query = """
        SELECT
            id,
            set_id,
            term,
            definition,
            created_at,
            updated_at

        FROM flashcards

        WHERE
            set_id = ?
            AND (
                term LIKE ?
                OR definition LIKE ?
            )

        ORDER BY id ASC
        """

        pattern = f"%{keyword}%"

        rows = self.database.fetch_all(
            query,
            (
                set_id,
                pattern,
                pattern
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
    ) -> Flashcard:
        """
        Chuyển sqlite3.Row thành Flashcard.
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

        return Flashcard(
            id=row["id"],
            set_id=row["set_id"],
            term=row["term"],
            definition=row["definition"],
            created_at=created_at,
            updated_at=updated_at
        )