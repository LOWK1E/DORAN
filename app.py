import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Import custom modules
from chatbot import Chatbot
from user_management import User, UserManager

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize CSRF Protection but we'll disable it for now to get the chat working
# csrf = CSRFProtect(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize user manager and chatbot
user_manager = UserManager()
chatbot = Chatbot()  # Rules are now loaded from soict.py automatically

@login_manager.user_loader
def load_user(user_id):
    return user_manager.get_user_by_id(user_id)

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if user_type == 'guest':
            # For guest users, create a temporary session without login
            session['guest_username'] = username
            flash('Welcome, Guest!', 'success')
            return redirect(url_for('chat'))
        
        # For admin and regular users
        user = user_manager.get_user_by_username(username)
        
        # If user doesn't exist and it's a new user registration
        if not user and user_type == 'user':
            user = user_manager.create_user(username, password, user_type)
            login_user(user)
            flash('Account created and logged in!', 'success')
            return redirect(url_for('chat'))
        
        # Validate existing user
        if user and check_password_hash(user.password_hash, password) and user.role == user_type:
            login_user(user)
            flash(f'Welcome back, {username}!', 'success')
            if user_type == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('chat'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', user_type=user_type)

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    if 'guest_username' in session:
        session.pop('guest_username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('welcome'))

@app.route('/chat')
def chat():
    username = None
    role = "guest"
    
    if current_user.is_authenticated:
        username = current_user.username
        role = current_user.role
    elif 'guest_username' in session:
        username = session['guest_username']
    else:
        return redirect(url_for('welcome'))
    
    chat_history = []
    if current_user.is_authenticated:
        chat_history = user_manager.get_chat_history(current_user.id)
    
    return render_template('chat.html', username=username, role=role, chat_history=chat_history)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    user_message = data.get('message', '')
    
    # Get chatbot response
    bot_response = chatbot.get_response(user_message)
    
    # Store chat history for authenticated users
    if current_user.is_authenticated:
        user_manager.add_chat_message(current_user.id, 'user', user_message)
        user_manager.add_chat_message(current_user.id, 'bot', bot_response)
    
    return jsonify({
        'response': bot_response, 
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    user_manager.clear_chat_history(current_user.id)
    return jsonify({'status': 'success'})

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))
    
    rules = chatbot.get_rules()
    return render_template('admin.html', rules=rules)

@app.route('/add_rule', methods=['POST'])
@login_required
def add_rule():
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})
    
    data = request.get_json()
    keywords = data.get('keywords', '').lower().split(',')
    keywords = [keyword.strip() for keyword in keywords if keyword.strip()]
    response = data.get('response', '')
    
    if not keywords or not response:
        return jsonify({'status': 'error', 'message': 'Keywords and response are required'})
    
    chatbot.add_rule(keywords, response)
    return jsonify({'status': 'success'})

@app.route('/delete_rule', methods=['POST'])
@login_required
def delete_rule():
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})
    
    data = request.get_json()
    rule_id = data.get('rule_id')
    
    if chatbot.delete_rule(rule_id):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Rule not found'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
