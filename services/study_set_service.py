from collections.abc import Iterable

from models.flashcard import Flashcard
from models.study_set import StudySet
from repositories.flashcard_repository import FlashcardRepository
from repositories.study_set_repository import StudySetRepository


class StudySetService:
    """
    Xử lý logic nghiệp vụ liên quan đến StudySet.

    Ngoài CRUD StudySet thông thường, service còn quản lý use case
    lưu đồng thời StudySet + toàn bộ thay đổi Flashcard trong một
    transaction nguyên tử.
    """

    def __init__(
        self,
        repository: StudySetRepository,
        flashcard_repository: FlashcardRepository | None = None
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
        description: str = ""
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
        card_number: int | None = None
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
        self
    ) -> FlashcardRepository:
        if self.flashcard_repository is None:
            raise RuntimeError(
                "StudySetService chưa được cấu hình FlashcardRepository."
            )

        if (
            self.flashcard_repository.database
            is not self.database
        ):
            raise RuntimeError(
                "StudySetRepository và FlashcardRepository phải dùng cùng Database."
            )

        return self.flashcard_repository

    # ========================================================
    # CREATE
    # ========================================================

    def create_study_set(
        self,
        title: str,
        description: str = ""
    ) -> StudySet:
        """Tạo một StudySet mới."""
        title, description = self._validate_study_set_content(
            title,
            description
        )

        study_set = StudySet(
            id=None,
            title=title,
            description=description
        )

        return self.repository.create(
            study_set
        )

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_study_set(
        self,
        set_id: int
    ) -> StudySet:
        """Lấy StudySet theo ID."""
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
        self
    ) -> list[StudySet]:
        """Lấy toàn bộ StudySet."""
        return self.repository.get_all()

    # ========================================================
    # UPDATE STUDY SET ONLY
    # ========================================================

    def update_study_set(
        self,
        set_id: int,
        title: str,
        description: str = ""
    ) -> StudySet:
        """Cập nhật riêng title và description của StudySet."""
        title, description = self._validate_study_set_content(
            title,
            description
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
        deleted_card_ids: Iterable[int] = ()
    ) -> StudySet:
        """
        Lưu toàn bộ thay đổi của một StudySet trong một transaction.

        ``cards`` có dạng::

            [
                (12, "purchase", "mua"),      # card đã tồn tại -> UPDATE
                (None, "equipment", "thiết bị") # card mới -> INSERT
            ]

        Card mới hoàn toàn trống được bỏ qua. Card chỉ trống một phía
        được coi là dữ liệu không hợp lệ.

        Nếu bất kỳ thao tác nào thất bại, toàn bộ UPDATE/DELETE/INSERT
        trong lần Save này sẽ rollback.
        """
        flashcard_repository = self._require_flashcard_repository()

        title, description = self._validate_study_set_content(
            title,
            description
        )

        normalized_cards: list[tuple[int | None, str, str]] = []

        for index, card in enumerate(cards, start=1):
            if len(card) != 3:
                raise ValueError(
                    f"Flashcard số {index} không hợp lệ."
                )

            card_id, term, definition = card

            # Bỏ qua dòng mới hoàn toàn trống.
            if (
                card_id is None
                and not term.strip()
                and not definition.strip()
            ):
                continue

            term, definition = self._validate_flashcard_content(
                term,
                definition,
                card_number=index
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

        # Một card vừa xuất hiện trong danh sách Save vừa nằm trong danh
        # sách Delete là trạng thái UI không hợp lệ.
        edited_ids = {
            card_id
            for card_id, _, _ in normalized_cards
            if card_id is not None
        }

        conflict_ids = edited_ids & deleted_ids
        if conflict_ids:
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

            # ------------------------------------------------
            # UPDATE STUDY SET
            # ------------------------------------------------
            existing_set.title = title
            existing_set.description = description

            updated_set = self.repository.update(
                existing_set
            )

            if updated_set is None:
                raise RuntimeError(
                    "Không thể cập nhật bộ học."
                )

            # ------------------------------------------------
            # DELETE CARDS
            # ------------------------------------------------
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

            # ------------------------------------------------
            # CREATE / UPDATE CARDS
            # ------------------------------------------------
            for card_id, term, definition in normalized_cards:
                if card_id is None:
                    flashcard_repository.create(
                        Flashcard(
                            id=None,
                            set_id=set_id,
                            term=term,
                            definition=definition
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

            # Đọc lại trước COMMIT vẫn dùng chính transaction connection.
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
        set_id: int
    ) -> None:
        """Xóa StudySet."""
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
        keyword: str
    ) -> list[StudySet]:
        """Tìm StudySet theo tên."""
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
        self
    ) -> int:
        """Đếm tổng số StudySet."""
        return self.repository.count()

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        set_id: int
    ) -> bool:
        """Kiểm tra StudySet có tồn tại không."""
        return self.repository.exists(
            set_id
        )
