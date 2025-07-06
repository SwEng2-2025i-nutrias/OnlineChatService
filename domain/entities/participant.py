from typing import TypedDict
from datetime import datetime

class Participant(TypedDict):
    user_id: int
    role: str
    joined_at: datetime