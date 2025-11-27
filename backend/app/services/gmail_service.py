from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import base64
import email
from email.mime.text import MIMEText
from app.core.config import settings


class GmailService:
    """Service for Gmail OAuth and email fetching."""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    @staticmethod
    def get_auth_url() -> str:
        """Generate OAuth authorization URL."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GmailService.SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        return auth_url

    @staticmethod
    def exchange_code_for_tokens(code: str) -> Dict:
        """Exchange authorization code for access tokens."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GmailService.SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.expiry
        }

    @staticmethod
    def fetch_emails(access_token: str, months: int = 3) -> List[Dict]:
        """
        Fetch emails from Gmail.

        Args:
            access_token: OAuth access token
            months: Number of months to fetch (default 3)

        Returns:
            List of email dictionaries
        """
        credentials = Credentials(token=access_token)
        service = build('gmail', 'v1', credentials=credentials)

        # Calculate date for filtering
        since_date = datetime.now() - timedelta(days=months * 30)
        query = f'after:{since_date.strftime("%Y/%m/%d")}'

        emails = []

        try:
            # Get list of messages
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=500  # Limit for MVP
            ).execute()

            messages = results.get('messages', [])

            for message in messages:
                # Get full message details
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                email_data = GmailService._parse_email(msg)
                emails.append(email_data)

        except Exception as e:
            print(f"Error fetching emails: {e}")

        return emails

    @staticmethod
    def _parse_email(msg: Dict) -> Dict:
        """Parse Gmail message into structured format."""
        headers = msg['payload'].get('headers', [])

        # Extract headers
        subject = ""
        sender = ""
        receiver = ""
        date_str = ""

        for header in headers:
            name = header['name'].lower()
            if name == 'subject':
                subject = header['value']
            elif name == 'from':
                sender = header['value']
            elif name == 'to':
                receiver = header['value']
            elif name == 'date':
                date_str = header['value']

        # Parse timestamp
        try:
            timestamp = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        except:
            timestamp = datetime.now()

        # Extract body
        body_text = GmailService._get_email_body(msg['payload'])

        # Extract attachments
        attachments = GmailService._get_attachments_info(msg['payload'])

        return {
            "gmail_id": msg['id'],
            "subject": subject,
            "sender": sender,
            "receiver": receiver,
            "timestamp": timestamp,
            "body_text": body_text,
            "attachments": attachments
        }

    @staticmethod
    def _get_email_body(payload: Dict) -> str:
        """Extract plain text body from email payload."""
        body = ""

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
                elif part['mimeType'] == 'multipart/alternative':
                    body = GmailService._get_email_body(part)
        else:
            if 'body' in payload and 'data' in payload['body']:
                body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')

        return body

    @staticmethod
    def _get_attachments_info(payload: Dict) -> List[Dict]:
        """Extract attachment information (PDFs only for MVP)."""
        attachments = []

        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename') and part['filename'].lower().endswith('.pdf'):
                    attachments.append({
                        "filename": part['filename'],
                        "mime_type": part['mimeType'],
                        "size": part['body'].get('size', 0),
                        "attachment_id": part['body'].get('attachmentId')
                    })

        return attachments

    @staticmethod
    def download_attachment(access_token: str, message_id: str, attachment_id: str) -> bytes:
        """Download email attachment."""
        credentials = Credentials(token=access_token)
        service = build('gmail', 'v1', credentials=credentials)

        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=attachment_id
        ).execute()

        data = base64.urlsafe_b64decode(attachment['data'])
        return data
