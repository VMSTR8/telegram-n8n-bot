from unittest.mock import Mock, patch

import pytest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from celery.result import AsyncResult

from app.schemas import QueueResult, TaskStatus, TaskResponse
from app.services.message_queue_service import MessageQueueService


@pytest.mark.unit
@pytest.mark.asyncio
class TestMessageQueueServiceSendMessage:
    """
    Unit tests for MessageQueueService.send_message method.
    """

    @patch('app.services.message_queue_service.celery_send_telegram_message')
    async def test_send_message_success_with_minimal_data(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending a message with minimal required data.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_message(
            chat_id=123456789,
            text='Test message'
        )

        assert result.status == 'queued'
        assert result.task_id == 'test-task-id-12345'
        assert result.chat_id == 123456789
        assert result.message is None

        mock_celery_task.delay.assert_called_once_with(
            chat_id=123456789,
            text='Test message',
            parse_mode='HTML',
            message_id=None,
            message_thread_id=None,
            reply_markup=None,
            disable_web_page_preview=False
        )

    @patch('app.services.message_queue_service.celery_send_telegram_message')
    async def test_send_message_success_with_full_data(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending a message with all possible parameters.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Test', callback_data='test')]]
        )

        result: QueueResult = await service.send_message(
            chat_id=987654321,
            text='Full test message',
            parse_mode='Markdown',
            message_id=111,
            message_thread_id=222,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

        assert result.status == 'queued'
        assert result.task_id == 'test-task-id-12345'
        assert result.chat_id == 987654321

        call_kwargs = mock_celery_task.delay.call_args.kwargs
        assert call_kwargs['reply_markup'] is not None
        assert isinstance(call_kwargs['reply_markup'], dict)
        assert call_kwargs['parse_mode'] == 'Markdown'
        assert call_kwargs['disable_web_page_preview'] is True

    @patch('app.services.message_queue_service.celery_send_telegram_message')
    async def test_send_message_error_on_celery_exception(
            self,
            mock_celery_task: Mock
    ):
        """
        Test error handling when Celery raises an exception.
        """
        mock_celery_task.delay.side_effect = Exception('Celery connection error')
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_message(
            chat_id=123456789,
            text='This will fail'
        )

        assert result.status == 'error'
        assert result.task_id is None
        assert result.chat_id == 123456789
        assert 'Celery connection error' in result.message

    @patch('app.services.message_queue_service.celery_send_telegram_message')
    async def test_send_message_with_reply_to_message_id(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending a message as a reply to another message.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_message(
            chat_id=123456789,
            text='Reply message',
            message_id=555
        )

        assert result.status == 'queued'
        mock_celery_task.delay.assert_called_once()
        assert mock_celery_task.delay.call_args.kwargs['message_id'] == 555


@pytest.mark.unit
@pytest.mark.asyncio
class TestMessageQueueServiceSendAndPinMessage:
    """
    Unit tests for MessageQueueService.send_and_pin_message method.
    """

    @patch('app.services.message_queue_service.send_and_pin_telegram_message')
    async def test_send_and_pin_message_success(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending and pinning a message successfully.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_and_pin_message(
            chat_id=123456789,
            text='Pinned message'
        )

        assert result.status == 'queued'
        assert result.task_id == 'test-task-id-12345'
        assert result.chat_id == 123456789

        mock_celery_task.delay.assert_called_once_with(
            chat_id=123456789,
            message_thread_id=None,
            text='Pinned message',
            parse_mode='HTML',
            disable_web_page_preview=False,
            message_id=None,
            disable_pin_notification=False
        )

    @patch('app.services.message_queue_service.send_and_pin_telegram_message')
    async def test_send_and_pin_message_with_thread_id(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending and pinning a message in a thread (topic).
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_and_pin_message(
            chat_id=123456789,
            text='Pinned in thread',
            message_thread_id=999
        )

        assert result.status == 'queued'
        call_kwargs = mock_celery_task.delay.call_args.kwargs
        assert call_kwargs['message_thread_id'] == 999

    @patch('app.services.message_queue_service.send_and_pin_telegram_message')
    async def test_send_and_pin_message_disable_notification(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending and pinning with disabled notification.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_and_pin_message(
            chat_id=123456789,
            text='Silent pin',
            disable_pin_notification=True
        )

        assert result.status == 'queued'
        call_kwargs = mock_celery_task.delay.call_args.kwargs
        assert call_kwargs['disable_pin_notification'] is True

    @patch('app.services.message_queue_service.send_and_pin_telegram_message')
    async def test_send_and_pin_message_error_handling(
            self,
            mock_celery_task: Mock
    ):
        """
        Test error handling in send_and_pin_message.
        """
        mock_celery_task.delay.side_effect = Exception('Pin task failed')
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_and_pin_message(
            chat_id=123456789,
            text='This will fail'
        )

        assert result.status == 'error'
        assert 'Pin task failed' in result.message
        assert result.task_id is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestMessageQueueServiceSendBulkMessages:
    """
    Unit tests for MessageQueueService.send_bulk_messages method.
    """

    @patch('app.services.message_queue_service.celery_send_bulk_messages')
    async def test_send_bulk_messages_success(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending multiple messages in bulk.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        messages = [
            {
                'chat_id': 111,
                'text': 'Message 1',
                'parse_mode': 'HTML',
                'disable_web_page_preview': False,
                'message_id': None,
                'message_thread_id': None
            },
            {
                'chat_id': 222,
                'text': 'Message 2',
                'parse_mode': 'HTML',
                'disable_web_page_preview': False,
                'message_id': None,
                'message_thread_id': None
            },
            {
                'chat_id': 333,
                'text': 'Message 3',
                'parse_mode': 'HTML',
                'disable_web_page_preview': False,
                'message_id': None,
                'message_thread_id': None
            }
        ]

        result: QueueResult = await service.send_bulk_messages(messages)

        assert result.status == 'queued'
        assert result.task_id == 'test-task-id-12345'
        assert result.message_count == 3

        mock_celery_task.delay.assert_called_once_with(messages)

    @patch('app.services.message_queue_service.celery_send_bulk_messages')
    async def test_send_bulk_messages_empty_list(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending an empty list of messages.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_bulk_messages([])

        assert result.status == 'queued'
        assert result.message_count == 0
        mock_celery_task.delay.assert_called_once_with([])

    @patch('app.services.message_queue_service.celery_send_bulk_messages')
    async def test_send_bulk_messages_error_handling(
            self,
            mock_celery_task: Mock
    ):
        """
        Test error handling in send_bulk_messages.
        """
        mock_celery_task.delay.side_effect = Exception('Bulk send failed')
        service: MessageQueueService = MessageQueueService()

        messages = [
            {'chat_id': 111, 'text': 'Message 1'},
            {'chat_id': 222, 'text': 'Message 2'}
        ]

        result: QueueResult = await service.send_bulk_messages(messages)

        assert result.status == 'error'
        assert 'Bulk send failed' in result.message
        assert result.task_id is None

    @patch('app.services.message_queue_service.celery_send_bulk_messages')
    async def test_send_bulk_messages_single_message(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending bulk with only one message.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        messages = [{'chat_id': 123, 'text': 'Single message'}]

        result: QueueResult = await service.send_bulk_messages(messages)

        assert result.status == 'queued'
        assert result.message_count == 1


@pytest.mark.unit
class TestMessageQueueServiceEdgeCases:
    """
    Unit tests for edge cases in MessageQueueService methods.
    """

    @patch('app.services.message_queue_service.celery_send_telegram_message')
    async def test_send_message_with_very_long_text(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending a message with very long text.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()
        long_text = 'A' * 5000

        result: QueueResult = await service.send_message(
            chat_id=123456789,
            text=long_text
        )

        assert result.status == 'queued'
        call_kwargs = mock_celery_task.delay.call_args.kwargs
        assert len(call_kwargs['text']) == 5000

    @patch('app.services.message_queue_service.celery_send_telegram_message')
    async def test_send_message_with_empty_text(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending a message with empty text.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_message(
            chat_id=123456789,
            text=''
        )

        assert result.status == 'queued'
        call_kwargs = mock_celery_task.delay.call_args.kwargs
        assert call_kwargs['text'] == ''

    @patch('app.services.message_queue_service.celery_send_telegram_message')
    async def test_send_message_with_none_reply_markup(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test that None reply_markup is passed correctly.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        result: QueueResult = await service.send_message(
            chat_id=123456789,
            text='Test',
            reply_markup=None
        )

        assert result.status == 'queued'
        call_kwargs = mock_celery_task.delay.call_args.kwargs
        assert call_kwargs['reply_markup'] is None

    @patch('app.services.message_queue_service.celery_send_bulk_messages')
    async def test_send_bulk_messages_with_large_batch(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock
    ):
        """
        Test sending a large batch of messages.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        messages = [
            {'chat_id': i, 'text': f'Message {i}'}
            for i in range(100)
        ]

        result: QueueResult = await service.send_bulk_messages(messages)

        assert result.status == 'queued'
        assert result.message_count == 100

    @patch('app.services.message_queue_service.celery_app')
    def test_get_task_status_with_empty_task_id(self, mock_celery_app: Mock):
        """
        Test getting status with empty task ID string.
        """
        mock_result = Mock(spec=AsyncResult)
        mock_result.status = 'PENDING'
        mock_result.ready.return_value = False
        mock_result.result = None
        mock_celery_app.AsyncResult.return_value = mock_result

        service: MessageQueueService = MessageQueueService()

        result: TaskStatus = service.get_task_status('')

        assert result.task_id == ''
        assert result.status == 'PENDING'


@pytest.mark.unit
@pytest.mark.asyncio
class TestMessageQueueServiceLogging:
    """
    Unit tests to verify proper logging in MessageQueueService.
    """

    @patch('app.services.message_queue_service.celery_send_telegram_message')
    async def test_send_message_logs_info_on_success(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """
        Test that successful message queueing is logged.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()

        await service.send_message(
            chat_id=123456789,
            text='Test message'
        )

        assert 'Message queued for chat 123456789' in caplog_debug.text
        assert 'test-task-id-12345' in caplog_debug.text

    @patch('app.services.message_queue_service.celery_send_telegram_message')
    async def test_send_message_logs_error_on_exception(
            self,
            mock_celery_task: Mock,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """
        Test that errors are logged properly.
        """
        mock_celery_task.delay.side_effect = Exception('Test error')
        service: MessageQueueService = MessageQueueService()

        await service.send_message(
            chat_id=123456789,
            text='This will fail'
        )

        assert 'Error queuing message for chat 123456789' in caplog_debug.text
        assert 'Test error' in caplog_debug.text

    @patch('app.services.message_queue_service.celery_send_bulk_messages')
    async def test_send_bulk_messages_logs_info(
            self,
            mock_celery_task: Mock,
            mock_celery_async_result: Mock,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """
        Test that bulk message queueing is logged with count.
        """
        mock_celery_task.delay.return_value = mock_celery_async_result
        service: MessageQueueService = MessageQueueService()
        messages = [{'chat_id': i, 'text': f'Msg {i}'} for i in range(5)]

        await service.send_bulk_messages(messages)

        assert 'Bulk messages queued' in caplog_debug.text
        assert 'count: 5' in caplog_debug.text


@pytest.mark.unit
@pytest.mark.asyncio
class TestMessageQueueServiceSendFormToCreator:
    """
    Unit tests for MessageQueueService.send_form_to_creator_with_tracking method.
    """

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_success(
            self,
            mock_celery_task: Mock
    ):
        """
        Test sending form to creator with successful response.
        """
        mock_task_result = Mock(spec=AsyncResult)
        mock_task_result.id = 'test-task-form-123'
        mock_task_result.get.return_value = {
            'status': 'success',
            'message': 'Form sent successfully'
        }
        mock_celery_task.delay.return_value = mock_task_result
        
        service: MessageQueueService = MessageQueueService()
        form_data = {
            'form_id': 'test_form_123',
            'responses': {'question1': 'answer1'}
        }

        result: TaskResponse = await service.send_form_to_creator_with_tracking(
            creator_id=123456789,
            form_data=form_data
        )

        assert result.status == 'success'
        assert result.message == 'Form sent successfully'

        mock_celery_task.delay.assert_called_once_with(
            creator_id=123456789,
            form_data=form_data
        )
        mock_task_result.get.assert_called_once_with(timeout=15)

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_with_custom_timeout(
            self,
            mock_celery_task: Mock
    ):
        """
        Test sending form with custom timeout.
        """
        mock_task_result = Mock(spec=AsyncResult)
        mock_task_result.id = 'test-task-form-456'
        mock_task_result.get.return_value = {
            'status': 'success',
            'message': 'Form sent'
        }
        mock_celery_task.delay.return_value = mock_task_result
        
        service: MessageQueueService = MessageQueueService()
        form_data = {'form_id': 'test_form_456'}

        result: TaskResponse = await service.send_form_to_creator_with_tracking(
            creator_id=987654321,
            form_data=form_data,
            timeout=30
        )

        assert result.status == 'success'
        mock_task_result.get.assert_called_once_with(timeout=30)

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_task_returns_error(
            self,
            mock_celery_task: Mock,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """
        Test when Celery task returns error status.
        """
        mock_task_result = Mock(spec=AsyncResult)
        mock_task_result.id = 'test-task-form-error'
        mock_task_result.get.return_value = {
            'status': 'error',
            'message': 'Failed to send message to creator'
        }
        mock_celery_task.delay.return_value = mock_task_result
        
        service: MessageQueueService = MessageQueueService()
        form_data = {'form_id': 'test_form_error'}

        result: TaskResponse = await service.send_form_to_creator_with_tracking(
            creator_id=123456789,
            form_data=form_data
        )

        assert result.status == 'error'
        assert result.message == 'Failed to send message to creator'
        assert 'Failed to send form response to creator 123456789' in caplog_debug.text

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_timeout_exception(
            self,
            mock_celery_task: Mock,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """
        Test when task exceeds timeout and raises TimeoutError.
        """
        from celery.exceptions import TimeoutError as CeleryTimeoutError
        
        mock_task_result = Mock(spec=AsyncResult)
        mock_task_result.id = 'test-task-timeout'
        mock_task_result.get.side_effect = CeleryTimeoutError('Task timed out')
        mock_celery_task.delay.return_value = mock_task_result
        
        service: MessageQueueService = MessageQueueService()
        form_data = {'form_id': 'test_timeout'}

        result: TaskResponse = await service.send_form_to_creator_with_tracking(
            creator_id=123456789,
            form_data=form_data,
            timeout=5
        )

        assert result.status == 'error'
        assert 'Timeout or error occurred' in result.message
        assert 'Task timed out' in result.message
        assert 'Error sending form response to creator 123456789' in caplog_debug.text

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_general_exception(
            self,
            mock_celery_task: Mock,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """
        Test error handling when general exception occurs.
        """
        mock_celery_task.delay.side_effect = Exception('Connection refused')
        
        service: MessageQueueService = MessageQueueService()
        form_data = {'form_id': 'test_exception'}

        result: TaskResponse = await service.send_form_to_creator_with_tracking(
            creator_id=123456789,
            form_data=form_data
        )

        assert result.status == 'error'
        assert 'Connection refused' in result.message
        assert 'Error sending form response to creator 123456789' in caplog_debug.text

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_with_complex_form_data(
            self,
            mock_celery_task: Mock
    ):
        """
        Test sending form with complex nested data structure.
        """
        mock_task_result = Mock(spec=AsyncResult)
        mock_task_result.id = 'test-task-complex'
        mock_task_result.get.return_value = {
            'status': 'success',
            'message': 'Complex form sent'
        }
        mock_celery_task.delay.return_value = mock_task_result
        
        service: MessageQueueService = MessageQueueService()
        form_data = {
            'form_id': 'complex_form',
            'responses': {
                'text_field': 'Some answer',
                'multiple_choice': ['option1', 'option2'],
                'nested_data': {
                    'sub_field': 'value',
                    'list_field': [1, 2, 3]
                }
            },
            'metadata': {
                'timestamp': '2025-11-11T12:00:00',
                'user_id': 999
            }
        }

        result: TaskResponse = await service.send_form_to_creator_with_tracking(
            creator_id=123456789,
            form_data=form_data
        )

        assert result.status == 'success'
        
        call_kwargs = mock_celery_task.delay.call_args.kwargs
        assert call_kwargs['form_data']['form_id'] == 'complex_form'
        assert 'responses' in call_kwargs['form_data']
        assert 'metadata' in call_kwargs['form_data']

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_task_returns_taskresponse_object(
            self,
            mock_celery_task: Mock
    ):
        """
        Test when task returns TaskResponse object instead of dict.
        """
        from app.schemas import TaskResponse
        
        mock_task_result = Mock(spec=AsyncResult)
        mock_task_result.id = 'test-task-object'
        # Task returns TaskResponse object directly
        mock_task_result.get.return_value = TaskResponse(
            status='success',
            message='Object response'
        )
        mock_celery_task.delay.return_value = mock_task_result
        
        service: MessageQueueService = MessageQueueService()
        form_data = {'form_id': 'test_object'}

        result: TaskResponse = await service.send_form_to_creator_with_tracking(
            creator_id=123456789,
            form_data=form_data
        )

        assert result.status == 'success'
        assert result.message == 'Object response'
        assert isinstance(result, TaskResponse)

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_logs_success(
            self,
            mock_celery_task: Mock,
            caplog_debug: pytest.LogCaptureFixture
    ):
        """
        Test that successful form submission is properly logged.
        """
        mock_task_result = Mock(spec=AsyncResult)
        mock_task_result.id = 'test-task-log-success'
        mock_task_result.get.return_value = {
            'status': 'success',
            'message': 'Logged successfully'
        }
        mock_celery_task.delay.return_value = mock_task_result
        
        service: MessageQueueService = MessageQueueService()
        form_data = {'form_id': 'log_test'}

        await service.send_form_to_creator_with_tracking(
            creator_id=555666777,
            form_data=form_data
        )

        assert 'Form response queued to send to creator 555666777' in caplog_debug.text
        assert 'test-task-log-success' in caplog_debug.text

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_with_empty_form_data(
            self,
            mock_celery_task: Mock
    ):
        """
        Test sending form with empty form data dict.
        """
        mock_task_result = Mock(spec=AsyncResult)
        mock_task_result.id = 'test-task-empty'
        mock_task_result.get.return_value = {
            'status': 'success',
            'message': 'Empty form processed'
        }
        mock_celery_task.delay.return_value = mock_task_result
        
        service: MessageQueueService = MessageQueueService()
        form_data = {}

        result: TaskResponse = await service.send_form_to_creator_with_tracking(
            creator_id=123456789,
            form_data=form_data
        )

        assert result.status == 'success'
        call_kwargs = mock_celery_task.delay.call_args.kwargs
        assert call_kwargs['form_data'] == {}

    @patch('app.services.message_queue_service.send_form_to_creator')
    async def test_send_form_to_creator_with_minimal_timeout(
            self,
            mock_celery_task: Mock
    ):
        """
        Test sending form with minimal timeout value.
        """
        mock_task_result = Mock(spec=AsyncResult)
        mock_task_result.id = 'test-task-min-timeout'
        mock_task_result.get.return_value = {
            'status': 'success',
            'message': 'Quick response'
        }
        mock_celery_task.delay.return_value = mock_task_result
        
        service: MessageQueueService = MessageQueueService()
        form_data = {'form_id': 'quick_test'}

        result: TaskResponse = await service.send_form_to_creator_with_tracking(
            creator_id=123456789,
            form_data=form_data,
            timeout=1
        )

        assert result.status == 'success'
        mock_task_result.get.assert_called_once_with(timeout=1)
