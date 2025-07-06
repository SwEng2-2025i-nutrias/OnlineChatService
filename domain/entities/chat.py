from datetime import datetime
from typing import Optional, List, Dict
from participant import Participant 

class Chat:
    def __init__(
        self,
        _id: str,
        type: str,
        participants: List[Participant],
        metadata: Optional[Dict[str, int]],
        title: Optional[str],
        created_at: datetime,
        last_message_at: Optional[datetime],
        unread_counts: Dict[str, int]
    ):
        self._id = _id
        self.type = type  # 'private' o 'group'
        self.participants = participants
        self.metadata = metadata
        self.title = title
        self.created_at = created_at
        self.last_message_at = last_message_at
        self.unread_counts = unread_counts
