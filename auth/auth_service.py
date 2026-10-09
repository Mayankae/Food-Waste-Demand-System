import datetime
import re
import jwt
from functools import wraps
from flask import request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from auth.models import UserModel
from two_factor_authentication.hooks import (
    is_2fa_required_for_user,
    initiate_2fa_challenge,
    validate_2fa_challenge
)

class AuthService:
    """Authentication and Authorization Service supporting Role-Based Access Control."""

    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY_HOURS = 24

    @classmethod
    def generate_token(cls, user):
        """Generate JWT bearer token containing user identity and role."""
        payload = {
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=cls.JWT_EXPIRY_HOURS)
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm=cls.JWT_ALGORITHM)

    @classmethod
    def decode_token(cls, token):
        """Decode and validate JWT bearer token."""
        try:
            return jwt.decode(token, Config.SECRET_KEY, algorithms=[cls.JWT_ALGORITHM])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    @classmethod
    def register(cls, full_name, email, password, role="Viewer"):
        """
        Create a new user account with validation and secure password hashing.
        """
        full_name = str(full_name).strip()
        email = str(email).strip().lower()
        password = str(password).strip()
        role = str(role).strip()

        # Validation
        if not full_name or len(full_name) < 2:
            return {"success": False, "error": "Full name must be at least 2 characters long", "status_code": 400}

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, email):
            return {"success": False, "error": "Please provide a valid email address", "status_code": 400}

        if len(password) < 6:
            return {"success": False, "error": "Password must be at least 6 characters long", "status_code": 400}

        valid_roles = ["Admin", "Analyst", "Viewer"]
        if role not in valid_roles:
            role = "Viewer"

        # Check existing user
        existing = UserModel.get_by_email(email)
        if existing:
            return {"success": False, "error": f"An account with email '{email}' already exists. Please sign in.", "status_code": 409}

        # Create user
        p_hash = generate_password_hash(password)
        user_id = UserModel.create_user(email, full_name, p_hash, role)

        return {
            "success": True,
            "message": f"User account created successfully as {role}! Please sign in.",
            "user_id": user_id,
            "email": email,
            "role": role,
            "status_code": 201
        }

    @classmethod
    def login(cls, email, password):
        """
        Authenticate user by email and password.
        Initiates 2-Step OTP Verification on valid password.
        """
        email = str(email).strip().lower()
        user = UserModel.get_by_email(email)
        if not user:
            return {"success": False, "error": "Invalid email or password", "status_code": 401}

        if not check_password_hash(user["password_hash"], password):
            return {"success": False, "error": "Invalid email or password", "status_code": 401}

        # ----------------------------------------------------------------------
        # 2-STEP AUTHENTICATION (OTP VERIFICATION)
        # Flow: Password verified -> generate OTP -> return OTP challenge
        # ----------------------------------------------------------------------
        if is_2fa_required_for_user(user):
            challenge = initiate_2fa_challenge(user)
            return {
                "success": True,
                "step": "OTP_REQUIRED",
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "message": f"Password verified! A 6-digit OTP has been generated for {user['email']}.",
                "expires_in_seconds": challenge.get("expires_in_seconds", 300),
                "demo_otp": challenge.get("demo_otp"),
                "status_code": 200
            }

        # Fallback if 2FA is globally toggled off
        token = cls.generate_token(user)
        return {
            "success": True,
            "step": "AUTHENTICATED",
            "token": token,
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"]
            },
            "status_code": 200
        }

    @classmethod
    def verify_2fa_step(cls, email, otp_code):
        """
        Validates OTP code for Step 2 of the login pipeline.
        """
        email = str(email).strip().lower()
        user = UserModel.get_by_email(email)
        if not user:
            return {"success": False, "error": "User account not found", "status_code": 404}

        is_valid, msg = validate_2fa_challenge(email, otp_code)
        if not is_valid:
            return {"success": False, "error": msg, "status_code": 400}

        # OTP verified! Issue final authenticated JWT session token
        token = cls.generate_token(user)
        return {
            "success": True,
            "step": "AUTHENTICATED",
            "token": token,
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"]
            },
            "message": "Authentication successful! Access granted.",
            "status_code": 200
        }

def require_auth(allowed_roles=None):
    """
    Role-Based Access Control decorator.
    Usage:
        @require_auth()                      # Any authenticated user
        @require_auth(["Admin"])             # Admin only
        @require_auth(["Admin", "Analyst"])  # Admin and Analyst
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Unauthorized: Missing or invalid authentication token"}), 401

            token = auth_header.split(" ")[1]
            payload = AuthService.decode_token(token)
            if not payload:
                return jsonify({"error": "Unauthorized: Session has expired or token is invalid"}), 401

            if allowed_roles and payload.get("role") not in allowed_roles:
                return jsonify({
                    "error": f"Forbidden: Insufficient permissions for role '{payload.get('role')}'. Required roles: {allowed_roles}",
                    "required_roles": allowed_roles,
                    "your_role": payload.get("role")
                }), 403

            request.current_user = payload
            return f(*args, **kwargs)
        return decorated_function
    return decorator
