from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

from adapters.input.chat_controller import chat_blueprint

app = Flask(__name__)

CORS(app, resources={r"/auth/*": {
    "origins": ["*"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

# Initialize Swagger for API documentation
swagger = Swagger(app)

app.register_blueprint(chat_blueprint, url_prefix='/chat')

if __name__ == "__main__":
    app.run(debug=True, port=5004)  # Port can be changed as needed