import os
import logging
import re
import json
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, jsonify, session, redirect, url_for, flash
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import custom modules
from chatbot import Chatbot
from user_management import UserManager
from models import Admin, User as UserModel
from extensions import db
from database import email_directory

app = Flask(__name__)
app.template_folder = 'htdocs'
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Add SQLAlchemy configuration for database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///doran.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Log SQL statements for debugging

# File upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'locations')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    try:
        db.create_all()
        app.logger.info("Database tables created successfully")
        user_manager = UserManager(db)
    except Exception as e:
        app.logger.error(f"Database initialization failed: {str(e)}. App will run without database features.")
        user_manager = None

chatbot = Chatbot()  # Rules are now loaded from soict.py automatically

@login_manager.user_loader
def load_user(user_id):
    """
    Load user by ID for Flask-Login.
    """
    user_type = session.get('user_type')
    if user_type == 'admin':
        admin = Admin.query.get(int(user_id))
        if admin:
            return admin
    elif user_type == 'user':
        user = user_manager.get_user_by_id(user_id)
        if user:
            return user
    return None

def is_admin(user):
    """
    Helper function to check if a user is an admin.
    """
    if user is None:
        return False
    if isinstance(user, Admin):
        return True
    if hasattr(user, 'role') and user.role == 'admin':
        return True
    return False

@app.route('/favicon.ico')
def favicon():
    """
    Suppress favicon requests by returning 204 No Content.
    """
    return '', 204

@app.route('/welcome')
def welcome_api():
    """
    Returns a welcome message via API.
    """
    app.logger.info(f"Request received: {request.method} {request.path}")
    return jsonify({'message': 'Welcome to the Flask API Service!'})

@app.route('/')
def welcome():
    """
    Render the welcome page.
    """
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login for regular users and guests.
    """
    user_type = request.args.get('user_type', 'user')
    if request.method == 'POST':
        if user_type == 'guest':
            username = request.form.get('username')
            if not username:
                flash('Please enter a username', 'danger')
                return render_template('login.html', user_type=user_type)
            session['guest_username'] = username
            session['user_type'] = 'guest'
            session['logged_in'] = True
            flash('Guest login successful!', 'success')
            return redirect(url_for('chat'))
        else:
            username_or_email = request.form.get('username') or request.form.get('email')
            password = request.form.get('password')

            if not username_or_email or not password:
                flash('Please enter both username/email and password', 'danger')
                return render_template('login.html', user_type=user_type)

            user = UserModel.query.filter(
                (UserModel.username == username_or_email) |
                (UserModel.email == username_or_email)
            ).first()

            if user and user.check_password(password.strip()):
                if not user.is_confirmed:
                    flash('Your account is pending admin confirmation. Please wait for approval.', 'warning')
                    return redirect(url_for('login', user_type='user'))
                login_user(user, remember=True)
                session['user_id'] = user.id
                session['user_type'] = 'user'
                session['logged_in'] = True
                flash('Login successful!', 'success')
                return redirect(url_for('chat'))

            flash('Invalid username or password')
    return render_template('login.html', user_type=user_type)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """
    Handle admin login.
    """
    from models import Admin as AdminModel
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please enter both email and password', 'danger')
            return render_template('admin_login.html')

        admin = AdminModel.query.filter_by(email=email).first()

        if admin and admin.check_password(password.strip()):
            login_user(admin, remember=True)
            session['user_id'] = admin.id
            session['user_type'] = 'admin'
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid username or password')
    return render_template('admin_login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handle user signup with validation.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not re.match(r'^[^@]+@wvsu\.edu\.ph$', email):
            flash('Email must be a wvsu.edu.ph email address', 'danger')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')

        existing_user_email = user_manager.get_user_by_email(email)
        if existing_user_email:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('login', user_type='user'))

        existing_user_username = user_manager.get_user_by_username(username)
        if existing_user_username:
            flash('Username already taken. Please choose another.', 'danger')
            return render_template('signup.html')

        # Create user with is_confirmed=False
        user = user_manager.create_user(username, email, password, 'user')
        # Set is_confirmed to False explicitly (in case create_user does not set it)
        user.is_confirmed = False
        user_manager.db.session.commit()

        flash('Account created! Please wait for admin confirmation before logging in.', 'info')
        return redirect(url_for('login', user_type='user'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    """
    Log out the current user or guest.
    """
    if current_user.is_authenticated:
        logout_user()
    if 'guest_username' in session:
        session.pop('guest_username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('welcome'))

@app.route('/chat')
def chat():
    """
    Render the chat page with user info and chat history.
    """
    from database import email_directory

    username = None
    role = session.get('user_type', 'guest')

    # Debug logging for role and authentication
    # app.logger.debug(f"User role in session: {role}")
    # app.logger.debug(f"Current user authenticated: {current_user.is_authenticated}")

    if current_user.is_authenticated:
        if role == 'admin':
            username = current_user.email
        elif role == 'user':
            username = current_user.username
        else:
            # Handle other user types safely
            if hasattr(current_user, 'username'):
                username = current_user.username
            elif hasattr(current_user, 'email'):
                username = current_user.email
            else:
                username = str(current_user.id)  # Fallback to user ID
    elif 'guest_username' in session:
        username = session['guest_username']
    else:
        return redirect(url_for('welcome'))

    session_date = request.args.get('session_date')
    chat_history = None
    chat_sessions_summary = None

    if current_user.is_authenticated and role == 'user':
        chat_sessions_summary = user_manager.get_chat_sessions_summary(current_user.id)
        if session_date:
            try:
                selected_date = datetime.strptime(session_date, "%Y-%m-%d").date()
            except ValueError:
                selected_date = None

            if selected_date:
                full_history = user_manager.get_chat_history(current_user.id)
                if selected_date in full_history:
                    chat_history = full_history[selected_date]
        else:
            chat_history = None

    emails = email_directory.get_all_emails()

    return render_template(
        'chat.html', username=username, role=role,
        chat_history=chat_history, chat_sessions_summary=chat_sessions_summary,
        emails=emails
    )

@app.route('/send_message', methods=['POST'])
def send_message():
    """
    Handle sending a message from the user and return chatbot response.
    """
    data = request.get_json()
    user_message = data.get('message', '')
    session_id = data.get('session_id', '')
    user_role = session.get('user_type', None)
    bot_response = chatbot.get_response(user_message, user_role=user_role)

    if current_user.is_authenticated and session_id:
        user_manager.add_chat_message(current_user.id, session_id, 'user', user_message)
        user_manager.add_chat_message(current_user.id, session_id, 'bot', bot_response)

    return jsonify({
        'response': bot_response,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    """
    Clear chat history for the current user.
    """
    user_manager.clear_chat_history(current_user.id)
    return jsonify({'status': 'success'})

@app.route('/get_chat_history')
@login_required
def get_chat_history():
    """
    Get chat history for the current user.
    """
    history = user_manager.get_chat_history(current_user.id)
    return jsonify(history)

@app.route('/get_chat_sessions_summary')
@login_required
def get_chat_sessions_summary():
    """
    Get chat sessions summary for sidebar display.
    """
    sessions = user_manager.get_chat_sessions_summary(current_user.id)
    return jsonify(sessions)

@app.route('/get_chat_session_history/<session_id>')
@login_required
def get_chat_session_history(session_id):
    """
    Get full chat history for a specific session.
    """
    history = user_manager.get_chat_session_history(current_user.id, session_id)
    return jsonify(history)

@app.route('/delete_chat_session/<session_id>', methods=['DELETE'])
@login_required
def delete_chat_session(session_id):
    """
    Delete a chat session and all its messages.
    """
    success = user_manager.delete_chat_session(current_user.id, session_id)
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Session not found or could not be deleted'}), 404

@app.route('/admin')
@login_required
def admin_dashboard():
    """
    Render the admin dashboard landing page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    # Get pending counts for badges
    pending_accounts = len(user_manager.get_pending_users())
    from models import Feedback
    pending_feedbacks = Feedback.query.count()

    return render_template('admin_dashboard.html', pending_accounts=pending_accounts, pending_feedbacks=pending_feedbacks)

@app.route('/admin/rules')
@login_required
def admin_rules():
    """
    Render the admin rules page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    rules = chatbot.rules
    guest_rules = chatbot.guest_rules

    # Add category to each rule if missing (default to 'soict' for user rules)
    def add_category(rules_list, default_category='soict'):
        new_list = []
        for rule in rules_list:
            if 'category' not in rule:
                rule['category'] = default_category
            new_list.append(rule)
        return new_list

    rules = add_category(rules, default_category='soict')
    guest_rules = add_category(guest_rules, default_category='guest')

    # Group rules by category for categorized display
    categorized_user_rules = {}
    categorized_guest_rules = {}

    for rule in rules:
        category = rule.get('category', 'soict')
        if category not in categorized_user_rules:
            categorized_user_rules[category] = []
        categorized_user_rules[category].append(rule)

    for rule in guest_rules:
        category = rule.get('category', 'guest')
        if category not in categorized_guest_rules:
            categorized_guest_rules[category] = []
        categorized_guest_rules[category].append(rule)

    return render_template('admin_rules.html',
                         rules=rules,
                         guest_rules=guest_rules,
                         categorized_user_rules=categorized_user_rules,
                         categorized_guest_rules=categorized_guest_rules)

@app.route('/admin/accounts')
@login_required
def admin_accounts():
    """
    Render the admin accounts page for managing user confirmations.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    pending_users = user_manager.get_pending_users()
    return render_template('admin_accounts.html', pending_users=pending_users)

@app.route('/admin/accounts/approve/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    """
    Approve a user's account.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    success = user_manager.confirm_user(user_id)
    if success:
        return jsonify({'status': 'success', 'message': 'User approved successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'User not found'})

@app.route('/admin/accounts/reject/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    """
    Reject a user's account (delete the user).
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    success = user_manager.reject_user(user_id)
    if success:
        return jsonify({'status': 'success', 'message': 'User rejected successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'User not found'})

@app.route('/admin/faqs')
@login_required
def admin_faqs():
    """
    Render the admin FAQs management page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    import os
    faqs_path = os.path.join(app.root_path, 'database', 'faqs.json')
    try:
        with open(faqs_path, 'r', encoding='utf-8') as f:
            faqs_list = json.load(f)
    except Exception as e:
        faqs_list = []
        app.logger.error(f"Failed to load faqs.json: {e}")

    return render_template('admin_faqs.html', info_list=faqs_list)

@app.route('/add_info', methods=['POST'])
@login_required
def add_info():
    """
    Add a new FAQ entry to faqs.json.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()

    if not question or not answer:
        return jsonify({'status': 'error', 'message': 'Question and answer are required'})

    import os
    faqs_path = os.path.join(app.root_path, 'database', 'faqs.json')
    try:
        with open(faqs_path, 'r', encoding='utf-8') as f:
            faqs_list = json.load(f)
    except Exception:
        faqs_list = []

    faqs_list.append({'question': question, 'answer': answer})

    try:
        with open(faqs_path, 'w', encoding='utf-8') as f:
            json.dump(faqs_list, f, indent=4)
        # Reload FAQs in chatbot memory
        chatbot.reload_faqs()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save FAQs: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/edit_info', methods=['POST'])
@login_required
def edit_info():
    """
    Edit an existing FAQ entry in faqs.json.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    info_id = data.get('info_id')
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()

    if info_id is None or not question or not answer:
        return jsonify({'status': 'error', 'message': 'ID, question, and answer are required'})

    import os
    faqs_path = os.path.join(app.root_path, 'database', 'faqs.json')
    try:
        with open(faqs_path, 'r', encoding='utf-8') as f:
            faqs_list = json.load(f)
    except Exception:
        faqs_list = []

    if info_id < 0 or info_id >= len(faqs_list):
        return jsonify({'status': 'error', 'message': 'Invalid FAQ ID'})

    faqs_list[info_id]['question'] = question
    faqs_list[info_id]['answer'] = answer

    try:
        with open(faqs_path, 'w', encoding='utf-8') as f:
            json.dump(faqs_list, f, indent=4)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save FAQs: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/delete_info', methods=['POST'])
@login_required
def delete_info():
    """
    Delete an FAQ entry from faqs.json.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    info_id = data.get('info_id')

    if info_id is None:
        return jsonify({'status': 'error', 'message': 'ID is required'})

    import os
    faqs_path = os.path.join(app.root_path, 'database', 'faqs.json')
    try:
        with open(faqs_path, 'r', encoding='utf-8') as f:
            faqs_list = json.load(f)
    except Exception:
        faqs_list = []

    if info_id < 0 or info_id >= len(faqs_list):
        return jsonify({'status': 'error', 'message': 'Invalid FAQ ID'})

    faqs_list.pop(info_id)

    try:
        with open(faqs_path, 'w', encoding='utf-8') as f:
            json.dump(faqs_list, f, indent=4)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save FAQs: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/admin/locations')
@login_required
def admin_locations():
    """
    Render the admin locations page.
    """
    import json
    import os

    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    # Load locations from database/locations/locations.json
    locations_path = os.path.join(app.root_path, 'database', 'locations', 'locations.json')
    try:
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)
    except Exception as e:
        locations = []
        app.logger.error(f"Failed to load locations.json: {e}")

    return render_template('admin_locations.html', locations=locations)

@app.route('/admin/visuals')
@login_required
def admin_visuals():
    """
    Render the admin visuals page.
    """
    import json
    import os

    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    # Load visuals from database/visuals/visuals.json
    visuals_path = os.path.join(app.root_path, 'database', 'visuals', 'visuals.json')
    try:
        with open(visuals_path, 'r', encoding='utf-8') as f:
            visuals = json.load(f)
    except Exception as e:
        visuals = []
        app.logger.error(f"Failed to load visuals.json: {e}")

    return render_template('admin_visuals.html', visuals=visuals)

@app.route('/add_location', methods=['POST'])
@login_required
def add_location():
    """
    Add a new location with images.
    """
    import json
    import os
    import uuid

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    keywords = request.form.get('keywords', '').strip()
    description = request.form.get('description', '').strip()
    user_type = request.form.get('user_type', 'both')

    if not keywords or not description:
        return jsonify({'status': 'error', 'message': 'Keywords and description are required'})

    # Process keywords as JSON array of strings, each string is a comma-separated set
    keywords_data = json.loads(keywords) if keywords else []
    keywords_list = []
    for set_str in keywords_data:
        if isinstance(set_str, str):
            set_list = [k.strip() for k in set_str.split(',') if k.strip()]
        elif isinstance(set_str, list):
            set_list = [k.strip() for k in set_str if k.strip()]
        else:
            set_list = []
        keywords_list.append(set_list)

    # Handle file uploads
    uploaded_files = request.files.getlist('images')
    image_urls = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            image_urls.append(f"uploads/locations/{unique_filename}")

    if not image_urls:
        return jsonify({'status': 'error', 'message': 'At least one image is required'})

    # Load existing locations
    locations_path = os.path.join(app.root_path, 'database', 'locations', 'locations.json')
    try:
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)
    except:
        locations = []

    # Create new location
    new_location = {
        'id': str(uuid.uuid4()),
        'keywords': keywords_list,
        'description': description,
        'user_type': user_type,
        'urls': image_urls,
        'url': image_urls[0]  # Primary image
    }

    locations.append(new_location)

    # Save updated locations
    try:
        with open(locations_path, 'w', encoding='utf-8') as f:
            json.dump(locations, f, indent=4)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save location: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/edit_location/<location_id>', methods=['POST'])
@login_required
def edit_location_with_id(location_id):
    """
    Edit an existing location with images.
    """
    import json
    import os
    import uuid

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    keywords = request.form.get('keywords', '').strip()
    description = request.form.get('description', '').strip()
    user_type = request.form.get('user_type', 'both')
    removed_images = json.loads(request.form.get('removedImages', '[]'))

    if not keywords or not description:
        return jsonify({'status': 'error', 'message': 'Keywords and description are required'})

    # Process keywords as JSON array of strings, each string is a comma-separated set
    import json
    keywords_data = json.loads(keywords) if keywords else []
    keywords_list = []
    for set_str in keywords_data:
        if isinstance(set_str, str):
            set_list = [k.strip() for k in set_str.split(',') if k.strip()]
        elif isinstance(set_str, list):
            set_list = [k.strip() for k in set_str if k.strip()]
        else:
            set_list = []
        keywords_list.append(set_list)

    # Load existing locations
    locations_path = os.path.join(app.root_path, 'database', 'locations', 'locations.json')
    try:
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)
    except:
        locations = []

    # Find location to edit
    location_to_edit = None
    for loc in locations:
        if str(loc.get('id')) == str(location_id):
            location_to_edit = loc
            break

    if not location_to_edit:
        return jsonify({'status': 'error', 'message': 'Location not found'})

    # Update location data
    location_to_edit['keywords'] = keywords_list
    location_to_edit['description'] = description
    location_to_edit['user_type'] = user_type

    # Handle image removal
    if 'urls' in location_to_edit:
        location_to_edit['urls'] = [url for url in location_to_edit['urls'] if url not in removed_images]

    if 'url' in location_to_edit and location_to_edit['url'] in removed_images:
        del location_to_edit['url']

    # Handle new image uploads
    uploaded_files = request.files.getlist('images')
    new_image_urls = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            new_image_urls.append(f"uploads/locations/{unique_filename}")

    # Add new images to existing ones
    if 'urls' not in location_to_edit:
        location_to_edit['urls'] = []

    location_to_edit['urls'].extend(new_image_urls)

    # Ensure primary url exists
    if not location_to_edit.get('url') and location_to_edit['urls']:
        location_to_edit['url'] = location_to_edit['urls'][0]

    # Save updated locations
    try:
        with open(locations_path, 'w', encoding='utf-8') as f:
            json.dump(locations, f, indent=4)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save location: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/delete_location', methods=['POST'])
@login_required
def delete_location():
    """
    Delete a location entry.
    """
    import json
    import os

    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    data = request.get_json()
    location_id = data.get('id')

    if not location_id:
        return jsonify({'status': 'error', 'message': 'ID is required'})

    locations_path = os.path.join(app.root_path, 'database', 'locations', 'locations.json')

    try:
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to load locations: {e}'})

    # Filter out the location to delete
    new_locations = [loc for loc in locations if str(loc.get('id')) != str(location_id)]

    if len(new_locations) == len(locations):
        return jsonify({'status': 'error', 'message': 'Location not found'})

    try:
        with open(locations_path, 'w', encoding='utf-8') as f:
            json.dump(new_locations, f, indent=4)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save locations: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/add_visual', methods=['POST'])
@login_required
def add_visual():
    """
    Add a new visual with images/videos.
    """
    import json
    import os
    import uuid

    app.logger.info(f"Request received: {request.method} {request.path}")

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    keywords = request.form.get('keywords', '').strip()
    description = request.form.get('description', '').strip()
    user_type = request.form.get('user_type', 'both')

    if not keywords or not description:
        return jsonify({'status': 'error', 'message': 'Keywords and description are required'})

    # Process keywords as JSON array of strings, each string is a comma-separated set
    keywords_data = json.loads(keywords) if keywords else []
    keywords_list = []
    for set_str in keywords_data:
        if isinstance(set_str, str):
            set_list = [k.strip() for k in set_str.split(',') if k.strip()]
        elif isinstance(set_str, list):
            set_list = [k.strip() for k in set_str if k.strip()]
        else:
            set_list = []
        keywords_list.append(set_list)

    # Handle file uploads
    uploaded_files = request.files.getlist('images')
    media_urls = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = re.sub(r'\.+', '.', filename)  # Replace multiple dots with single dot
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            media_urls.append(f"uploads/locations/{unique_filename}")

    if not media_urls:
        return jsonify({'status': 'error', 'message': 'At least one image or video is required'})

    # Load existing visuals
    visuals_path = os.path.join(app.root_path, 'database', 'visuals', 'visuals.json')
    try:
        with open(visuals_path, 'r', encoding='utf-8') as f:
            visuals = json.load(f)
    except:
        visuals = []

    # Create new visual
    new_visual = {
        'id': str(uuid.uuid4()),
        'keywords': keywords_list,
        'description': description,
        'user_type': user_type,
        'urls': media_urls,
        'url': media_urls[0]  # Primary media
    }

    visuals.append(new_visual)

    # Save updated visuals
    try:
        with open(visuals_path, 'w', encoding='utf-8') as f:
            json.dump(visuals, f, indent=4)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save visual: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/edit_visual/<visual_id>', methods=['POST'])
@login_required
def edit_visual_with_id(visual_id):
    """
    Edit an existing visual with images/videos.
    """
    import json
    import os
    import uuid

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    keywords = request.form.get('keywords', '').strip()
    description = request.form.get('description', '').strip()
    user_type = request.form.get('user_type', 'both')
    removed_images = json.loads(request.form.get('removedImages', '[]'))

    if not keywords or not description:
        return jsonify({'status': 'error', 'message': 'Keywords and description are required'})

    # Process keywords as JSON array of strings, each string is a comma-separated set
    keywords_data = json.loads(keywords) if keywords else []
    keywords_list = []
    for set_str in keywords_data:
        if isinstance(set_str, str):
            set_list = [k.strip() for k in set_str.split(',') if k.strip()]
        elif isinstance(set_str, list):
            set_list = [k.strip() for k in set_str if k.strip()]
        else:
            set_list = []
        keywords_list.append(set_list)

    # Load existing visuals
    visuals_path = os.path.join(app.root_path, 'database', 'visuals', 'visuals.json')
    try:
        with open(visuals_path, 'r', encoding='utf-8') as f:
            visuals = json.load(f)
    except:
        visuals = []

    # Find visual to edit
    visual_to_edit = None
    for vis in visuals:
        if str(vis.get('id')) == str(visual_id):
            visual_to_edit = vis
            break

    if not visual_to_edit:
        return jsonify({'status': 'error', 'message': 'Visual not found'})

    # Update visual data
    visual_to_edit['keywords'] = keywords_list
    visual_to_edit['description'] = description
    visual_to_edit['user_type'] = user_type

    # Handle image removal
    if 'urls' in visual_to_edit:
        visual_to_edit['urls'] = [url for url in visual_to_edit['urls'] if url not in removed_images]

    if 'url' in visual_to_edit and visual_to_edit['url'] in removed_images:
        del visual_to_edit['url']

    # Handle new media uploads
    uploaded_files = request.files.getlist('images')
    new_media_urls = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            new_media_urls.append(f"uploads/locations/{unique_filename}")

    # Add new media to existing ones
    if 'urls' not in visual_to_edit:
        visual_to_edit['urls'] = []

    visual_to_edit['urls'].extend(new_media_urls)

    # Ensure primary url exists
    if not visual_to_edit.get('url') and visual_to_edit['urls']:
        visual_to_edit['url'] = visual_to_edit['urls'][0]

    # Save updated visuals
    try:
        with open(visuals_path, 'w', encoding='utf-8') as f:
            json.dump(visuals, f, indent=4)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save visual: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/delete_visual', methods=['POST'])
@login_required
def delete_visual():
    """
    Delete a visual entry.
    """
    import json
    import os

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    visual_id = data.get('id')

    if not visual_id:
        return jsonify({'status': 'error', 'message': 'ID is required'})

    visuals_path = os.path.join(app.root_path, 'database', 'visuals', 'visuals.json')

    try:
        with open(visuals_path, 'r', encoding='utf-8') as f:
            visuals = json.load(f)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to load visuals: {e}'})

    # Filter out the visual to delete
    new_visuals = [vis for vis in visuals if str(vis.get('id')) != str(visual_id)]

    if len(new_visuals) == len(visuals):
        return jsonify({'status': 'error', 'message': 'Visual not found'})

    try:
        with open(visuals_path, 'w', encoding='utf-8') as f:
            json.dump(new_visuals, f, indent=4)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save visuals: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/admin/emails')
@login_required
def admin_emails():
    """
    Render the admin emails page.
    """
    from database import email_directory

    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    emails = email_directory.get_all_emails()

    return render_template('admin_emails.html', emails=emails)

@app.route('/add_rule', methods=['POST'])
@login_required
def add_rule():
    """
    Add a new rule.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    question = data.get('keywords', '').strip()  # JS sends 'keywords' as question
    response = data.get('response', '').strip()
    user_type = data.get('user_type', 'user')
    category = data.get('category', 'soict')

    if not question or not response:
        return jsonify({'status': 'error', 'message': 'Question and response are required'})

    try:
        added_id = chatbot.add_rule(question, response, user_type=user_type, category=category)
        return jsonify({'status': 'success', 'id': added_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/edit_rule', methods=['POST'])
@login_required
def edit_rule():
    """
    Edit an existing rule.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    rule_id = data.get('rule_id')
    question = data.get('keywords', '').strip()
    response = data.get('response', '').strip()
    user_type = data.get('user_type', 'user')

    if not rule_id or not question or not response:
        return jsonify({'status': 'error', 'message': 'Rule ID, question, and response are required'})

    try:
        edited = chatbot.edit_rule(rule_id, question, response, user_type=user_type)
        if edited:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Rule not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/delete_rule', methods=['POST'])
@login_required
def delete_rule():
    """
    Delete a rule.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    rule_id = data.get('rule_id')
    user_type = data.get('user_type', 'user')

    if not rule_id:
        return jsonify({'status': 'error', 'message': 'Rule ID is required'})

    try:
        deleted = chatbot.delete_rule(rule_id, user_type=user_type)
        if deleted:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Rule not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    """
    Add a new category (placeholder).
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    # Placeholder implementation
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
