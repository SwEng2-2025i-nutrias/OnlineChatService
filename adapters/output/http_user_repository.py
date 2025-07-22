import httpx
from typing import Optional, Dict
import os

class HttpUserRepository:
    def __init__(self):
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:5001")
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Obtener información del usuario desde AuthenticationService"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.auth_service_url}/auth/users/{user_id}")
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"Error fetching user {user_id}: {e}")
            return None
