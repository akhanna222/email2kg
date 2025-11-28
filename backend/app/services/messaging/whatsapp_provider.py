"""
WhatsApp messaging provider using WhatsApp Business API.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import json

from .base_provider import BaseMessagingProvider, Message, Attachment, MessageType


class WhatsAppProvider(BaseMessagingProvider):
    """
    WhatsApp Business API provider.

    Requires WhatsApp Business account and API credentials.
    Documentation: https://developers.facebook.com/docs/whatsapp/cloud-api
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.phone_number_id = config.get('phone_number_id')
        self.business_account_id = config.get('business_account_id')
        self.api_version = config.get('api_version', 'v18.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def get_authorization_url(self, redirect_uri: str) -> str:
        """Get WhatsApp Business authorization URL."""
        # WhatsApp Business uses Facebook OAuth
        client_id = self.config.get('app_id')
        scope = 'whatsapp_business_management,whatsapp_business_messaging'

        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}&"
            f"response_type=code"
        )

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for WhatsApp Business access token."""
        app_id = self.config.get('app_id')
        app_secret = self.config.get('app_secret')

        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            'client_id': app_id,
            'client_secret': app_secret,
            'code': code,
            'redirect_uri': redirect_uri
        }

        response = requests.get(token_url, params=params)
        data = response.json()

        return {
            'access_token': data['access_token'],
            'token_type': data.get('token_type', 'bearer'),
            'provider': 'whatsapp'
        }

    def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with WhatsApp Business API."""
        # For WhatsApp, credentials contain the access token
        return credentials

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh WhatsApp access token.
        Note: Long-lived tokens for WhatsApp Business don't expire.
        """
        return {'access_token': refresh_token}

    def fetch_messages(
        self,
        access_token: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """
        Fetch WhatsApp messages using webhooks.

        Note: WhatsApp Business API uses webhooks for incoming messages.
        This method retrieves messages from a webhook queue/database.
        """
        # In practice, WhatsApp messages are received via webhooks
        # This method would query a local database where webhook data is stored

        # Placeholder implementation
        return []

    def send_message(
        self,
        access_token: str,
        recipient: str,
        message: str,
        attachments: Optional[List[Attachment]] = None
    ) -> str:
        """Send WhatsApp message."""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Format phone number (remove + if present)
        recipient = recipient.replace('+', '').replace('-', '').replace(' ', '')

        # Send text message
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': recipient,
            'type': 'text',
            'text': {
                'preview_url': False,
                'body': message
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if response.status_code == 200:
            return data['messages'][0]['id']
        else:
            raise Exception(f"WhatsApp API error: {data}")

    def send_media_message(
        self,
        access_token: str,
        recipient: str,
        media_type: str,
        media_url: str,
        caption: Optional[str] = None
    ) -> str:
        """
        Send WhatsApp media message (image, video, document, audio).

        Args:
            access_token: WhatsApp Business access token
            recipient: Recipient phone number
            media_type: One of: image, video, document, audio
            media_url: URL of the media file
            caption: Optional caption for the media

        Returns:
            Message ID
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        recipient = recipient.replace('+', '').replace('-', '').replace(' ', '')

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': recipient,
            'type': media_type,
            media_type: {
                'link': media_url
            }
        }

        if caption and media_type in ['image', 'video', 'document']:
            payload[media_type]['caption'] = caption

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if response.status_code == 200:
            return data['messages'][0]['id']
        else:
            raise Exception(f"WhatsApp API error: {data}")

    def download_attachment(self, access_token: str, attachment_id: str) -> Attachment:
        """Download WhatsApp media attachment."""
        # First, get media URL
        url = f"{self.base_url}/{attachment_id}"
        headers = {'Authorization': f'Bearer {access_token}'}

        response = requests.get(url, headers=headers)
        media_data = response.json()

        media_url = media_data['url']

        # Download media
        media_response = requests.get(media_url, headers=headers)

        return Attachment(
            filename=media_data.get('file_name', 'whatsapp_media'),
            content=media_response.content,
            mime_type=media_data.get('mime_type', 'application/octet-stream'),
            size=len(media_response.content)
        )

    def normalize_message(self, raw_message: Dict[str, Any]) -> Message:
        """
        Convert WhatsApp webhook message to unified Message format.

        WhatsApp webhook payload structure:
        {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [...]
                    }
                }]
            }]
        }
        """
        # Extract message from webhook payload
        msg = raw_message

        # Determine message type
        msg_type = msg.get('type', 'text')
        body_text = ''
        attachments = []

        if msg_type == 'text':
            body_text = msg['text']['body']
        elif msg_type == 'image':
            # Has media attachment
            body_text = msg['image'].get('caption', '')
            # Attachment ID stored for later download
        elif msg_type == 'document':
            body_text = msg['document'].get('caption', '')
        elif msg_type == 'audio':
            body_text = '[Audio message]'
        elif msg_type == 'video':
            body_text = msg['video'].get('caption', '')

        return Message(
            platform_id=msg['id'],
            platform_type=MessageType.WHATSAPP,
            sender=msg['from'],
            receiver=self.phone_number_id,
            subject=None,
            body_text=body_text,
            timestamp=datetime.fromtimestamp(int(msg['timestamp'])),
            attachments=attachments,
            metadata={
                'type': msg_type,
                'context': msg.get('context', {}),
                'profile_name': msg.get('profile', {}).get('name', '')
            }
        )

    def mark_as_read(self, access_token: str, message_id: str) -> bool:
        """Mark WhatsApp message as read."""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'messaging_product': 'whatsapp',
            'status': 'read',
            'message_id': message_id
        }

        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200

    def send_template_message(
        self,
        access_token: str,
        recipient: str,
        template_name: str,
        language_code: str = 'en',
        parameters: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Send WhatsApp template message (pre-approved message templates).

        Args:
            access_token: WhatsApp Business access token
            recipient: Recipient phone number
            template_name: Name of approved template
            language_code: Language code (default: en)
            parameters: Template parameters

        Returns:
            Message ID
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        recipient = recipient.replace('+', '').replace('-', '').replace(' ', '')

        payload = {
            'messaging_product': 'whatsapp',
            'to': recipient,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {
                    'code': language_code
                }
            }
        }

        if parameters:
            payload['template']['components'] = [
                {
                    'type': 'body',
                    'parameters': parameters
                }
            ]

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if response.status_code == 200:
            return data['messages'][0]['id']
        else:
            raise Exception(f"WhatsApp API error: {data}")
