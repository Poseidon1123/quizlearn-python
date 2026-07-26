from collections.abc import Iterable

from models.flashcard import Flashcard
from models.study_set import StudySet
from repositories.flashcard_repository import FlashcardRepository
from repositories.study_set_repository import StudySetRepository


class StudySetService:
    """
    Xử lý logic nghiệp vụ liên quan đến StudySet.

    Các use case tạo/sửa StudySet kèm Flashcard đều được thực hiện
    trong transaction để đảm bảo dữ liệu luôn nhất quán.
    """

    def __init__(
        self,
        repository: StudySetRepository,
        flashcard_repository: FlashcardRepository | None = None,
    ):
        self.repository = repository
        self.flashcard_repository = flashcard_repository
        self.database = repository.database

    # ========================================================
    # VALIDATION HELPERS
    # ========================================================

    @staticmethod
    def _validate_study_set_content(
        title: str,
        description: str = "",
    ) -> tuple[str, str]:
        title = title.strip()
        description = description.strip()

        if not title:
            raise ValueError(
                "Tên bộ học không được để trống."
            )

        if len(title) > 100:
            raise ValueError(
                "Tên bộ học không được vượt quá 100 ký tự."
            )

        return title, description

    @staticmethod
    def _validate_flashcard_content(
        term: str,
        definition: str,
        card_number: int | None = None,
    ) -> tuple[str, str]:
        term = term.strip()
        definition = definition.strip()

        prefix = (
            f"Flashcard số {card_number}: "
            if card_number is not None
            else ""
        )

        if not term:
            raise ValueError(
                f"{prefix}Term / Question không được để trống."
            )

        if len(term) > 500:
            raise ValueError(
                f"{prefix}Term / Question quá dài."
            )

        if not definition:
            raise ValueError(
                f"{prefix}Definition / Answer không được để trống."
            )

        if len(definition) > 2000:
            raise ValueError(
                f"{prefix}Definition / Answer quá dài."
            )

        return term, definition

    def _require_flashcard_repository(
        self,
    ) -> FlashcardRepository:
        if self.flashcard_repository is None:
            raise RuntimeError(
                "StudySetService chưa được cấu hình FlashcardRepository."
            )

        if self.flashcard_repository.database is not self.database:
            raise RuntimeError(
                "StudySetRepository và FlashcardRepository phải dùng cùng Database."
            )

        return self.flashcard_repository

    def _normalize_new_cards(
        self,
        cards: Iterable[tuple[str, str]],
    ) -> list[tuple[str, str]]:
        normalized_cards: list[tuple[str, str]] = []

        for index, card in enumerate(cards, start=1):
            if len(card) != 2:
                raise ValueError(
                    f"Flashcard số {index} không hợp lệ."
                )

            term, definition = card

            # Cho phép UI có các dòng mới hoàn toàn trống.
            if not term.strip() and not definition.strip():
                continue

            term, definition = self._validate_flashcard_content(
                term,
                definition,
                card_number=index,
            )

            normalized_cards.append(
                (term, definition)
            )

        if not normalized_cards:
            raise ValueError(
                "Study Set phải có ít nhất một flashcard."
            )

        return normalized_cards

    # ========================================================
    # CREATE STUDY SET ONLY
    # ========================================================

    def create_study_set(
        self,
        title: str,
        description: str = "",
    ) -> StudySet:
        """Tạo riêng một StudySet, không kèm Flashcard."""
        title, description = self._validate_study_set_content(
            title,
            description,
        )

        return self.repository.create(
            StudySet(
                id=None,
                title=title,
                description=description,
            )
        )

    # ========================================================
    # CREATE STUDY SET + FLASHCARDS
    # ========================================================

    def create_study_set_with_flashcards(
        self,
        title: str,
        description: str,
        cards: Iterable[tuple[str, str]],
    ) -> StudySet:
        """
        Tạo StudySet và toàn bộ Flashcard trong một transaction.

        Nếu bất kỳ INSERT nào thất bại, StudySet và tất cả Flashcard
        vừa tạo trong transaction sẽ được rollback hoàn toàn.
        """
        flashcard_repository = self._require_flashcard_repository()

        title, description = self._validate_study_set_content(
            title,
            description,
        )
        normalized_cards = self._normalize_new_cards(cards)

        with self.database.transaction():
            study_set = self.repository.create(
                StudySet(
                    id=None,
                    title=title,
                    description=description,
                )
            )

            if study_set.id is None:
                raise RuntimeError(
                    "Không thể xác định ID của Study Set vừa tạo."
                )

            for term, definition in normalized_cards:
                flashcard_repository.create(
                    Flashcard(
                        id=None,
                        set_id=study_set.id,
                        term=term,
                        definition=definition,
                    )
                )

            final_set = self.repository.get_by_id(
                study_set.id
            )

            if final_set is None:
                raise RuntimeError(
                    "Không thể đọc lại Study Set sau khi tạo."
                )

            return final_set

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_study_set(
        self,
        set_id: int,
    ) -> StudySet:
        study_set = self.repository.get_by_id(
            set_id
        )

        if study_set is None:
            raise ValueError(
                "Không tìm thấy bộ học."
            )

        return study_set

    # ========================================================
    # GET ALL
    # ========================================================

    def get_all_study_sets(
        self,
    ) -> list[StudySet]:
        return self.repository.get_all()

    # ========================================================
    # UPDATE STUDY SET ONLY
    # ========================================================

    def update_study_set(
        self,
        set_id: int,
        title: str,
        description: str = "",
    ) -> StudySet:
        title, description = self._validate_study_set_content(
            title,
            description,
        )

        existing_set = self.repository.get_by_id(
            set_id
        )

        if existing_set is None:
            raise ValueError(
                "Không tìm thấy bộ học cần cập nhật."
            )

        existing_set.title = title
        existing_set.description = description

        updated_set = self.repository.update(
            existing_set
        )

        if updated_set is None:
            raise RuntimeError(
                "Không thể cập nhật bộ học."
            )

        return updated_set

    # ========================================================
    # SAVE STUDY SET + FLASHCARDS
    # ========================================================

    def save_study_set_with_flashcards(
        self,
        set_id: int,
        title: str,
        description: str,
        cards: list[tuple[int | None, str, str]],
        deleted_card_ids: Iterable[int] = (),
    ) -> StudySet:
        """Lưu toàn bộ thay đổi StudySet + Flashcard trong transaction."""
        flashcard_repository = self._require_flashcard_repository()

        title, description = self._validate_study_set_content(
            title,
            description,
        )

        normalized_cards: list[tuple[int | None, str, str]] = []

        for index, card in enumerate(cards, start=1):
            if len(card) != 3:
                raise ValueError(
                    f"Flashcard số {index} không hợp lệ."
                )

            card_id, term, definition = card

            if (
                card_id is None
                and not term.strip()
                and not definition.strip()
            ):
                continue

            term, definition = self._validate_flashcard_content(
                term,
                definition,
                card_number=index,
            )

            normalized_cards.append(
                (card_id, term, definition)
            )

        if not normalized_cards:
            raise ValueError(
                "Study Set phải có ít nhất một flashcard."
            )

        deleted_ids = {
            int(card_id)
            for card_id in deleted_card_ids
        }

        edited_ids = {
            card_id
            for card_id, _, _ in normalized_cards
            if card_id is not None
        }

        if edited_ids & deleted_ids:
            raise ValueError(
                "Có flashcard vừa được sửa vừa được đánh dấu xóa."
            )

        with self.database.transaction():
            existing_set = self.repository.get_by_id(
                set_id
            )

            if existing_set is None:
                raise ValueError(
                    "Không tìm thấy bộ học cần cập nhật."
                )

            existing_set.title = title
            existing_set.description = description

            updated_set = self.repository.update(
                existing_set
            )

            if updated_set is None:
                raise RuntimeError(
                    "Không thể cập nhật bộ học."
                )

            for card_id in deleted_ids:
                existing_card = flashcard_repository.get_by_id(
                    card_id
                )

                if existing_card is None:
                    raise ValueError(
                        f"Không tìm thấy flashcard ID {card_id} cần xóa."
                    )

                if existing_card.set_id != set_id:
                    raise ValueError(
                        "Không thể xóa flashcard thuộc Study Set khác."
                    )

                flashcard_repository.delete(
                    card_id
                )

            for card_id, term, definition in normalized_cards:
                if card_id is None:
                    flashcard_repository.create(
                        Flashcard(
                            id=None,
                            set_id=set_id,
                            term=term,
                            definition=definition,
                        )
                    )
                    continue

                existing_card = flashcard_repository.get_by_id(
                    card_id
                )

                if existing_card is None:
                    raise ValueError(
                        f"Không tìm thấy flashcard ID {card_id} cần cập nhật."
                    )

                if existing_card.set_id != set_id:
                    raise ValueError(
                        "Không thể cập nhật flashcard thuộc Study Set khác."
                    )

                existing_card.term = term
                existing_card.definition = definition

                updated_card = flashcard_repository.update(
                    existing_card
                )

                if updated_card is None:
                    raise RuntimeError(
                        f"Không thể cập nhật flashcard ID {card_id}."
                    )

            final_set = self.repository.get_by_id(
                set_id
            )

            if final_set is None:
                raise RuntimeError(
                    "Không thể đọc lại Study Set sau khi cập nhật."
                )

            return final_set

    # ========================================================
    # DELETE
    # ========================================================

    def delete_study_set(
        self,
        set_id: int,
    ) -> None:
        if not self.repository.exists(
            set_id
        ):
            raise ValueError(
                "Không tìm thấy bộ học cần xóa."
            )

        self.repository.delete(
            set_id
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def search_study_sets(
        self,
        keyword: str,
    ) -> list[StudySet]:
        keyword = keyword.strip()

        if not keyword:
            return self.get_all_study_sets()

        return self.repository.search_by_title(
            keyword
        )

    # ========================================================
    # COUNT
    # ========================================================

    def count_study_sets(
        self,
    ) -> int:
        return self.repository.count()

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        set_id: int,
    ) -> bool:
        return self.repository.exists(
            set_id
        )
