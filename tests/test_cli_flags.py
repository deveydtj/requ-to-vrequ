#!/usr/bin/env python3
"""
Test script for CLI flags (--no-sequence and --sequence-log).

This script validates that the CLI flags work correctly:
1. --no-sequence disables ID sequencing
2. --sequence-log prints sequencing information to stdout
3. Flags can be combined or used independently
4. Default behavior preserves sequencing when flags are not used
"""

import sys
import os
import tempfile
import subprocess
import traceback


def get_script_path():
    """Get the path to the main script."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'generate_verification_yaml.py'
    )


def test_default_sequencing():
    """Test that default behavior (no flags) enables sequencing."""
    print("Testing default behavior (sequencing enabled)...")
    
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    output_path = None
    try:
        output_path = input_path.replace('.yaml', '_output.yaml')
        
        # Run without flags
        result = subprocess.run(
            [sys.executable, get_script_path(), input_path, output_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            assert False, "Script execution failed"
        
        with open(output_path, 'r') as f:
            output = f.read()
        
        # Verify sequencing happened (should have .2 and .3)
        assert "REQU.TEST.1" in output, "Should have .1"
        assert "REQU.TEST.2" in output, "Should have .2 (sequenced)"
        assert "REQU.TEST.3" in output, "Should have .3 (sequenced)"
        
        # Count occurrences of .X (should only be in comments or none)
        # Requirements section should not have .X
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if 'ID: REQU.TEST.' in line:
                assert '.X' not in line, f"Should not have .X in requirements: {line}"
        
        print("✓ Default sequencing test passed")
        
    finally:
        os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)


def test_no_sequence_flag():
    """Test that --no-sequence flag disables sequencing."""
    print("\nTesting --no-sequence flag...")
    
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    output_path = None
    try:
        output_path = input_path.replace('.yaml', '_output.yaml')
        
        # Run with --no-sequence
        result = subprocess.run(
            [sys.executable, get_script_path(), '--no-sequence', input_path, output_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            assert False, "Script execution failed"
        
        with open(output_path, 'r') as f:
            output = f.read()
        
        # Verify sequencing did NOT happen (should still have .X)
        assert "REQU.TEST.1" in output, "Should have .1"
        assert "REQU.TEST.X" in output, "Should still have .X (not sequenced)"
        
        # Should NOT have .2 or .3
        assert "REQU.TEST.2" not in output, "Should not have .2 (sequencing disabled)"
        assert "REQU.TEST.3" not in output, "Should not have .3 (sequencing disabled)"
        
        # Verification IDs should also use .X
        assert "VREQU.TEST.X" in output, "Verification should also use .X"
        
        print("✓ --no-sequence flag test passed")
        
    finally:
        os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)


def test_sequence_log_flag():
    """Test that --sequence-log flag prints sequencing information."""
    print("\nTesting --sequence-log flag...")
    
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    output_path = None
    try:
        output_path = input_path.replace('.yaml', '_output.yaml')
        
        # Run with --sequence-log
        result = subprocess.run(
            [sys.executable, get_script_path(), '--sequence-log', input_path, output_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            assert False, "Script execution failed"
        
        # Check stdout for sequencing information
        stdout = result.stdout
        
        # Should have header
        assert "ID Sequencing Summary:" in stdout, "Should have summary header"
        
        # Should show the sequenced IDs
        assert "REQU.DMGR.TEST.X -> REQU.DMGR.TEST.2" in stdout, \
            "Should show DMGR sequencing"
        assert "REQU.BRDG.TEST.X -> REQU.BRDG.TEST.6" in stdout, \
            "Should show BRDG sequencing"
        
        # Verify output file still has sequenced IDs
        with open(output_path, 'r') as f:
            output = f.read()
        
        assert "REQU.DMGR.TEST.2" in output, "Output should have DMGR.TEST.2"
        assert "REQU.BRDG.TEST.6" in output, "Output should have BRDG.TEST.6"
        
        print("✓ --sequence-log flag test passed")
        
    finally:
        os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)


def test_no_sequence_with_sequence_log():
    """Test that --sequence-log has no effect when --no-sequence is used."""
    print("\nTesting --no-sequence with --sequence-log (log should be empty)...")
    
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    output_path = None
    try:
        output_path = input_path.replace('.yaml', '_output.yaml')
        
        # Run with both flags
        result = subprocess.run(
            [sys.executable, get_script_path(), '--no-sequence', '--sequence-log', 
             input_path, output_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            assert False, "Script execution failed"
        
        # Should not print any sequencing info (since sequencing is disabled)
        stdout = result.stdout
        assert "ID Sequencing Summary:" not in stdout, \
            "Should not show summary when sequencing is disabled"
        
        # Verify output has .X (not sequenced)
        with open(output_path, 'r') as f:
            output = f.read()
        
        assert "REQU.TEST.X" in output, "Should still have .X"
        assert "REQU.TEST.2" not in output, "Should not have .2"
        
        print("✓ Combined flags test passed")
        
    finally:
        os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)


def test_sequence_log_with_no_placeholders():
    """Test that --sequence-log handles files with no placeholder IDs gracefully."""
    print("\nTesting --sequence-log with no placeholder IDs...")
    
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    output_path = None
    try:
        output_path = input_path.replace('.yaml', '_output.yaml')
        
        # Run with --sequence-log
        result = subprocess.run(
            [sys.executable, get_script_path(), '--sequence-log', input_path, output_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            assert False, "Script execution failed"
        
        # Should not print summary if there's nothing to sequence
        stdout = result.stdout
        assert "ID Sequencing Summary:" not in stdout, \
            "Should not show summary when there are no placeholders"
        
        print("✓ No placeholders test passed")
        
    finally:
        os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)


def main():
    """Run all CLI flag tests."""
    print("=" * 60)
    print("Running CLI flag tests")
    print("=" * 60)
    
    try:
        test_default_sequencing()
        test_no_sequence_flag()
        test_sequence_log_flag()
        test_no_sequence_with_sequence_log()
        test_sequence_log_with_no_placeholders()
        
        print("\n" + "=" * 60)
        print("All CLI flag tests passed! ✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
