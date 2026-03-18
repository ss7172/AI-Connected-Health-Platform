from typing import Optional
from flask_jwt_extended import create_access_token
from app.extensions import db
from app.models.user import User


class AuthService:
    """Handles authentication logic: login, register, profile lookup."""

    @staticmethod
    def login(email: str, password: str) -> dict:
        """
        Authenticate user and return access token.

        Args:
            email: User's email/username
            password: Plain text password

        Returns:
            Dict with access_token and user data

        Raises:
            ValueError: If credentials are invalid or account is inactive
        """
        user = User.query.filter_by(email=email).first()

        if not user:
            raise ValueError("Invalid credentials")

        if not user.check_password(password):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        access_token = create_access_token(identity=str(user.id))

        return {
            'access_token': access_token,
            'user': user.to_dict()
        }

    @staticmethod
    def register(email: str, password: str, full_name: str, role: str) -> dict:
        """
        Register a new staff user. Admin only.

        Args:
            email: Login username
            password: Plain text password (will be hashed)
            full_name: Display name
            role: One of admin, doctor, front_desk

        Returns:
            Dict with created user data

        Raises:
            ValueError: If email already exists or role is invalid
        """
        VALID_ROLES = ['admin', 'doctor', 'front_desk']

        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {VALID_ROLES}")

        existing = User.query.filter_by(email=email).first()
        if existing:
            raise ValueError(f"User with email '{email}' already exists")

        user = User(
            email=email,
            full_name=full_name,
            role=role,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return {'user': user.to_dict()}

    @staticmethod
    def get_current_user(user_id: int) -> Optional[User]:
        """
        Fetch user by ID for /me endpoint.

        Args:
            user_id: User ID from JWT token

        Returns:
            User object or None
        """
        return User.query.get(user_id)