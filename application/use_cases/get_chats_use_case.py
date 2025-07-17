from typing import List
from domain.entities.chat import Chat
from infrastructure.repositories.mongo_chat_repository import MongoChatRepository
from adapters.output.http_user_repository import HttpUserRepository

class GetChatsUseCase:
    def __init__(self, chat_repository: MongoChatRepository):
        self.chat_repository = chat_repository
        self.user_repository = HttpUserRepository()
    
    async def get_user_chats(self, user_id: str) -> List[Chat]:
        """Obtener todos los chats de un usuario con información enriquecida"""
        if not user_id:
            raise ValueError("user_id es requerido")
        
        chats = await self.chat_repository.get_chats_by_user_id(user_id)
        
        # Enriquecer participantes con información de usuarios
        for chat in chats:
            enriched_participants = []
            for participant in chat.participants:
                user_data = await self.user_repository.get_user_by_id(participant["user_id"])
                
                enriched_participant = {
                    "user_id": participant["user_id"],
                    "role": participant["role"],
                    "joined_at": participant["joined_at"],
                    "user_name": user_data.get("name", "Usuario") if user_data else "Usuario",
                    "user_email": user_data.get("email", "") if user_data else ""
                }
                enriched_participants.append(enriched_participant)
            
            # Actualizar participantes del chat
            chat.participants = enriched_participants
        
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