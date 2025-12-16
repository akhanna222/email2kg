"""
Email providers: Gmail, Outlook, and generic IMAP.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import base64
import email
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import imaplib
import smtplib

from .base_provider import BaseMessagingProvider, Message, Attachment, MessageType


class GmailProvider(BaseMessagingProvider):
    """Gmail email provider using OAuth2."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly',
                      'https://www.googleapis.com/auth/gmail.send']

    def get_authorization_url(self, redirect_uri: str) -> str:
        """Get Gmail OAuth2 authorization URL."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.scopes,
            redirect_uri=redirect_uri
        )
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.scopes,
            redirect_uri=redirect_uri
        )
        flow.fetch_token(code=code)

        credentials = flow.credentials
        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': credentials.expiry,
            'provider': 'gmail'
        }

    def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with Gmail using credentials."""
        return credentials

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Gmail access token."""
        from google.auth.transport.requests import Request

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        creds.refresh(Request())

        return {
            'access_token': creds.token,
            'token_expiry': creds.expiry
        }

    def fetch_messages(
        self,
        access_token: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """Fetch emails from Gmail."""
        creds = Credentials(token=access_token)
        service = build('gmail', 'v1', credentials=creds)

        # Build query
        query = ''
        if since:
            query = f'after:{int(since.timestamp())}'

        try:
            results = service.users().messages().list(
                userId='me',
                maxResults=limit,
                q=query
            ).execute()

            messages = []
            if 'messages' in results:
                for msg in results['messages']:
                    full_msg = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    messages.append(self.normalize_message(full_msg))

            return messages

        except HttpError as error:
            print(f'Gmail API error: {error}')
            return []

    def normalize_message(self, raw_message: Dict[str, Any]) -> Message:
        """Convert Gmail message to unified Message format."""
        headers = {h['name']: h['value'] for h in raw_message['payload']['headers']}

        # Extract body
        body_text = ''
        if 'parts' in raw_message['payload']:
            for part in raw_message['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in raw_message['payload'] and 'data' in raw_message['payload']['body']:
            body_text = base64.urlsafe_b64decode(
                raw_message['payload']['body']['data']
            ).decode('utf-8')

        # Extract attachments
        attachments = []
        if 'parts' in raw_message['payload']:
            for part in raw_message['payload']['parts']:
                if 'filename' in part and part['filename']:
                    # Attachment found (not downloading content here for efficiency)
                    pass

        return Message(
            platform_id=raw_message['id'],
            platform_type=MessageType.EMAIL,
            sender=headers.get('From', ''),
            receiver=headers.get('To', ''),
            subject=headers.get('Subject', ''),
            body_text=body_text,
            timestamp=datetime.fromtimestamp(int(raw_message['internalDate']) / 1000),
            attachments=attachments,
            metadata={'labels': raw_message.get('labelIds', [])}
        )

    def send_message(
        self,
        access_token: str,
        recipient: str,
        message: str,
        attachments: Optional[List[Attachment]] = None
    ) -> str:
        """Send email via Gmail."""
        creds = Credentials(token=access_token)
        service = build('gmail', 'v1', credentials=creds)

        email_message = MIMEText(message)
        email_message['to'] = recipient
        email_message['subject'] = 'Email2KG Notification'

        raw_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode('utf-8')

        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        return sent_message['id']

    def download_attachment(self, access_token: str, attachment_id: str) -> Attachment:
        """Download attachment from Gmail."""
        creds = Credentials(token=access_token)
        service = build('gmail', 'v1', credentials=creds)

        message_id, att_id = attachment_id.split(':')
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=att_id
        ).execute()

        data = base64.urlsafe_b64decode(attachment['data'])

        return Attachment(
            filename='attachment',
            content=data,
            mime_type='application/octet-stream',
            size=len(data)
        )


class OutlookProvider(BaseMessagingProvider):
    """Microsoft Outlook email provider using OAuth2."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.scopes = ['https://graph.microsoft.com/Mail.Read',
                      'https://graph.microsoft.com/Mail.Send']

    def get_authorization_url(self, redirect_uri: str) -> str:
        """Get Outlook OAuth2 authorization URL."""
        # Microsoft Graph OAuth implementation
        base_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_mode': 'query'
        }
        from urllib.parse import urlencode
        return f"{base_url}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for Outlook tokens."""
        import requests

        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        response = requests.post(token_url, data=data)
        tokens = response.json()

        return {
            'access_token': tokens['access_token'],
            'refresh_token': tokens.get('refresh_token'),
            'token_expiry': datetime.utcnow() + timedelta(seconds=tokens['expires_in']),
            'provider': 'outlook'
        }

    def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with Outlook."""
        return credentials

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Outlook access token."""
        import requests

        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }

        response = requests.post(token_url, data=data)
        tokens = response.json()

        return {
            'access_token': tokens['access_token'],
            'token_expiry': datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
        }

    def fetch_messages(
        self,
        access_token: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """Fetch emails from Outlook using Microsoft Graph API."""
        import requests

        headers = {'Authorization': f'Bearer {access_token}'}
        url = f'https://graph.microsoft.com/v1.0/me/messages?$top={limit}'

        if since:
            url += f'&$filter=receivedDateTime ge {since.isoformat()}Z'

        response = requests.get(url, headers=headers)
        data = response.json()

        messages = []
        for msg in data.get('value', []):
            messages.append(self.normalize_message(msg))

        return messages

    def normalize_message(self, raw_message: Dict[str, Any]) -> Message:
        """Convert Outlook message to unified Message format."""
        return Message(
            platform_id=raw_message['id'],
            platform_type=MessageType.EMAIL,
            sender=raw_message['from']['emailAddress']['address'],
            receiver=raw_message['toRecipients'][0]['emailAddress']['address'] if raw_message['toRecipients'] else '',
            subject=raw_message['subject'],
            body_text=raw_message['body']['content'],
            timestamp=datetime.fromisoformat(raw_message['receivedDateTime'].replace('Z', '+00:00')),
            attachments=[],
            metadata={'importance': raw_message.get('importance')}
        )

    def send_message(
        self,
        access_token: str,
        recipient: str,
        message: str,
        attachments: Optional[List[Attachment]] = None
    ) -> str:
        """Send email via Outlook."""
        import requests

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        email_data = {
            'message': {
                'subject': 'Email2KG Notification',
                'body': {
                    'contentType': 'Text',
                    'content': message
                },
                'toRecipients': [
                    {
                        'emailAddress': {
                            'address': recipient
                        }
                    }
                ]
            }
        }

        response = requests.post(
            'https://graph.microsoft.com/v1.0/me/sendMail',
            headers=headers,
            json=email_data
        )

        return 'sent' if response.status_code == 202 else 'failed'

    def download_attachment(self, access_token: str, attachment_id: str) -> Attachment:
        """Download attachment from Outlook."""
        import requests

        headers = {'Authorization': f'Bearer {access_token}'}
        message_id, att_id = attachment_id.split(':')

        url = f'https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments/{att_id}'
        response = requests.get(url, headers=headers)
        data = response.json()

        return Attachment(
            filename=data['name'],
            content=base64.b64decode(data['contentBytes']),
            mime_type=data['contentType'],
            size=data['size']
        )


class IMAPProvider(BaseMessagingProvider):
    """Generic IMAP email provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.imap_server = config.get('imap_server')
        self.imap_port = config.get('imap_port', 993)
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)

    def get_authorization_url(self, redirect_uri: str) -> str:
        """IMAP doesn't use OAuth, return empty string."""
        return ""

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """IMAP doesn't use OAuth."""
        return {}

    def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with IMAP using username/password."""
        username = credentials.get('username')
        password = credentials.get('password')

        # Test connection
        mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        mail.login(username, password)
        mail.logout()

        return {
            'username': username,
            'password': password,
            'provider': 'imap'
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """IMAP doesn't use tokens."""
        return {}

    def fetch_messages(
        self,
        access_token: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """Fetch emails from IMAP server."""
        # access_token contains username:password for IMAP
        username, password = access_token.split(':', 1)

        mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        mail.login(username, password)
        mail.select('INBOX')

        # Search criteria
        if since:
            date_str = since.strftime("%d-%b-%Y")
            _, message_numbers = mail.search(None, f'SINCE {date_str}')
        else:
            _, message_numbers = mail.search(None, 'ALL')

        messages = []
        for num in message_numbers[0].split()[:limit]:
            _, msg_data = mail.fetch(num, '(RFC822)')
            email_message = email.message_from_bytes(msg_data[0][1])
            messages.append(self.normalize_message(email_message))

        mail.logout()
        return messages

    def normalize_message(self, raw_message) -> Message:
        """Convert IMAP email message to unified Message format."""
        # Extract body
        body_text = ''
        if raw_message.is_multipart():
            for part in raw_message.walk():
                if part.get_content_type() == 'text/plain':
                    body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body_text = raw_message.get_payload(decode=True).decode('utf-8', errors='ignore')

        return Message(
            platform_id=raw_message['Message-ID'],
            platform_type=MessageType.EMAIL,
            sender=raw_message['From'],
            receiver=raw_message['To'],
            subject=raw_message['Subject'],
            body_text=body_text,
            timestamp=email.utils.parsedate_to_datetime(raw_message['Date']),
            attachments=[],
            metadata={}
        )

    def send_message(
        self,
        access_token: str,
        recipient: str,
        message: str,
        attachments: Optional[List[Attachment]] = None
    ) -> str:
        """Send email via SMTP."""
        username, password = access_token.split(':', 1)

        msg = MIMEText(message)
        msg['Subject'] = 'Email2KG Notification'
        msg['From'] = username
        msg['To'] = recipient

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)

        return 'sent'

    def download_attachment(self, access_token: str, attachment_id: str) -> Attachment:
        """Download attachment from IMAP."""
        # Implementation for downloading specific attachment
        raise NotImplementedError("IMAP attachment download not implemented")
