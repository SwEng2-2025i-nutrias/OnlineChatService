from typing import TypedDict
from datetime import datetime

class Participant(TypedDict):
    user_id: str
    role: str
    joined_at: datetime