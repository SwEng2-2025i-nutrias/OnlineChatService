from ...domain.ports.input.chat.create_chat import CreateChat
from ...domain.ports.output.chat_repository import ChatRepository
from ...domain.entities.chat import Chat

from ...domain.ports.output.user_repository import UserRepository
from ...domain.entities.participant import Participant

from typing import Optional

from datetime import datetime

class CreateChatUseCase(CreateChat):
    def __init__(self, chat_repository: ChatRepository, user_repository:UserRepository):
        self.chat_repository = chat_repository
        self.user_repository = user_repository

    def create_chat(self, user_ids: list[str], description: Optional[str] = None) -> Chat:
        # Validate user IDs
        if not user_ids or len(user_ids) < 2:
            raise ValueError("At least two user IDs are required to create a chat.")
        
        current_timestamp = datetime.now()
        
        # Creation of participants

        ## Get the user information from the user_ids
        participants: list[Participant] = []
        for user_id in user_ids:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                raise ValueError(f"Participant with ID {user_id} does not exist.")
            
            # Create a participant entity
            participant = Participant(
                user_id=user.user_id,
                role=user.role,
                joined_at=current_timestamp
            )

            participants.append(participant)



        # Create a new chat instance
        chat = Chat.create(
            participants=participants,
            type='group',  # Assuming group chat for multiple participants
            created_at=current_timestamp
        )

        # Save the chat using the repository
        saved_chat = self.chat_repository.create_chat(chat)

        return saved_chat
