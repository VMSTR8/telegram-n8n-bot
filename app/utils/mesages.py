from app.services import MessageQueueService
from app.utils import ValidationResult


async def send_callsign_validation_error(
        message_queue_service: MessageQueueService,
        chat_id: int,
        validation_result: ValidationResult,
        command: str,
        message_id: int
) -> None:
    """
    Send error message about invalid callsign format.

    Args:
        message_queue_service (MessageQueueService): The message queue service instance.
        chat_id (int): Telegram chat ID of the user.
        validation_result (ValidationResult): The result of the callsign validation.
        command (str): The command that triggered the validation.
        message_id (int): The ID of the original message.

    Returns:
        None
    """
    await message_queue_service.send_message(
        chat_id=chat_id,
        text=f'❌ Неверный формат позывного.\n\n'
             f'{validation_result.error_message}\n\n'
             f'Используйте: `{command} позывной`\n\n'
             f'Требования к позывному:\n'
             f'🔤 Только латинские буквы\n'
             f'📏 Длина от 1 до 20 символов\n'
             f'🚫 Без цифр, спец символов и пробелов\n'
             f'🆔 Позывной должен быть уникальным',
        parse_mode='Markdown',
        message_id=message_id
    )
