from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestTelegramWebhook:
    """Test suite for /webhook endpoint"""

    async def test_telegram_webhook_success(
            self,
            async_client: AsyncClient,
            test_settings
    ):
        """
        Test successful processing of a valid Telegram update.
        Should return status ok.
        """
        update_data = {
            'update_id': 123456,
            'message': {
                'message_id': 1,
                'date': 1609459200,
                'chat': {'id': 111, 'type': 'private'},
                'from': {'id': 222, 'is_bot': False, 'first_name': 'Test'},
                'text': 'Hello'
            }
        }

        response = await async_client.post(
            '/webhook',
            json=update_data,
            headers={'X-Telegram-Bot-Api-Secret-Token': test_settings.telegram.webhook_secret}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'ok'

    async def test_telegram_webhook_invalid_data(
            self,
            async_client: AsyncClient,
            test_settings
    ):
        """
        Test handling of invalid update data (ValueError).
        Should return 400 error.
        """
        invalid_data = {'invalid': 'data'}

        response = await async_client.post(
            '/webhook',
            json=invalid_data,
            headers={'X-Telegram-Bot-Api-Secret-Token': test_settings.telegram.webhook_secret}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Invalid update data format.'


@pytest.mark.asyncio
class TestTelegramWebhookHealth:
    """Test suite for /webhook/health endpoint"""

    async def test_health_check(self, async_client: AsyncClient):
        """
        Test health check endpoint.
        Should return healthy status.
        """
        response = await async_client.get('/webhook/health')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'healthy'
