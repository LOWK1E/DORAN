from werkzeug.security import generate_password_hash
from flask_login import UserMixin
import logging
from datetime import datetime
import uuid

class User(UserMixin):
    def __init__(self, id, username, password_hash, role):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

class UserManager:
    def __init__(self):
        # In-memory user storage
        self.users = {}
        self.chat_history = {}
        self.next_user_id = 1
        
        # Create default admin user - with debug output
        admin_user = self.create_user("admin", "admin123", "admin")
        logging.debug(f"Created default admin user with ID: {admin_user.id}, username: {admin_user.username}, role: {admin_user.role}")
        
        # Debug check for verification
        check_admin = self.get_user_by_username("admin")
        if check_admin:
            logging.debug(f"Verified admin user exists with ID: {check_admin.id}, role: {check_admin.role}")
        else:
            logging.error("Failed to create admin user!")
            
        logging.debug(f"User database now contains {len(self.users)} users")
    
    def create_user(self, username, password, role):
        """Create a new user and store it in memory"""
        user_id = str(self.next_user_id)
        password_hash = generate_password_hash(password)
        
        user = User(user_id, username, password_hash, role)
        self.users[user_id] = user
        self.chat_history[user_id] = []
        
        self.next_user_id += 1
        logging.debug(f"Created user: {username} with role: {role}")
        return user
    
    def get_user_by_id(self, user_id):
        """Get a user by their ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username):
        """Get a user by their username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def add_chat_message(self, user_id, sender_type, message):
        """Add a message to a user's chat history"""
        if user_id in self.chat_history:
            self.chat_history[user_id].append({
                'id': str(uuid.uuid4()),
                'sender': sender_type,  # 'user' or 'bot'
                'message': message,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            logging.debug(f"Added {sender_type} message to user {user_id}'s chat history")
    
    def get_chat_history(self, user_id):
        """Get a user's chat history"""
        return self.chat_history.get(user_id, [])
    
    def clear_chat_history(self, user_id):
        """Clear a user's chat history"""
        if user_id in self.chat_history:
            self.chat_history[user_id] = []
            logging.debug(f"Cleared chat history for user {user_id}")
