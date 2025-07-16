import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from infrastructure.websocket.websocket_handlers import WebSocketHandlers
from domain.entities.chat import Chat
from domain.entities.message import Message


@pytest.mark.unit
@pytest.mark.websocket
class TestWebSocketHandlers:
    
    @pytest.fixture
    def websocket_handlers(self, mock_chat_repository, mock_message_repository):
        """Fixture para WebSocketHandlers con repositorios mock"""
        with patch('infrastructure.websocket.websocket_handlers.MongoChatRepository', return_value=mock_chat_repository), \
             patch('infrastructure.websocket.websocket_handlers.MongoMessageRepository', return_value=mock_message_repository):
            handlers = WebSocketHandlers()
            handlers.chat_repository = mock_chat_repository
            handlers.message_repository = mock_message_repository
            return handlers

    @pytest.mark.asyncio
    async def test_check_authentication_valid_session(self, websocket_handlers):
        """Test para verificar autenticación con sesión válida"""
        # Arrange
        sid = "test_session_123"
        mock_session = {
            'authenticated': True,
            'user_id': 'test_user_1',
            'auth_data': {'user_id': 'test_user_1', 'name': 'Test User'}
        }
        
        with patch('infrastructure.websocket.websocket_handlers.websocket_server') as mock_server:
            mock_server.sio.get_session = AsyncMock(return_value=mock_session)
            
            # Act
            is_auth, user_id, auth_data = await websocket_handlers._check_authentication(sid)
            
            # Assert
            assert is_auth is True
            assert user_id == 'test_user_1'
            assert auth_data == {'user_id': 'test_user_1', 'name': 'Test User'}

    @pytest.mark.asyncio
    async def test_check_authentication_invalid_session(self, websocket_handlers):
        """Test para verificar autenticación con sesión inválida"""
        # Arrange
        sid = "test_session_123"
        
        with patch('infrastructure.websocket.websocket_handlers.websocket_server') as mock_server:
            mock_server.sio.get_session = AsyncMock(side_effect=Exception("Session not found"))
            
            # Act
            is_auth, user_id, auth_data = await websocket_handlers._check_authentication(sid)
            
            # Assert
            assert is_auth is False
            assert user_id is None
            assert auth_data == {}

    @pytest.mark.asyncio
    async def test_create_chat_success(self, websocket_handlers, mock_chat_repository, sample_chat):
        """Test para crear chat exitosamente"""
        # Arrange
        sid = "test_session_123"
        data = {
            'user_ids': ['test_user_1', 'test_user_2'],
            'description': 'Chat de prueba'
        }
        
        mock_chat_repository.create_chat = AsyncMock(return_value=sample_chat)
        
        with patch.object(websocket_handlers, '_check_authentication') as mock_auth:
            mock_auth.return_value = (True, 'test_user_1', {'user_id': 'test_user_1'})
            
            with patch('infrastructure.websocket.websocket_handlers.websocket_server') as mock_server:
                mock_server.sio.emit = AsyncMock()
                
                # Act
                await websocket_handlers.create_chat_use_case.create_chat(
                    data['user_ids'], 
                    data['description']
                )
                
                # Assert
                mock_chat_repository.create_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_success(self, websocket_handlers, mock_message_repository, 
                                       mock_chat_repository, sample_chat, sample_message):
        """Test para enviar mensaje exitosamente"""
        # Arrange
        sid = "test_session_123"
        data = {
            'chat_id': 'test_chat_123',
            'user_id': 'test_user_1',
            'content': 'Mensaje de prueba',
            'type': 'text'
        }
        
        mock_chat_repository.get_chat_by_id = AsyncMock(return_value=sample_chat)
        mock_message_repository.save = AsyncMock(return_value=sample_message)
        mock_chat_repository.update_chat = AsyncMock()
        
        with patch.object(websocket_handlers, '_check_authentication') as mock_auth:
            mock_auth.return_value = (True, 'test_user_1', {'user_id': 'test_user_1'})
            
            with patch('infrastructure.websocket.websocket_handlers.websocket_server') as mock_server:
                mock_server.sio.emit = AsyncMock()
                mock_server.sio.get_session = AsyncMock(return_value={
                    'authenticated': True,
                    'user_id': 'test_user_1'
                })
                
                # Act
                result = await websocket_handlers.send_message_use_case.send_message(
                    data['chat_id'],
                    data['user_id'], 
                    data['content'],
                    message_type=data['type']
                )
                
                # Assert
                assert result.chat_id == data['chat_id']
                assert result.sender_id == data['user_id']
                assert result.content == data['content']
                mock_message_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_user_not_participant(self, websocket_handlers, 
                                                    mock_chat_repository, sample_chat):
        """Test para enviar mensaje cuando usuario no es participante"""
        # Arrange
        # Modificar el chat para que no incluya al usuario
        sample_chat.participants = [p for p in sample_chat.participants if p["user_id"] != "test_user_3"]
        
        mock_chat_repository.get_chat_by_id = AsyncMock(return_value=sample_chat)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Usuario no es participante del chat"):
            await websocket_handlers.send_message_use_case.send_message(
                "test_chat_123",
                "test_user_3",  # Usuario que no es participante
                "Mensaje de prueba"
            )

    @pytest.mark.asyncio
    async def test_send_message_chat_not_found(self, websocket_handlers, mock_chat_repository):
        """Test para enviar mensaje cuando el chat no existe"""
        # Arrange
        mock_chat_repository.get_chat_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Chat no encontrado"):
            await websocket_handlers.send_message_use_case.send_message(
                "nonexistent_chat",
                "test_user_1",
                "Mensaje de prueba"
            )

    @pytest.mark.asyncio
    async def test_get_user_chats_success(self, websocket_handlers, mock_chat_repository, sample_chat):
        """Test para obtener chats de usuario exitosamente"""
        # Arrange
        mock_chat_repository.get_chats_by_user_id = AsyncMock(return_value=[sample_chat])
        
        # Act
        result = await websocket_handlers.get_chats_use_case.get_user_chats("test_user_1")
        
        # Assert
        assert len(result) == 1
        assert result[0]._id == sample_chat._id
        mock_chat_repository.get_chats_by_user_id.assert_called_once_with("test_user_1")

    @pytest.mark.asyncio
    async def test_get_user_chats_empty_result(self, websocket_handlers, mock_chat_repository):
        """Test para obtener chats cuando usuario no tiene chats"""
        # Arrange
        mock_chat_repository.get_chats_by_user_id = AsyncMock(return_value=[])
        
        # Act
        result = await websocket_handlers.get_chats_use_case.get_user_chats("test_user_1")
        
        # Assert
        assert len(result) == 0
        mock_chat_repository.get_chats_by_user_id.assert_called_once_with("test_user_1")

    @pytest.mark.asyncio
    async def test_get_user_chats_invalid_user_id(self, websocket_handlers):
        """Test para obtener chats con user_id inválido"""
        # Act & Assert
        with pytest.raises(ValueError, match="user_id es requerido"):
            await websocket_handlers.get_chats_use_case.get_user_chats("")

    @pytest.mark.asyncio
    async def test_get_chat_messages_success(self, websocket_handlers, mock_message_repository, sample_message):
        """Test para obtener mensajes de chat exitosamente"""
        # Arrange
        mock_message_repository.get_recent_messages = AsyncMock(return_value=[sample_message])
        
        # Act
        result = await websocket_handlers.send_message_use_case.get_chat_messages("test_chat_123", 50)
        
        # Assert
        assert len(result) == 1
        assert result[0]._id == sample_message._id
        mock_message_repository.get_recent_messages.assert_called_once_with("test_chat_123", 50) 