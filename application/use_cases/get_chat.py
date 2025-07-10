from ...domain.ports.input.get_chat import GetChat
from ...domain.ports.output.chat_repository import ChatRepository
from ...domain.entities.chat import Chat

from typing import Optional

class GetChatUseCase(GetChat):
    def __init__(self, chat_repository: ChatRepository):
        self.chat_repository = chat_repository

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        # Validate chat ID
        if not chat_id:
            raise ValueError("Chat ID cannot be empty.")
        
        # Retrieve the chat using the repository
        chat = self.chat_repository.get_chat_by_id(chat_id)
        
        if not chat:
            raise ValueError(f"Chat with ID {chat_id} does not exist.")
        
        return chat
