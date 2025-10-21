import pytest

from app.models import Chat
from app.services.chat_service import ChatAlreadyBoundError, ChatService


@pytest.mark.unit
@pytest.mark.asyncio
class TestChatServiceGetMethods:
    """
    Unit tests for ChatService get methods.
    """

    async def test_get_bound_chat_exists(self, db: None, test_chat: Chat):
        """
        Test retrieving the bound chat when it exists.
        """
        service: ChatService = ChatService()

        chat: Chat | None = await service.get_bound_chat()

        assert chat is not None
        assert chat.telegram_id == test_chat.telegram_id
        assert chat.title == test_chat.title
        assert chat.chat_type == test_chat.chat_type

    async def test_get_bound_chat_not_exists(self, db: None):
        """
        Test retrieving the bound chat when no chat is bound.
        """
        service: ChatService = ChatService()

        chat: Chat | None = await service.get_bound_chat()

        assert chat is None

    async def test_get_chat_by_telegram_id_exists(self, db: None, test_chat: Chat):
        """
        Test retrieving a chat by its Telegram ID when the chat exists.
        """
        service: ChatService = ChatService()

        chat: Chat | None = await service.get_chat_by_telegram_id(
            telegram_id=test_chat.telegram_id)

        assert chat is not None
        assert chat.telegram_id == test_chat.telegram_id
        assert chat.title == test_chat.title
        assert chat.chat_type == test_chat.chat_type

    async def test_get_chat_by_telegram_id_not_exists(self, db: None):
        """
        Test retrieving a chat by its Telegram ID when the chat does not exist.
        """
        service: ChatService = ChatService()

        chat: Chat | None = await service.get_chat_by_telegram_id(
            telegram_id=-1001111111111)

        assert chat is None

    async def test_get_chat_by_telegram_id_with_thread(self, db: None, test_chat_with_thread: Chat):
        """
        Test retrieving a chat with thread by its Telegram ID.
        """
        service: ChatService = ChatService()

        chat: Chat | None = await service.get_chat_by_telegram_id(
            telegram_id=test_chat_with_thread.telegram_id)

        assert chat is not None
        assert chat.telegram_id == test_chat_with_thread.telegram_id
        assert chat.thread_id == test_chat_with_thread.thread_id
        assert chat.is_thread_enabled is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestChatServiceBindUnbind:
    """
    Unit tests for ChatService bind and unbind methods.
    """

    async def test_bind_chat_success_with_minimal_data(self, db: None):
        """
        Test binding a chat with minimal required data.
        """
        service: ChatService = ChatService()

        chat: Chat = await service.bind_chat(
            telegram_id=-1001234567890,
            chat_type='supergroup'
        )

        assert chat.id is not None
        assert chat.telegram_id == -1001234567890
        assert chat.chat_type == 'supergroup'
        assert chat.title is None
        assert chat.thread_id is None
        assert chat.is_thread_enabled is False

    async def test_bind_chat_success_with_full_data(self, db: None):
        """
        Test binding a chat with all possible data fields.
        """
        service: ChatService = ChatService()

        chat: Chat = await service.bind_chat(
            telegram_id=-1009876543210,
            chat_type='supergroup',
            title='Test Chat Full'
        )

        assert chat.id is not None
        assert chat.telegram_id == -1009876543210
        assert chat.chat_type == 'supergroup'
        assert chat.title == 'Test Chat Full'
        assert chat.thread_id is None

    async def test_bind_chat_raises_error_when_chat_already_exists(self, db: None, test_chat: Chat):
        """
        Test that binding a chat raises ChatAlreadyBoundError when a chat is already bound.
        """
        service: ChatService = ChatService()

        with pytest.raises(ChatAlreadyBoundError) as exc_info:
            await service.bind_chat(
                telegram_id=-1002222222222,
                chat_type='supergroup',
                title='Second Chat'
            )

        assert '❌ В базе уже есть привязанный чат' in str(exc_info.value)

    async def test_unbind_chat_success(self, db: None, test_chat: Chat):
        """
        Test unbinding the currently bound chat.
        """
        service: ChatService = ChatService()

        deleted_count: int = await service.unbind_chat()

        assert deleted_count == 1

        chat: Chat | None = await service.get_bound_chat()
        assert chat is None

    async def test_unbind_chat_when_no_chat_bound(self, db: None):
        """
        Test unbinding when no chat is bound.
        """
        service: ChatService = ChatService()

        deleted_count: int = await service.unbind_chat()

        assert deleted_count == 0

    async def test_bind_unbind_cycle(self, db: None):
        """
        Test binding and unbinding a chat multiple times.
        """
        service: ChatService = ChatService()

        chat1: Chat = await service.bind_chat(
            telegram_id=-1001111111111,
            chat_type='supergroup',
            title='First Chat'
        )
        assert chat1.telegram_id == -1001111111111

        deleted: int = await service.unbind_chat()
        assert deleted == 1

        chat2: Chat = await service.bind_chat(
            telegram_id=-1002222222222,
            chat_type='group',
            title='Second Chat'
        )
        assert chat2.telegram_id == -1002222222222
        assert chat2.chat_type == 'group'


@pytest.mark.unit
@pytest.mark.asyncio
class TestChatServiceThreadManagement:
    """
    Unit tests for ChatService thread management methods.
    """

    async def test_set_thread_id_success(self, db: None, test_chat: Chat):
        """
        Test setting the thread ID for a chat.
        """
        service: ChatService = ChatService()

        result: bool = await service.set_thread_id(
            telegram_id=test_chat.telegram_id,
            thread_id=12345
        )

        assert result is True

        updated_chat: Chat | None = await service.get_chat_by_telegram_id(
            telegram_id=test_chat.telegram_id)
        assert updated_chat is not None
        assert updated_chat.thread_id == 12345
        assert updated_chat.is_thread_enabled is True

    async def test_set_thread_id_chat_not_found(self, db: None):
        """
        Test setting the thread ID when chat does not exist.
        """
        service: ChatService = ChatService()

        result: bool = await service.set_thread_id(
            telegram_id=-1009999999999,
            thread_id=12345
        )

        assert result is False

    async def test_set_thread_id_overwrite_existing(self, db: None, test_chat_with_thread: Chat):
        """
        Test overwriting an existing thread ID.
        """
        service: ChatService = ChatService()

        original_thread_id: int | None = test_chat_with_thread.thread_id
        assert original_thread_id is not None

        result: bool = await service.set_thread_id(
            telegram_id=test_chat_with_thread.telegram_id,
            thread_id=99999
        )

        assert result is True

        updated_chat: Chat | None = await service.get_chat_by_telegram_id(
            test_chat_with_thread.telegram_id
        )
        assert updated_chat is not None
        assert updated_chat.thread_id == 99999
        assert updated_chat.thread_id != original_thread_id

    async def test_delete_thread_id_success(self, db: None, test_chat_with_thread: Chat):
        """
        Test deleting the thread ID from a chat.
        """
        service: ChatService = ChatService()

        assert test_chat_with_thread.thread_id is not None

        result: bool = await service.delete_thread_id(
            telegram_id=test_chat_with_thread.telegram_id
        )

        assert result is True

        updated_chat: Chat | None = await service.get_chat_by_telegram_id(
            test_chat_with_thread.telegram_id
        )
        assert updated_chat is not None
        assert updated_chat.thread_id is None
        assert updated_chat.is_thread_enabled is False

    async def test_delete_thread_id_chat_not_found(self, db: None):
        """
        Test deleting the thread ID when chat does not exist.
        """
        service: ChatService = ChatService()

        result: bool = await service.delete_thread_id(
            telegram_id=-1009999999999
        )

        assert result is False

    async def test_delete_thread_id_when_no_thread(self, db: None, test_chat: Chat):
        """
        Test deleting the thread ID when chat has no thread.
        """
        service: ChatService = ChatService()

        assert test_chat.thread_id is None

        result: bool = await service.delete_thread_id(
            telegram_id=test_chat.telegram_id
        )

        assert result is True

        updated_chat: Chat | None = await service.get_chat_by_telegram_id(
            telegram_id=test_chat.telegram_id)
        assert updated_chat is not None
        assert updated_chat.thread_id is None

    async def test_set_and_delete_thread_id_cycle(self, db: None, test_chat: Chat):
        """
        Test setting and deleting thread ID multiple times.
        """
        service: ChatService = ChatService()

        set_result: bool = await service.set_thread_id(
            telegram_id=test_chat.telegram_id,
            thread_id=11111
        )
        assert set_result is True

        chat: Chat | None = await service.get_chat_by_telegram_id(
            telegram_id=test_chat.telegram_id)
        assert chat is not None
        assert chat.thread_id == 11111

        delete_result: bool = await service.delete_thread_id(
            telegram_id=test_chat.telegram_id
        )
        assert delete_result is True

        chat = await service.get_chat_by_telegram_id(
            telegram_id=test_chat.telegram_id)
        assert chat is not None
        assert chat.thread_id is None

        set_result = await service.set_thread_id(
            telegram_id=test_chat.telegram_id,
            thread_id=22222
        )
        assert set_result is True

        chat = await service.get_chat_by_telegram_id(
            telegram_id=test_chat.telegram_id)
        assert chat is not None
        assert chat.thread_id == 22222


@pytest.mark.unit
@pytest.mark.asyncio
class TestChatServiceEdgeCases:
    """
    Unit tests for edge cases in ChatService methods.
    """

    async def test_bind_chat_with_different_chat_types(self, db: None):
        """
        Test binding chats with different chat types.
        """
        service: ChatService = ChatService()

        chat_types: list[str] = ['private', 'group', 'supergroup', 'channel']

        for idx, chat_type in enumerate(chat_types):
            if idx > 0:
                await service.unbind_chat()

            chat: Chat = await service.bind_chat(
                telegram_id=-1001000000000 - idx,
                chat_type=chat_type,
                title=f'Test {chat_type} Chat'
            )

            assert chat.chat_type == chat_type
            assert chat.title == f'Test {chat_type} Chat'

    async def test_bind_chat_with_very_long_title(self, db: None):
        """
        Test binding a chat with a very long title (max 255 chars).
        """
        service: ChatService = ChatService()

        long_title: str = 'A' * 255

        chat: Chat = await service.bind_chat(
            telegram_id=-1001234567890,
            chat_type='supergroup',
            title=long_title
        )

        assert chat.title == long_title
        assert len(chat.title) == 255

    async def test_bind_chat_with_empty_title(self, db: None):
        """
        Test binding a chat with an empty string as title.
        """
        service: ChatService = ChatService()

        chat: Chat = await service.bind_chat(
            telegram_id=-1001234567890,
            chat_type='supergroup',
            title=''
        )

        assert chat.title == ''

    async def test_get_bound_chat_returns_first_when_multiple_exist_in_db(self, db: None):
        """
        Test that get_bound_chat returns the first chat if multiple exist (edge case, should not happen in production).
        """
        service: ChatService = ChatService()

        chat1: Chat = await Chat.create(
            telegram_id=-1001111111111,
            chat_type='supergroup',
            title='First Chat'
        )
        chat2: Chat = await Chat.create(
            telegram_id=-1002222222222,
            chat_type='supergroup',
            title='Second Chat'
        )

        bound_chat: Chat | None = await service.get_bound_chat()

        assert bound_chat is not None
        assert bound_chat.telegram_id == chat1.telegram_id

    async def test_set_thread_id_with_zero(self, db: None, test_chat: Chat):
        """
        Test setting thread ID to 0 (edge case for thread ID).
        """
        service: ChatService = ChatService()

        result: bool = await service.set_thread_id(
            telegram_id=test_chat.telegram_id,
            thread_id=0
        )

        assert result is True

        chat: Chat | None = await service.get_chat_by_telegram_id(
            telegram_id=test_chat.telegram_id)
        assert chat is not None
        assert chat.thread_id == 0

    async def test_set_thread_id_with_negative_value(self, db: None, test_chat: Chat):
        """
        Test setting thread ID to a negative value (edge case).
        """
        service: ChatService = ChatService()

        result: bool = await service.set_thread_id(
            telegram_id=test_chat.telegram_id,
            thread_id=-12345
        )

        assert result is True

        chat: Chat | None = await service.get_chat_by_telegram_id(
            telegram_id=test_chat.telegram_id)
        assert chat is not None
        assert chat.thread_id == -12345

    async def test_chat_model_property_is_thread_enabled(self, db: None):
        """
        Test the is_thread_enabled property of Chat model.
        """
        service: ChatService = ChatService()

        chat_no_thread: Chat = await service.bind_chat(
            telegram_id=-1001234567890,
            chat_type='supergroup'
        )
        assert chat_no_thread.is_thread_enabled is False

        await service.set_thread_id(
            telegram_id=chat_no_thread.telegram_id,
            thread_id=12345
        )
        await chat_no_thread.refresh_from_db()
        assert chat_no_thread.is_thread_enabled is True

    async def test_unbind_chat_removes_all_chats(self, db: None):
        """
        Test that unbind_chat removes all chats from the database (if multiple exist).
        """
        service: ChatService = ChatService()

        await Chat.create(
            telegram_id=-1001111111111,
            chat_type='supergroup',
            title='First Chat'
        )
        await Chat.create(
            telegram_id=-1002222222222,
            chat_type='supergroup',
            title='Second Chat'
        )

        deleted_count: int = await service.unbind_chat()

        assert deleted_count == 2

        remaining_chats: int = await Chat.all().count()
        assert remaining_chats == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestChatServiceConcurrency:
    """
    Unit tests for concurrency scenarios in ChatService.
    """

    async def test_bind_chat_race_condition_protection(self, db: None):
        """
        Test that bind_chat protects against race conditions using transactions.
        This test verifies that only one chat can be bound even in concurrent scenarios.
        """
        service: ChatService = ChatService()

        chat1: Chat = await service.bind_chat(
            telegram_id=-1001111111111,
            chat_type='supergroup',
            title='First Chat'
        )
        assert chat1 is not None

        with pytest.raises(ChatAlreadyBoundError):
            await service.bind_chat(
                telegram_id=-1002222222222,
                chat_type='supergroup',
                title='Second Chat'
            )

        all_chats: list[Chat] = await Chat.all()
        assert len(all_chats) == 1
        assert all_chats[0].telegram_id == chat1.telegram_id
