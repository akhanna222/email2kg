"""
Base messaging provider interface for all messaging platforms.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class MessageType(str, Enum):
    """Type of message platform."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"


@dataclass
class Attachment:
    """Represents a message attachment."""
    filename: str
    content: bytes
    mime_type: str
    size: int


@dataclass
class Message:
    """Unified message structure across all platforms."""
    platform_id: str  # Unique ID from the platform
    platform_type: MessageType
    sender: str
    receiver: Optional[str]
    subject: Optional[str]  # For emails, None for chat messages
    body_text: str
    timestamp: datetime
    attachments: List[Attachment]
    metadata: Dict[str, Any]  # Platform-specific data


class BaseMessagingProvider(ABC):
    """Abstract base class for all messaging providers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the messaging provider.

        Args:
            config: Provider-specific configuration
        """
        self.config = config

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate with the messaging platform.

        Args:
            credentials: Platform-specific credentials

        Returns:
            Authentication tokens/data
        """
        pass

    @abstractmethod
    def fetch_messages(
        self,
        access_token: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """
        Fetch messages from the platform.

        Args:
            access_token: Authentication token
            limit: Maximum number of messages to fetch
            since: Only fetch messages after this datetime

        Returns:
            List of Message objects
        """
        pass

    @abstractmethod
    def send_message(
        self,
        access_token: str,
        recipient: str,
        message: str,
        attachments: Optional[List[Attachment]] = None
    ) -> str:
        """
        Send a message through the platform.

        Args:
            access_token: Authentication token
            recipient: Message recipient
            message: Message content
            attachments: Optional list of attachments

        Returns:
            Message ID from the platform
        """
        pass

    @abstractmethod
    def download_attachment(
        self,
        access_token: str,
        attachment_id: str
    ) -> Attachment:
        """
        Download an attachment from the platform.

        Args:
            access_token: Authentication token
            attachment_id: Platform-specific attachment ID

        Returns:
            Attachment object with content
        """
        pass

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str) -> str:
        """
        Get OAuth authorization URL (if applicable).

        Args:
            redirect_uri: Callback URL after authorization

        Returns:
            Authorization URL
        """
        pass

    @abstractmethod
    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access tokens.

        Args:
            code: Authorization code
            redirect_uri: Callback URL

        Returns:
            Dictionary with access_token, refresh_token, expiry
        """
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.

        Args:
            refresh_token: Refresh token

        Returns:
            Dictionary with new access_token and expiry
        """
        pass

    def normalize_message(self, raw_message: Dict[str, Any]) -> Message:
        """
        Convert platform-specific message format to unified Message format.

        Args:
            raw_message: Platform-specific message data

        Returns:
            Normalized Message object
        """
        # Default implementation - should be overridden by subclasses
        raise NotImplementedError("Subclass must implement normalize_message")
