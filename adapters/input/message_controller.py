from flask import Blueprint, g
# from flasgger import swag_from
from flask_socketio import emit, join_room, leave_room # type: ignore

from typing import Dict, Any

# Use cases
from application.use_cases.message.send_message import SendMessageUseCase

# Output adapters
from adapters.output.json_message_repository import JsonMessageRepository
from adapters.output.json_chat_repository import JsonChatRepository

# socketio instance
from app import socketio

# Middleware
from adapters.middleware.auth_middleware import AuthMiddleware
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:5001/auth")

message_blueprint = Blueprint('message', __name__)

# Output adapters
message_repository = JsonMessageRepository()
chat_repository = JsonChatRepository()

# Use cases instantiation
send_message_use_case = SendMessageUseCase(message_repository=message_repository, chat_repository=chat_repository)

# Middleware
auth_middleware = AuthMiddleware(auth_service_url=BASE_URL + '/validate-token')
require_auth = auth_middleware.require_auth

# Handle message sending
@socketio.on('join')
def handle_join(data: Dict[str, Any]):
    room:str = data['chat_id']
    join_room(room)
    emit('status', {'msg': f'User {g.user_id} has entered the room {room}'}, to=room)

# Message sending endpoint
@socketio.on('send_message')
@require_auth
def handle_send_message(data: Dict[str, Any]):
    chat_id = data['chat_id']
    message_data = data['message']
    user_id = g.user_id
    
    # Aquí llamas a tu caso de uso para guardar el mensaje
    saved_message = send_message_use_case.send_message(
        chat_id = chat_id,
        user_id = user_id,
        content = message_data
    )

    emit('new_message', saved_message.to_dict(), to=chat_id)

# Cuando un usuario cierra la pestaña o sale del chat visualmente
@socketio.on('leave')
def handle_leave(data: Dict[str, Any]):
    room = data['chat_id']
    leave_room(room)
    emit('status', {'msg': f'User left room {room}'}, to=room)