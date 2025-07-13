"""
Servicio mock de autenticación para pruebas y desarrollo
Este archivo simula un servicio de autenticación real
"""

import jwt
import os
from typing import Dict, Any

class MockAuthService:
    """Servicio mock de autenticación para pruebas"""
    
    def __init__(self):
        # Clave secreta para firmar tokens (solo para pruebas)
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'test-secret-key-only-for-development')
        
        # Usuarios mock para pruebas
        self.mock_users = {
            'user1': {
                'user_id': 'user1',
                'name': 'Usuario De Prueba 1',
                'email': 'user1@test.com',
                'role': 'user'
            },
            'user2': {
                'user_id': 'user2',
                'name': 'Usuario De Prueba 2',
                'email': 'user2@test.com',
                'role': 'user'
            },
            'admin': {
                'user_id': 'admin',
                'name': 'Administrador',
                'email': 'admin@test.com',
                'role': 'admin'
            }
        }
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Valida un token JWT mock"""
        try:
            # Intentar decodificar el token
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            except jwt.InvalidTokenError:
                # Si falla la decodificación, intentar con tokens de prueba simples
                if token == 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcjEiLCJuYW1lIjoiVXN1YXJpbyBEZSBQcnVlYmEifQ.test':
                    payload = {'user_id': 'user1', 'name': 'Usuario De Prueba'}
                elif token == 'user2_token':
                    payload = {'user_id': 'user2', 'name': 'Usuario De Prueba 2'}
                elif token == 'admin_token':
                    payload = {'user_id': 'admin', 'name': 'Administrador'}
                else:
                    return {"valid": False, "error": "Token inválido"}
            
            user_id = payload.get('user_id')
            if not user_id:
                return {"valid": False, "error": "Token no contiene user_id"}
            
            # Obtener información del usuario mock
            user_info = self.mock_users.get(user_id, {
                'user_id': user_id,
                'name': payload.get('name', f'Usuario {user_id}'),
                'email': f'{user_id}@test.com',
                'role': 'user'
            })
            
            return {
                "valid": True,
                "user_id": user_id,
                **user_info,
                "exp": payload.get('exp'),
                "iat": payload.get('iat'),
                "token_type": "Bearer"
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Error procesando token: {str(e)}"}
    
    def generate_test_token(self, user_id: str) -> str:
        """Genera un token de prueba para testing"""
        user_info = self.mock_users.get(user_id, {'user_id': user_id, 'name': f'Usuario {user_id}'})
        
        payload = {
            'user_id': user_id,
            'name': user_info.get('name'),
            'email': user_info.get('email'),
            'role': user_info.get('role')
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

# Instancia global del servicio mock
mock_auth_service = MockAuthService()

def get_test_tokens():
    """Obtener tokens de prueba para diferentes usuarios"""
    return {
        'user1': mock_auth_service.generate_test_token('user1'),
        'user2': mock_auth_service.generate_test_token('user2'),
        'admin': mock_auth_service.generate_test_token('admin')
    }

if __name__ == "__main__":
    # Pruebas del servicio mock
    print("🧪 Probando servicio mock de autenticación...")
    
    # Generar tokens de prueba
    tokens = get_test_tokens()
    print("\n📝 Tokens de prueba generados:")
    for user, token in tokens.items():
        print(f"  {user}: {token}")
    
    # Probar validación
    print("\n✅ Probando validación de tokens:")
    for user, token in tokens.items():
        result = mock_auth_service.validate_token(token)
        print(f"  {user}: {result}")
    
    # Probar token inválido
    print("\n❌ Probando token inválido:")
    invalid_result = mock_auth_service.validate_token("invalid_token")
    print(f"  Token inválido: {invalid_result}") 