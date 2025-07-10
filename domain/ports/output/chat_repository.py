from abc import ABC, abstractmethod
from typing import List
from ...entities.chat import Chat

from typing import Optional

# Interface for chat repository
class ChatRepository(ABC):
    @abstractmethod
    def get_chat_by_id(self, chat_id: str) -> Optional[Chat]:
        """Retrieve a chat by its ID."""
        pass

    @abstractmethod
    def get_chats_by_user_id(self, user_id: str) -> Optional[List[Chat]]:
        """Retrieve all chats for a specific user."""
        pass

    @abstractmethod
    def create_chat(self, chat: Chat) -> Chat:
        """Create and return a new chat."""
        pass

    @abstractmethod
    def update_chat(self, chat: Chat) -> None:
        """Update an existing chat."""
        pass

    @abstractmethod
    def delete_chat(self, chat_id: str) -> None:
        """Delete a chat by its ID."""
        pass
