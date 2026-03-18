from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User


def role_required(allowed_roles: list[str]):
    """
    Decorator that restricts route access by role.
    
    Usage:
        @role_required(['admin', 'doctor'])
        def my_route():
            ...
    
    Args:
        allowed_roles: List of roles permitted to access the route
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # First verify a valid JWT exists
            verify_jwt_in_request()

            # Get the user ID stored in the token
            user_id = int(get_jwt_identity())

            # Look up the actual user in the database
            user = User.query.get(user_id)

            if not user:
                return jsonify(error="User not found"), 404

            if not user.is_active:
                return jsonify(error="Account is deactivated"), 403

            if user.role not in allowed_roles:
                return jsonify(
                    error=f"Access denied. Required roles: {allowed_roles}"
                ), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator