"""
Shared JWT authentication utilities for all Python services.
Provides centralized JWT handling to avoid code duplication.
"""

import os
import uuid
from typing import Any

import jwt


class AuthenticatedUser:
    """
    Represents an authenticated user from JWT token.
    Compatible with Django's User object interface.
    Stores IDs as strings to ensure JSON serialization compatibility.
    """

    def __init__(
        self,
        user_id: str,
        email: str,
        role: str,
        company_id: str | None,
        visible_company_ids: list[str] | None = None,
    ):
        self.id = user_id
        self.user_id = user_id  # Alias for compatibility
        self.email = email
        self.role = role
        self.company_id = company_id
        # All company IDs this user can access (own + ancestors + descendants)
        self.visible_company_ids = visible_company_ids or []
        self.is_authenticated = True
        self.is_system_admin = role == "SYSTEM_ADMIN"
        self.is_company_admin = role == "COMPANY_ADMIN"

    def __str__(self) -> str:
        return f"User({self.email}, {self.role})"


class AnonymousUser:
    """
    Represents an unauthenticated user.
    Compatible with Django's AnonymousUser.
    """

    def __init__(self):
        self.id = None
        self.user_id = None
        self.email = None
        self.role = None
        self.company_id = None
        self.visible_company_ids = []
        self.is_authenticated = False
        self.is_system_admin = False
        self.is_company_admin = False

    def __str__(self) -> str:
        return "AnonymousUser"


def get_jwt_secret() -> str:
    """
    Get JWT secret from environment.
    Raises error if not configured for security.
    """
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
    return secret


def decode_jwt_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token.
    Returns payload if valid, None otherwise.
    """
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token


def get_user_from_token(token: str) -> AuthenticatedUser | AnonymousUser:
    """
    Extract user information from JWT token.
    Returns AuthenticatedUser if valid, AnonymousUser if invalid.
    IDs are kept as strings for JSON serialization compatibility.
    """
    payload = decode_jwt_token(token)
    if not payload:
        return AnonymousUser()

    try:
        user_id = payload.get("user_id")
        if not user_id:
            return AnonymousUser()
        # Validate it's a valid UUID format but keep as string
        uuid.UUID(user_id)

        email = payload.get("email")
        role = payload.get("role", "USER")
        company_id = payload.get("company_id")  # Already a string or None
        # Validate company_id if present
        if company_id:
            uuid.UUID(company_id)

        # Get visible company IDs (all companies user can access in hierarchy)
        visible_company_ids = payload.get("visible_company_ids", [])

        return AuthenticatedUser(user_id, email, role, company_id, visible_company_ids)
    except (ValueError, KeyError):
        return AnonymousUser()


class JWTAuthenticationMiddleware:
    """
    Django middleware to extract JWT from Authorization header and attach user to request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check multiple possible header formats for compatibility
        auth_header = (
            request.META.get("HTTP_AUTHORIZATION", "")
            or request.META.get("HTTP_AUTHORISATION", "")  # British spelling
            or request.headers.get("Authorization", "")
            or request.headers.get("authorization", "")
        )

        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            request.user = get_user_from_token(token)
        else:
            request.user = AnonymousUser()

        response = self.get_response(request)
        return response
