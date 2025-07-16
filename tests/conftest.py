import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.websocket.websocket_server import WebSocketServer
from infrastructure.auth.mock_auth_service import mock_auth_service
from infrastructure.repositories.mongo_chat_repository import MongoChatRepository
from infrastructure.repositories.mongo_message_repository import MongoMessageRepository
from domain.entities.chat import Chat
from domain.entities.message import Message
from domain.entities.participant import Participant
from domain.entities.attachment import Attachment

@pytest.fixture
def event_loop():
    """Fixture para el loop de eventos de asyncio"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_websocket_server():
    """Mock del servidor WebSocket"""
    server = MagicMock()
    server.sio = AsyncMock()
    server.active_connections = {}
    server.session_users = {}
    return server

@pytest.fixture
def valid_jwt_token():
    """Token JWT válido para testing"""
    return mock_auth_service.generate_test_token("test_user_1")

@pytest.fixture
def invalid_jwt_token():
    """Token JWT inválido para testing"""
    return "invalid.jwt.token"

@pytest.fixture
def test_user_data():
    """Datos de usuario para testing"""
    return {
        "user_id": "test_user_1",
        "name": "Usuario Test",
        "email": "test@example.com",
        "role": "user"
    }

@pytest.fixture
def sample_participants():
    """Participantes de ejemplo"""
    return [
        {"user_id": "test_user_1", "role": "admin", "joined_at": datetime.now(timezone.utc)},
        {"user_id": "test_user_2", "role": "member", "joined_at": datetime.now(timezone.utc)}
    ]

@pytest.fixture
def sample_chat(sample_participants):
    """Chat de ejemplo para testing"""
    return Chat(
        _id="test_chat_123",
        type="private",
        participants=sample_participants,
        metadata={},
        title="Chat de prueba",
        created_at=datetime.now(timezone.utc),
        last_message_at=None,
        unread_counts={"test_user_1": 0, "test_user_2": 0}
    )

@pytest.fixture
def sample_message():
    """Mensaje de ejemplo para testing"""
    return Message(
        _id="test_message_123",
        chat_id="test_chat_123",
        sender_id="test_user_1",
        sent_at=datetime.now(timezone.utc),
        type="text",
        content="Mensaje de prueba",
        attachment=[],
        status="sent"
    )

@pytest.fixture
def sample_attachment():
    """Attachment de ejemplo"""
    return Attachment(
        url="https://example.com/file.jpg",
        filename="test_image.jpg",
        mime_type="image/jpeg",
        size_bytes=1024
    )

@pytest.fixture
def mock_chat_repository():
    """Mock del repositorio de chats"""
    repo = AsyncMock(spec=MongoChatRepository)
    return repo

@pytest.fixture
def mock_message_repository():
    """Mock del repositorio de mensajes"""
    repo = AsyncMock(spec=MongoMessageRepository)
    return repo

@pytest.fixture
async def websocket_test_client():
    """Cliente WebSocket para testing"""
    import socketio
    
    client = socketio.AsyncClient()
    yield client
    
    if client.connected:
        await client.disconnect() 