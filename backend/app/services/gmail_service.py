from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import base64
import email
import os
from email.mime.text import MIMEText
from app.core.config import settings


class GmailService:
    """Service for Gmail OAuth and email fetching."""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    @staticmethod
    def get_auth_url(user_id: int) -> str:
        """
        Generate OAuth authorization URL with user context.

        Args:
            user_id: User ID to pass through OAuth flow via state parameter

        Returns:
            OAuth authorization URL
        """
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

        # Pass user_id as state to identify user after OAuth redirect
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            state=str(user_id)
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
    def fetch_emails(access_token: str, months: int = 3, max_emails: Optional[int] = None) -> List[Dict]:
        """
        Fetch emails from Gmail.

        Args:
            access_token: OAuth access token
            months: Number of months to fetch (default 3)
            max_emails: Maximum number of emails to fetch (None = unlimited)

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
            # Get list of messages (fetch all matching messages with pagination)
            messages = []
            page_token = None

            while True:
                # Determine how many to fetch in this page
                if max_emails:
                    remaining = max_emails - len(messages)
                    if remaining <= 0:
                        break
                    page_size = min(500, remaining)
                else:
                    page_size = 500

                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=page_size,
                    pageToken=page_token
                ).execute()

                messages.extend(results.get('messages', []))
                page_token = results.get('nextPageToken')

                # Break if no more pages or reached max_emails
                if not page_token:
                    break
                if max_emails and len(messages) >= max_emails:
                    break

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
        """
        Extract email body from payload.
        Tries to get plain text first, falls back to HTML converted to text.
        """
        plain_body = ""
        html_body = ""

        def extract_body_parts(part: Dict):
            """Recursively extract text and HTML parts."""
            nonlocal plain_body, html_body

            if 'parts' in part:
                for subpart in part['parts']:
                    extract_body_parts(subpart)
            else:
                mime_type = part.get('mimeType', '')
                body_data = part.get('body', {}).get('data')

                if body_data:
                    try:
                        decoded = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')

                        if mime_type == 'text/plain' and not plain_body:
                            plain_body = decoded
                        elif mime_type == 'text/html' and not html_body:
                            html_body = decoded
                    except Exception as e:
                        print(f"Error decoding body part: {e}")

        # Extract all body parts
        extract_body_parts(payload)

        # Prefer plain text, fall back to HTML (converted to text)
        if plain_body:
            return plain_body
        elif html_body:
            # Convert HTML to plain text (basic conversion)
            return GmailService._html_to_text(html_body)
        else:
            return ""

    @staticmethod
    def _html_to_text(html: str) -> str:
        """
        Convert HTML to plain text.
        Removes HTML tags and decodes entities.
        """
        import re
        from html import unescape

        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Replace <br> and <p> with newlines
        html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</p>', '\n\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<p[^>]*>', '\n', html, flags=re.IGNORECASE)

        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', html)

        # Decode HTML entities
        text = unescape(text)

        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
        text = text.strip()

        return text

    @staticmethod
    def _get_attachments_info(payload: Dict) -> List[Dict]:
        """
        Extract attachment information from email payload.
        Supports PDFs and images (jpg, jpeg, png, tiff, tif, webp, bmp).
        """
        attachments = []
        supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.bmp'}

        def _extract_from_part(part: Dict):
            """Recursively extract attachments from email parts."""
            if isinstance(part, dict):
                filename = part.get('filename', '')
                if filename:
                    file_ext = os.path.splitext(filename.lower())[1]
                    if file_ext in supported_extensions:
                        attachment_id = part.get('body', {}).get('attachmentId')
                        if attachment_id:
                            attachments.append({
                                "filename": filename,
                                "mime_type": part.get('mimeType', 'application/octet-stream'),
                                "size": part.get('body', {}).get('size', 0),
                                "attachment_id": attachment_id
                            })

                # Check nested parts
                if 'parts' in part:
                    for subpart in part['parts']:
                        _extract_from_part(subpart)

        _extract_from_part(payload)
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
