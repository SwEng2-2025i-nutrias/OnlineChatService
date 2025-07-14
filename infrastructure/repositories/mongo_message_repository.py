from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from domain.entities.message import Message
from domain.entities.attachment import Attachment
from domain.ports.output.message_repository import MessageRepository
from infrastructure.database.mongodb_config import get_database

class MongoMessageRepository(MessageRepository):
    def __init__(self):
        self.collection_name = "messages"
    
    async def get_by_id(self, message_id: str) -> Optional[Message]:
        """Obtener mensaje por ID"""
        db = await get_database()
        collection = db[self.collection_name]
        
        try:
            message_data = await collection.find_one({"_id": ObjectId(message_id)})
            if message_data:
                return self._to_entity(message_data)
            return None
        except Exception:
            return None
    
    async def get_by_chat_id(self, chat_id: str) -> List[Message]:
        """Obtener mensajes de un chat"""
        db = await get_database()
        collection = db[self.collection_name]
        
        query = {"chat_id": chat_id}
        cursor = collection.find(query).sort("sent_at", 1)  # Ordenar por tiempo
        
        messages = []
        async for message_data in cursor:
            messages.append(self._to_entity(message_data))
        
        return messages
    
    async def save(self, message: Message) -> Message:
        """Guardar nuevo mensaje"""
        db = await get_database()
        collection = db[self.collection_name]
        
        message_data = self._to_document(message)
        result = await collection.insert_one(message_data)
        
        # Actualizar ID del mensaje
        message._id = str(result.inserted_id)
        return message
    
    async def update_status(self, message_id: str, status: str) -> None:
        """Actualizar estado del mensaje"""
        db = await get_database()
        collection = db[self.collection_name]
        
        await collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"status": status}}
        )
    
    async def get_recent_messages(self, chat_id: str, limit: int = 50) -> List[Message]:
        """Obtener mensajes recientes de un chat"""
        db = await get_database()
        collection = db[self.collection_name]
        
        query = {"chat_id": chat_id}
        cursor = collection.find(query).sort("sent_at", -1).limit(limit)
        
        messages = []
        async for message_data in cursor:
            messages.append(self._to_entity(message_data))
        
        # Devolver en orden cronológico
        return messages[::-1]
    
    def _to_entity(self, message_data: Dict) -> Message:
        """Convertir documento de MongoDB a entidad Message"""
        attachments = []
        if message_data.get("attachments"):
            attachments = [
                Attachment(
                    url=att["url"],
                    filename=att["filename"],
                    mime_type=att["mime_type"],
                    size_bytes=att["size_bytes"]
                )
                for att in message_data["attachments"]
            ]
        
        return Message(
            _id=str(message_data["_id"]),
            chat_id=message_data["chat_id"],
            sender_id=message_data["sender_id"],
            sent_at=message_data["sent_at"],
            type=message_data["type"],
            content=message_data.get("content"),
            attachment=attachments,
            status=message_data["status"]
        )
    
    def _to_document(self, message: Message) -> Dict:
        """Convertir entidad Message a documento de MongoDB"""
        doc = {
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "sent_at": message.sent_at,
            "type": message.type,
            "content": message.content,
            "status": message.status,
            "attachments": [
                {
                    "url": att["url"],
                    "filename": att["filename"],
                    "mime_type": att["mime_type"],
                    "size_bytes": att["size_bytes"]
                }
                for att in message.attachment
            ]
        }
        
        # Solo incluir _id si ya existe
        if message._id and message._id != "":
            doc["_id"] = ObjectId(message._id)
            
        return doc 