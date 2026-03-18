from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Register all route blueprints with URL prefixes."""

    from app.routes.auth import auth_bp
    from app.routes.patients import patients_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(patients_bp, url_prefix='/api/v1/patients')