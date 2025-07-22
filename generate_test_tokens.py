#!/usr/bin/env python3
"""
Script para generar tokens JWT de prueba para el servicio de chat
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno desde .env
load_dotenv()

# Verificar que las variables de entorno necesarias estén configuradas
if not os.getenv('JWT_SECRET_KEY'):
    print("⚠️ Advertencia: JWT_SECRET_KEY no está configurado. Usando valor por defecto.")
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key-only-for-development'

if not os.getenv('USE_MOCK_AUTH'):
    print("⚠️ Advertencia: USE_MOCK_AUTH no está configurado. Usando valor por defecto.")
    os.environ['USE_MOCK_AUTH'] = 'true'

from infrastructure.auth.mock_auth_service import mock_auth_service, get_test_tokens

def main():
    print("🚀 Generador de Tokens JWT para OnlineChatService")
    print("=" * 60)
    
    # Generar tokens para usuarios predefinidos
    print("\n📝 Tokens de usuarios predefinidos:")
    tokens = get_test_tokens()
    
    for user, token in tokens.items():
        user_info = mock_auth_service.mock_users.get(user, {})
        print(f"\n👤 {user_info.get('name', user)} ({user}):")
        print(f"   Role: {user_info.get('role', 'user')}")
        print(f"   Email: {user_info.get('email', 'N/A')}")
        print(f"   Token: {token}")
    
    # Generar token para usuario personalizado
    print("\n" + "=" * 60)
    print("🔧 Generar token personalizado:")
    
    while True:
        custom_user = input("\nIngresa un user_id personalizado (o 'exit' para salir): ").strip()
        
        if custom_user.lower() == 'exit':
            break
        
        if not custom_user:
            print("❌ El user_id no puede estar vacío")
            continue
        
        # Generar token para el usuario personalizado
        try:
            custom_token = mock_auth_service.generate_test_token(custom_user)
            print(f"\n✅ Token generado para '{custom_user}':")
            print(f"   Token: {custom_token}")
            
            # Verificar el token
            validation = mock_auth_service.validate_token(custom_token)
            if validation.get('valid'):
                print(f"   ✅ Token válido - User ID: {validation.get('user_id')}")
            else:
                print(f"   ❌ Error: {validation.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Error generando token: {e}")
    
    print("\n👋 ¡Gracias por usar el generador de tokens!")
    print("\n📚 Para usar estos tokens:")
    print("   1. Copia el token deseado")
    print("   2. Abre client_example.html en tu navegador")
    print("   3. Pega el token en el campo 'Token JWT'")
    print("   4. Haz clic en 'Autenticar'")
    
    api_base_url = f"http://{os.getenv('HOST', 'localhost')}:{os.getenv('PORT', '8000')}"
    print("\n🌐 También puedes usar los tokens en API REST:")
    print(f"   curl -H 'Authorization: Bearer <TOKEN>' {api_base_url}/api/...")

if __name__ == "__main__":
    main() 