import os
from flask import Flask
from app.config import config
from app.extensions import db, migrate, jwt, cors


def create_app(config_name: str = 'development') -> Flask:
    """
    Application factory. Creates and configures the Flask app.
    
    Args:
        config_name: One of 'development', 'production', 'testing'
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Import models so Flask-Migrate can detect all tables
    with app.app_context():
        from app.models import (
            User, Department, Doctor, Patient,
            Appointment, Visit, BillingRecord,
            BillingItem, PatientDocument
        )

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    return app