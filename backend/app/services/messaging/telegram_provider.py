"""
Telegram messaging provider using Telegram Bot API.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests

from .base_provider import BaseMessagingProvider, Message, Attachment, MessageType


class TelegramProvider(BaseMessagingProvider):
    """
    Telegram Bot API provider.

    Requires a Telegram Bot token from @BotFather.
    Documentation: https://core.telegram.org/bots/api
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get('bot_token')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def get_authorization_url(self, redirect_uri: str) -> str:
        """
        Telegram bots don't use OAuth.
        Return instructions for adding the bot.
        """
        bot_username = self.config.get('bot_username', 'your_bot')
        return f"https://t.me/{bot_username}"

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Telegram bots use a token, not OAuth."""
        return {
            'bot_token': self.bot_token,
            'provider': 'telegram'
        }

    def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with Telegram bot token."""
        # Test bot token
        response = requests.get(f"{self.base_url}/getMe")
        if response.status_code == 200:
            bot_info = response.json()['result']
            return {
                'bot_token': self.bot_token,
                'bot_info': bot_info,
                'provider': 'telegram'
            }
        else:
            raise Exception("Invalid Telegram bot token")

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Telegram bot tokens don't expire."""
        return {'bot_token': refresh_token}

    def fetch_messages(
        self,
        access_token: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """
        Fetch Telegram messages using long polling.

        Note: Telegram uses webhook or long polling for messages.
        This implements long polling.
        """
        url = f"{self.base_url}/getUpdates"
        params = {'limit': limit, 'timeout': 30}

        response = requests.get(url, params=params)
        data = response.json()

        messages = []
        if data['ok']:
            for update in data['result']:
                if 'message' in update:
                    messages.append(self.normalize_message(update['message']))

        return messages

    def send_message(
        self,
        access_token: str,
        recipient: str,
        message: str,
        attachments: Optional[List[Attachment]] = None
    ) -> str:
        """
        Send Telegram message.

        Args:
            access_token: Bot token (not used, uses instance token)
            recipient: Chat ID (can be user ID or channel username)
            message: Message text
            attachments: Optional attachments

        Returns:
            Message ID
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': recipient,
            'text': message,
            'parse_mode': 'HTML'  # Support HTML formatting
        }

        response = requests.post(url, json=payload)
        data = response.json()

        if data['ok']:
            return str(data['result']['message_id'])
        else:
            raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")

    def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: Optional[str] = None
    ) -> str:
        """Send photo message."""
        url = f"{self.base_url}/sendPhoto"
        payload = {
            'chat_id': chat_id,
            'photo': photo_url
        }

        if caption:
            payload['caption'] = caption

        response = requests.post(url, json=payload)
        data = response.json()

        if data['ok']:
            return str(data['result']['message_id'])
        else:
            raise Exception(f"Telegram API error: {data.get('description')}")

    def send_document(
        self,
        chat_id: str,
        document_url: str,
        caption: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """Send document message."""
        url = f"{self.base_url}/sendDocument"
        payload = {
            'chat_id': chat_id,
            'document': document_url
        }

        if caption:
            payload['caption'] = caption
        if filename:
            payload['filename'] = filename

        response = requests.post(url, json=payload)
        data = response.json()

        if data['ok']:
            return str(data['result']['message_id'])
        else:
            raise Exception(f"Telegram API error: {data.get('description')}")

    def download_attachment(self, access_token: str, attachment_id: str) -> Attachment:
        """Download Telegram file."""
        # First, get file path
        file_url = f"{self.base_url}/getFile"
        params = {'file_id': attachment_id}

        response = requests.get(file_url, params=params)
        data = response.json()

        if not data['ok']:
            raise Exception(f"Failed to get file info: {data.get('description')}")

        file_path = data['result']['file_path']

        # Download file
        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        file_response = requests.get(download_url)

        return Attachment(
            filename=file_path.split('/')[-1],
            content=file_response.content,
            mime_type='application/octet-stream',
            size=len(file_response.content)
        )

    def normalize_message(self, raw_message: Dict[str, Any]) -> Message:
        """
        Convert Telegram message to unified Message format.

        Telegram message structure:
        {
            "message_id": 123,
            "from": {
                "id": 123456,
                "first_name": "John",
                "username": "john_doe"
            },
            "chat": {
                "id": 123456,
                "type": "private"
            },
            "date": 1234567890,
            "text": "Hello"
        }
        """
        # Extract sender info
        sender_name = raw_message['from'].get('username') or raw_message['from'].get('first_name', '')
        sender_id = str(raw_message['from']['id'])

        # Extract text
        body_text = ''
        if 'text' in raw_message:
            body_text = raw_message['text']
        elif 'caption' in raw_message:
            body_text = raw_message['caption']
        elif 'photo' in raw_message:
            body_text = '[Photo]'
        elif 'document' in raw_message:
            body_text = f"[Document: {raw_message['document'].get('file_name', 'file')}]"
        elif 'voice' in raw_message:
            body_text = '[Voice message]'
        elif 'video' in raw_message:
            body_text = '[Video]'
        elif 'audio' in raw_message:
            body_text = '[Audio]'

        # Extract attachments
        attachments = []
        if 'photo' in raw_message:
            # Telegram photos come in multiple sizes, take the largest
            largest_photo = max(raw_message['photo'], key=lambda p: p['file_size'])
            # Store file_id for later download
        elif 'document' in raw_message:
            # Document file_id stored
            pass

        return Message(
            platform_id=str(raw_message['message_id']),
            platform_type=MessageType.TELEGRAM,
            sender=f"{sender_name} ({sender_id})",
            receiver=str(raw_message['chat']['id']),
            subject=None,
            body_text=body_text,
            timestamp=datetime.fromtimestamp(raw_message['date']),
            attachments=attachments,
            metadata={
                'chat_type': raw_message['chat']['type'],
                'chat_id': raw_message['chat']['id'],
                'from_id': raw_message['from']['id']
            }
        )

    def set_webhook(self, webhook_url: str) -> bool:
        """
        Set webhook for receiving updates.

        Args:
            webhook_url: HTTPS URL to receive webhook updates

        Returns:
            True if successful
        """
        url = f"{self.base_url}/setWebhook"
        payload = {'url': webhook_url}

        response = requests.post(url, json=payload)
        data = response.json()

        return data.get('ok', False)

    def delete_webhook(self) -> bool:
        """Delete webhook (switch to polling mode)."""
        url = f"{self.base_url}/deleteWebhook"
        response = requests.post(url)
        data = response.json()

        return data.get('ok', False)

    def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Get information about a chat."""
        url = f"{self.base_url}/getChat"
        params = {'chat_id': chat_id}

        response = requests.get(url, params=params)
        data = response.json()

        if data['ok']:
            return data['result']
        else:
            raise Exception(f"Failed to get chat info: {data.get('description')}")

    def send_chat_action(self, chat_id: str, action: str = 'typing'):
        """
        Send chat action (typing indicator).

        Args:
            chat_id: Chat ID
            action: One of: typing, upload_photo, record_video, upload_video,
                   record_voice, upload_voice, upload_document, find_location
        """
        url = f"{self.base_url}/sendChatAction"
        payload = {
            'chat_id': chat_id,
            'action': action
        }

        requests.post(url, json=payload)

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> bool:
        """
        Answer callback query from inline keyboard.

        Args:
            callback_query_id: Callback query ID
            text: Optional notification text
            show_alert: Show alert instead of notification

        Returns:
            True if successful
        """
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {'callback_query_id': callback_query_id}

        if text:
            payload['text'] = text
        if show_alert:
            payload['show_alert'] = True

        response = requests.post(url, json=payload)
        data = response.json()

        return data.get('ok', False)

    def send_message_with_keyboard(
        self,
        chat_id: str,
        message: str,
        buttons: List[List[Dict[str, str]]]
    ) -> str:
        """
        Send message with inline keyboard.

        Args:
            chat_id: Chat ID
            message: Message text
            buttons: List of button rows, each button is {'text': '...', 'callback_data': '...'}

        Returns:
            Message ID
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'reply_markup': {
                'inline_keyboard': buttons
            }
        }

        response = requests.post(url, json=payload)
        data = response.json()

        if data['ok']:
            return str(data['result']['message_id'])
        else:
            raise Exception(f"Telegram API error: {data.get('description')}")
