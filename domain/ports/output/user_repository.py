from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.user import User

# Interface for users
class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID."""
        pass