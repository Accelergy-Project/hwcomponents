"""Minimal setup.py to ensure hwcomponents._version_scheme is importable during build."""
import sys
import os
from pathlib import Path

# Add current directory to Python path so hwcomponents._version_scheme can be imported
# This must happen before setuptools-scm tries to import the version scheme
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Also ensure we can import hwcomponents as a module
hwcomponents_dir = current_dir / "hwcomponents"
if str(hwcomponents_dir.parent) not in sys.path:
    sys.path.insert(0, str(hwcomponents_dir.parent))

from setuptools import setup

setup()
