from abc import ABC, abstractmethod
from typing import Optional
from ...entities.participant import Participant

# Interface for users
class ParticipantRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[Participant]:
        """Retrieve a user by their ID."""
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[Participant]:
        """Retrieve a user by their username."""
        pass