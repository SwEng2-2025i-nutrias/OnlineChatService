from flask import request, jsonify, Blueprint, g
from flasgger import swag_from

#Use cases
from application.use_cases.chat.create_chat import CreateChatUseCase
from application.use_cases.chat.get_chat import GetChatUseCase
from application.use_cases.chat.get_user_chats import GetUserChatsUseCase

# Output adapters
from adapters.output.http_user_repository import HttpUserRepository
from adapters.output.json_chat_repository import JsonChatRepository

# Load environment variables
import os

# Middleware
from adapters.middleware.auth_middleware import AuthMiddleware

BASE_URL = os.getenv("BASE_URL", "http://localhost:5001/auth")

chat_blueprint = Blueprint('chat', __name__)

# Output adapters
user_repository = HttpUserRepository(base_url=BASE_URL)
chat_repository = JsonChatRepository()


# Usecases instantiation
create_chat_use_case = CreateChatUseCase(
    chat_repository=chat_repository,  # Replace with actual repository instance
    user_repository=user_repository   # Replace with actual repository instance
)
get_user_chats_use_case = GetUserChatsUseCase(
    chat_repository=chat_repository  # Replace with actual repository instance
)
get_chat_use_case = GetChatUseCase(
    chat_repository=chat_repository  # Replace with actual repository instance
)

# Middleware instantiation
auth_middleware = AuthMiddleware(auth_service_url=BASE_URL + '/validate-token')
require_auth = auth_middleware.require_auth

# Chat creation endpoint
# The correct order for the decorators is important
@chat_blueprint.route('/chats', methods=['POST'])
@require_auth
@swag_from("docs/create_chat.yaml")
def create_chat():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid input"}), 400
    
    if  'user_ids' not in data or not data["user_ids"]:
        return jsonify({"error": "user_ids is required"}), 400
    
    user_ids:list[str] = data["user_ids"]

    # Check if user_ids has the token of the user who is creating the chat
    user_id = g.user_id
    if user_id not in user_ids:
        return jsonify({"error": "You must include your user ID in the user_ids list"}), 400

    try:
        chat = create_chat_use_case.create_chat(
            user_ids=user_ids,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(chat.to_dict()), 201

# Get a chat by ID endpoint
@chat_blueprint.route('/chats/<string:chat_id>', methods=['GET'])
@require_auth
@swag_from("docs/get_chat.yaml")
def get_chat(chat_id:str):
    try:
        chat = get_chat_use_case.get_chat(chat_id)


        if not chat:
            return jsonify({"error": "Chat not found"}), 404
        
        user_id = g.user_id
        if user_id not in [participant["user_id"] for participant in chat.participants]:
            return jsonify({"error": "You are not a participant of this chat"}), 403
        
        return jsonify(chat.to_dict()), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    
# Get chats by user ID endpoint
@chat_blueprint.route('/chats', methods=['GET'])
@require_auth
# @swag_from("docs/get_user_chats.yaml")
def get_user_chats():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    token_user_id = g.user_id

    if user_id != token_user_id:
        return jsonify({"error": "You can only get your own chats"}), 403

    try:
        chats = get_user_chats_use_case.get_user_chats(user_id)
        return jsonify([chat.to_dict() for chat in chats]), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404