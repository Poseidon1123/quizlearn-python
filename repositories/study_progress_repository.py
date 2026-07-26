from datetime import datetime

from database.database import Database
from models.study_progress import StudyProgress


class StudyProgressRepository:
    """Repository quản lý trạng thái học tập của flashcard."""

    def __init__(self, database: Database):
        self.database = database

    def create(self, progress: StudyProgress) -> StudyProgress:
        query = """
        INSERT INTO study_progress (
            flashcard_id,
            correct_count,
            wrong_count,
            review_count,
            status,
            ease_factor,
            interval_days,
            last_review,
            next_review
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        new_id = self.database.execute(
            query,
            (
                progress.flashcard_id,
                progress.correct_count,
                progress.wrong_count,
                progress.review_count,
                progress.status,
                progress.ease_factor,
                progress.interval_days,
                self._datetime_to_db(progress.last_review),
                self._datetime_to_db(progress.next_review),
            ),
        )

        created = self.get_by_id(new_id)
        if created is None:
            raise RuntimeError("Không thể đọc lại StudyProgress vừa tạo.")
        return created

    def get_by_id(self, progress_id: int) -> StudyProgress | None:
        row = self.database.fetch_one(
            """
            SELECT *
            FROM study_progress
            WHERE id = ?
            """,
            (progress_id,),
        )
        return self._row_to_model(row) if row is not None else None

    def get_by_flashcard_id(
        self,
        flashcard_id: int,
    ) -> StudyProgress | None:
        row = self.database.fetch_one(
            """
            SELECT *
            FROM study_progress
            WHERE flashcard_id = ?
            """,
            (flashcard_id,),
        )
        return self._row_to_model(row) if row is not None else None

    def get_by_set_id(self, set_id: int) -> list[StudyProgress]:
        rows = self.database.fetch_all(
            """
            SELECT sp.*
            FROM study_progress AS sp
            INNER JOIN flashcards AS f
                ON f.id = sp.flashcard_id
            WHERE f.set_id = ?
            ORDER BY f.id ASC
            """,
            (set_id,),
        )
        return [self._row_to_model(row) for row in rows]

    def update(self, progress: StudyProgress) -> StudyProgress:
        if progress.id is None:
            raise ValueError("Không thể update StudyProgress chưa có ID.")

        self.database.execute(
            """
            UPDATE study_progress
            SET
                correct_count = ?,
                wrong_count = ?,
                review_count = ?,
                status = ?,
                ease_factor = ?,
                interval_days = ?,
                last_review = ?,
                next_review = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                progress.correct_count,
                progress.wrong_count,
                progress.review_count,
                progress.status,
                progress.ease_factor,
                progress.interval_days,
                self._datetime_to_db(progress.last_review),
                self._datetime_to_db(progress.next_review),
                progress.id,
            ),
        )

        updated = self.get_by_id(progress.id)
        if updated is None:
            raise RuntimeError("Không thể đọc lại StudyProgress sau khi update.")
        return updated

    def delete_by_flashcard_id(self, flashcard_id: int) -> None:
        self.database.execute(
            """
            DELETE FROM study_progress
            WHERE flashcard_id = ?
            """,
            (flashcard_id,),
        )

    def get_summary_by_set_id(self, set_id: int) -> dict[str, int]:
        """
        Tổng hợp tiến độ của toàn bộ card trong Study Set.

        Flashcard chưa có row trong study_progress được tính là NEW.
        """
        row = self.database.fetch_one(
            """
            SELECT
                COUNT(f.id) AS total,
                SUM(
                    CASE
                        WHEN sp.id IS NULL OR sp.status = 'NEW' THEN 1
                        ELSE 0
                    END
                ) AS new_count,
                SUM(CASE WHEN sp.status = 'LEARNING' THEN 1 ELSE 0 END)
                    AS learning_count,
                SUM(CASE WHEN sp.status = 'REVIEW' THEN 1 ELSE 0 END)
                    AS review_count,
                SUM(CASE WHEN sp.status = 'MASTERED' THEN 1 ELSE 0 END)
                    AS mastered_count,
                SUM(
                    CASE
                        WHEN sp.next_review IS NOT NULL
                             AND sp.next_review <= CURRENT_TIMESTAMP
                             AND sp.status != 'MASTERED'
                        THEN 1
                        ELSE 0
                    END
                ) AS due_count
            FROM flashcards AS f
            LEFT JOIN study_progress AS sp
                ON sp.flashcard_id = f.id
            WHERE f.set_id = ?
            """,
            (set_id,),
        )

        if row is None:
            return {
                "total": 0,
                "new": 0,
                "learning": 0,
                "review": 0,
                "mastered": 0,
                "due": 0,
            }

        return {
            "total": int(row["total"] or 0),
            "new": int(row["new_count"] or 0),
            "learning": int(row["learning_count"] or 0),
            "review": int(row["review_count"] or 0),
            "mastered": int(row["mastered_count"] or 0),
            "due": int(row["due_count"] or 0),
        }

    @staticmethod
    def _datetime_to_db(value: datetime | None) -> str | None:
        return value.isoformat(sep=" ", timespec="seconds") if value else None

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None

    def _row_to_model(self, row) -> StudyProgress:
        return StudyProgress(
            id=row["id"],
            flashcard_id=row["flashcard_id"],
            correct_count=row["correct_count"],
            wrong_count=row["wrong_count"],
            review_count=row["review_count"],
            status=row["status"],
            ease_factor=row["ease_factor"],
            interval_days=row["interval_days"],
            last_review=self._parse_datetime(row["last_review"]),
            next_review=self._parse_datetime(row["next_review"]),
            created_at=self._parse_datetime(row["created_at"]),
            updated_at=self._parse_datetime(row["updated_at"]),
        )
