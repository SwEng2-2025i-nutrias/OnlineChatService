import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime

# Imports de la aplicación
from infrastructure.database.mongodb_config import mongo_config
from infrastructure.websocket.websocket_server import websocket_server
from infrastructure.websocket.websocket_handlers import websocket_handlers
from infrastructure.auth.auth_middleware import get_current_user
from application.use_cases.create_chat_use_case import CreateChatUseCase
from application.use_cases.send_message_use_case import SendMessageUseCase
from application.use_cases.get_chats_use_case import GetChatsUseCase
from infrastructure.repositories.mongo_chat_repository import MongoChatRepository
from infrastructure.repositories.mongo_message_repository import MongoMessageRepository

# Modelos Pydantic para API REST
class CreateChatRequest(BaseModel):
    user_ids: List[str]
    description: Optional[str] = None

class SendMessageRequest(BaseModel):
    chat_id: str
    user_id: str
    content: str
    attachments: Optional[List[Dict]] = None
    type: str = "text"

class MessageResponse(BaseModel):
    id: str
    chat_id: str
    sender_id: str
    sent_at: str
    type: str
    content: Optional[str]
    attachments: List[Dict]
    status: str

class ChatResponse(BaseModel):
    id: str
    type: str
    participants: List[Dict]
    title: Optional[str]
    created_at: str
    last_message_at: Optional[str]
    unread_counts: Dict[str, int]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejar el ciclo de vida de la aplicación"""
    # Startup
    print("🚀 Iniciando aplicación...")
    
    # Conectar a MongoDB
    await mongo_config.connect_to_mongo()
    
    # Inicializar manejadores de WebSocket
    websocket_handlers
    
    print("✅ Aplicación iniciada correctamente")
    
    yield
    
    # Shutdown
    print("🔄 Cerrando aplicación...")
    await mongo_config.close_mongo_connection()
    print("✅ Aplicación cerrada correctamente")

# Crear aplicación FastAPI
app = FastAPI(
    title="Online Chat Service",
    description="Servicio de chat en tiempo real con WebSocket y MongoDB",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Integrar Socket.IO con FastAPI
import socketio
socket_app = socketio.ASGIApp(websocket_server.sio, app)

# Inicializar repositorios y casos de uso
chat_repository = MongoChatRepository()
message_repository = MongoMessageRepository()

create_chat_use_case = CreateChatUseCase(chat_repository)
send_message_use_case = SendMessageUseCase(message_repository, chat_repository)
get_chats_use_case = GetChatsUseCase(chat_repository)

# Endpoints REST API
@app.get("/")
async def root():
    """Endpoint de bienvenida"""
    return {
        "message": "Online Chat Service API",
        "version": "1.0.0",
        "websocket_url": "/socket.io/",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Verificar salud del servicio"""
    try:
        # Verificar conexión a MongoDB
        db = mongo_config.get_database()
        if db is None:
            raise Exception("Base de datos no disponible")
        
        # Verificar WebSocket
        active_users = websocket_server.get_active_users()
        
        return {
            "status": "healthy",
            "database": "connected",
            "websocket": "active",
            "active_users": len(active_users),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/api/chats", response_model=ChatResponse)
async def create_chat_endpoint(
    request: CreateChatRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Crear nuevo chat via REST API"""
    try:
        # Asegurar que el usuario actual esté en la lista de participantes
        user_id = current_user.get("user_id")
        if user_id and isinstance(user_id, str) and user_id not in request.user_ids:
            request.user_ids.append(user_id)
        
        chat = await create_chat_use_case.create_chat(
            user_ids=request.user_ids,
            description=request.description
        )
        
        return ChatResponse(
            id=chat._id,
            type=chat.type,
            participants=[
                {
                    "user_id": p["user_id"],
                    "role": p["role"],
                    "joined_at": p["joined_at"].isoformat()
                }
                for p in chat.participants
            ],
            title=chat.title,
            created_at=chat.created_at.isoformat(),
            last_message_at=chat.last_message_at.isoformat() if chat.last_message_at else None,
            unread_counts=chat.unread_counts
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/users/{user_id}/chats", response_model=List[ChatResponse])
async def get_user_chats_endpoint(
    user_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtener chats de un usuario via REST API"""
    try:
        # Verificar que el usuario solo pueda ver sus propios chats
        if user_id != current_user.get("user_id"):
            raise HTTPException(
                status_code=403, 
                detail="No tienes permisos para ver los chats de otro usuario"
            )
        
        chats = await get_chats_use_case.get_user_chats(user_id)
        
        return [
            ChatResponse(
                id=chat._id,
                type=chat.type,
                participants=[
                    {
                        "user_id": p["user_id"],
                        "role": p["role"],
                        "joined_at": p["joined_at"].isoformat(),
                        "user_name": p.get("user_name", "Usuario"),
                        "user_email": p.get("user_email", "")
                    }
                    for p in chat.participants
                ],
                title=chat.title,
                created_at=chat.created_at.isoformat(),
                last_message_at=chat.last_message_at.isoformat() if chat.last_message_at else None,
                unread_counts=chat.unread_counts
            )
            for chat in chats
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/messages", response_model=MessageResponse)
async def send_message_endpoint(
    request: SendMessageRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Enviar mensaje via REST API"""
    try:
        # Verificar que el usuario autenticado sea quien envía el mensaje
        if request.user_id != current_user.get("user_id"):
            raise HTTPException(
                status_code=403, 
                detail="No puedes enviar mensajes como otro usuario"
            )
        # Procesar attachments
        attachments = []
        if request.attachments:
            for att in request.attachments:
                attachments.append({
                    "url": att.get("url", ""),
                    "filename": att.get("filename", ""),
                    "mime_type": att.get("mime_type", ""),
                    "size_bytes": att.get("size_bytes", 0)
                })
        
        message = await send_message_use_case.send_message(
            chat_id=request.chat_id,
            user_id=request.user_id,
            content=request.content,
            attachments=attachments if attachments else None,
            message_type=request.type
        )
        
        return MessageResponse(
            id=message._id,
            chat_id=message.chat_id,
            sender_id=message.sender_id,
            sent_at=message.sent_at.isoformat(),
            type=message.type,
            content=message.content,
            attachments=[
                {
                    "url": att["url"],
                    "filename": att["filename"],
                    "mime_type": att["mime_type"],
                    "size_bytes": att["size_bytes"]
                }
                for att in message.attachment
            ],
            status=message.status
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages_endpoint(
    chat_id: str, 
    limit: int = 50, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtener mensajes de un chat via REST API"""
    try:
        # Verificar que el usuario sea participante del chat
        chat = await get_chats_use_case.get_chat_by_id(chat_id)
        user_id = current_user.get("user_id")
        user_is_participant = any(
            p["user_id"] == user_id for p in chat.participants
        )
        if not user_is_participant:
            raise HTTPException(
                status_code=403, 
                detail="No tienes acceso a este chat"
            )
        
        messages = await send_message_use_case.get_chat_messages(chat_id, limit)
        
        return [
            MessageResponse(
                id=message._id,
                chat_id=message.chat_id,
                sender_id=message.sender_id,
                sent_at=message.sent_at.isoformat(),
                type=message.type,
                content=message.content,
                attachments=[
                    {
                        "url": att["url"],
                        "filename": att["filename"],
                        "mime_type": att["mime_type"],
                        "size_bytes": att["size_bytes"]
                    }
                    for att in message.attachment
                ],
                status=message.status
            )
            for message in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Obtener estadísticas del servicio"""
    try:
        active_users = websocket_server.get_active_users()
        
        return {
            "active_users": len(active_users),
            "active_user_ids": active_users,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Punto de entrada principal
if __name__ == "__main__":
    # Configuración desde variables de entorno
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"🚀 Iniciando servidor en {host}:{port}")
    print(f"📡 WebSocket disponible en ws://{host}:{port}/socket.io/")
    print(f"📚 Documentación en http://{host}:{port}/docs")
    
    uvicorn.run(
        socket_app,
        host=host,
        port=port,
        log_level="info" if not debug else "debug"
    ) 