#!/usr/bin/env python3
"""
Database initialization script for Railway deployment.
This script creates all necessary tables and default admin user.
"""

import os
from app import app
from extensions import db
from models import Admin
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize the database with tables and default data."""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully")

        # Create default admin user if not exists
        if not Admin.query.filter_by(email='admin@wvsu.edu.ph').first():
            admin = Admin(
                email='admin@wvsu.edu.ph',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin@wvsu.edu.ph / admin123")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    init_database()
