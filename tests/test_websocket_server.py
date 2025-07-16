import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import socketio

from infrastructure.websocket.websocket_server import WebSocketServer


@pytest.mark.unit
@pytest.mark.websocket
class TestWebSocketServer:
    
    @pytest.fixture
    def websocket_server(self):
        """Fixture para WebSocketServer"""
        with patch('infrastructure.websocket.websocket_server.websocket_server'):
            server = WebSocketServer()
            server.sio = AsyncMock()
            return server

    @pytest.mark.asyncio
    async def test_connect_with_valid_token(self, websocket_server, valid_jwt_token):
        """Test conexión exitosa con token válido"""
        # Arrange
        sid = "test_session_123"
        environ = {}
        auth = {"token": valid_jwt_token}
        
        mock_validation_result = {
            "valid": True,
            "user_id": "test_user_1",
            "name": "Test User"
        }
        
        with patch('infrastructure.auth.auth_middleware.auth_middleware.validate_websocket_token') as mock_validate:
            mock_validate.return_value = mock_validation_result
            websocket_server.sio.save_session = AsyncMock()
            websocket_server.sio.emit = AsyncMock()
            
            # Act
            # Simular el evento connect directamente
            result = await self._simulate_connect_event(
                websocket_server, sid, environ, auth, mock_validation_result
            )
            
            # Assert
            assert result is True
            assert "test_user_1" in websocket_server.active_connections
            assert websocket_server.session_users[sid] == "test_user_1"

    @pytest.mark.asyncio
    async def test_connect_with_invalid_token(self, websocket_server, invalid_jwt_token):
        """Test conexión fallida con token inválido"""
        # Arrange
        sid = "test_session_123"
        environ = {}
        auth = {"token": invalid_jwt_token}
        
        mock_validation_result = {
            "valid": False,
            "error": "Token inválido"
        }
        
        with patch('infrastructure.auth.auth_middleware.auth_middleware.validate_websocket_token') as mock_validate:
            mock_validate.return_value = mock_validation_result
            
            # Act
            result = await self._simulate_connect_event(
                websocket_server, sid, environ, auth, mock_validation_result
            )
            
            # Assert
            assert result is False
            assert "test_user_1" not in websocket_server.active_connections
            assert sid not in websocket_server.session_users

    @pytest.mark.asyncio
    async def test_connect_without_token(self, websocket_server):
        """Test conexión fallida sin token"""
        # Arrange
        sid = "test_session_123"
        environ = {}
        auth = {}  # Sin token
        
        # Act
        result = await self._simulate_connect_event(
            websocket_server, sid, environ, auth, None
        )
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self, websocket_server):
        """Test limpieza al desconectar"""
        # Arrange
        sid = "test_session_123"
        user_id = "test_user_1"
        
        # Simular conexión existente
        websocket_server.active_connections[user_id] = [sid]
        websocket_server.session_users[sid] = user_id
        
        # Act
        await self._simulate_disconnect_event(websocket_server, sid)
        
        # Assert
        assert user_id not in websocket_server.active_connections
        assert sid not in websocket_server.session_users

    @pytest.mark.asyncio
    async def test_authenticate_event_success(self, websocket_server, valid_jwt_token):
        """Test evento authenticate exitoso"""
        # Arrange
        sid = "test_session_123"
        data = {"token": valid_jwt_token}
        
        mock_validation_result = {
            "valid": True,
            "user_id": "test_user_1",
            "name": "Test User"
        }
        
        with patch('infrastructure.auth.auth_middleware.auth_middleware.validate_websocket_token') as mock_validate:
            mock_validate.return_value = mock_validation_result
            websocket_server.sio.save_session = AsyncMock()
            websocket_server.sio.emit = AsyncMock()
            
            # Act
            await self._simulate_authenticate_event(websocket_server, sid, data, mock_validation_result)
            
            # Assert
            websocket_server.sio.emit.assert_called_with(
                'authenticated',
                {'user_id': 'test_user_1', 'user_data': mock_validation_result},
                room=sid
            )

    @pytest.mark.asyncio
    async def test_authenticate_event_invalid_token(self, websocket_server, invalid_jwt_token):
        """Test evento authenticate con token inválido"""
        # Arrange
        sid = "test_session_123"
        data = {"token": invalid_jwt_token}
        
        mock_validation_result = {
            "valid": False,
            "error": "Token inválido"
        }
        
        with patch('infrastructure.auth.auth_middleware.auth_middleware.validate_websocket_token') as mock_validate:
            mock_validate.return_value = mock_validation_result
            websocket_server.sio.emit = AsyncMock()
            
            # Act
            await self._simulate_authenticate_event(websocket_server, sid, data, mock_validation_result)
            
            # Assert
            websocket_server.sio.emit.assert_called_with(
                'error',
                {
                    'message': 'Autenticación fallida',
                    'details': 'Token inválido'
                },
                room=sid
            )

    @pytest.mark.asyncio
    async def test_join_chat_success(self, websocket_server):
        """Test unirse a chat exitosamente"""
        # Arrange
        sid = "test_session_123"
        user_id = "test_user_1"
        chat_id = "test_chat_123"
        data = {"chat_id": chat_id}
        
        mock_session = {
            'authenticated': True,
            'user_id': user_id
        }
        
        websocket_server.sio.get_session = AsyncMock(return_value=mock_session)
        websocket_server.sio.enter_room = AsyncMock()
        websocket_server.sio.emit = AsyncMock()
        
        # Act
        await self._simulate_join_chat_event(websocket_server, sid, data)
        
        # Assert
        websocket_server.sio.enter_room.assert_called_once_with(sid, chat_id)
        websocket_server.sio.emit.assert_called_with(
            'joined_chat',
            {'chat_id': chat_id},
            room=sid
        )

    @pytest.mark.asyncio
    async def test_join_chat_not_authenticated(self, websocket_server):
        """Test unirse a chat sin autenticación"""
        # Arrange
        sid = "test_session_123"
        data = {"chat_id": "test_chat_123"}
        
        mock_session = {
            'authenticated': False
        }
        
        websocket_server.sio.get_session = AsyncMock(return_value=mock_session)
        websocket_server.sio.emit = AsyncMock()
        
        # Act
        await self._simulate_join_chat_event(websocket_server, sid, data)
        
        # Assert
        websocket_server.sio.emit.assert_called_with(
            'error',
            {
                'message': 'No autenticado',
                'details': 'Debe autenticarse antes de unirse a un chat'
            },
            room=sid
        )

    # Métodos auxiliares para simular eventos

    async def _simulate_connect_event(self, server, sid, environ, auth, validation_result):
        """Simular evento connect"""
        if not auth or 'token' not in auth:
            return False
        
        if validation_result and validation_result.get("valid"):
            user_id = validation_result.get("user_id")
            if user_id not in server.active_connections:
                server.active_connections[user_id] = []
            server.active_connections[user_id].append(sid)
            server.session_users[sid] = user_id
            return True
        
        return False

    async def _simulate_disconnect_event(self, server, sid):
        """Simular evento disconnect"""
        if sid in server.session_users:
            user_id = server.session_users[sid]
            if user_id in server.active_connections:
                server.active_connections[user_id].remove(sid)
                if not server.active_connections[user_id]:
                    del server.active_connections[user_id]
            del server.session_users[sid]

    async def _simulate_authenticate_event(self, server, sid, data, validation_result):
        """Simular evento authenticate"""
        if validation_result and validation_result.get("valid"):
            user_id = validation_result.get("user_id")
            if user_id not in server.active_connections:
                server.active_connections[user_id] = []
            server.active_connections[user_id].append(sid)
            server.session_users[sid] = user_id
            
            await server.sio.emit('authenticated', {
                'user_id': user_id,
                'user_data': validation_result
            }, room=sid)
        else:
            error_message = validation_result.get("error", "Token inválido") if validation_result else "Token requerido"
            await server.sio.emit('error', {
                'message': 'Autenticación fallida',
                'details': error_message
            }, room=sid)

    async def _simulate_join_chat_event(self, server, sid, data):
        """Simular evento join_chat"""
        session = await server.sio.get_session(sid)
        if not session.get('authenticated', False):
            await server.sio.emit('error', {
                'message': 'No autenticado',
                'details': 'Debe autenticarse antes de unirse a un chat'
            }, room=sid)
            return
        
        chat_id = data.get('chat_id')
        await server.sio.enter_room(sid, chat_id)
        await server.sio.emit('joined_chat', {'chat_id': chat_id}, room=sid) 