"""Configuration for pytest."""
import os
import sys
import pytest

# Add parent directory to path so modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
