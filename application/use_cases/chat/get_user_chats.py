from domain.ports.input.chat.get_user_chats import GetUserChats
from domain.ports.output.chat_repository import ChatRepository
from domain.entities.chat import Chat

class GetUserChatsUseCase(GetUserChats):
    def __init__(self, chat_repository: ChatRepository):
        self.chat_repository = chat_repository

    def get_user_chats(self, user_id: str) -> list[Chat]:
        # Validate user ID
        if not user_id:
            raise ValueError("User ID cannot be empty.")
        
        # Retrieve all chats for the user using the repository
        try:
            chats = self.chat_repository.get_chats_by_user_id(user_id)
        except Exception as e:
            raise ValueError(f"An error occurred while retrieving chats for user {user_id}: {str(e)}")
        
        return chats if chats else []