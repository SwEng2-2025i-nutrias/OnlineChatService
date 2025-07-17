from typing import List, Optional, Dict
import asyncio
from datetime import datetime
from domain.entities.chat import Chat
from domain.entities.participant import Participant
from domain.ports.input.create_chat import CreateChat
from infrastructure.repositories.mongo_chat_repository import MongoChatRepository
from infrastructure.websocket.websocket_server import websocket_server
from adapters.output.http_user_repository import HttpUserRepository

class CreateChatUseCase(CreateChat):
    def __init__(self, chat_repository: MongoChatRepository):
        self.chat_repository = chat_repository
        self.user_repository = HttpUserRepository()
        self._user_cache = {}  # ✅ Cache simple en memoria para usuarios
    
    async def create_chat(
        self,
        user_ids: List[str],
        description: Optional[str] = None,
        chat_type: str = "private"
    ) -> Chat:
        """Crear un nuevo chat o devolver uno existente"""
        
        # Validar parámetros
        if not user_ids or len(user_ids) < 2:
            raise ValueError("Se requieren al menos 2 usuarios para crear un chat")
        
        # Determinar tipo de chat
        if len(user_ids) == 2:
            chat_type = "private"
            # ✅ NUEVA FUNCIONALIDAD: Verificar si ya existe un chat entre estos usuarios
            existing_chat = await self._find_existing_private_chat(user_ids)
            if existing_chat:
                # ✅ Verificar si los datos están actualizados
                if self._are_user_data_fresh(existing_chat):
                    return existing_chat
                else:
                    # Solo enriquecer si los datos están desactualizados
                    enriched_chat = await self._enrich_chat_with_user_data_parallel(existing_chat)
                    return enriched_chat
        else:
            chat_type = "group"
        
        # ✅ OBTENER DATOS DE USUARIOS AL CREAR EL CHAT (denormalización)
        user_data_dict = await self._get_users_data_parallel(user_ids)
        
        # Crear participantes CON DATOS DE USUARIO
        participants = []
        for i, user_id in enumerate(user_ids):
            user_data = user_data_dict.get(user_id, {"name": "Usuario", "email": ""})
            participant = Participant(
                user_id=user_id,
                role="admin" if i == 0 else "member",  # Primer usuario es admin
                joined_at=datetime.utcnow(),
                user_name=user_data.get("name", "Usuario"),      # ✅ Guardado en MongoDB
                user_email=user_data.get("email", "")           # ✅ Guardado en MongoDB
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
        
        # Guardar en base de datos (YA CON DATOS DE USUARIO)
        created_chat = await self.chat_repository.create_chat(chat)
        
        # Notificar via WebSocket
        await self._notify_chat_created(created_chat)
        
        return created_chat
    
    async def _find_existing_private_chat(self, user_ids: List[str]) -> Optional[Chat]:
        """Buscar chat privado existente entre dos usuarios"""
        try:
            # Obtener chats del primer usuario
            user1_chats = await self.chat_repository.get_chats_by_user_id(user_ids[0])
            
            # Buscar un chat privado que contenga exactamente estos dos usuarios
            for chat in user1_chats:
                if (chat.type == "private" and 
                    len(chat.participants) == 2 and
                    set(p["user_id"] for p in chat.participants) == set(user_ids)):
                    return chat
            
            return None
        except Exception as e:
            print(f"Error buscando chat existente: {e}")
            return None
    
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
    
    async def _enrich_chat_with_user_data_parallel(self, chat: Chat) -> Chat:
        """Enriquecer chat con información de usuarios usando paralelización"""
        try:
            user_ids = [p["user_id"] for p in chat.participants]
            user_data_dict = await self._get_users_data_parallel(user_ids)
            
            # Actualizar participantes
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
            
            chat.participants = enriched_participants
            return chat
        except Exception as e:
            print(f"Error enriqueciendo chat: {e}")
            return chat
    
    async def _enrich_chat_with_user_data(self, chat: Chat) -> Chat:
        """Enriquecer chat con información de usuarios"""
        try:
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
            return chat
        except Exception as e:
            print(f"Error enriqueciendo chat: {e}")
            return chat
    
    async def _notify_chat_created(self, chat: Chat):
        """Notificar creación de chat via WebSocket"""
        chat_data = {
            "id": chat._id,
            "type": chat.type,
            "participants": [
                {
                    "user_id": p.get("user_id"),
                    "role": p.get("role"),
                    "joined_at": p.get("joined_at").isoformat() if hasattr(p.get("joined_at"), 'isoformat') else str(p.get("joined_at")),
                    "user_name": p.get("user_name", "Usuario"),
                    "user_email": p.get("user_email", "")
                }
                for p in chat.participants
            ],
            "title": chat.title,
            "created_at": chat.created_at.isoformat(),
            "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
            "unread_counts": chat.unread_counts
        }
        
        await websocket_server.broadcast_chat_created(chat_data) 