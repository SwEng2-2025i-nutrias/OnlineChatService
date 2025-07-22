from typing import List, Dict, Optional
import asyncio
from domain.entities.chat import Chat
from infrastructure.repositories.mongo_chat_repository import MongoChatRepository
from adapters.output.http_user_repository import HttpUserRepository

class GetChatsUseCase:
    def __init__(self, chat_repository: MongoChatRepository):
        self.chat_repository = chat_repository
        self.user_repository = HttpUserRepository()
        self._user_cache = {}  # ✅ Cache simple para usuarios
    
    async def get_user_chats(self, user_id: str) -> List[Chat]:
        """Obtener todos los chats de un usuario con información enriquecida (optimizado)"""
        if not user_id:
            raise ValueError("user_id es requerido")
        
        chats = await self.chat_repository.get_chats_by_user_id(user_id)
        
        # ✅ OPTIMIZACIÓN: Solo enriquecer chats que no tengan datos frescos
        chats_to_enrich = []
        for chat in chats:
            if not self._are_user_data_fresh(chat):
                chats_to_enrich.append(chat)
        
        if chats_to_enrich:
            # Obtener todos los user_ids únicos de todos los chats que necesitan enriquecimiento
            all_user_ids = set()
            for chat in chats_to_enrich:
                for participant in chat.participants:
                    all_user_ids.add(participant["user_id"])
            
            # ✅ PARALELIZACIÓN: Hacer todas las llamadas de usuarios en paralelo
            user_data_dict = await self._get_users_data_parallel(list(all_user_ids))
            
            # Enriquecer todos los chats que lo necesitan
            for chat in chats_to_enrich:
                enriched_participants = []
                for participant in chat.participants:
                    user_data = user_data_dict.get(participant["user_id"], {"name": "Usuario", "email": ""})
                    
                    enriched_participant = {
                        "user_id": participant["user_id"],
                        "role": participant["role"],
                        "joined_at": participant["joined_at"],
                        "user_name": user_data.get("name", "Usuario"),
                        "user_email": user_data.get("email", "")
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
    
    async def _get_users_data_parallel(self, user_ids: List[str]) -> Dict[str, Dict]:
        """Obtener datos de múltiples usuarios en paralelo con cache"""
        tasks = []
        for user_id in user_ids:
            if user_id in self._user_cache:
                # Usar cache
                task = asyncio.create_task(self._get_cached_user(user_id))
            else:
                # Hacer llamada HTTP y cachear
                task = asyncio.create_task(self._get_and_cache_user(user_id))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        user_data_dict = {}
        for user_id, result in zip(user_ids, results):
            if not isinstance(result, Exception) and result:
                user_data_dict[user_id] = result
            else:
                user_data_dict[user_id] = {"name": "Usuario", "email": ""}
        
        return user_data_dict
    
    async def _get_cached_user(self, user_id: str) -> Dict:
        """Obtener usuario del cache"""
        return self._user_cache.get(user_id, {"name": "Usuario", "email": ""})
    
    async def _get_and_cache_user(self, user_id: str) -> Dict:
        """Obtener usuario y guardarlo en cache"""
        try:
            user_data = await self.user_repository.get_user_by_id(user_id)
            if user_data:
                self._user_cache[user_id] = user_data
                return user_data
            return {"name": "Usuario", "email": ""}
        except Exception as e:
            print(f"Error obteniendo usuario {user_id}: {e}")
            return {"name": "Usuario", "email": ""}
    
    def _are_user_data_fresh(self, chat: Chat) -> bool:
        """Verificar si los datos de usuarios están frescos (evitar llamadas innecesarias)"""
        for participant in chat.participants:
            if not participant.get("user_name") or participant.get("user_name") == "Usuario":
                return False
        return True
    
    async def get_chat_by_id(self, chat_id: str) -> Chat:
        """Obtener chat por ID"""
        if not chat_id:
            raise ValueError("chat_id es requerido")
        
        chat = await self.chat_repository.get_chat_by_id(chat_id)
        if not chat:
            raise ValueError("Chat no encontrado")
        
        return chat 