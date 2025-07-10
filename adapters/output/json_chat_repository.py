import json
from pathlib import Path
from domain.ports.output.chat_repository import ChatRepository
from domain.entities.chat import Chat, Any

from typing import Optional, List

DB_FILE = Path(__file__).parent / 'db.json'

class JsonChatRepository(ChatRepository):
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

    def get_chat_by_id(self, chat_id: str) -> Optional[Chat]:
        db = self._load_db()
        for chat_data in db:
            if chat_data['_id'] == chat_id:
                return Chat.from_dict(chat_data)
        return None
    
    def get_chats_by_user_id(self, user_id: str) -> Optional[list[Chat]]:
        db = self._load_db()
        chats:List[Chat] = []
        for chat_data in db:
            if any(participant['user_id'] == user_id for participant in chat_data['participants']):
                chats.append(Chat.from_dict(chat_data))
        return chats if chats else None
    
    def create_chat(self, chat: Chat) -> Chat:
        db = self._load_db()
        chat.set_id(self._generate_id(db))
        chat_data = chat.to_dict()
        db.append(chat_data)
        self._save_db(db)
        return chat
    
    def update_chat(self, chat: Chat) -> None:
        db = self._load_db()
        for i, chat_data in enumerate(db):
            if chat_data['_id'] == chat.get_id():
                db[i] = chat.to_dict()
                self._save_db(db)
                return
        raise ValueError(f"Chat with id {chat.get_id()} not found.")
    
    def delete_chat(self, chat_id: str) -> None:
        db = self._load_db()
        for i, chat_data in enumerate(db):
            if chat_data['_id'] == chat_id:
                del db[i]
                self._save_db(db)
                return
        raise ValueError(f"Chat with id {chat_id} not found.")
    