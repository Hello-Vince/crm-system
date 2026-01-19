"""
Test settings for identity service.
Uses SQLite in-memory database for fast, isolated tests.
"""
from .settings import *  # noqa: F401, F403

# Override database to use SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable debug mode in tests
DEBUG = False
