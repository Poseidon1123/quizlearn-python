import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator


class Database:
    """
    Quản lý kết nối và các thao tác cơ bản với SQLite.

    Mặc định, mỗi lệnh ghi độc lập sẽ tự commit/rollback như trước.
    Khi chạy bên trong ``with database.transaction():``, tất cả lệnh
    execute/execute_many/fetch dùng chung một connection và chỉ commit
    khi toàn bộ transaction thành công.
    """

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Connection đang được dùng bởi transaction hiện tại.
        # Ứng dụng desktop hiện chạy thao tác DB trên UI thread nên một
        # connection active trên Database instance là đủ cho kiến trúc này.
        self._transaction_connection: sqlite3.Connection | None = None
        self._transaction_depth = 0

    # ========================================================
    # CONNECTION
    # ========================================================

    def connect(self) -> sqlite3.Connection:
        """Tạo và trả về một connection SQLite mới."""
        connection = sqlite3.connect(
            self.database_path
        )
        connection.row_factory = sqlite3.Row
        connection.execute(
            "PRAGMA foreign_keys = ON;"
        )
        return connection

    # ========================================================
    # TRANSACTION
    # ========================================================

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """
        Gom nhiều thao tác database thành một transaction nguyên tử.

        Ví dụ::

            with database.transaction():
                repository_a.update(...)
                repository_b.delete(...)
                repository_b.create(...)

        Nếu tất cả thao tác thành công -> COMMIT.
        Nếu có exception -> ROLLBACK toàn bộ.

        Transaction lồng nhau trên cùng Database instance được hỗ trợ:
        chỉ transaction ngoài cùng chịu trách nhiệm commit/rollback.
        """
        if self._transaction_connection is not None:
            self._transaction_depth += 1
            try:
                yield self._transaction_connection
            finally:
                self._transaction_depth -= 1
            return

        connection = self.connect()
        self._transaction_connection = connection
        self._transaction_depth = 1

        try:
            # BEGIN rõ ràng để transaction bao phủ cả các thao tác đọc/ghi
            # tiếp theo trên cùng connection.
            connection.execute("BEGIN;")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            self._transaction_depth = 0
            self._transaction_connection = None
            connection.close()

    # ========================================================
    # INTERNAL CONNECTION HELPERS
    # ========================================================

    def _get_connection(
        self
    ) -> tuple[sqlite3.Connection, bool]:
        """
        Trả về (connection, owns_connection).

        owns_connection=True nghĩa là method gọi hàm này đã tự mở
        connection và phải tự commit/rollback/close nó.
        """
        if self._transaction_connection is not None:
            return self._transaction_connection, False

        return self.connect(), True

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(
        self,
        query: str,
        parameters: Iterable[Any] = ()
    ) -> int:
        """
        Thực thi INSERT, UPDATE, DELETE hoặc SQL không cần trả danh sách.

        Ngoài transaction: tự commit/rollback.
        Trong transaction: để transaction ngoài cùng quản lý commit/rollback.

        Trả về lastrowid.
        """
        connection, owns_connection = self._get_connection()

        try:
            cursor = connection.cursor()
            cursor.execute(
                query,
                tuple(parameters)
            )

            if owns_connection:
                connection.commit()

            return cursor.lastrowid

        except sqlite3.Error:
            if owns_connection:
                connection.rollback()
            raise

        finally:
            if owns_connection:
                connection.close()

    # ========================================================
    # EXECUTE MANY
    # ========================================================

    def execute_many(
        self,
        query: str,
        parameters_list: Iterable[Iterable[Any]]
    ) -> None:
        """Thực thi nhiều câu lệnh với cùng một query."""
        connection, owns_connection = self._get_connection()

        try:
            cursor = connection.cursor()
            cursor.executemany(
                query,
                [
                    tuple(parameters)
                    for parameters in parameters_list
                ]
            )

            if owns_connection:
                connection.commit()

        except sqlite3.Error:
            if owns_connection:
                connection.rollback()
            raise

        finally:
            if owns_connection:
                connection.close()

    # ========================================================
    # FETCH ONE
    # ========================================================

    def fetch_one(
        self,
        query: str,
        parameters: Iterable[Any] = ()
    ) -> sqlite3.Row | None:
        """Lấy một dòng dữ liệu."""
        connection, owns_connection = self._get_connection()

        try:
            cursor = connection.cursor()
            cursor.execute(
                query,
                tuple(parameters)
            )
            return cursor.fetchone()
        finally:
            if owns_connection:
                connection.close()

    # ========================================================
    # FETCH ALL
    # ========================================================

    def fetch_all(
        self,
        query: str,
        parameters: Iterable[Any] = ()
    ) -> list[sqlite3.Row]:
        """Lấy toàn bộ dữ liệu phù hợp với query."""
        connection, owns_connection = self._get_connection()

        try:
            cursor = connection.cursor()
            cursor.execute(
                query,
                tuple(parameters)
            )
            return cursor.fetchall()
        finally:
            if owns_connection:
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

        Chủ yếu dùng cho schema/migration. Không cho chạy bên trong
        transaction() vì sqlite3.executescript() có semantics transaction
        riêng và có thể phá tính nguyên tử của transaction đang mở.
        """
        if self._transaction_connection is not None:
            raise RuntimeError(
                "execute_script() không được gọi bên trong transaction()."
            )

        connection = self.connect()

        try:
            cursor = connection.cursor()
            cursor.executescript(script)
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
        """Kiểm tra database có kết nối được hay không."""
        try:
            connection = self.connect()
            connection.execute("SELECT 1;")
            connection.close()
            return True
        except sqlite3.Error:
            return False
