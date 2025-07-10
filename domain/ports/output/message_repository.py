# domain/ports/message_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from entities.message import Message

class MessageRepository(ABC):
    @abstractmethod
    def get_by_id(self, message_id: str) -> Optional[Message]:
        pass

    @abstractmethod
    def get_by_chat_id(self, chat_id: str) -> List[Message]:
        pass

    @abstractmethod
    def save(self, message: Message) -> Message:
        pass

    @abstractmethod
    def update_status(self, message_id: str, status: str) -> None:
        pass
