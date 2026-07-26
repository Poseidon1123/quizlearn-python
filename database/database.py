import sqlite3
from pathlib import Path
from typing import Any, Iterable


class Database:
    """
    Lớp quản lý kết nối và thao tác cơ bản với SQLite.
    """

    def __init__(self, database_path: str | Path):

        self.database_path = Path(database_path)

        # Đảm bảo thư mục chứa database tồn tại
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    # ========================================================
    # CONNECTION
    # ========================================================

    def connect(self) -> sqlite3.Connection:
        """
        Tạo và trả về kết nối tới SQLite database.
        """

        connection = sqlite3.connect(
            self.database_path
        )

        # Cho phép truy cập dữ liệu theo tên cột
        # Ví dụ:
        # row["term"]
        # thay vì chỉ row[0]
        connection.row_factory = sqlite3.Row

        # Bật kiểm tra khóa ngoại SQLite
        connection.execute(
            "PRAGMA foreign_keys = ON;"
        )

        return connection

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(
        self,
        query: str,
        parameters: Iterable[Any] = ()
    ) -> int:
        """
        Thực thi INSERT, UPDATE, DELETE hoặc các câu SQL
        không cần trả về danh sách dữ liệu.

        Trả về lastrowid.
        """

        connection = self.connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
                query,
                tuple(parameters)
            )

            connection.commit()

            return cursor.lastrowid

        except sqlite3.Error:

            connection.rollback()

            raise

        finally:

            connection.close()

    # ========================================================
    # EXECUTE MANY
    # ========================================================

    def execute_many(
        self,
        query: str,
        parameters_list: Iterable[Iterable[Any]]
    ) -> None:
        """
        Thực thi nhiều câu lệnh với cùng một query.

        Ví dụ dùng khi import nhiều flashcard.
        """

        connection = self.connect()

        try:

            cursor = connection.cursor()

            cursor.executemany(
                query,
                [
                    tuple(parameters)
                    for parameters
                    in parameters_list
                ]
            )

            connection.commit()

        except sqlite3.Error:

            connection.rollback()

            raise

        finally:

            connection.close()

    # ========================================================
    # FETCH ONE
    # ========================================================

    def fetch_one(
        self,
        query: str,
        parameters: Iterable[Any] = ()
    ) -> sqlite3.Row | None:
        """
        Lấy một dòng dữ liệu.
        """

        connection = self.connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
                query,
                tuple(parameters)
            )

            return cursor.fetchone()

        finally:

            connection.close()

    # ========================================================
    # FETCH ALL
    # ========================================================

    def fetch_all(
        self,
        query: str,
        parameters: Iterable[Any] = ()
    ) -> list[sqlite3.Row]:
        """
        Lấy toàn bộ dữ liệu phù hợp với query.
        """

        connection = self.connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
                query,
                tuple(parameters)
            )

            rows = cursor.fetchall()

            return rows

        finally:

            connection.close()

    # ========================================================
    # EXECUTE SCRIPT
    # ========================================================

    def execute_script(
        self,
        script: str
    ) -> None:
        """
        Thực thi nhiều câu SQL cùng lúc.

        Thường dùng cho schema.py.
        """

        connection = self.connect()

        try:

            cursor = connection.cursor()

            cursor.executescript(
                script
            )

            connection.commit()

        except sqlite3.Error:

            connection.rollback()

            raise

        finally:

            connection.close()

    # ========================================================
    # CHECK DATABASE
    # ========================================================

    def test_connection(self) -> bool:
        """
        Kiểm tra database có kết nối được hay không.
        """

        try:

            connection = self.connect()

            connection.execute(
                "SELECT 1;"
            )

            connection.close()

            return True

        except sqlite3.Error:

            return False
