from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth_service import AuthService
from app.utils.helpers import error_response, success_response
from app.utils.decorators import role_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.
    POST /api/v1/auth/login
    Body: { email, password }
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return error_response("Email and password are required", 400)

    try:
        result = AuthService.login(email, password)
        return success_response(result, 200)
    except ValueError as e:
        return error_response(str(e), 401)


@auth_bp.route('/register', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def register():
    """
    Register a new staff user. Admin only.
    POST /api/v1/auth/register
    Body: { email, password, full_name, role }
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    required_fields = ['email', 'password', 'full_name', 'role']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return error_response(f"Missing required fields: {missing}", 400)

    try:
        result = AuthService.register(
            email=data['email'].strip(),
            password=data['password'],
            full_name=data['full_name'].strip(),
            role=data['role'].strip(),
        )
        return success_response(result, 201)
    except ValueError as e:
        return error_response(str(e), 400)


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """
    Get current authenticated user profile.
    GET /api/v1/auth/me
    """
    user_id = int(get_jwt_identity())
    user = AuthService.get_current_user(user_id)

    if not user:
        return error_response("User not found", 404)

    return success_response({'user': user.to_dict()}, 200)