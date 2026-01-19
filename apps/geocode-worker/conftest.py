"""Pytest configuration for geocode-worker tests."""

import sys
from pathlib import Path


# Add shared-python library to the Python path
libs_path = Path(__file__).resolve().parent.parent.parent / "libs" / "shared-python"
sys.path.insert(0, str(libs_path))

# Add the geocode-worker package to the Python path
worker_path = Path(__file__).resolve().parent
sys.path.insert(0, str(worker_path))
