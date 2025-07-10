from abc import ABC, abstractmethod
from typing import Optional
from ....entities.chat import Chat

# Interface for getting user chats
class GetUserChats(ABC):
    @abstractmethod
    def get_user_chats(self, user_id: str) -> Optional[list[Chat]]:
        """Retrieve all chats for a specific user."""
        pass