import os
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
# SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """
    Initialize the database with the Flask application.
    """
    try:
        # Database configuration
        db_dir = os.path.join(os.path.dirname(__file__), 'instance')
        os.makedirs(db_dir, exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "quantumhub.db")}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Initialize SQLAlchemy with the app
        db.init_app(app)

        # Create all database tables
        with app.app_context():
            db.create_all()
            logging.info("Database tables created successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        # Note: In a production environment, you might want to handle this differently
        raise

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def get_id(self):
        return str(self.id)

class JobResult(db.Model):
    __tablename__ = 'job_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    hardware_counts = db.Column(db.Text, nullable=True)
    expectation_value = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('job_results', lazy=True))

