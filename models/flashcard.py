from dataclasses import dataclass
from datetime import datetime


@dataclass
class Flashcard:
    """
    Đại diện cho một flashcard trong ứng dụng.
    """

    id: int | None

    set_id: int

    term: str

    definition: str

    created_at: datetime | None = None

    updated_at: datetime | None = None