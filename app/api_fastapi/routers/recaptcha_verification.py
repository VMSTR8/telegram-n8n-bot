import logging
import traceback
from typing import Any

import aiohttp
from fastapi import APIRouter, HTTPException, status

from app.api_fastapi.schemas import RecaptchaResponseSchema
from app.schemas import SubmitFormSchema, TaskResponse
from app.services import FormService
from config import settings

logger = logging.getLogger(__name__)
recaptcha_verification_router: APIRouter = APIRouter()


async def verify_recaptcha_token(
        token: str,
        expected_action: str = None
) -> dict[str, bool | float]:
    """
    Verify the reCAPTCHA token with Google's reCAPTCHA API.
    Args:
        token (str): The reCAPTCHA token to verify.
        expected_action (str, optional): The expected action name for validation.
        
    Returns:
        dict: A dictionary containing 'valid' (bool) and 'score' (float).
    """
    recaptcha_secret_key: str | None = settings.recaptcha_secret_key

    if not recaptcha_secret_key:
        logger.error('reCAPTCHA secret key is not configured.')
        return {'valid': False, 'score': 0.0}

    payload: dict[str, str | None] = {
        'secret': recaptcha_secret_key,
        'response': token
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                    'https://www.google.com/recaptcha/api/siteverify',
                    data=payload
            ) as response:
                result: dict[str, Any] = await response.json()

                success: bool = result.get('success', False)
                score: float = result.get('score', 0.0)
                action: str = result.get('action', '')

                if not success:
                    return {'valid': False, 'score': score}

                if expected_action and action != expected_action:
                    return {'valid': False, 'score': score}

                valid = score >= 0.5
                return {'valid': valid, 'score': score}

        except Exception as e:
            logger.error(
                'Error verifying reCAPTCHA token: %s | Traceback: %s',
                str(e),
                traceback.format_exc()
            )
            return {'valid': False, 'score': 0.0}


@recaptcha_verification_router.post(path='/recaptcha-verify', response_model=RecaptchaResponseSchema)
async def recaptcha_verification(
        data: SubmitFormSchema
) -> RecaptchaResponseSchema:
    """
    Endpoint to verify reCAPTCHA token.

    Args:
        data (SubmitFormSchema): The form submission data containing the reCAPTCHA token.
    
    Raises:
        HTTPException: If verification fails or an error occurs.
    
    Returns:
        RecaptchaResponseSchema: Response schema indicating success or failure.
    """
    try:
        result = await verify_recaptcha_token(
            token=data.recaptchaToken,
            expected_action='submit'
        )
        if not result['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='reCAPTCHA verification failed.'
            )

        form_service: FormService = FormService()

        try:
            send_result: TaskResponse = await form_service.process_and_send_form_to_creator(form_data=data)

            if send_result.status != 'success':
                logger.error(
                    'Form response delivery failed: %s', send_result.message
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Failed to deliver form response to creator.'
                )
            
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(
                'Failed to send form response to creator: %s | Traceback: %s',
                str(e),
                traceback.format_exc()
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Unable to deliver form response to creator at this time. Please try again later.'
            )

        return RecaptchaResponseSchema(
            status='ok',
            message='reCAPTCHA verification successful.',
            score=result['score']
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            'Error during reCAPTCHA verification: %s | Traceback: %s',
            str(e),
            traceback.format_exc()
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error during reCAPTCHA verification.'
        )
