from typing import List, Optional
from datetime import datetime
import pytz
from domain.entities.message import Message
from domain.entities.attachment import Attachment
from domain.entities.chat import Chat
from domain.ports.input.send_message import SendMessage
from infrastructure.repositories.mongo_message_repository import MongoMessageRepository
from infrastructure.repositories.mongo_chat_repository import MongoChatRepository
from infrastructure.websocket.websocket_server import websocket_server

class SendMessageUseCase(SendMessage):
    def __init__(
        self,
        message_repository: MongoMessageRepository,
        chat_repository: MongoChatRepository
    ):
        self.message_repository = message_repository
        self.chat_repository = chat_repository
    
    async def send_message(
        self,
        chat_id: str,
        user_id: str,
        content: str,
        attachments: Optional[List[Attachment]] = None,
        message_type: str = "text"
    ) -> Message:
        """Enviar un mensaje en un chat"""
        
        # Validar parámetros
        if not chat_id or not user_id:
            raise ValueError("chat_id y user_id son requeridos")
        
        if not content and not attachments:
            raise ValueError("El mensaje debe tener contenido o archivos adjuntos")
        
        # Verificar que el chat existe
        chat = await self.chat_repository.get_chat_by_id(chat_id)
        if not chat:
            raise ValueError("Chat no encontrado")
        
        # Verificar que el usuario es participante del chat
        user_is_participant = any(
            p["user_id"] == user_id for p in chat.participants
        )
        if not user_is_participant:
            raise ValueError("Usuario no es participante del chat")
        
        # Obtener zona horaria de Colombia
        colombia_tz = pytz.timezone('America/Bogota')
        
        # Crear mensaje
        message = Message(
            _id="",  # Se asignará por MongoDB
            chat_id=chat_id,
            sender_id=user_id,
            sent_at=datetime.now(colombia_tz),
            type=message_type,
            content=content,
            attachment=attachments or [],
            status="sent"
        )
        
        # Guardar mensaje
        saved_message = await self.message_repository.save(message)
        
        # Actualizar último mensaje del chat
        chat.last_message_at = saved_message.sent_at
        await self.chat_repository.update_chat(chat)
        
        # Actualizar contadores de mensajes no leídos
        await self._update_unread_counts(chat, user_id)
        
        # Notificar via WebSocket
        await self._notify_new_message(saved_message)
        
        return saved_message
    
    async def _update_unread_counts(self, chat: Chat, sender_id: str):
        """Actualizar contadores de mensajes no leídos"""
        for participant in chat.participants:
            user_id = participant["user_id"]
            if user_id != sender_id:
                chat.unread_counts[user_id] = chat.unread_counts.get(user_id, 0) + 1
        
        await self.chat_repository.update_chat(chat)
    
    async def _notify_new_message(self, message: Message):
        """Notificar nuevo mensaje via WebSocket"""
        message_data = {
            "id": message._id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "sent_at": message.sent_at.isoformat(),
            "type": message.type,
            "content": message.content,
            "attachments": [
                {
                    "url": att["url"],
                    "filename": att["filename"],
                    "mime_type": att["mime_type"],
                    "size_bytes": att["size_bytes"]
                }
                for att in message.attachment
            ],
            "status": message.status
        }
        
        await websocket_server.broadcast_new_message(message_data)
    
    async def mark_message_as_read(self, message_id: str, user_id: str):
        """Marcar mensaje como leído"""
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            raise ValueError("Mensaje no encontrado")
        
        # Actualizar estado del mensaje
        await self.message_repository.update_status(message_id, "read")
        
        # Notificar cambio de estado
        await websocket_server.broadcast_message_status(
            message_id, "read", message.chat_id
        )
    
    async def get_chat_messages(self, chat_id: str, limit: int = 50) -> List[Message]:
        """Obtener mensajes de un chat"""
        return await self.message_repository.get_recent_messages(chat_id, limit) 