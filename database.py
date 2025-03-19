import os
from dotenv import load_dotenv
from supabase import create_client, Client
import requests
from flask import request

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or API Key is missing. Check your .env file.")

# Initialize Supabase client
try:
    supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    raise RuntimeError(f"Failed to connect to Supabase: {e}")

def get_user_from_token():
    """Validates the Supabase user token and returns the user ID."""

    auth_header = request.headers.get("Authorization")
    token = None                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            

    # Check Authorization header first
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1].strip()
    else:
        # Fallback: Check query parameters
        token = request.args.get("token")

    if not token:
        print("Error: No token provided.")
        return None

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {token}"
    }

    # Request Supabase auth API to verify the token
    response = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("id")  # Ensure we're returning the user ID
    else:
        print(f"Auth Error: {response.status_code} - {response.text}")
        return None
    
# Chats CRUD
def create_chat(user_id, chat_name):
    """Creates a new chat and returns the chat details."""
    try:
        response = supabase_client.table("chats").insert(
            {"user_id": user_id, "name": chat_name}
        ).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating chat: {e}")
        return None

def delete_chat(chat_id, user_id):
    """Deletes a chat only if the user is the owner."""
    try:
        response = (
            supabase_client.table("chats")
            .delete()
            .match({"id": chat_id, "user_id": user_id})
            .execute()
        )
        return response.data if response.data else None
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return None

# Messages CRUD
def insert_message(chat_id, sender, text):
    """Inserts a message into the database, linking it to a user."""
    print(chat_id, sender, text)
    try:
        response = supabase_client.table("messages").insert({
            "chat_id": chat_id,
            "sender": sender,
            "text": text
        }).execute()

        if response.data:
            print("Inserted msg:", response.data[0])
            return response.data[0]
        else:
            print("No data returned from insert_message")
            return None

    except Exception as e:
        print(f"Error inserting message: {e}")
        return None

def get_user_chats(user_id):
    """Fetch all chats where the user is a participant."""
    try:
        response = supabase_client.table("chats").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching user chats: {e}")
        return []

def get_chat_messages(chat_id):
    """Fetch all messages for a given chat, sorted by timestamp."""
    try:
        response = (
            supabase_client.table("messages")
            .select("*")
            .eq("chat_id", chat_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching chat messages: {e}")
        return []
