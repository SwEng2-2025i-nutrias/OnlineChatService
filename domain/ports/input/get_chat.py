from abc import ABC, abstractmethod
from typing import Optional
from ...entities.chat import Chat

# Interface for getting a chat by ID
class GetUserChats(ABC):
    @abstractmethod
    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Retrieve all chats for a specific user."""
        pass