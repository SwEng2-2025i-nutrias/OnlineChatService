from typing import TypedDict, Optional
from datetime import datetime

class Participant(TypedDict):
    user_id: int
    role: str
    joined_at: datetime
    user_name: Optional[str]  # ✅ Nuevo campo para denormalización
    user_email: Optional[str]  # ✅ Nuevo campo para denormalización