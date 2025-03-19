from flask_socketio import SocketIO, join_room, emit
from flask import request
import json
from database import insert_message
from redis_queue import redis_client
from database import get_user_from_token  # New: Import authentication helper

socketio = SocketIO(cors_allowed_origins="*")

@socketio.on("join_chat")
def handle_join(data):
    """User joins a chat room after authentication."""
    try:
        user_id = get_user_from_token()  # Extract user ID from token
        chat_id = data.get("chat_id")

        if not user_id:
            emit("error", {"message": "Unauthorized: Invalid token"}, room=request.sid)
            return

        if not chat_id:
            emit("error", {"message": "Invalid request: Missing chat_id"}, room=request.sid)
            return

        join_room(chat_id)
        # print(f"✅ User {user_id} joined chat {chat_id} - SID: {request.sid}")

        # Acknowledge successful join
        emit("join_success", {"message": f"Joined chat {chat_id}"}, room=request.sid)

    except Exception as e:
        print(f"❌ Error in handle_join: {e}")
        emit("error", {"message": "Failed to join chat"}, room=request.sid)


@socketio.on("send_message")
def handle_send_message(data):
    """Handles incoming messages with authentication."""
    try:
        user_id = get_user_from_token()  # Extract user ID from token
        chat_id = data.get("chat_id")
        text = data.get("text")

        # print(f"📩 Received message from {user_id}: {text} (chat_id: {chat_id})")

        if not user_id:
            emit("error", {"message": "Unauthorized: Invalid token"}, room=request.sid)
            return

        if not chat_id or not text:
            emit("error", {"message": "Invalid message: Missing chat_id or text"}, room=request.sid)
            return

        # Store user message in DB
        message = insert_message(chat_id, "user", text)
        
        if not message:
            emit("error", {"message": "Failed to save message"}, room=request.sid)
            return

        # print(f"✅ Message saved to DB: {message}")

        # Broadcast message to chat room
        emit("new_message", message, room=chat_id)
        # print(f"📢 Emitted new_message event to room {chat_id}")

        # Publish message to Redis for AI processing
        redis_payload = json.dumps({"chat_id": chat_id, "text": text})
        redis_client.publish("ai_requests", redis_payload)
        # print(f"📡 Published to Redis 'ai_requests': {redis_payload}")

        # Acknowledge message receipt
        emit("message_ack", {"message": "Message received"}, room=request.sid)

    except Exception as e:
        print(f"❌ Error in handle_send_message: {e}")
        emit("error", {"message": "Failed to send message"}, room=request.sid)
