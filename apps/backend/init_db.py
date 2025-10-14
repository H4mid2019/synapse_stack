"""Initialize database tables from models"""
from app_factory import create_app
from database import db

app = create_app('operations')

with app.app_context():
    print("Creating all tables...")
    db.create_all()
    print("Done! Tables created successfully.")
