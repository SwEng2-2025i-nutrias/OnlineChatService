from abc import ABC, abstractmethod
from typing import Optional, List
from ...entities.chat import Chat

# Interface for creating a chat
class CreateChat(ABC):
    @abstractmethod
    def create_chat(
        self,
        user_ids: List[str],
        description: Optional[str] = None,
    ) -> Chat:
        """Create a new chat with the given parameters."""
        pass