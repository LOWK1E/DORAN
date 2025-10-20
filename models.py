from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Note: column name is 'password' in MySQL
    is_confirmed = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=False)
    Password_hash = db.Column(db.String(255), nullable=False)  # Note: capital P in MySQL

    def set_password(self, password):
        self.Password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.Password_hash, password)

    def get_id(self):
        return str(self.id)

class ChatMessage(db.Model):
    __tablename__ = 'chatmessages'  # Note: lowercase in MySQL
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(11), nullable=False)  # Note: varchar in MySQL
    session_id = db.Column(db.String(36), nullable=False)
    Sender_type = db.Column(db.String(10), nullable=False)  # Note: capital S in MySQL
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class EmailDirectory(db.Model):
    __tablename__ = 'email directory'  # Note: space in MySQL table name
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    school = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_id = db.Column(db.Integer, nullable=False)  # Note: capital U in MySQL
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    is_done = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def formatted_timestamp(self):
        return self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
