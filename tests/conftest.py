"""
Pytest configuration and shared fixtures for requ-to-vrequ test suite.

This module provides common test fixtures and utilities used across multiple test files.
"""

import sys
import os
import tempfile
import pytest

# Add parent directory to path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_yaml_file():
    """
    Fixture to create and cleanup temporary YAML files.
    
    Usage:
        def test_something(temp_yaml_file):
            yaml_content = "- Type: Requirement\\n  ID: REQU.1"
            temp_path = temp_yaml_file(yaml_content)
            # temp_path is automatically cleaned up after the test
    
    Yields:
        A function that creates a temporary YAML file and returns its path.
        The file is automatically deleted after the test completes.
    """
    temp_files = []
    
    def _create_temp_file(content):
        """Create a temporary YAML file with the given content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
            f.write(content)
        temp_files.append(temp_path)
        return temp_path
    
    yield _create_temp_file
    
    # Cleanup all created temporary files
    for path in temp_files:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass  # Ignore cleanup errors


def get_script_path():
    """
    Get the absolute path to the main generate_verification_yaml.py script.
    
    Returns:
        str: Absolute path to the script
    """
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'generate_verification_yaml.py'
    )


# Make get_script_path available as a fixture as well
@pytest.fixture
def script_path():
    """
    Fixture that provides the path to the main script.
    
    Usage:
        def test_something(script_path):
            result = subprocess.run([sys.executable, script_path, ...])
    """
    return get_script_path()
