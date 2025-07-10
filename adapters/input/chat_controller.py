from flask import request, jsonify, Blueprint
from flasgger import swag_from

#Use cases
from ...application.use_cases.chat.create_chat import CreateChatUseCase
from ...application.use_cases.chat.get_chat import GetChatUseCase
from ...application.use_cases.chat.get_user_chats import GetUserChatsUseCase

# Output adapters
from ...adapters.output.http_user_repository import HttpUserRepository
from ...adapters.output.json_chat_repository import JsonChatRepository

chat_blueprint = Blueprint('chat', __name__)

# Output adapters
user_repository = HttpUserRepository(base_url="http://example.com/api")
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

# Chat creation endpoint
@chat_blueprint.route('/chats', methods=['POST'])
@swag_from("docs/create_chat.yaml")
def create_chat():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid input"}), 400
    
    if  'user_ids' not in data or not data["user_ids"]:
        return jsonify({"error": "user_ids is required"}), 400
    
    user_ids:list[str] = data["user_ids"]

    chat = create_chat_use_case.create_chat(
        user_ids=user_ids,
    )
    return jsonify(chat.to_dict()), 201