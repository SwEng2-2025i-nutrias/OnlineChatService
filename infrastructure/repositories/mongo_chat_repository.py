from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from domain.entities.chat import Chat
from domain.entities.participant import Participant
from domain.ports.output.chat_repository import ChatRepository
from infrastructure.database.mongodb_config import get_database

class MongoChatRepository(ChatRepository):
    def __init__(self):
        self.collection_name = "chats"
    
    async def get_chat_by_id(self, chat_id: str) -> Optional[Chat]:
        """Obtener chat por ID"""
        db = await get_database()
        collection = db[self.collection_name]
        
        try:
            chat_data = await collection.find_one({"_id": ObjectId(chat_id)})
            if chat_data:
                return self._to_entity(chat_data)
            return None
        except Exception:
            return None
    
    async def get_chats_by_user_id(self, user_id: str) -> List[Chat]:
        """Obtener chats de un usuario"""
        db = await get_database()
        collection = db[self.collection_name]
        
        query = {"participants.user_id": user_id}
        cursor = collection.find(query)
        
        chats = []
        async for chat_data in cursor:
            chats.append(self._to_entity(chat_data))
        
        return chats
    
    async def create_chat(self, chat: Chat) -> Chat:
        """Crear nuevo chat"""
        db = await get_database()
        collection = db[self.collection_name]
        
        chat_data = self._to_document(chat)
        result = await collection.insert_one(chat_data)
        
        # Actualizar ID del chat
        chat._id = str(result.inserted_id)
        return chat
    
    async def update_chat(self, chat: Chat) -> None:
        """Actualizar chat existente"""
        db = await get_database()
        collection = db[self.collection_name]
        
        chat_data = self._to_document(chat)
        await collection.replace_one(
            {"_id": ObjectId(chat._id)},
            chat_data
        )
    
    async def delete_chat(self, chat_id: str) -> None:
        """Eliminar chat por ID"""
        db = await get_database()
        collection = db[self.collection_name]
        
        await collection.delete_one({"_id": ObjectId(chat_id)})
    
    def _to_entity(self, chat_data: Dict) -> Chat:
        """Convertir documento de MongoDB a entidad Chat"""
        participants = [
            Participant(
                user_id=p["user_id"],
                role=p["role"],
                joined_at=p["joined_at"]
            )
            for p in chat_data.get("participants", [])
        ]
        
        return Chat(
            _id=str(chat_data["_id"]),
            type=chat_data["type"],
            participants=participants,
            metadata=chat_data.get("metadata"),
            title=chat_data.get("title"),
            created_at=chat_data["created_at"],
            last_message_at=chat_data.get("last_message_at"),
            unread_counts=chat_data.get("unread_counts", {})
        )
    
    def _to_document(self, chat: Chat) -> Dict:
        """Convertir entidad Chat a documento de MongoDB"""
        doc = {
            "type": chat.type,
            "participants": [
                {
                    "user_id": p["user_id"],
                    "role": p["role"],
                    "joined_at": p["joined_at"]
                }
                for p in chat.participants
            ],
            "metadata": chat.metadata,
            "title": chat.title,
            "created_at": chat.created_at,
            "last_message_at": chat.last_message_at,
            "unread_counts": chat.unread_counts
        }
        
        # Solo incluir _id si ya existe
        if chat._id and chat._id != "":
            doc["_id"] = ObjectId(chat._id)
            
        return doc 