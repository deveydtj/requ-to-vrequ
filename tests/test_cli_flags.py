#!/usr/bin/env python3
"""
Pytest tests for CLI flags (--no-sequence and --sequence-log).

This test suite validates that the CLI flags work correctly:
1. --no-sequence disables ID sequencing
2. --sequence-log prints sequencing information to stdout
3. Flags can be combined or used independently
4. Default behavior preserves sequencing when flags are not used

Target Python version: 3.10.0+
"""

import sys
import os
import tempfile
import subprocess
import pytest


# Fixtures and helper functions

@pytest.fixture
def temp_yaml_file():
    """Fixture to create and cleanup temporary YAML files."""
    temp_files = []
    
    def _create_temp_file(content):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        temp_path = f.name
        f.write(content)
        f.close()
        temp_files.append(temp_path)
        return temp_path
    
    yield _create_temp_file
    
    # Cleanup
    for path in temp_files:
        if os.path.exists(path):
            os.remove(path)


def get_script_path():
    """Get the path to the main script."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'generate_verification_yaml.py'
    )


def test_default_sequencing(temp_yaml_file):
    """Test that default behavior (no flags) enables sequencing."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First requirement
  Text: |
    (U) Test requirement.
  Verified_By: 

- Type: Requirement
  ID: REQU.TEST.X
  Name: Second requirement
  Text: |
    (U) Test requirement.
  Verified_By: 

- Type: Requirement
  ID: REQU.TEST.X
  Name: Third requirement
  Text: |
    (U) Test requirement.
  Verified_By: 
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    try:
        # Run without flags
        result = subprocess.run(
            [sys.executable, get_script_path(), input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        
        with open(output_path, 'r') as f:
            output = f.read()
        
        # Verify sequencing happened (should have .2 and .3)
        assert "REQU.TEST.1" in output
        assert "REQU.TEST.2" in output
        assert "REQU.TEST.3" in output
        
        # Verify .X is not in ID lines
        lines = output.split('\n')
        for line in lines:
            if 'ID: REQU.TEST.' in line:
                assert '.X' not in line, f"Should not have .X in requirements: {line}"
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_no_sequence_flag(temp_yaml_file):
    """Test that --no-sequence flag disables sequencing."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First requirement
  Text: |
    (U) Test requirement.
  Verified_By: 

- Type: Requirement
  ID: REQU.TEST.X
  Name: Second requirement
  Text: |
    (U) Test requirement.
  Verified_By: 

- Type: Requirement
  ID: REQU.TEST.X
  Name: Third requirement
  Text: |
    (U) Test requirement.
  Verified_By: 
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    try:
        # Run with --no-sequence
        result = subprocess.run(
            [sys.executable, get_script_path(), '--no-sequence', input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        
        with open(output_path, 'r') as f:
            output = f.read()
        
        # Verify sequencing did NOT happen (should still have .X)
        assert "REQU.TEST.1" in output
        assert "REQU.TEST.X" in output, "Should still have .X (not sequenced)"
        
        # Should NOT have .2 or .3
        assert "REQU.TEST.2" not in output, "Should not have .2 (sequencing disabled)"
        assert "REQU.TEST.3" not in output, "Should not have .3 (sequencing disabled)"
        
        # Verification IDs should also use .X
        assert "VREQU.TEST.X" in output, "Verification should also use .X"
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_sequence_log_flag(temp_yaml_file):
    """Test that --sequence-log flag prints sequencing information."""
    test_yaml = """- Type: Requirement
  ID: REQU.DMGR.TEST.1
  Name: Render first
  Text: |
    (U) The system shall render the first item.
  Verified_By: 

- Type: Requirement
  ID: REQU.DMGR.TEST.X
  Name: Render second
  Text: |
    (U) The system shall render the second item.
  Verified_By: 

- Type: Requirement
  ID: REQU.BRDG.TEST.5
  Name: Set first
  Text: |
    (U) The system shall set the first value.
  Verified_By: 

- Type: Requirement
  ID: REQU.BRDG.TEST.X
  Name: Set second
  Text: |
    (U) The system shall set the second value.
  Verified_By: 
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    try:
        # Run with --sequence-log
        result = subprocess.run(
            [sys.executable, get_script_path(), '--sequence-log', input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        
        # Check stdout for sequencing information
        stdout = result.stdout
        
        # Should have header
        assert "ID Sequencing Summary:" in stdout, "Should have summary header"
        
        # Should show the sequenced IDs
        assert "REQU.DMGR.TEST.X -> REQU.DMGR.TEST.2" in stdout, "Should show DMGR sequencing"
        assert "REQU.BRDG.TEST.X -> REQU.BRDG.TEST.6" in stdout, "Should show BRDG sequencing"
        
        # Verify output file still has sequenced IDs
        with open(output_path, 'r') as f:
            output = f.read()
        
        assert "REQU.DMGR.TEST.2" in output
        assert "REQU.BRDG.TEST.6" in output
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_no_sequence_with_sequence_log(temp_yaml_file):
    """Test that --sequence-log has no effect when --no-sequence is used."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First requirement
  Text: |
    (U) Test requirement.
  Verified_By: 

- Type: Requirement
  ID: REQU.TEST.X
  Name: Second requirement
  Text: |
    (U) Test requirement.
  Verified_By: 
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    try:
        # Run with both flags
        result = subprocess.run(
            [sys.executable, get_script_path(), '--no-sequence', '--sequence-log', 
             input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        
        # Should not print any sequencing info (since sequencing is disabled)
        stdout = result.stdout
        assert "ID Sequencing Summary:" not in stdout, \
            "Should not show summary when sequencing is disabled"
        
        # Verify output has .X (not sequenced)
        with open(output_path, 'r') as f:
            output = f.read()
        
        assert "REQU.TEST.X" in output
        assert "REQU.TEST.2" not in output
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_sequence_log_with_no_placeholders(temp_yaml_file):
    """Test that --sequence-log handles files with no placeholder IDs gracefully."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First requirement
  Text: |
    (U) Test requirement.
  Verified_By: 

- Type: Requirement
  ID: REQU.TEST.2
  Name: Second requirement
  Text: |
    (U) Test requirement.
  Verified_By: 
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    try:
        # Run with --sequence-log
        result = subprocess.run(
            [sys.executable, get_script_path(), '--sequence-log', input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        
        # Should not print summary if there's nothing to sequence
        stdout = result.stdout
        assert "ID Sequencing Summary:" not in stdout, \
            "Should not show summary when there are no placeholders"
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

