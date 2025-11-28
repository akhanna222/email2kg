"""
Messaging module for handling multiple messaging platforms.
Supports Email (Gmail, Outlook, IMAP), WhatsApp, and Telegram.
"""

from .base_provider import BaseMessagingProvider, Message, Attachment
from .email_providers import GmailProvider, OutlookProvider, IMAPProvider
from .whatsapp_provider import WhatsAppProvider
from .telegram_provider import TelegramProvider

__all__ = [
    'BaseMessagingProvider',
    'Message',
    'Attachment',
    'GmailProvider',
    'OutlookProvider',
    'IMAPProvider',
    'WhatsAppProvider',
    'TelegramProvider',
]
