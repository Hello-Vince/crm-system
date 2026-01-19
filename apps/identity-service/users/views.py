"""
Authentication views for JWT-based login.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import User


def create_jwt_token(user: User) -> str:
    """
    Create a JWT token for the given user.
    """
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'role': user.role,
        'company_id': str(user.company.id) if user.company else None,
        'exp': datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token.
    Returns payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@api_view(['POST'])
def login_view(request: Request) -> Response:
    """
    Login endpoint - accepts email and password, returns JWT token.
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {'error': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate user
    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if not user.is_active:
            return Response(
                {'error': 'User account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate JWT token
    token = create_jwt_token(user)

    # Return token and user info
    return Response({
        'token': token,
        'user': {
            'id': str(user.id),
            'email': user.email,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'role': user.role,
            'companyId': str(user.company.id) if user.company else None,
            'companyName': user.company.name if user.company else None,
        }
    })


@api_view(['GET'])
def me_view(request: Request) -> Response:
    """
    Get current user info from JWT token.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response(
            {'error': 'Authorization header missing or invalid'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token = auth_header.replace('Bearer ', '')
    payload = decode_jwt_token(token)

    if not payload:
        return Response(
            {'error': 'Invalid or expired token'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        user_id = uuid.UUID(payload['user_id'])
        user = User.objects.select_related('company').get(id=user_id)
    except (User.DoesNotExist, ValueError, KeyError):
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'user': {
            'id': str(user.id),
            'email': user.email,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'role': user.role,
            'companyId': str(user.company.id) if user.company else None,
            'companyName': user.company.name if user.company else None,
        }
    })
