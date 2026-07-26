from dataclasses import dataclass
from datetime import datetime


STATUS_NEW = "NEW"
STATUS_LEARNING = "LEARNING"
STATUS_REVIEW = "REVIEW"
STATUS_MASTERED = "MASTERED"

VALID_PROGRESS_STATUSES = {
    STATUS_NEW,
    STATUS_LEARNING,
    STATUS_REVIEW,
    STATUS_MASTERED,
}

RATING_AGAIN = "AGAIN"
RATING_HARD = "HARD"
RATING_GOOD = "GOOD"
RATING_EASY = "EASY"

VALID_REVIEW_RATINGS = {
    RATING_AGAIN,
    RATING_HARD,
    RATING_GOOD,
    RATING_EASY,
}


@dataclass
class StudyProgress:
    """Trạng thái học tập của một flashcard."""

    id: int | None
    flashcard_id: int
    correct_count: int = 0
    wrong_count: int = 0
    review_count: int = 0
    status: str = STATUS_NEW
    ease_factor: float = 2.5
    interval_days: int = 0
    last_review: datetime | None = None
    next_review: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
