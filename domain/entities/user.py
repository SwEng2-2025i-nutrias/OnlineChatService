from typing import Dict

class User:
    def __init__(self, user_id: str, email: str, name: str, role: str):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.role = role

    @classmethod
    def from_dict(cls, data: dict[str, str]):
        return cls(
            user_id=data["user_id"],
            email=data["email"],
            name=data["name"],
            role=data["role"]
        )
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "role": self.role
        }
