from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from app.api_fastapi.routers.recaptcha_verification import verify_recaptcha_token


def _create_mock_aiohttp_session(response_data: dict | None = None, raise_error: Exception | None = None):
    """
    Helper to create mock aiohttp.ClientSession with less boilerplate.
    
    Args:
        response_data: Dict to return from response.json()
        raise_error: Exception to raise from session.post()
    
    Returns:
        Mock ClientSession class
    """
    mock_session_class = MagicMock()
    
    if raise_error:
        mock_session = MagicMock()
        mock_session.post = MagicMock(side_effect=raise_error)
    else:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=response_data)
        
        mock_post_cm = MagicMock()
        mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post_cm.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_post_cm)
    
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)
    
    mock_session_class.return_value = mock_session_cm
    return mock_session_class


@pytest.mark.asyncio
class TestRecaptchaVerification:
    """Test suite for /recaptcha-verify endpoint"""

    async def test_recaptcha_verification_success(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """Test successful reCAPTCHA verification and form submission."""
        mock_form_service = MagicMock()
        mock_form_service.process_and_send_form_to_creator = AsyncMock(
            return_value=MagicMock(status='success', message='Form sent successfully')
        )

        with patch('config.settings.settings', test_settings), \
                patch('app.api_fastapi.routers.recaptcha_verification.verify_recaptcha_token') as mock_verify, \
                patch('app.api_fastapi.routers.recaptcha_verification.FormService', return_value=mock_form_service):
            
            mock_verify.return_value = {'valid': True, 'score': 0.9}

            form_data = {
                'name': 'John Doe',
                'age': 30,
                'contactType': 'telegram',
                'telegram': '@johndoe',
                'experience': 'yes',
                'recaptchaToken': 'valid_token_123'
            }

            response = await async_client.post(
                '/recaptcha-verify',
                json=form_data
            )

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data['status'] == 'ok'
            assert response_data['message'] == 'reCAPTCHA verification successful.'
            assert response_data['score'] == 0.9

            mock_verify.assert_awaited_once_with(
                token='valid_token_123',
                expected_action='submit'
            )
            mock_form_service.process_and_send_form_to_creator.assert_awaited_once()

    async def test_recaptcha_verification_invalid_token(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """Test reCAPTCHA verification with invalid token (400 Bad Request)."""
        with patch('config.settings.settings', test_settings), \
                patch('app.api_fastapi.routers.recaptcha_verification.verify_recaptcha_token') as mock_verify:
            
            mock_verify.return_value = {'valid': False, 'score': 0.1}

            form_data = {
                'name': 'John Doe',
                'age': 30,
                'contactType': 'telegram',
                'telegram': '@johndoe',
                'experience': 'yes',
                'recaptchaToken': 'invalid_token'
            }

            response = await async_client.post(
                '/recaptcha-verify',
                json=form_data
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            response_data = response.json()
            assert response_data['detail'] == 'reCAPTCHA verification failed.'

    async def test_recaptcha_verification_low_score(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """Test reCAPTCHA verification with low score < 0.5 (400 Bad Request)."""
        with patch('config.settings.settings', test_settings), \
                patch('app.api_fastapi.routers.recaptcha_verification.verify_recaptcha_token') as mock_verify:
            
            mock_verify.return_value = {'valid': False, 'score': 0.3}

            form_data = {
                'name': 'Jane Doe',
                'age': 25,
                'contactType': 'telegram',
                'telegram': '@janedoe',
                'experience': 'no',
                'recaptchaToken': 'low_score_token'
            }

            response = await async_client.post(
                '/recaptcha-verify',
                json=form_data
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            response_data = response.json()
            assert 'reCAPTCHA verification failed' in response_data['detail']

    async def test_recaptcha_verification_telegram_delivery_failure(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """Test when Telegram API fails to deliver message (bot blocked, API down, network error) - returns 503."""
        mock_form_service = MagicMock()
        mock_form_service.process_and_send_form_to_creator = AsyncMock(
            return_value=MagicMock(status='error', message='Bot was blocked by the user')
        )

        with patch('config.settings.settings', test_settings), \
                patch('app.api_fastapi.routers.recaptcha_verification.verify_recaptcha_token') as mock_verify, \
                patch('app.api_fastapi.routers.recaptcha_verification.FormService', return_value=mock_form_service):
            
            mock_verify.return_value = {'valid': True, 'score': 0.8}

            form_data = {
                'name': 'Test User',
                'age': 28,
                'contactType': 'telegram',
                'telegram': '@testuser',
                'experience': 'yes',
                'recaptchaToken': 'valid_token'
            }

            response = await async_client.post(
                '/recaptcha-verify',
                json=form_data
            )

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            response_data = response.json()
            assert response_data['detail'] == 'Failed to deliver form response to creator.'
            assert 'Form response delivery failed' in caplog_debug.text

    async def test_recaptcha_verification_internal_service_exception(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """Test when internal exception occurs in FormService (database error, validation, etc) - returns 503."""
        mock_form_service = MagicMock()
        mock_form_service.process_and_send_form_to_creator = AsyncMock(
            side_effect=Exception('Database connection error')
        )

        with patch('config.settings.settings', test_settings), \
                patch('app.api_fastapi.routers.recaptcha_verification.verify_recaptcha_token') as mock_verify, \
                patch('app.api_fastapi.routers.recaptcha_verification.FormService', return_value=mock_form_service):
            
            mock_verify.return_value = {'valid': True, 'score': 0.85}

            form_data = {
                'name': 'Error Test',
                'age': 35,
                'contactType': 'telegram',
                'telegram': '@errortest',
                'experience': 'no',
                'recaptchaToken': 'valid_token'
            }

            response = await async_client.post(
                '/recaptcha-verify',
                json=form_data
            )

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            response_data = response.json()
            assert 'Unable to deliver form response to creator' in response_data['detail']
            assert 'Failed to send form response to creator' in caplog_debug.text
            assert 'Database connection error' in caplog_debug.text

    async def test_recaptcha_verification_invalid_form_data(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """Test with invalid form data structure (422 Unprocessable Entity)."""
        form_data = {
            'name': 'John Doe',
            'age': 'invalid_age',  # Should be int
            'contactType': 'telegram',
            'telegram': '@johndoe',
            'recaptchaToken': 'token'
            # Missing 'experience' field
        }

        response = await async_client.post(
            '/recaptcha-verify',
            json=form_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_recaptcha_verification_missing_required_fields(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """Test with missing required fields (422 Unprocessable Entity)."""
        form_data = {
            'name': 'John Doe',
            'telegram': '@johndoe'
            # Missing age, contactType, experience, recaptchaToken
        }

        response = await async_client.post(
            '/recaptcha-verify',
            json=form_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_recaptcha_verification_general_exception(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """Test when unexpected exception occurs (500 Internal Server Error)."""
        with patch('config.settings.settings', test_settings), \
                patch('app.api_fastapi.routers.recaptcha_verification.verify_recaptcha_token') as mock_verify:
            
            mock_verify.side_effect = Exception('Unexpected error')

            form_data = {
                'name': 'Exception Test',
                'age': 40,
                'contactType': 'telegram',
                'telegram': '@exceptiontest',
                'experience': 'yes',
                'recaptchaToken': 'token'
            }

            response = await async_client.post(
                '/recaptcha-verify',
                json=form_data
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            response_data = response.json()
            assert 'Internal server error' in response_data['detail']
            assert 'Error during reCAPTCHA verification' in caplog_debug.text

    async def test_recaptcha_verification_with_edge_case_data(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """Test with edge case form data (cyrillic, special characters, min age)."""
        mock_form_service = MagicMock()
        mock_form_service.process_and_send_form_to_creator = AsyncMock(
            return_value=MagicMock(status='success', message='Form sent')
        )

        with patch('config.settings.settings', test_settings), \
                patch('app.api_fastapi.routers.recaptcha_verification.verify_recaptcha_token') as mock_verify, \
                patch('app.api_fastapi.routers.recaptcha_verification.FormService', return_value=mock_form_service):
            
            mock_verify.return_value = {'valid': True, 'score': 0.95}

            form_data = {
                'name': 'Иван Иванов-Петров',  # Cyrillic with hyphen
                'age': 18,  # Min age
                'contactType': 'telegram',
                'telegram': '@user_123',
                'experience': 'Да, 5+ лет опыта работы с дронами',
                'recaptchaToken': 'edge_case_token_' + 'x' * 100
            }

            response = await async_client.post(
                '/recaptcha-verify',
                json=form_data
            )

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data['status'] == 'ok'

    async def test_recaptcha_verification_high_score(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """Test with perfect reCAPTCHA score (1.0)."""
        mock_form_service = MagicMock()
        mock_form_service.process_and_send_form_to_creator = AsyncMock(
            return_value=MagicMock(status='success', message='Form sent')
        )

        with patch('config.settings.settings', test_settings), \
                patch('app.api_fastapi.routers.recaptcha_verification.verify_recaptcha_token') as mock_verify, \
                patch('app.api_fastapi.routers.recaptcha_verification.FormService', return_value=mock_form_service):
            
            mock_verify.return_value = {'valid': True, 'score': 1.0}

            form_data = {
                'name': 'Perfect User',
                'age': 30,
                'contactType': 'telegram',
                'telegram': '@perfectuser',
                'experience': 'yes',
                'recaptchaToken': 'perfect_token'
            }

            response = await async_client.post(
                '/recaptcha-verify',
                json=form_data
            )

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data['score'] == 1.0

    async def test_recaptcha_verification_boundary_score(
            self,
            async_client: AsyncClient,
            db: None,
            test_settings
    ):
        """Test with boundary reCAPTCHA score (exactly 0.5, should pass)."""
        mock_form_service = MagicMock()
        mock_form_service.process_and_send_form_to_creator = AsyncMock(
            return_value=MagicMock(status='success', message='Form sent')
        )

        with patch('config.settings.settings', test_settings), \
                patch('app.api_fastapi.routers.recaptcha_verification.verify_recaptcha_token') as mock_verify, \
                patch('app.api_fastapi.routers.recaptcha_verification.FormService', return_value=mock_form_service):
            
            mock_verify.return_value = {'valid': True, 'score': 0.5}

            form_data = {
                'name': 'Boundary User',
                'age': 25,
                'contactType': 'telegram',
                'telegram': '@boundaryuser',
                'experience': 'yes',
                'recaptchaToken': 'boundary_token'
            }

            response = await async_client.post(
                '/recaptcha-verify',
                json=form_data
            )

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data['score'] == 0.5


@pytest.mark.asyncio
class TestVerifyRecaptchaTokenFunction:
    """Test suite for verify_recaptcha_token helper function"""

    async def test_verify_recaptcha_token_success(self, test_settings):
        """Test successful token verification with Google API."""
        mock_response_data = {
            'success': True,
            'score': 0.9,
            'action': 'submit'
        }

        with patch('config.settings.settings', test_settings), \
                patch('aiohttp.ClientSession', _create_mock_aiohttp_session(mock_response_data)):
            
            result = await verify_recaptcha_token(token='test_token', expected_action='submit')

            assert result['valid'] is True
            assert result['score'] == 0.9

    async def test_verify_recaptcha_token_failed_verification(self, test_settings):
        """Test when Google API returns success=False."""
        mock_response_data = {
            'success': False,
            'score': 0.1,
            'error-codes': ['invalid-input-response']
        }

        with patch('config.settings.settings', test_settings), \
                patch('aiohttp.ClientSession', _create_mock_aiohttp_session(mock_response_data)):
            
            result = await verify_recaptcha_token(token='invalid_token')

            assert result['valid'] is False
            assert result['score'] == 0.1

    async def test_verify_recaptcha_token_wrong_action(self, test_settings):
        """Test when action doesn't match expected_action."""
        mock_response_data = {
            'success': True,
            'score': 0.9,
            'action': 'wrong_action'
        }

        with patch('config.settings.settings', test_settings), \
                patch('aiohttp.ClientSession', _create_mock_aiohttp_session(mock_response_data)):
            
            result = await verify_recaptcha_token(token='test_token', expected_action='submit')

            assert result['valid'] is False
            assert result['score'] == 0.9

    async def test_verify_recaptcha_token_no_secret_key(self, test_settings):
        """Test when reCAPTCHA secret key is not configured."""
        test_settings.recaptcha_secret_key = None

        with patch('config.settings.settings', test_settings):
            result = await verify_recaptcha_token(token='test_token')

            assert result['valid'] is False
            assert result['score'] == 0.0

    async def test_verify_recaptcha_token_network_error(self, test_settings, caplog_debug: pytest.LogCaptureFixture):
        """Test when network error occurs during verification."""
        with patch('config.settings.settings', test_settings), \
                patch('aiohttp.ClientSession', _create_mock_aiohttp_session(raise_error=Exception('Network error'))):
            
            result = await verify_recaptcha_token(token='test_token')

            assert result['valid'] is False
            assert result['score'] == 0.0
            assert 'Error verifying reCAPTCHA token' in caplog_debug.text
            assert 'Network error' in caplog_debug.text

    async def test_verify_recaptcha_token_without_expected_action(self, test_settings):
        """Test token verification without specifying expected_action."""
        mock_response_data = {
            'success': True,
            'score': 0.8,
            'action': 'any_action'
        }

        with patch('config.settings.settings', test_settings), \
                patch('aiohttp.ClientSession', _create_mock_aiohttp_session(mock_response_data)):
            
            result = await verify_recaptcha_token(token='test_token')

            assert result['valid'] is True
            assert result['score'] == 0.8

    async def test_verify_recaptcha_token_exactly_threshold_score(self, test_settings):
        """Test with score exactly at threshold (0.5)."""
        mock_response_data = {
            'success': True,
            'score': 0.5,
            'action': 'submit'
        }

        with patch('config.settings.settings', test_settings), \
                patch('aiohttp.ClientSession', _create_mock_aiohttp_session(mock_response_data)):
            
            result = await verify_recaptcha_token(token='test_token', expected_action='submit')

            assert result['valid'] is True
            assert result['score'] == 0.5

    async def test_verify_recaptcha_token_below_threshold_score(self, test_settings):
        """Test with score just below threshold (0.49)."""
        mock_response_data = {
            'success': True,
            'score': 0.49,
            'action': 'submit'
        }

        with patch('config.settings.settings', test_settings), \
                patch('aiohttp.ClientSession', _create_mock_aiohttp_session(mock_response_data)):
            
            result = await verify_recaptcha_token(token='test_token', expected_action='submit')

            assert result['valid'] is False
            assert result['score'] == 0.49
