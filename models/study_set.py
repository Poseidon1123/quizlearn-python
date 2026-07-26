from dataclasses import dataclass
from datetime import datetime


@dataclass
class StudySet:
    """
    Đại diện cho một bộ flashcard.
    """

    id: int | None

    title: str

    description: str = ""

    created_at: datetime | None = None

    updated_at: datetime | None = None