#!/usr/bin/env python3
"""
Script para generar tokens JWT de prueba para el servicio de chat
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    
    print("\n🌐 También puedes usar los tokens en API REST:")
    print("   curl -H 'Authorization: Bearer <TOKEN>' http://localhost:8000/api/...")

if __name__ == "__main__":
    main() 