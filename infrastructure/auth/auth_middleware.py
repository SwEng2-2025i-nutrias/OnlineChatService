import os
import requests
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import aiohttp
from functools import wraps

class AuthMiddleware:
    """Middleware para validación de tokens JWT en FastAPI"""
    
    def __init__(self, auth_service_url: Optional[str] = None):
        self.auth_service_url = auth_service_url or os.getenv(
            'AUTH_SERVICE_URL', 
            'http://localhost:5001/auth/validate-token'
        )
        self.use_mock_auth = os.getenv('USE_MOCK_AUTH', 'false').lower() == 'true'
        self.security = HTTPBearer()
        
        if self.use_mock_auth:
            print("🧪 Usando servicio mock de autenticación para desarrollo")
    
    async def _validate_token_async(self, token: str) -> Dict[str, Any]:
        """Valida el token contra el servicio de autenticación de forma asíncrona"""
        # Usar servicio mock si está habilitado
        if self.use_mock_auth:
            from .mock_auth_service import mock_auth_service
            return mock_auth_service.validate_token(token)
        
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.auth_service_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {**data, "valid": True}
                    else:
                        return {
                            "valid": False, 
                            "error": f"Auth service returned {response.status}"
                        }
                        
        except Exception as e:
            return {
                "valid": False, 
                "error": f"Auth service unavailable: {str(e)}"
            }
    
    def _validate_token_sync(self, token: str) -> Dict[str, Any]:
        """Valida el token de forma síncrona (para WebSocket)"""
        # Usar servicio mock si está habilitado
        if self.use_mock_auth:
            from .mock_auth_service import mock_auth_service
            return mock_auth_service.validate_token(token)
        
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                self.auth_service_url,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {**data, "valid": True}
            else:
                return {
                    "valid": False, 
                    "error": f"Auth service returned {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "valid": False, 
                "error": f"Auth service unavailable: {str(e)}"
            }
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> Dict[str, Any]:
        """Dependency para FastAPI que valida el token y retorna datos del usuario"""
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autorización requerido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        validation_result = await self._validate_token_async(credentials.credentials)
        
        if not validation_result.get("valid", False):
            error_message = validation_result.get("error", "Token inválido")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token no válido: {error_message}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return validation_result
    
    async def validate_websocket_token(self, token: str) -> Dict[str, Any]:
        """Valida token para conexiones WebSocket"""
        return await self._validate_token_async(token)
    
    def validate_websocket_token_sync(self, token: str) -> Dict[str, Any]:
        """Valida token para conexiones WebSocket de forma síncrona"""
        return self._validate_token_sync(token)
    
    def require_auth_websocket(self, f):
        """Decorador para eventos WebSocket que requiere autenticación"""
        @wraps(f)
        async def decorated_function(sid, data, *args, **kwargs):
            # Obtener token del data o desde la sesión
            token = None
            
            # Primero intentar obtener de los datos del evento
            if isinstance(data, dict):
                token = data.get('token') or data.get('auth_token')
            
            # Si no hay token en los datos, intentar obtenerlo de la sesión
            if not token:
                # Aquí podrías almacenar el token durante la autenticación inicial
                # Por ahora retornamos error
                return {
                    "error": "Token de autorización requerido",
                    "message": "Debe proporcionar un token en el evento o autenticarse primero"
                }
            
            # Validar token
            validation_result = self.validate_websocket_token_sync(token)
            
            if not validation_result.get("valid", False):
                error_message = validation_result.get("error", "Token inválido")
                return {
                    "error": "Token no válido",
                    "message": error_message
                }
            
            # Agregar información del usuario a los datos
            if isinstance(data, dict):
                data['_auth_data'] = validation_result
                data['_user_id'] = validation_result.get("user_id")
            
            return await f(sid, data, *args, **kwargs)
        
        return decorated_function

# Instancia global del middleware
auth_middleware = AuthMiddleware()

# Dependency para FastAPI
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> Dict[str, Any]:
    """Dependency de conveniencia para obtener usuario actual"""
    return await auth_middleware.get_current_user(credentials)

# Decorador para WebSocket
def require_auth_websocket(f):
    """Decorador de conveniencia para eventos WebSocket"""
    return auth_middleware.require_auth_websocket(f) 