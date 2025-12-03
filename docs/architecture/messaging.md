# Messaging Module Documentation

The Email2KG platform now supports multiple messaging platforms through a unified, modular architecture.

## Supported Platforms

### 📧 Email Providers
- **Gmail** - OAuth2 authentication with Google API
- **Outlook/Office 365** - Microsoft Graph API integration
- **IMAP** - Generic support for any IMAP email server

### 💬 Messaging Platforms
- **WhatsApp Business API** - For WhatsApp business messaging
- **Telegram Bot API** - For Telegram bot integration

## Architecture

### Base Provider Interface

All messaging providers implement the `BaseMessagingProvider` abstract class, ensuring consistent API across platforms:

```python
from app.services.messaging import (
    GmailProvider,
    OutlookProvider,
    IMAPProvider,
    WhatsAppProvider,
    TelegramProvider
)
```

### Unified Message Structure

```python
@dataclass
class Message:
    platform_id: str          # Unique ID from platform
    platform_type: MessageType # EMAIL, WHATSAPP, TELEGRAM
    sender: str
    receiver: Optional[str]
    subject: Optional[str]     # For emails only
    body_text: str
    timestamp: datetime
    attachments: List[Attachment]
    metadata: Dict[str, Any]   # Platform-specific data
```

## Configuration

### Environment Variables

Add to your `.env` file:

#### Gmail
```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

#### Outlook
```bash
OUTLOOK_CLIENT_ID=your_outlook_client_id
OUTLOOK_CLIENT_SECRET=your_outlook_client_secret
OUTLOOK_REDIRECT_URI=http://localhost:8000/api/auth/outlook/callback
```

#### IMAP (Generic Email)
```bash
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USERNAME=your_email@example.com
IMAP_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

#### WhatsApp Business
```bash
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_APP_ID=your_facebook_app_id
WHATSAPP_APP_SECRET=your_facebook_app_secret
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
```

#### Telegram
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_BOT_USERNAME=your_bot_username
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/telegram/webhook
```

## Usage Examples

### Gmail Provider

```python
from app.services.messaging import GmailProvider

# Initialize
gmail = GmailProvider({
    'client_id': 'YOUR_CLIENT_ID',
    'client_secret': 'YOUR_CLIENT_SECRET'
})

# Get authorization URL
auth_url = gmail.get_authorization_url('http://localhost:8000/callback')

# Exchange code for tokens
tokens = gmail.exchange_code_for_tokens(code, 'http://localhost:8000/callback')

# Fetch messages
messages = gmail.fetch_messages(
    access_token=tokens['access_token'],
    limit=100
)

# Send message
message_id = gmail.send_message(
    access_token=tokens['access_token'],
    recipient='user@example.com',
    message='Hello from Email2KG!'
)
```

### WhatsApp Provider

```python
from app.services.messaging import WhatsAppProvider

# Initialize
whatsapp = WhatsAppProvider({
    'phone_number_id': 'YOUR_PHONE_NUMBER_ID',
    'app_id': 'YOUR_APP_ID',
    'app_secret': 'YOUR_APP_SECRET'
})

# Send text message
message_id = whatsapp.send_message(
    access_token='YOUR_ACCESS_TOKEN',
    recipient='+1234567890',
    message='Hello from Email2KG!'
)

# Send media message
message_id = whatsapp.send_media_message(
    access_token='YOUR_ACCESS_TOKEN',
    recipient='+1234567890',
    media_type='image',
    media_url='https://example.com/image.jpg',
    caption='Check this out!'
)

# Send template message (pre-approved)
message_id = whatsapp.send_template_message(
    access_token='YOUR_ACCESS_TOKEN',
    recipient='+1234567890',
    template_name='hello_world',
    language_code='en'
)
```

### Telegram Provider

```python
from app.services.messaging import TelegramProvider

# Initialize
telegram = TelegramProvider({
    'bot_token': 'YOUR_BOT_TOKEN',
    'bot_username': 'your_bot'
})

# Send message
message_id = telegram.send_message(
    access_token='',  # Not needed, uses bot_token
    recipient='123456789',  # Chat ID
    message='Hello from Email2KG!'
)

# Send photo
message_id = telegram.send_photo(
    chat_id='123456789',
    photo_url='https://example.com/image.jpg',
    caption='Check this out!'
)

# Send message with inline keyboard
message_id = telegram.send_message_with_keyboard(
    chat_id='123456789',
    message='Choose an option:',
    buttons=[
        [
            {'text': 'Option 1', 'callback_data': 'opt1'},
            {'text': 'Option 2', 'callback_data': 'opt2'}
        ]
    ]
)

# Set webhook
telegram.set_webhook('https://your-domain.com/api/telegram/webhook')
```

## Setting Up Messaging Platforms

### WhatsApp Business API

1. Create a Facebook App at https://developers.facebook.com/
2. Add WhatsApp product to your app
3. Set up a WhatsApp Business Account
4. Get your Phone Number ID and Business Account ID
5. Generate an access token
6. Configure webhook for receiving messages

**Webhook Endpoint**: `POST /api/whatsapp/webhook`

### Telegram Bot API

1. Message @BotFather on Telegram
2. Create a new bot with `/newbot` command
3. Get your bot token
4. Set webhook URL or use long polling

**Webhook Endpoint**: `POST /api/telegram/webhook`

## Webhook Integration

### WhatsApp Webhook Handling

```python
@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()

    # Verify webhook
    if request.query_params.get('hub.mode') == 'subscribe':
        if request.query_params.get('hub.verify_token') == VERIFY_TOKEN:
            return request.query_params.get('hub.challenge')

    # Process message
    for entry in data.get('entry', []):
        for change in entry.get('changes', []):
            value = change.get('value', {})
            for message in value.get('messages', []):
                # Process message
                whatsapp = WhatsAppProvider(config)
                normalized_msg = whatsapp.normalize_message(message)
                # Store message in database
```

### Telegram Webhook Handling

```python
@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    telegram = TelegramProvider(config)

    if 'message' in data:
        # Process message
        normalized_msg = telegram.normalize_message(data['message'])
        # Store message in database

    if 'callback_query' in data:
        # Handle button callback
        callback_id = data['callback_query']['id']
        callback_data = data['callback_query']['data']
        telegram.answer_callback_query(callback_id, "Received!")
```

## Best Practices

### 1. Token Management
- Store access tokens securely in database
- Implement token refresh logic for OAuth providers
- Use environment variables for API keys

### 2. Error Handling
```python
try:
    messages = provider.fetch_messages(access_token, limit=100)
except Exception as e:
    logger.error(f"Failed to fetch messages: {e}")
    # Handle error appropriately
```

### 3. Rate Limiting
- WhatsApp Business API: 1,000 messages per second
- Telegram: 30 messages per second per chat
- Gmail: 250 quota units per user per second

### 4. Message Processing
```python
for message in messages:
    # Process attachments if present
    for attachment in message.attachments:
        # Download and process
        attachment_data = provider.download_attachment(
            access_token,
            attachment.platform_id
        )

        # Extract text from PDF attachments
        if attachment_data.mime_type == 'application/pdf':
            ocr_result = ocr_service.extract_text_from_pdf(
                attachment_data.content
            )
```

## Migration Guide

### From Old Gmail Service to New Messaging Module

**Old Code:**
```python
from app.services.gmail_service import GmailService

emails = GmailService.fetch_emails(access_token, months=3)
```

**New Code:**
```python
from app.services.messaging import GmailProvider
from datetime import datetime, timedelta

gmail = GmailProvider(config)
since = datetime.now() - timedelta(days=90)
messages = gmail.fetch_messages(access_token, limit=500, since=since)
```

## Troubleshooting

### Gmail OAuth Issues
- Ensure redirect URI matches exactly in Google Console
- Check that Gmail API is enabled
- Verify scopes include `gmail.readonly` and `gmail.send`

### WhatsApp Webhook Not Receiving Messages
- Verify webhook URL is HTTPS
- Check webhook verification token matches
- Ensure webhook is subscribed to message events

### Telegram Bot Not Responding
- Verify bot token is correct
- Check bot has permission to read messages
- Ensure webhook URL is accessible

## Future Enhancements

- Slack integration
- Discord bot support
- SMS via Twilio
- Signal messenger
- WeChat integration
- Message queue for high-volume processing
- Multi-language support
- Message templates system
- Auto-reply capabilities
