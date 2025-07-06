from typing import TypedDict

class Attachment(TypedDict):
    url: str
    filename: str
    mime_type: str
    size_bytes: int