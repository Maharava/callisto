#!/usr/bin/env python
"""Test runner for Callisto."""
import os
import sys
import pytest

if __name__ == "__main__":
    # Add current directory to path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    args = [
        "-v",  # Verbose output
        "--cov=callisto",  # Coverage for callisto package
        "--cov-report=term",  # Terminal coverage report
        "--cov-report=html:coverage_html",  # HTML coverage report
        "tests"  # Test directory
    ]
    
    # Add any command line arguments passed to this script
    args.extend(sys.argv[1:])
    
    # Run tests
    result = pytest.main(args)
    
    sys.exit(result)
