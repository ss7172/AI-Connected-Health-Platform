from flask import Flask, app


def register_blueprints(app: Flask) -> None:
    """Register all route blueprints with URL prefixes."""

    from app.routes.auth import auth_bp
    from app.routes.patients import patients_bp
    from app.routes.departments import departments_bp
    from app.routes.doctors import doctors_bp
    from app.routes.appointments import appointments_bp
    from app.routes.visits import visits_bp
    from app.routes.billing import billing_bp
    from app.routes.documents import documents_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.pipeline import pipeline_bp
    from app.routes.assistant import assistant_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(patients_bp, url_prefix='/api/v1/patients')
    app.register_blueprint(departments_bp, url_prefix='/api/v1/departments')
    app.register_blueprint(doctors_bp, url_prefix='/api/v1/doctors')
    app.register_blueprint(appointments_bp, url_prefix='/api/v1/appointments')
    app.register_blueprint(visits_bp, url_prefix='/api/v1/visits')
    app.register_blueprint(billing_bp, url_prefix='/api/v1/billing')
    app.register_blueprint(documents_bp, url_prefix='/api/v1/documents')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')
    app.register_blueprint(pipeline_bp, url_prefix='/api/v1/pipeline')
    app.register_blueprint(assistant_bp, url_prefix='/api/v1/assistant')

