from typing import List
from domain.entities.chat import Chat
from infrastructure.repositories.mongo_chat_repository import MongoChatRepository

class GetChatsUseCase:
    def __init__(self, chat_repository: MongoChatRepository):
        self.chat_repository = chat_repository
    
    async def get_user_chats(self, user_id: str) -> List[Chat]:
        """Obtener todos los chats de un usuario"""
        if not user_id:
            raise ValueError("user_id es requerido")
        
        chats = await self.chat_repository.get_chats_by_user_id(user_id)
        
        # Ordenar por último mensaje (más reciente primero)
        chats.sort(
            key=lambda x: x.last_message_at or x.created_at,
            reverse=True
        )
        
        return chats
    
    async def get_chat_by_id(self, chat_id: str) -> Chat:
        """Obtener chat por ID"""
        if not chat_id:
            raise ValueError("chat_id es requerido")
        
        chat = await self.chat_repository.get_chat_by_id(chat_id)
        if not chat:
            raise ValueError("Chat no encontrado")
        
        return chat 