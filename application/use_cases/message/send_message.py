from ....domain.ports.input.message.send_message import SendMessage
from ....domain.ports.output.message_repository import MessageRepository
from ....domain.entities.message import Message, Attachment

from typing import Optional, List

class SendMessageUseCase(SendMessage):
    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    def send_message(
        self,
        chat_id: str,
        user_id: str,
        content: str,
        attachments: Optional[List[Attachment]] = None,
    ) -> Message:
        # Validate inputs
        if not chat_id or not user_id or not content:
            raise ValueError("Chat ID, User ID, and content cannot be empty.")
        
        # Create a new message entity
        message = Message.create(sender_id=user_id, chat_id=chat_id, type="text", content=content, attachments=attachments)
        
        # Save the message using the repository
        saved_message = self.message_repository.save(message)
        
        return saved_message