from typing import Dict, List
from datetime import datetime
from domain.entities.attachment import Attachment
from application.use_cases.create_chat_use_case import CreateChatUseCase
from application.use_cases.send_message_use_case import SendMessageUseCase
from application.use_cases.get_chats_use_case import GetChatsUseCase
from infrastructure.repositories.mongo_chat_repository import MongoChatRepository
from infrastructure.repositories.mongo_message_repository import MongoMessageRepository
from infrastructure.websocket.websocket_server import websocket_server
from infrastructure.auth.auth_middleware import auth_middleware

class WebSocketHandlers:
    def __init__(self):
        # Inicializar repositorios
        self.chat_repository = MongoChatRepository()
        self.message_repository = MongoMessageRepository()
        
        # Inicializar casos de uso
        self.create_chat_use_case = CreateChatUseCase(self.chat_repository)
        self.send_message_use_case = SendMessageUseCase(
            self.message_repository, 
            self.chat_repository
        )
        self.get_chats_use_case = GetChatsUseCase(self.chat_repository)
        
        # Registrar manejadores de eventos
        self._register_handlers()
    
    async def _check_authentication(self, sid):
        """Verificar si el usuario está autenticado"""
        try:
            session = await websocket_server.sio.get_session(sid)
            return session.get('authenticated', False), session.get('user_id'), session.get('auth_data', {})
        except:
            return False, None, {}
    
    def _register_handlers(self):
        """Registrar manejadores de eventos WebSocket"""
        
        @websocket_server.sio.event
        async def create_chat(sid, data):
            """Crear nuevo chat"""
            try:
                # Verificar autenticación
                is_authenticated, user_id, auth_data = await self._check_authentication(sid)
                if not is_authenticated:
                    await websocket_server.sio.emit('error', {
                        'message': 'No autenticado',
                        'details': 'Debe autenticarse primero con un token JWT válido'
                    }, room=sid)
                    return
                
                user_ids = data.get('user_ids', [])
                description = data.get('description')
                
                # Asegurar que el usuario autenticado esté en la lista
                if user_id and user_id not in user_ids:
                    user_ids.append(user_id)
                
                if not user_ids:
                    await websocket_server.sio.emit('error', {
                        'message': 'user_ids es requerido'
                    }, room=sid)
                    return
                
                # Crear chat
                chat = await self.create_chat_use_case.create_chat(
                    user_ids=user_ids,
                    description=description
                )
                
                # Responder al cliente
                await websocket_server.sio.emit('chat_created', {
                    'id': chat._id,
                    'type': chat.type,
                    'participants': [
                        {
                            'user_id': p['user_id'],
                            'role': p['role'],
                            'joined_at': p['joined_at'].isoformat()
                        }
                        for p in chat.participants
                    ],
                    'title': chat.title,
                    'created_at': chat.created_at.isoformat(),
                    'unread_counts': chat.unread_counts
                }, room=sid)
                
            except Exception as e:
                await websocket_server.sio.emit('error', {
                    'message': str(e)
                }, room=sid)
        
        @websocket_server.sio.event
        async def send_message(sid, data):
            """Enviar mensaje"""
            try:
                # Verificar autenticación
                is_authenticated, authenticated_user_id, auth_data = await self._check_authentication(sid)
                if not is_authenticated:
                    await websocket_server.sio.emit('error', {
                        'message': 'No autenticado',
                        'details': 'Debe autenticarse primero con un token JWT válido'
                    }, room=sid)
                    return
                
                chat_id = data.get('chat_id')
                user_id = data.get('user_id', authenticated_user_id)  # Usar user_id autenticado por defecto
                content = data.get('content')
                attachments_data = data.get('attachments', [])
                message_type = data.get('type', 'text')
                
                # Verificar que el usuario autenticado sea quien envía el mensaje
                if user_id != authenticated_user_id:
                    await websocket_server.sio.emit('error', {
                        'message': 'No autorizado',
                        'details': 'No puedes enviar mensajes como otro usuario'
                    }, room=sid)
                    return
                
                if not chat_id:
                    await websocket_server.sio.emit('error', {
                        'message': 'chat_id es requerido'
                    }, room=sid)
                    return
                
                # Procesar archivos adjuntos
                attachments = []
                for att_data in attachments_data:
                    attachment = Attachment(
                        url=att_data.get('url', ''),
                        filename=att_data.get('filename', ''),
                        mime_type=att_data.get('mime_type', ''),
                        size_bytes=att_data.get('size_bytes', 0)
                    )
                    attachments.append(attachment)
                
                # Enviar mensaje
                message = await self.send_message_use_case.send_message(
                    chat_id=chat_id,
                    user_id=user_id,
                    content=content,
                    attachments=attachments if attachments else None,
                    message_type=message_type
                )
                
                # El broadcast ya se hace en el caso de uso
                
            except Exception as e:
                await websocket_server.sio.emit('error', {
                    'message': str(e)
                }, room=sid)
        
        @websocket_server.sio.event
        async def get_user_chats(sid, data):
            """Obtener chats del usuario"""
            try:
                # Verificar autenticación
                is_authenticated, authenticated_user_id, auth_data = await self._check_authentication(sid)
                if not is_authenticated:
                    await websocket_server.sio.emit('error', {
                        'message': 'No autenticado',
                        'details': 'Debe autenticarse primero con un token JWT válido'
                    }, room=sid)
                    return
                
                user_id = data.get('user_id', authenticated_user_id)
                
                # Verificar que el usuario solo pueda ver sus propios chats
                if user_id != authenticated_user_id:
                    await websocket_server.sio.emit('error', {
                        'message': 'No autorizado',
                        'details': 'Solo puedes ver tus propios chats'
                    }, room=sid)
                    return
                
                chats = await self.get_chats_use_case.get_user_chats(user_id)
                
                chats_data = []
                for chat in chats:
                    chat_data = {
                        'id': chat._id,
                        'type': chat.type,
                        'participants': [
                            {
                                'user_id': p['user_id'],
                                'role': p['role'],
                                'joined_at': p['joined_at'].isoformat()
                            }
                            for p in chat.participants
                        ],
                        'title': chat.title,
                        'created_at': chat.created_at.isoformat(),
                        'last_message_at': chat.last_message_at.isoformat() if chat.last_message_at else None,
                        'unread_counts': chat.unread_counts
                    }
                    chats_data.append(chat_data)
                
                await websocket_server.sio.emit('user_chats', {
                    'chats': chats_data
                }, room=sid)
                
            except Exception as e:
                await websocket_server.sio.emit('error', {
                    'message': str(e)
                }, room=sid)
        
        @websocket_server.sio.event
        async def get_chat_messages(sid, data):
            """Obtener mensajes de un chat"""
            try:
                chat_id = data.get('chat_id')
                limit = data.get('limit', 50)
                
                if not chat_id:
                    await websocket_server.sio.emit('error', {
                        'message': 'chat_id es requerido'
                    }, room=sid)
                    return
                
                messages = await self.send_message_use_case.get_chat_messages(chat_id, limit)
                
                messages_data = []
                for message in messages:
                    message_data = {
                        'id': message._id,
                        'chat_id': message.chat_id,
                        'sender_id': message.sender_id,
                        'sent_at': message.sent_at.isoformat(),
                        'type': message.type,
                        'content': message.content,
                        'attachments': [
                            {
                                'url': att['url'],
                                'filename': att['filename'],
                                'mime_type': att['mime_type'],
                                'size_bytes': att['size_bytes']
                            }
                            for att in message.attachment
                        ],
                        'status': message.status
                    }
                    messages_data.append(message_data)
                
                await websocket_server.sio.emit('chat_messages', {
                    'chat_id': chat_id,
                    'messages': messages_data
                }, room=sid)
                
            except Exception as e:
                await websocket_server.sio.emit('error', {
                    'message': str(e)
                }, room=sid)
        
        @websocket_server.sio.event
        async def mark_message_read(sid, data):
            """Marcar mensaje como leído"""
            try:
                message_id = data.get('message_id')
                user_id = data.get('user_id')
                
                if not message_id or not user_id:
                    await websocket_server.sio.emit('error', {
                        'message': 'message_id y user_id son requeridos'
                    }, room=sid)
                    return
                
                await self.send_message_use_case.mark_message_as_read(message_id, user_id)
                
                await websocket_server.sio.emit('message_marked_read', {
                    'message_id': message_id
                }, room=sid)
                
            except Exception as e:
                await websocket_server.sio.emit('error', {
                    'message': str(e)
                }, room=sid)

# Instancia global de manejadores
websocket_handlers = WebSocketHandlers() 