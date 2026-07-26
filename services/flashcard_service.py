from models.flashcard import Flashcard

from repositories.flashcard_repository import (
    FlashcardRepository
)

from repositories.study_set_repository import (
    StudySetRepository
)


class FlashcardService:
    """
    Xử lý logic nghiệp vụ liên quan đến Flashcard.
    """

    def __init__(
        self,
        flashcard_repository: FlashcardRepository,
        study_set_repository: StudySetRepository
    ):
        self.flashcard_repository = flashcard_repository
        self.study_set_repository = study_set_repository

    # ========================================================
    # CREATE
    # ========================================================

    def create_flashcard(
        self,
        set_id: int,
        term: str,
        definition: str
    ) -> Flashcard:
        """
        Tạo một flashcard mới.
        """

        term = term.strip()
        definition = definition.strip()

        # ----------------------------------------------------
        # Validate StudySet
        # ----------------------------------------------------

        if not self.study_set_repository.exists(
            set_id
        ):
            raise ValueError(
                "Bộ học không tồn tại."
            )

        # ----------------------------------------------------
        # Validate term
        # ----------------------------------------------------

        if not term:
            raise ValueError(
                "Term / Question không được để trống."
            )

        if len(term) > 500:
            raise ValueError(
                "Term / Question quá dài."
            )

        # ----------------------------------------------------
        # Validate definition
        # ----------------------------------------------------

        if not definition:
            raise ValueError(
                "Definition / Answer không được để trống."
            )

        if len(definition) > 2000:
            raise ValueError(
                "Definition / Answer quá dài."
            )

        # ----------------------------------------------------
        # Create Model
        # ----------------------------------------------------

        flashcard = Flashcard(
            id=None,
            set_id=set_id,
            term=term,
            definition=definition
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        return self.flashcard_repository.create(
            flashcard
        )

    # ========================================================
    # CREATE MANY
    # ========================================================

    def create_many_flashcards(
        self,
        set_id: int,
        cards: list[tuple[str, str]]
    ) -> int:
        """
        Tạo nhiều flashcard cùng lúc.

        cards có dạng:

        [
            ("purchase", "mua"),
            ("equipment", "thiết bị"),
            ("available", "có sẵn")
        ]

        Trả về số lượng flashcard đã tạo.
        """

        if not self.study_set_repository.exists(
            set_id
        ):
            raise ValueError(
                "Bộ học không tồn tại."
            )

        if not cards:
            return 0

        flashcards = []

        for index, card in enumerate(
            cards,
            start=1
        ):

            if len(card) != 2:
                raise ValueError(
                    f"Flashcard số {index} không hợp lệ."
                )

            term = card[0].strip()
            definition = card[1].strip()

            if not term:
                raise ValueError(
                    f"Flashcard số {index}: "
                    "Term không được để trống."
                )

            if not definition:
                raise ValueError(
                    f"Flashcard số {index}: "
                    "Definition không được để trống."
                )

            flashcards.append(
                Flashcard(
                    id=None,
                    set_id=set_id,
                    term=term,
                    definition=definition
                )
            )

        self.flashcard_repository.create_many(
            flashcards
        )

        return len(flashcards)

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_flashcard(
        self,
        card_id: int
    ) -> Flashcard:
        """
        Lấy một flashcard theo ID.
        """

        flashcard = (
            self.flashcard_repository.get_by_id(
                card_id
            )
        )

        if flashcard is None:
            raise ValueError(
                "Không tìm thấy flashcard."
            )

        return flashcard

    # ========================================================
    # GET BY STUDY SET
    # ========================================================

    def get_flashcards_by_set(
        self,
        set_id: int
    ) -> list[Flashcard]:
        """
        Lấy toàn bộ flashcard thuộc một bộ học.
        """

        if not self.study_set_repository.exists(
            set_id
        ):
            raise ValueError(
                "Bộ học không tồn tại."
            )

        return (
            self.flashcard_repository
            .get_by_set_id(
                set_id
            )
        )

    # ========================================================
    # GET ALL
    # ========================================================

    def get_all_flashcards(
        self
    ) -> list[Flashcard]:
        """
        Lấy toàn bộ flashcard trong ứng dụng.
        """

        return (
            self.flashcard_repository
            .get_all()
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update_flashcard(
        self,
        card_id: int,
        term: str,
        definition: str
    ) -> Flashcard:
        """
        Cập nhật nội dung flashcard.
        """

        term = term.strip()
        definition = definition.strip()

        if not term:
            raise ValueError(
                "Term / Question không được để trống."
            )

        if not definition:
            raise ValueError(
                "Definition / Answer không được để trống."
            )

        existing_card = (
            self.flashcard_repository.get_by_id(
                card_id
            )
        )

        if existing_card is None:
            raise ValueError(
                "Không tìm thấy flashcard cần cập nhật."
            )

        existing_card.term = term

        existing_card.definition = (
            definition
        )

        updated_card = (
            self.flashcard_repository.update(
                existing_card
            )
        )

        if updated_card is None:
            raise RuntimeError(
                "Không thể cập nhật flashcard."
            )

        return updated_card

    # ========================================================
    # MOVE CARD
    # ========================================================

    def move_flashcard(
        self,
        card_id: int,
        new_set_id: int
    ) -> Flashcard:
        """
        Chuyển flashcard sang một StudySet khác.
        """

        if not self.study_set_repository.exists(
            new_set_id
        ):
            raise ValueError(
                "Bộ học đích không tồn tại."
            )

        flashcard = (
            self.flashcard_repository.get_by_id(
                card_id
            )
        )

        if flashcard is None:
            raise ValueError(
                "Không tìm thấy flashcard."
            )

        flashcard.set_id = new_set_id

        updated_card = (
            self.flashcard_repository.update(
                flashcard
            )
        )

        if updated_card is None:
            raise RuntimeError(
                "Không thể chuyển flashcard."
            )

        return updated_card

    # ========================================================
    # DELETE
    # ========================================================

    def delete_flashcard(
        self,
        card_id: int
    ) -> None:
        """
        Xóa một flashcard.
        """

        if not self.flashcard_repository.exists(
            card_id
        ):
            raise ValueError(
                "Không tìm thấy flashcard cần xóa."
            )

        self.flashcard_repository.delete(
            card_id
        )

    # ========================================================
    # COUNT BY SET
    # ========================================================

    def count_flashcards_by_set(
        self,
        set_id: int
    ) -> int:
        """
        Đếm số flashcard trong một StudySet.
        """

        if not self.study_set_repository.exists(
            set_id
        ):
            return 0

        return (
            self.flashcard_repository
            .count_by_set_id(
                set_id
            )
        )

    # ========================================================
    # TOTAL COUNT
    # ========================================================

    def count_all_flashcards(
        self
    ) -> int:
        """
        Đếm toàn bộ flashcard.
        """

        return (
            self.flashcard_repository.count()
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def search_flashcards(
        self,
        set_id: int,
        keyword: str
    ) -> list[Flashcard]:
        """
        Tìm kiếm flashcard trong một StudySet.
        """

        if not self.study_set_repository.exists(
            set_id
        ):
            raise ValueError(
                "Bộ học không tồn tại."
            )

        keyword = keyword.strip()

        if not keyword:

            return (
                self.flashcard_repository
                .get_by_set_id(
                    set_id
                )
            )

        return (
            self.flashcard_repository.search(
                set_id,
                keyword
            )
        )