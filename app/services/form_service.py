import logging

from app.schemas import SubmitFormSchema, TaskResponse
from app.text_utils import escape_markdown
from config import settings
from .message_queue_service import MessageQueueService

logger = logging.getLogger(__name__)


class FormService:
    """
    Service class for managing form-related operations.
    
    Methods:
        process_and_send_form_to_creator: Processes form data and sends it to the creator via message queue.
    """

    @staticmethod
    async def process_and_send_form_to_creator(
            form_data: SubmitFormSchema
    ) -> TaskResponse:
        """
        Processes form data and sends it to the creator via message queue.
        
        Args:
            form_data (SubmitFormSchema): The form data submitted by the user.
        Returns:
            TaskResponse: The response from the message queue service.
        """
        message_queue_service: MessageQueueService = MessageQueueService()

        form_dict = {
            'name': form_data.name,
            'age': form_data.age,
            'telegram': form_data.telegram,
            'phone': form_data.phone,
            'contactType': form_data.contactType,
            'experience': form_data.experience
        }

        return await message_queue_service.send_form_to_creator_with_tracking(
            creator_id=int(settings.telegram.creator_id),
            form_data=form_dict,
            timeout=15
        )
