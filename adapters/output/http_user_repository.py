import requests
from domain.ports.output.user_repository import UserRepository
from domain.entities.user import User

from typing import Optional

class HttpUserRepository(UserRepository):
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_by_id(self, user_id: str) -> Optional[User]:
        response = requests.get(f"{self.base_url}/users/{user_id}")
        # TODO: Test if the response is correctly formatted
        if response.status_code == 200:
            json_data = response.json()
            if json_data:
                json_data["user_id"] = json_data["id"]
                return User.from_dict(json_data)
        return None