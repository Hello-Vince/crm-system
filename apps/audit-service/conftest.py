"""
Pytest configuration for audit-service tests.
"""
import os
import sys
from pathlib import Path

# Set Django settings module to test settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audit_project.test_settings')

# Add the service root to Python path
SERVICE_DIR = Path(__file__).parent
sys.path.insert(0, str(SERVICE_DIR))

# Add shared-python library to path
LIBS_DIR = SERVICE_DIR.parent.parent / 'libs' / 'shared-python'
sys.path.insert(0, str(LIBS_DIR))

import django
django.setup()
