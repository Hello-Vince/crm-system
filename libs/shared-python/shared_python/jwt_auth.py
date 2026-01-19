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
    """
    def __init__(self, user_id: uuid.UUID, email: str, role: str, company_id: uuid.UUID | None):
        self.id = user_id
        self.user_id = user_id  # Alias for compatibility
        self.email = email
        self.role = role
        self.company_id = company_id
        self.is_authenticated = True
        self.is_system_admin = role == 'SYSTEM_ADMIN'
        self.is_company_admin = role == 'COMPANY_ADMIN'

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
    secret = os.getenv('JWT_SECRET_KEY')
    if not secret:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
    return secret


def decode_jwt_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token.
    Returns payload if valid, None otherwise.
    """
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token


def get_user_from_token(token: str) -> AuthenticatedUser | AnonymousUser:
    """
    Extract user information from JWT token.
    Returns AuthenticatedUser if valid, AnonymousUser if invalid.
    """
    payload = decode_jwt_token(token)
    if not payload:
        return AnonymousUser()

    try:
        user_id = uuid.UUID(payload.get('user_id'))
        email = payload.get('email')
        role = payload.get('role', 'USER')
        company_id_str = payload.get('company_id')
        company_id = uuid.UUID(company_id_str) if company_id_str else None

        return AuthenticatedUser(user_id, email, role, company_id)
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
            request.META.get('HTTP_AUTHORIZATION', '') or
            request.META.get('HTTP_AUTHORISATION', '') or  # British spelling
            request.headers.get('Authorization', '') or
            request.headers.get('authorization', '')
        )

        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            request.user = get_user_from_token(token)
        else:
            request.user = AnonymousUser()

        response = self.get_response(request)
        return response