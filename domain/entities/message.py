from datetime import datetime
from typing import Optional, List
from attachment import Attachment  

class Message:
    def __init__(
        self,
        _id: str,
        chat_id: str,
        sender_id: str,
        sent_at: datetime,
        type: str,
        content: Optional[str],
        attachment: Optional[List[Attachment]],
        status: str
    ):
        self._id = _id
        self.chat_id = chat_id
        self.sender_id = sender_id
        self.sent_at = sent_at
        self.type = type
        self.content = content
        self.attachment = attachment or []
        self.status = status
