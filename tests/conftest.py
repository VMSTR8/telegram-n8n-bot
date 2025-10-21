import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Chat as TelegramChat
from aiogram.types import Message as TelegramMessage
from aiogram.types import Update, User as TelegramUser
from celery.result import AsyncResult
from fastapi.testclient import TestClient
from httpx import AsyncClient
from tortoise import Tortoise

from app.api_fastapi.main import create_app
from app.models import (
    Chat,
    Penalty,
    Survey,
    User,
    UserRole
)
from app.services import (
    ChatService,
    MessageQueueService,
    PenaltyService,
    SurveyService,
    UserService
)
from config.settings import AppSettings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the event loop for the session scope.
    
    Yields:
        An instance of asyncio.AbstractEventLoop.
        
    Returns:
        Generator yielding the event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> AppSettings:
    """Provide application settings for testing."""
    settings = AppSettings(
        timezone='Europe/Moscow',
        polling_mode=True
    )
    settings.telegram.bot_token = '123456:TEST_BOT_TOKEN_FOR_TESTING'
    settings.telegram.creator_id = 123456789
    settings.telegram.webhook_url = None
    settings.telegram.webhook_secret = 'test_webhook_secret'

    settings.database.host = 'localhost'
    settings.database.port = 5432
    settings.database.user = 'test_db'
    settings.database.password = 'test_password'
    settings.database.basename = 'test_db'

    settings.rabbitmq.host = 'localhost'
    settings.rabbitmq.port = 5672
    settings.rabbitmq.user = 'test_user'
    settings.rabbitmq.password = 'test_password'

    settings.n8n.n8n_webhook_url = 'http://localhost:5678/webhook-test'
    settings.n8n.n8n_webhook_header = 'X-N8N-Secret-Token'
    settings.n8n.n8n_webhook_secret = 'test_n8n_secret'

    return settings


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[None, None]:
    """
    Initialize test database (SQLite in-memory) before each test and finalize it after the test.
    
    Returns:
        AsyncGenerator yielding None.
    """
    await Tortoise.init(
        db_url='sqlite://:memory:',
        modules={'models': [
            'app.models.user',
            'app.models.chat',
            'app.models.survey',
            'app.models.penalty',
            'app.models.survey_template'
        ]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def test_user_creator(db: None) -> User:
    """
    Create a test user with creator role.
    
    Args:
        db: Database fixture to ensure database is initialized.

    Returns:
        User: Instance representing the creator.
    """
    user = await User.create(
        telegram_id=123456789,
        username='creator_user',
        first_name='test',
        last_name='creator',
        callsign='creator',
        role=UserRole.CREATOR,
        active=True
    )
    return user


@pytest_asyncio.fixture
async def test_user_admin(db: None) -> User:
    """
    Create a test user with admin role.

    Args:
        db: Database fixture to ensure database is initialized.
    
    Returns:
        User: Instance representing the admin.
    """
    user = await User.create(
        telegram_id=987654321,
        username='admin_user',
        first_name='test_admin',
        last_name='admin',
        callsign='admin',
        role=UserRole.ADMIN,
        active=True
    )
    return user


@pytest_asyncio.fixture
async def test_user_regular(db: None) -> User:
    """
    Create a test user with regular role.

    Args:
        db: Database fixture to ensure database is initialized.
    
    Returns:
        User: Instance representing the regular user.
    """
    user = await User.create(
        telegram_id=111222333,
        username='regular_user',
        first_name='test_regular',
        last_name='regular',
        callsign='regular',
        role=UserRole.USER,
        active=True
    )
    return user


@pytest_asyncio.fixture
async def test_users_bulk(db: None) -> list[User]:
    """
    Create multiple test users for bulk operations.

    Args:
        db: Database fixture to ensure database is initialized.

    Returns:
        List of User instances representing the created users.
    """
    users = []
    for i in range(5):
        role = UserRole.USER if i > 1 else (UserRole.ADMIN if i == 1 else UserRole.CREATOR)
        user = await User.create(
            telegram_id=100000 + i,
            username=f'user_{i}',
            first_name=f'Test {i}',
            last_name=f'User {i}',
            callsign=f'user_{i}',
            role=role,
            active=True,
            reserved=False
        )
        users.append(user)
    return users


@pytest_asyncio.fixture
async def test_survey(db: None) -> Survey:
    """
    Create a test survey.

    Args:
        db: Database fixture to ensure database is initialized.

    Returns:
        Survey: Instance representing the created survey.
    """
    ended_at = datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=7)
    survey = await Survey.create(
        google_form_id='test_form_id_123',
        title='Test Survey',
        form_url='https://forms.google.com/test_form_id_123',
        ended_at=ended_at,
        expired=False
    )
    return survey


@pytest_asyncio.fixture
async def test_expired_survey(db: None) -> Survey:
    """
    Create a test expired survey.

    Args:
        db: Database fixture to ensure database is initialized.

    Returns:
        Survey: Instance representing the created expired survey.
    """
    ended_at = datetime.now(ZoneInfo('Europe/Moscow')) - timedelta(days=1)
    survey = await Survey.create(
        google_form_id='expired_form_id_456',
        title='Expired Survey',
        form_url='https://forms.google.com/expired_form_id_456',
        ended_at=ended_at,
        expired=True
    )
    return survey


@pytest_asyncio.fixture
async def test_penalty(db: None, test_user_regular: User, test_survey: Survey) -> Penalty:
    """
    Create a test penalty.

    Args:
        db: Database fixture to ensure database is initialized.
        test_user_regular: Regular user fixture.
        test_survey: Survey fixture.

    Returns:
        Penalty: Instance representing the created penalty.
    """
    penalty = await Penalty.create(
        user_id=test_user_regular,
        survey_id=test_survey,
        reason='Не прошел опрос вовремя'
    )
    return penalty


@pytest_asyncio.fixture
async def test_chat(db: None) -> Chat:
    """
    Create a test chat.

    Args:
        db: Database fixture to ensure database is initialized.

    Returns:
        Chat: Instance representing the created chat.
    """
    chat = await Chat.create(
        telegram_id=-1001234567890,
        title='Test Chat',
        chat_type='supergroup',
        thread_id=None
    )
    return chat


@pytest_asyncio.fixture
async def test_chat_with_thread(db: None) -> Chat:
    """
    Create a test chat with a thread.

    Args:
        db: Database fixture to ensure database is initialized.

    Returns:
        Chat instance representing the created chat with thread.
    """
    chat = await Chat.create(
        telegram_id=-1009876543210,
        title='Test Chat with Thread',
        chat_type='supergroup',
        thread_id=12345
    )
    return chat


@pytest.fixture
def mock_bot() -> Mock:
    """
    Create a mock Bot instance.

    Returns:
        Mock: Instance of aiogram.Bot.
    """
    bot = MagicMock(spec=Bot)
    bot.token = '123456:TEST_BOT_TOKEN_FOR_TESTING'
    bot.id = 12344321
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=1))
    bot.send_photo = AsyncMock(return_value=MagicMock(message_id=2))
    bot.ban_chat_member = AsyncMock(return_value=True)
    bot.unban_chat_member = AsyncMock(return_value=True)
    bot.get_chat = AsyncMock()
    bot.get_me = AsyncMock()
    return bot


@pytest.fixture
def mock_dispatcher() -> Dispatcher:
    """
    Create a mock Dispatcher instance.

    Returns:
        Mock instance of aiogram.Dispatcher.
    """
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    return dispatcher


@pytest.fixture
def mock_telegram_user() -> TelegramUser:
    """
    Create a mock Telegram user.

    Returns:
        TelegramUser: Instance representing the mock user.
    """
    return TelegramUser(
        id=123456789,
        is_bot=False,
        first_name='Test',
        last_name='User',
        username='test_user',
        language_code='ru'
    )


@pytest.fixture
def mock_telegram_chat() -> TelegramChat:
    """
    Create a mock Telegram chat.

    Returns:
        TelegramChat: Instance representing the mock chat.
    """
    return TelegramChat(
        id=-1001234567890,
        type='supergroup',
        title='Test Chat'
    )


@pytest.fixture
def mock_telegram_message(
        mock_telegram_user: TelegramUser,
        mock_telegram_chat: TelegramChat
) -> TelegramMessage:
    """
    Create a mock Telegram message.

    Args:
        mock_telegram_user: Mock Telegram user fixture.
        mock_telegram_chat: Mock Telegram chat fixture.

    Returns:
        TelegramMessage: Instance representing the mock message.
    """
    return TelegramMessage(
        message_id=1,
        from_user=mock_telegram_user,
        chat=mock_telegram_chat,
        date=datetime.now(tz=ZoneInfo('UTC')),
        text='/start'
    )


@pytest.fixture
def mock_telegram_update(
        mock_telegram_message: TelegramMessage
) -> Update:
    """
    Create a mock Telegram update.

    Args:
        mock_telegram_message: Mock Telegram message fixture.

    Returns:
        Update: Instance representing the mock update.
    """
    return Update(
        update_id=1000001,
        message=mock_telegram_message
    )


@pytest.fixture
def mock_user_service() -> Mock:
    """
    Create a mock UserService instance.

    Returns:
        Mock: Instance of UserService.
    """
    service = MagicMock(spec=UserService)
    service.get_user_by_telegram_id = AsyncMock(return_value=None)
    service.get_user_by_callsign = AsyncMock(return_value=None)
    service.create_user = AsyncMock()
    service.update_user = AsyncMock()
    service.delete_user = AsyncMock()
    service.get_all_users = AsyncMock(return_value=[])
    service.get_active_users = AsyncMock(return_value=[])
    service.set_user_reservation = AsyncMock()
    return service


@pytest.fixture
def mock_survey_service() -> Mock:
    """
    Create a mock SurveyService instance.

    Returns:
        Mock: Instance of SurveyService.
    """
    service = MagicMock(spec=SurveyService)
    service.create_survey = AsyncMock()
    service.get_survey_by_form_id = AsyncMock(return_value=None)
    service.update_survey = AsyncMock()
    service.mark_survey_as_expired = AsyncMock()
    service.get_all_surveys = AsyncMock(return_value=[])
    service.get_active_surveys = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_penalty_service() -> Mock:
    """
    Create a mock PenaltyService instance.

    Returns:
        Mock: Instance of PenaltyService.
    """
    service = MagicMock(spec=PenaltyService)
    service.add_penalty = AsyncMock()
    service.get_penalties_by_user = AsyncMock(return_value=[])
    service.get_penalties_by_survey = AsyncMock(return_value=[])
    service.count_user_penalties = AsyncMock(return_value=0)
    service.delete_all_penalties = AsyncMock()
    return service


@pytest.fixture
def mock_chat_service() -> Mock:
    """
    Create a mock ChatService instance.

    Returns:
        Mock: Instance of ChatService.
    """
    service = MagicMock(spec=ChatService)
    service.get_or_create_chat = AsyncMock()
    service.get_chat_by_telegram_id = AsyncMock(return_value=None)
    service.update_chat = AsyncMock()
    service.get_all_chats = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_message_queue_service() -> Mock:
    """
    Create a mock MessageQueueService instance.

    Returns:
        Mock: Instance of MessageQueueService.
    """
    service = MagicMock(spec=MessageQueueService)
    service.send_message = AsyncMock()
    service.send_bulk_messages = AsyncMock()
    return service


@pytest.fixture
def mock_celery_task() -> Mock:
    """
    Create a mock Celery task.

    Returns:
        Mock: Instance of a Celery task.
    """
    task = MagicMock()
    task.apply_async = MagicMock(return_value=MagicMock(id='test_task_id'))
    task.delay = MagicMock(return_value=MagicMock(id='test_task_id'))
    return task


@pytest.fixture
def mock_celery_async_result() -> Mock:
    """
    Create a mock Celery AsyncResult.

    Returns:
        Mock: Instance of Celery AsyncResult.
    """
    mock_result = Mock(spec=AsyncResult)
    mock_result.id = 'test-task-id-12345'
    mock_result.status = 'PENDING'
    mock_result.ready.return_value = False
    mock_result.result = None

    return mock_result


@pytest.fixture
def mock_n8n_webhook() -> Mock:
    """
    Create a mock for N8N webhook calls.

    Returns:
        Mock: Instance representing the N8N webhook.
    """
    client = AsyncMock()
    client.post = AsyncMock(return_value=MagicMock(
        status_code=200,
        json=MagicMock(return_value={"status": "success"})
    ))
    return client


@pytest.fixture
def mock_rabbitmq_connection() -> Mock:
    """
    Create a mock RabbitMQ connection.

    Returns:
        Mock: Instance representing the RabbitMQ connection.
    """
    connection = MagicMock()
    channel = MagicMock()
    connection.channel = MagicMock(return_value=channel)
    return connection


@pytest.fixture
def test_client(test_settings: AppSettings) -> TestClient:
    """
    Create a TestClient for FastAPI application.

    Args:
        test_settings: Application settings fixture.
    
    Returns:
        TestClient: Instance of FastAPI TestClient.
    """
    with patch('config.settings.settings', test_settings):
        app = create_app()
        client = TestClient(app)
        return client


@pytest_asyncio.fixture
async def async_client(test_settings: AppSettings) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an AsyncClient for FastAPI application.

    Args:
        test_settings: Application settings fixture.

    Yields:
        AsyncClient: Instance of FastAPI AsyncClient.
    """
    with patch('config.settings.settings', test_settings):
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client


@pytest.fixture
def sample_survey_data() -> dict:
    """
    Provide sample survey data for testing.

    Returns:
        dict: Sample survey data.
    """
    return {
        "google_form_id": "sample_form_id_789",
        "title": "Sample Survey for Testing",
        "form_url": "https://forms.google.com/sample_form_id_789",
        "ended_at": (datetime.now(tz=ZoneInfo("Europe/Moscow")) + timedelta(days=3)).isoformat(),
    }


@pytest.fixture
def sample_webhook_payload() -> dict:
    """
    Provide sample webhook payload data for testing.

    Returns:
        dict: Sample webhook payload data.
    """
    return {
        "event": "form_created",
        "data": {
            "form_id": "webhook_form_123",
            "title": "Webhook Survey",
            "url": "https://forms.google.com/webhook_form_123",
            "deadline": (datetime.now(tz=ZoneInfo("Europe/Moscow")) + timedelta(days=5)).isoformat(),
        }
    }


@pytest.fixture
def sample_completed_survey_response() -> dict:
    """
    Provide sample completed survey response data for testing.

    Returns:
        dict: Sample completed survey response data.
    """
    return {
        "form_id": "test_form_id_123",
        "completed_users": ["Chertolet", "Gennadich"],
        "not_completed_users": ["Chert"],
    }


@pytest.fixture
def caplog_debug(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """
    Configure caplog to capture debug level logs.

    Args:
        caplog: Pytest LogCaptureFixture.

    Returns:
        LogCaptureFixture: Configured caplog fixture.
    """
    caplog.set_level('DEBUG')
    return caplog


@pytest.fixture
def moscow_timezone() -> ZoneInfo:
    """
    Provide Moscow timezone information.

    Returns:
        ZoneInfo: Instance representing Moscow timezone.
    """
    return ZoneInfo('Europe/Moscow')


@pytest.fixture
def datetime_now_moscow(moscow_timezone: ZoneInfo) -> datetime:
    """
    Provide current datetime in Moscow timezone.

    Args:
        moscow_timezone: Moscow timezone fixture.

    Returns:
        datetime: Current datetime in Moscow timezone.
    """
    return datetime.now(tz=moscow_timezone)
