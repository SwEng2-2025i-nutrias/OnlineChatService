import socketio
import os
from fastapi import FastAPI
from typing import Dict, List
import json
from datetime import datetime

class WebSocketServer:
    def __init__(self):
        # Configuración de CORS desde variables de entorno
        cors_origins = os.getenv("CORS_ORIGINS", "*")
        # Si es una lista separada por comas, convertir a lista
        if cors_origins and "," in cors_origins:
            cors_origins = [origin.strip() for origin in cors_origins.split(",")]
        
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins=cors_origins,
            logger=os.getenv("DEBUG", "false").lower() == "true"
        )
        
        # Almacenar conexiones activas
        self.active_connections: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        self.session_users: Dict[str, str] = {}  # session_id -> user_id
        
        # Configurar eventos
        self._setup_events()
    
    def _setup_events(self):
        """Configurar eventos del websocket"""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            """Cliente conectado"""
            print(f"🟢 Cliente conectado: {sid}")
            
            if not auth or 'token' not in auth:
                print(f"❌ Autenticación fallida para {sid}: No se proporcionó token")
                return False
            
            try:
                token = auth['token']
                # Importar aquí para evitar circular imports
                from infrastructure.auth.auth_middleware import auth_middleware
                
                # Validar token JWT
                validation_result = await auth_middleware.validate_websocket_token(token)
                
                if not validation_result.get("valid", False):
                    error_message = validation_result.get("error", "Token inválido")
                    print(f"❌ Autenticación fallida para {sid}: {error_message}")
                    return False
                
                user_id = validation_result.get("user_id")
                if not user_id:
                    print(f"❌ Autenticación fallida para {sid}: Token sin user_id")
                    return False
                
                # Registrar conexión
                if user_id not in self.active_connections:
                    self.active_connections[user_id] = []
                self.active_connections[user_id].append(sid)
                self.session_users[sid] = user_id
                
                # Guardar información de autenticación en la sesión
                await self.sio.save_session(sid, {
                    'user_id': user_id,
                    'auth_data': validation_result,
                    'authenticated': True,
                    'token': token
                })
                
                await self.sio.emit('authenticated', {
                    'user_id': user_id,
                    'user_data': validation_result
                }, room=sid)
                print(f"✅ Usuario {user_id} autenticado en sesión {sid}")
                
                return True
            except Exception as e:
                print(f"❌ Error en autenticación para {sid}: {str(e)}")
                return False
        
        @self.sio.event
        async def disconnect(sid):
            """Cliente desconectado"""
            print(f"🔴 Cliente desconectado: {sid}")
            
            # Limpiar conexiones
            if sid in self.session_users:
                user_id = self.session_users[sid]
                if user_id in self.active_connections:
                    self.active_connections[user_id].remove(sid)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                del self.session_users[sid]
        
        @self.sio.event
        async def authenticate(sid, data):
            """Autenticar usuario con JWT"""
            try:
                token = data.get('token')
                if not token:
                    await self.sio.emit('error', {
                        'message': 'Token JWT requerido',
                        'details': 'Debe proporcionar un token JWT válido para autenticarse'
                    }, room=sid)
                    return
                
                # Importar aquí para evitar circular imports
                from infrastructure.auth.auth_middleware import auth_middleware
                
                # Validar token JWT
                validation_result = await auth_middleware.validate_websocket_token(token)
                
                if not validation_result.get("valid", False):
                    error_message = validation_result.get("error", "Token inválido")
                    await self.sio.emit('error', {
                        'message': 'Autenticación fallida',
                        'details': error_message
                    }, room=sid)
                    return
                
                user_id = validation_result.get("user_id")
                if not user_id:
                    await self.sio.emit('error', {
                        'message': 'Token válido pero sin user_id',
                        'details': 'El token no contiene información de usuario válida'
                    }, room=sid)
                    return
                
                # Registrar conexión
                if user_id not in self.active_connections:
                    self.active_connections[user_id] = []
                self.active_connections[user_id].append(sid)
                self.session_users[sid] = user_id
                
                # Guardar información de autenticación en la sesión
                await self.sio.save_session(sid, {
                    'user_id': user_id,
                    'auth_data': validation_result,
                    'authenticated': True,
                    'token': token  # Guardar el token para futuros usos
                })
                
                await self.sio.emit('authenticated', {
                    'user_id': user_id,
                    'user_data': validation_result
                }, room=sid)
                print(f"✅ Usuario {user_id} autenticado en sesión {sid}")
                
            except Exception as e:
                await self.sio.emit('error', {
                    'message': 'Error de autenticación',
                    'details': str(e)
                }, room=sid)
        
        @self.sio.event
        async def join_chat(sid, data):
            """Unirse a un chat"""
            try:
                chat_id = data.get('chat_id')
                if not chat_id:
                    await self.sio.emit('error', {'message': 'chat_id requerido'}, room=sid)
                    return
                
                # Verificar autenticación
                try:
                    session = await self.sio.get_session(sid)
                    if not session.get('authenticated', False):
                        await self.sio.emit('error', {
                            'message': 'No autenticado',
                            'details': 'Debe autenticarse antes de unirse a un chat'
                        }, room=sid)
                        return
                    
                    user_id = session.get('user_id')
                    print(f"👤 Usuario {user_id} intentando unirse al chat {chat_id}")
                    
                except Exception as e:
                    await self.sio.emit('error', {
                        'message': 'Error de sesión',
                        'details': str(e)
                    }, room=sid)
                    return
                
                await self.sio.enter_room(sid, chat_id)
                await self.sio.emit('joined_chat', {'chat_id': chat_id}, room=sid)
                print(f"✅ Sesión {sid} (usuario {user_id}) se unió al chat {chat_id}")
                
            except Exception as e:
                print(f"❌ Error en join_chat: {e}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)
        
        @self.sio.event
        async def leave_chat(sid, data):
            """Salir de un chat"""
            try:
                chat_id = data.get('chat_id')
                if not chat_id:
                    await self.sio.emit('error', {'message': 'chat_id requerido'}, room=sid)
                    return
                
                # Verificar autenticación
                try:
                    session = await self.sio.get_session(sid)
                    user_id = session.get('user_id', 'unknown')
                except:
                    user_id = 'unknown'
                
                await self.sio.leave_room(sid, chat_id)
                await self.sio.emit('left_chat', {'chat_id': chat_id}, room=sid)
                print(f"📤 Sesión {sid} (usuario {user_id}) salió del chat {chat_id}")
                
            except Exception as e:
                print(f"❌ Error en leave_chat: {e}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)
        
        @self.sio.event
        async def typing_start(sid, data):
            """Usuario empezó a escribir"""
            try:
                chat_id = data.get('chat_id')
                user_id = self.session_users.get(sid)
                
                if not chat_id or not user_id:
                    return
                
                # Notificar a otros usuarios en el chat
                await self.sio.emit('user_typing', {
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'typing': True
                }, room=chat_id, skip_sid=sid)
                
            except Exception as e:
                print(f"Error en typing_start: {e}")
        
        @self.sio.event
        async def typing_stop(sid, data):
            """Usuario dejó de escribir"""
            try:
                chat_id = data.get('chat_id')
                user_id = self.session_users.get(sid)
                
                if not chat_id or not user_id:
                    return
                
                # Notificar a otros usuarios en el chat
                await self.sio.emit('user_typing', {
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'typing': False
                }, room=chat_id, skip_sid=sid)
                
            except Exception as e:
                print(f"Error en typing_stop: {e}")
    
    async def broadcast_new_message(self, message_data: Dict):
        """Broadcast de nuevo mensaje a todos los usuarios del chat"""
        chat_id = message_data.get('chat_id')
        if chat_id:
            print(f"📢 Broadcasting mensaje a chat {chat_id}: {message_data.get('content', '')[:50]}...")
            await self.sio.emit('new_message', message_data, room=chat_id)
            print(f"✅ Mensaje enviado a sala {chat_id}")
        else:
            print(f"❌ No se puede enviar mensaje: chat_id faltante en {message_data}")
    
    async def broadcast_message_status(self, message_id: str, status: str, chat_id: str):
        """Broadcast de cambio de estado de mensaje"""
        print(f"📢 Broadcasting cambio de estado del mensaje {message_id} a {status} en chat {chat_id}")
        await self.sio.emit('message_status_updated', {
            'message_id': message_id,
            'status': status
        }, room=chat_id)
    
    async def broadcast_chat_created(self, chat_data: Dict):
        """Broadcast de nuevo chat creado"""
        participants = chat_data.get('participants', [])
        for participant in participants:
            user_id = participant.get('user_id')
            if user_id and user_id in self.active_connections:
                for session_id in self.active_connections[user_id]:
                    await self.sio.emit('chat_created', chat_data, room=session_id)
    
    async def notify_user_online(self, user_id: str):
        """Notificar que usuario está online"""
        await self.sio.emit('user_online', {'user_id': user_id})
    
    async def notify_user_offline(self, user_id: str):
        """Notificar que usuario está offline"""
        await self.sio.emit('user_offline', {'user_id': user_id})
    
    def get_active_users(self) -> List[str]:
        """Obtener lista de usuarios activos"""
        return list(self.active_connections.keys())
    
    def is_user_online(self, user_id: str) -> bool:
        """Verificar si usuario está online"""
        return user_id in self.active_connections

# Instancia global del servidor WebSocket
websocket_server = WebSocketServer() 