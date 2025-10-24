import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, Mock, patch
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from celery.result import AsyncResult
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise

from app.api_fastapi.dependencies import verify_n8n_webhook_secret, verify_telegram_webhook_secret
from app.api_fastapi.main import create_app
from app.models import (
    Chat,
    Penalty,
    Survey,
    User,
    UserRole
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


@pytest_asyncio.fixture
async def async_client(test_settings: AppSettings) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an AsyncClient for FastAPI application.

    Args:
        test_settings: Application settings fixture.

    Yields:
        AsyncClient: Instance of FastAPI AsyncClient.
    """

    async def mock_verify_n8n_secret(x_n8n_secret_token: str | None = None) -> str:
        return 'test_n8n_secret'

    async def mock_verify_telegram_secret(x_telegram_bot_api_secret_token: str | None = None) -> str:
        return 'test_webhook_secret'

    with patch('config.settings.settings', test_settings):
        app = create_app()
        app.dependency_overrides[verify_n8n_webhook_secret] = mock_verify_n8n_secret
        app.dependency_overrides[verify_telegram_webhook_secret] = mock_verify_telegram_secret

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            yield client

        app.dependency_overrides.clear()


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


@pytest_asyncio.fixture
async def test_user_without_reservation(db: None) -> User:
    """
    Create a test user without reservation status.

    Args:
        db: Database fixture to ensure database is initialized.

    Returns:
        User: Instance representing the user without reservation.
    """
    user = await User.create(
        telegram_id=444555666,
        username='no_reservation_user',
        first_name='test_no_res',
        last_name='user',
        callsign='nores',
        role=UserRole.USER,
        active=True,
        reserved=False
    )
    return user
