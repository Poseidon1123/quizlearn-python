from database.database import Database


# ============================================================
# DATABASE SCHEMA
# ============================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS study_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,

    description TEXT DEFAULT '',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    set_id INTEGER NOT NULL,

    term TEXT NOT NULL,

    definition TEXT NOT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (set_id)
        REFERENCES study_sets(id)
        ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS study_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    flashcard_id INTEGER NOT NULL UNIQUE,

    correct_count INTEGER NOT NULL DEFAULT 0,

    wrong_count INTEGER NOT NULL DEFAULT 0,

    review_count INTEGER NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'NEW'
        CHECK (status IN ('NEW', 'LEARNING', 'REVIEW', 'MASTERED')),

    ease_factor REAL NOT NULL DEFAULT 2.5,

    interval_days INTEGER NOT NULL DEFAULT 0,

    last_review DATETIME,

    next_review DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (flashcard_id)
        REFERENCES flashcards(id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_flashcards_set_id
ON flashcards(set_id);


CREATE INDEX IF NOT EXISTS idx_study_sets_title
ON study_sets(title);


CREATE INDEX IF NOT EXISTS idx_study_progress_status
ON study_progress(status);


CREATE INDEX IF NOT EXISTS idx_study_progress_next_review
ON study_progress(next_review);
"""


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables(database: Database) -> None:
    """
    Tạo toàn bộ bảng cần thiết cho ứng dụng.

    Hàm này an toàn khi chạy nhiều lần vì sử dụng
    CREATE TABLE IF NOT EXISTS.
    """
    database.execute_script(
        SCHEMA
    )
