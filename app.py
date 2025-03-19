from sockets import socketio
import logging
from flask import Flask
from flask_cors import CORS  # ✅ Import CORS
from flask_socketio import SocketIO
from redis_queue import ai_listener
from routes.chat import chat_bp  # ✅ Import chat routes
import threading
import time
import os

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})  # ✅ Allow all origins (for development)

# Initialize WebSockets
socketio.init_app(app, cors_allowed_origins="*")  # ✅ Allow WebSocket connections

# Register API Routes
app.register_blueprint(chat_bp)  # ✅ Add chat routes

# Function to restart Redis listener if it fails
def start_ai_listener():
    while True:
        try:
            ai_listener(socketio) 
        except Exception as e:
            print(f"AI Listener Error: {e}, restarting in 5 seconds...")
            time.sleep(5)  # ✅ Prevent infinite crash loops

# Run Redis AI listener in a separate thread
threading.Thread(target=start_ai_listener, daemon=True).start()

# Disable Flask logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Change to WARNING or ERROR to limit logs


os.environ["FLASK_ENV"] = "production"

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
