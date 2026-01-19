"""Pytest configuration for shared-python tests."""

import sys
from pathlib import Path


# Add shared-python library to the Python path
lib_path = Path(__file__).resolve().parent
sys.path.insert(0, str(lib_path))
