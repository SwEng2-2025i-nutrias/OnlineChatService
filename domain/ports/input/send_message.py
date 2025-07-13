from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.message import Message
from domain.entities.attachment import Attachment

# Interface for sending messages
class SendMessage(ABC):
    @abstractmethod
    def send_message(
        self,
        chat_id: str,
        user_id: str,
        content: str,
        attachments: Optional[List[Attachment]] = None,
    ) -> Message:
        """Send a message in a chat."""
        pass