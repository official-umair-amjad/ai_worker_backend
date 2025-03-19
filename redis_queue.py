import redis
import json
import os
import time
from database import insert_message

# Load Redis connection details from .env
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
except Exception as e:
    raise RuntimeError(f"Failed to connect to Redis: {e}")

def ai_listener(socketio):
    """Listens for AI responses from Redis and updates the chat room via WebSockets."""
    while True:
        try:
            pubsub = redis_client.pubsub()
            pubsub.subscribe("ai_responses")
            print("Server AI Listener: Subscribed to 'ai_responses' channel.")

            for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                print("Server AI Listener: Received message:", message)
                try:
                    data = json.loads(message["data"])
                    chat_id = data.get("chat_id")
                    ai_response = data.get("text")

                    if not chat_id or not ai_response:
                        print("Server AI Listener: Incomplete AI response received.")
                        continue

                    # Store AI response in DB
                    insert_message(chat_id, "ai", ai_response)
                    print(f"Server AI Listener: AI response stored in DB for chat {chat_id}")

                    # Emit the AI response to the chat room
                    socketio.emit(
                        "new_message",
                        {"chat_id": chat_id, "sender": "ai", "text": ai_response},
                        room=chat_id,
                    )
                    print(f"Server AI Listener: Emitted new_message for AI response to chat {chat_id}")
                except json.JSONDecodeError:
                    print("Server AI Listener: Received invalid JSON from Redis.")
                except Exception as e:
                    print(f"Server AI Listener: Error processing AI response: {e}")
        except redis.ConnectionError:
            print("Server AI Listener: Redis connection lost. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Server AI Listener: Critical error: {e}. Restarting in 5 seconds...")
            time.sleep(5)
