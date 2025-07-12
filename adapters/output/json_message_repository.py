import json
from pathlib import Path
from domain.ports.output.message_repository import MessageRepository
from domain.entities.message import Message

from typing import Optional, Any

DB_FILE = Path(__file__).parent / 'db_message.json'

class JsonMessageRepository(MessageRepository):
    def _load_db(self)->list[dict[str, Any]]:
        try:
            with open(DB_FILE, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        
    def _save_db(self, db:list[dict[str, Any]])->None:
        with open(DB_FILE, 'w') as file:
            json.dump(db, file, indent=2)

    # Generar id
    def _generate_id(self, db:list[dict[str, Any]])->str:
        return str(len(db) + 1)

    def get_by_id(self, message_id: str) -> Optional[Message]:
        db = self._load_db()
        for message_data in db:
            if message_data['_id'] == message_id:
                return Message.from_dict(message_data)
        return None
    
    def get_by_chat_id(self, chat_id: str) -> list[Message]:
        db = self._load_db()
        messages:list[Message] = []
        for message_data in db:
            if message_data['chat_id'] == chat_id:
                messages.append(Message.from_dict(message_data))
        return messages
    
    def save(self, message: Message) -> Message:
        db = self._load_db()
        message_data = message.to_dict()
        if not message_data.get('_id'):
            message_data['_id'] = self._generate_id(db)
        db.append(message_data)
        self._save_db(db)
        return Message.from_dict(message_data)
    
    def update_status(self, message_id: str, status: str) -> None:
        db = self._load_db()
        for message_data in db:
            if message_data['_id'] == message_id:
                message_data['status'] = status
                self._save_db(db)
                return
        raise ValueError(f"Message with id {message_id} not found.")
    
    