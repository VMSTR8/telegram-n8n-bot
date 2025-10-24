from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from fastapi import status

from app.models import Chat, Survey, User


@pytest.mark.asyncio
class TestNewFormWebhook:
    """Test suite for /webhook/new-form endpoint"""

    async def test_new_form_webhook_success(
            self,
            async_client: AsyncClient,
            db: None,
            test_chat: Chat,
            test_settings
    ):
        """
        Test successful processing of new form webhook.
        Should send message to bound chat and return success response.
        """
        mock_chat_service = MagicMock()
        mock_chat_service.get_bound_chat = AsyncMock(return_value=test_chat)

        mock_mq_service = MagicMock()
        mock_mq_service.send_and_pin_message = AsyncMock()

        with patch('app.api_fastapi.routers.n8n_webhook.settings', test_settings), \
             patch('app.api_fastapi.dependencies.ChatService', return_value=mock_chat_service), \
             patch('app.api_fastapi.dependencies.MessageQueueService', return_value=mock_mq_service):

            form_data = {
                'id': 1,
                'google_form_id': 'test_form_123',
                'title': 'New Test Survey',
                'form_url': 'https://forms.google.com/test_form_123',
                'created_at': datetime.now(tz=ZoneInfo('Europe/Moscow')).isoformat(),
                'ended_at': (datetime.now(tz=ZoneInfo('Europe/Moscow')) + timedelta(days=7)).isoformat(),
                'expired': False
            }

            response = await async_client.post(
                '/webhook/new-form',
                json=form_data,
                headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
            )

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data['success'] == 'received'
            assert response_data['data']['google_form_id'] == 'test_form_123'
            mock_mq_service.send_and_pin_message.assert_awaited_once()

    async def test_new_form_webhook_no_bound_chat(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """
        Test new form webhook when no bound chat is configured.
        Should return 400 error.
        """
        mock_chat_service = MagicMock()
        mock_chat_service.get_bound_chat = AsyncMock(return_value=None)

        with patch('app.api_fastapi.dependencies.ChatService', return_value=mock_chat_service):
            form_data = {
                'id': 1,
                'google_form_id': 'test_form_123',
                'title': 'New Test Survey',
                'form_url': 'https://forms.google.com/test_form_123',
                'created_at': datetime.now(tz=ZoneInfo('Europe/Moscow')).isoformat(),
                'ended_at': (datetime.now(tz=ZoneInfo('Europe/Moscow')) + timedelta(days=7)).isoformat(),
                'expired': False
            }

            response = await async_client.post(
                '/webhook/new-form',
                json=form_data,
                headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'No bound chat configured' in response.json()['detail']

    async def test_new_form_webhook_invalid_data(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """
        Test new form webhook with invalid data structure.
        Should return 422 validation error.
        """
        form_data = {
            'invalid_field': 'test'
        }

        response = await async_client.post(
            '/webhook/new-form',
            json=form_data,
            headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
class TestSurveyCompletionStatusWebhook:
    """Test suite for /webhook/send-survey-completion-status endpoint"""

    async def test_survey_completion_status_with_not_answered_users(
            self,
            async_client: AsyncClient,
            db: None,
            test_chat: Chat,
            test_survey: Survey,
            test_user_regular: User,
            test_settings
    ):
        """
        Test survey completion status when some users have not answered.
        Should send reminder messages and list non-respondents.
        """
        mock_chat_service = MagicMock()
        mock_chat_service.get_bound_chat = AsyncMock(return_value=test_chat)

        mock_survey_service = MagicMock()
        mock_survey_service.get_survey_by_google_form_id = AsyncMock(return_value=test_survey)

        mock_user_service = MagicMock()
        mock_user_service.get_users_without_reservation_exclude_creators = AsyncMock(
            return_value=[test_user_regular]
        )

        with patch('app.api_fastapi.routers.n8n_webhook.settings', test_settings), \
             patch('app.api_fastapi.dependencies.ChatService', return_value=mock_chat_service), \
             patch('app.api_fastapi.dependencies.SurveyService', return_value=mock_survey_service), \
             patch('app.api_fastapi.dependencies.UserService', return_value=mock_user_service), \
             patch('app.api_fastapi.routers.n8n_webhook.send_bulk_messages') as mock_send_bulk:

            survey_responses = {
                'google_form_id': test_survey.google_form_id,
                'answers': [
                    {'answer': 'other_user'}
                ]
            }

            response = await async_client.post(
                '/webhook/send-survey-completion-status',
                json=survey_responses,
                headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
            )

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data['success'] == 'received'
            mock_send_bulk.delay.assert_called_once()

    async def test_survey_completion_status_all_answered(
            self,
            async_client: AsyncClient,
            db: None,
            test_chat: Chat,
            test_survey: Survey,
            test_user_regular: User,
            test_settings
    ):
        """
        Test survey completion status when all users have answered.
        Should not send any messages.
        """
        mock_chat_service = MagicMock()
        mock_chat_service.get_bound_chat = AsyncMock(return_value=test_chat)

        mock_survey_service = MagicMock()
        mock_survey_service.get_survey_by_google_form_id = AsyncMock(return_value=test_survey)

        mock_user_service = MagicMock()
        mock_user_service.get_users_without_reservation_exclude_creators = AsyncMock(
            return_value=[test_user_regular]
        )

        with patch('app.api_fastapi.routers.n8n_webhook.settings', test_settings), \
             patch('app.api_fastapi.dependencies.ChatService', return_value=mock_chat_service), \
             patch('app.api_fastapi.dependencies.SurveyService', return_value=mock_survey_service), \
             patch('app.api_fastapi.dependencies.UserService', return_value=mock_user_service), \
             patch('app.api_fastapi.routers.n8n_webhook.send_bulk_messages') as mock_send_bulk:

            survey_responses = {
                'google_form_id': test_survey.google_form_id,
                'answers': [
                    {'answer': test_user_regular.callsign}
                ]
            }

            response = await async_client.post(
                '/webhook/send-survey-completion-status',
                json=survey_responses,
                headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
            )

            assert response.status_code == status.HTTP_200_OK
            mock_send_bulk.delay.assert_not_called()

    async def test_survey_completion_status_no_bound_chat(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """
        Test survey completion status when no bound chat is configured.
        Should return 400 error.
        """
        mock_chat_service = MagicMock()
        mock_chat_service.get_bound_chat = AsyncMock(return_value=None)

        with patch('app.api_fastapi.dependencies.ChatService', return_value=mock_chat_service):
            survey_responses = {
                'google_form_id': 'test_form_123',
                'answers': []
            }

            response = await async_client.post(
                '/webhook/send-survey-completion-status',
                json=survey_responses,
                headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
class TestSurveyFinishedWebhook:
    """Test suite for /webhook/send-survey-finished endpoint"""

    async def test_survey_finished_with_penalties(
            self,
            async_client: AsyncClient,
            db: None,
            test_chat: Chat,
            test_survey: Survey,
            test_user_regular: User,
            test_settings
    ):
        """
        Test survey finished webhook when users need to be penalized.
        Should add penalties and send notification.
        """
        mock_chat_service = MagicMock()
        mock_chat_service.get_bound_chat = AsyncMock(return_value=test_chat)

        mock_survey_service = MagicMock()
        mock_survey_service.get_survey_by_google_form_id = AsyncMock(return_value=test_survey)

        mock_user_service = MagicMock()
        mock_user_service.get_users_without_reservation_exclude_creators = AsyncMock(
            return_value=[test_user_regular]
        )
        mock_user_service.get_active_user_by_callsign_exclude_creator = AsyncMock(
            return_value=test_user_regular
        )

        mock_penalty_service = MagicMock()
        mock_penalty_service.add_penalty = AsyncMock()
        mock_penalty_service.get_all_users_with_three_penalties = AsyncMock(return_value=[])

        with patch('app.api_fastapi.routers.n8n_webhook.settings', test_settings), \
             patch('app.api_fastapi.dependencies.ChatService', return_value=mock_chat_service), \
             patch('app.api_fastapi.dependencies.SurveyService', return_value=mock_survey_service), \
             patch('app.api_fastapi.dependencies.UserService', return_value=mock_user_service), \
             patch('app.api_fastapi.dependencies.PenaltyService', return_value=mock_penalty_service), \
             patch('app.api_fastapi.routers.n8n_webhook.send_bulk_messages') as mock_send_bulk:

            survey_responses = {
                'google_form_id': test_survey.google_form_id,
                'answers': []
            }

            response = await async_client.post(
                '/webhook/send-survey-finished',
                json=survey_responses,
                headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
            )

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data['success'] == 'received'
            mock_penalty_service.add_penalty.assert_awaited_once()
            mock_send_bulk.delay.assert_called_once()

    async def test_survey_finished_all_completed(
            self,
            async_client: AsyncClient,
            db: None,
            test_chat: Chat,
            test_survey: Survey,
            test_user_regular: User,
            test_settings
    ):
        """
        Test survey finished when all users completed survey.
        Should send success message without penalties.
        """
        mock_chat_service = MagicMock()
        mock_chat_service.get_bound_chat = AsyncMock(return_value=test_chat)

        mock_survey_service = MagicMock()
        mock_survey_service.get_survey_by_google_form_id = AsyncMock(return_value=test_survey)

        mock_user_service = MagicMock()
        mock_user_service.get_users_without_reservation_exclude_creators = AsyncMock(
            return_value=[test_user_regular]
        )

        mock_penalty_service = MagicMock()
        mock_penalty_service.get_all_users_with_three_penalties = AsyncMock(return_value=[])

        mock_mq_service = MagicMock()
        mock_mq_service.send_message = AsyncMock()

        with patch('app.api_fastapi.routers.n8n_webhook.settings', test_settings), \
             patch('app.api_fastapi.dependencies.ChatService', return_value=mock_chat_service), \
             patch('app.api_fastapi.dependencies.SurveyService', return_value=mock_survey_service), \
             patch('app.api_fastapi.dependencies.UserService', return_value=mock_user_service), \
             patch('app.api_fastapi.dependencies.PenaltyService', return_value=mock_penalty_service), \
             patch('app.api_fastapi.dependencies.MessageQueueService', return_value=mock_mq_service):

            survey_responses = {
                'google_form_id': test_survey.google_form_id,
                'answers': [
                    {'answer': test_user_regular.callsign}
                ]
            }

            response = await async_client.post(
                '/webhook/send-survey-finished',
                json=survey_responses,
                headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
            )

            assert response.status_code == status.HTTP_200_OK
            mock_mq_service.send_message.assert_awaited_once()

    async def test_survey_finished_with_three_penalties_ban(
            self,
            async_client: AsyncClient,
            db: None,
            test_chat: Chat,
            test_survey: Survey,
            test_user_regular: User,
            test_settings
    ):
        """
        Test survey finished when user reaches 3 penalties.
        Should ban user and deactivate account.
        """
        mock_chat_service = MagicMock()
        mock_chat_service.get_bound_chat = AsyncMock(return_value=test_chat)

        mock_survey_service = MagicMock()
        mock_survey_service.get_survey_by_google_form_id = AsyncMock(return_value=test_survey)

        mock_user_service = MagicMock()
        mock_user_service.get_users_without_reservation_exclude_creators = AsyncMock(
            return_value=[test_user_regular]
        )
        mock_user_service.get_active_user_by_callsign_exclude_creator = AsyncMock(
            return_value=test_user_regular
        )
        mock_user_service.deactivate_user = AsyncMock()

        mock_penalty_service = MagicMock()
        mock_penalty_service.add_penalty = AsyncMock()
        mock_penalty_service.get_all_users_with_three_penalties = AsyncMock(
            return_value=[{
                'telegram_id': test_user_regular.telegram_id,
                'username': test_user_regular.username,
                'callsign': test_user_regular.callsign,
                'penalty_count': 3
            }]
        )

        with patch('app.api_fastapi.routers.n8n_webhook.settings', test_settings), \
             patch('app.api_fastapi.dependencies.ChatService', return_value=mock_chat_service), \
             patch('app.api_fastapi.dependencies.SurveyService', return_value=mock_survey_service), \
             patch('app.api_fastapi.dependencies.UserService', return_value=mock_user_service), \
             patch('app.api_fastapi.dependencies.PenaltyService', return_value=mock_penalty_service), \
             patch('app.api_fastapi.routers.n8n_webhook.ban_user_from_chat') as mock_ban_user, \
             patch('app.api_fastapi.routers.n8n_webhook.send_bulk_messages') as mock_send_bulk:

            survey_responses = {
                'google_form_id': test_survey.google_form_id,
                'answers': []
            }

            response = await async_client.post(
                '/webhook/send-survey-finished',
                json=survey_responses,
                headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
            )

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data['success'] == 'received'
            assert len(response_data['users_with_three_penalties']) == 1
            assert response_data['users_with_three_penalties'][0]['penalty_count'] == 3
            mock_ban_user.delay.assert_called_once()
            mock_user_service.deactivate_user.assert_awaited_once_with(test_user_regular.telegram_id)

    async def test_survey_finished_no_bound_chat(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """
        Test survey finished when no bound chat is configured.
        Should return 400 error.
        """
        mock_chat_service = MagicMock()
        mock_chat_service.get_bound_chat = AsyncMock(return_value=None)

        with patch('app.api_fastapi.dependencies.ChatService', return_value=mock_chat_service):
            survey_responses = {
                'google_form_id': 'test_form_123',
                'answers': []
            }

            response = await async_client.post(
                '/webhook/send-survey-finished',
                json=survey_responses,
                headers={'X-N8N-Secret-Token': test_settings.n8n.n8n_webhook_secret}
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestSplitUsersIntoChunks:
    """Test suite for _split_users_into_chunks helper function"""

    def test_split_users_empty_list(self):
        """Test splitting with empty users list"""
        from app.api_fastapi.routers.n8n_webhook import _split_users_into_chunks

        base_text = 'Test message:\n'
        users_list = []

        result = _split_users_into_chunks(base_text, users_list)

        assert len(result) == 1
        assert result[0] == base_text

    def test_split_users_single_message(self):
        """Test splitting when all users fit in one message"""
        from app.api_fastapi.routers.n8n_webhook import _split_users_into_chunks

        base_text = 'Test message:\n'
        users_list = ['@user1', '@user2', '@user3']

        result = _split_users_into_chunks(base_text, users_list)

        assert len(result) == 1
        assert '@user1' in result[0]
        assert '@user2' in result[0]
        assert '@user3' in result[0]

    def test_split_users_multiple_messages(self):
        """Test splitting when users exceed max_length"""
        from app.api_fastapi.routers.n8n_webhook import _split_users_into_chunks

        base_text = 'Test:\n'
        users_list = ['@' + 'u' * 100 for _ in range(50)]

        result = _split_users_into_chunks(base_text, users_list, max_length=500)

        assert len(result) > 1
        assert result[0].startswith(base_text)

    def test_split_users_base_text_exceeds_max_length(self):
        """Test that ValueError is raised when base_text alone exceeds max_length"""
        from app.api_fastapi.routers.n8n_webhook import _split_users_into_chunks

        base_text = 'x' * 5000
        users_list = ['@user1']

        with pytest.raises(ValueError, match='Base text alone exceeds maximum message length'):
            _split_users_into_chunks(base_text, users_list, max_length=4096)