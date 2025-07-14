from typing import List, Optional
from datetime import datetime
from domain.entities.chat import Chat
from domain.entities.participant import Participant
from domain.ports.input.create_chat import CreateChat
from infrastructure.repositories.mongo_chat_repository import MongoChatRepository
from infrastructure.websocket.websocket_server import websocket_server

class CreateChatUseCase(CreateChat):
    def __init__(self, chat_repository: MongoChatRepository):
        self.chat_repository = chat_repository
    
    async def create_chat(
        self,
        user_ids: List[str],
        description: Optional[str] = None,
        chat_type: str = "private"
    ) -> Chat:
        """Crear un nuevo chat"""
        
        # Validar parámetros
        if not user_ids or len(user_ids) < 2:
            raise ValueError("Se requieren al menos 2 usuarios para crear un chat")
        
        # Determinar tipo de chat
        if len(user_ids) == 2:
            chat_type = "private"
        else:
            chat_type = "group"
        
        # Crear participantes
        participants = []
        for i, user_id in enumerate(user_ids):
            participant = Participant(
                user_id=user_id,
                role="admin" if i == 0 else "member",  # Primer usuario es admin
                joined_at=datetime.utcnow()
            )
            participants.append(participant)
        
        # Crear chat
        chat = Chat(
            _id="",  # Se asignará por MongoDB
            type=chat_type,
            participants=participants,
            metadata={},
            title=description,
            created_at=datetime.utcnow(),
            last_message_at=None,
            unread_counts={user_id: 0 for user_id in user_ids}
        )
        
        # Guardar en base de datos
        created_chat = await self.chat_repository.create_chat(chat)
        
        # Notificar via WebSocket
        await self._notify_chat_created(created_chat)
        
        return created_chat
    
    async def _notify_chat_created(self, chat: Chat):
        """Notificar creación de chat via WebSocket"""
        chat_data = {
            "id": chat._id,
            "type": chat.type,
            "participants": [
                {
                    "user_id": p["user_id"],
                    "role": p["role"],
                    "joined_at": p["joined_at"].isoformat()
                }
                for p in chat.participants
            ],
            "title": chat.title,
            "created_at": chat.created_at.isoformat(),
            "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
            "unread_counts": chat.unread_counts
        }
        
        await websocket_server.broadcast_chat_created(chat_data) 