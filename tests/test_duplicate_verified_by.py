"""
Tests for the duplicate Verified_By field issue.

This test suite validates that:
1. A Requirement contains exactly one Verified_By field after script execution
2. Running the script multiple times produces identical output (idempotency)
3. Existing Verified_By values are replaced, not duplicated
"""

import sys
import os
import subprocess
import tempfile

# Add parent directory to path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conftest import get_script_path, temp_yaml_file


def test_no_duplicate_verified_by_new_requirement(temp_yaml_file):
    """
    Test that a new Requirement (without existing Verified_By) gets exactly one Verified_By field.
    """
    input_content = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Test Requirement
  Text: |
    The system shall do something.
"""
    
    input_path = temp_yaml_file(input_content)
    output_path = input_path + ".out"
    
    # Run the script
    script_path = get_script_path()
    result = subprocess.run(
        ["python", script_path, input_path, output_path],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Read the output
    with open(output_path, 'r') as f:
        output_content = f.read()
    
    # Count occurrences of "Verified_By:" in the Requirement block
    # Split by item markers to isolate the Requirement block
    lines = output_content.split('\n')
    requirement_block = []
    in_requirement = False
    
    for line in lines:
        if line.lstrip().startswith('- Type:') and 'Requirement' in line:
            in_requirement = True
            requirement_block = [line]
        elif in_requirement:
            if line.lstrip().startswith('- Type:'):
                # Next item started
                break
            requirement_block.append(line)
    
    # Count Verified_By occurrences in the requirement block
    verified_by_count = sum(1 for line in requirement_block if 'Verified_By:' in line)
    
    assert verified_by_count == 1, \
        f"Expected exactly 1 Verified_By field, found {verified_by_count}.\n" \
        f"Requirement block:\n{''.join(requirement_block)}"
    
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_no_duplicate_verified_by_existing_field(temp_yaml_file):
    """
    Test that a Requirement with an existing Verified_By field doesn't get a duplicate.
    The existing value should be replaced, not duplicated.
    """
    input_content = """- Type: Requirement
  ID: REQU.TEST.2
  Name: Test Requirement
  Text: |
    The system shall do something.
  Verified_By: OLD.VALUE
"""
    
    input_path = temp_yaml_file(input_content)
    output_path = input_path + ".out"
    
    # Run the script
    script_path = get_script_path()
    result = subprocess.run(
        ["python", script_path, input_path, output_path],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Read the output
    with open(output_path, 'r') as f:
        output_content = f.read()
    
    # Count occurrences of "Verified_By:" in the Requirement block
    lines = output_content.split('\n')
    requirement_block = []
    in_requirement = False
    
    for line in lines:
        if line.lstrip().startswith('- Type:') and 'Requirement' in line:
            in_requirement = True
            requirement_block = [line]
        elif in_requirement:
            if line.lstrip().startswith('- Type:'):
                # Next item started
                break
            requirement_block.append(line)
    
    # Count Verified_By occurrences in the requirement block
    verified_by_count = sum(1 for line in requirement_block if 'Verified_By:' in line)
    
    assert verified_by_count == 1, \
        f"Expected exactly 1 Verified_By field, found {verified_by_count}.\n" \
        f"Requirement block:\n" + '\n'.join(requirement_block)
    
    # Verify the value was updated to the new verification ID
    verified_by_line = next((line for line in requirement_block if 'Verified_By:' in line), None)
    assert verified_by_line is not None
    assert 'VREQU.TEST.2' in verified_by_line, \
        f"Expected Verified_By to contain 'VREQU.TEST.2', got: {verified_by_line}"
    assert 'OLD.VALUE' not in verified_by_line, \
        f"Old value should be replaced, not kept: {verified_by_line}"
    
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_idempotency_multiple_runs(temp_yaml_file):
    """
    Test that running the script multiple times produces identical output (idempotent behavior).
    """
    input_content = """- Type: Requirement
  ID: REQU.TEST.3
  Name: Test Requirement
  Text: |
    The system shall do something.
"""
    
    input_path = temp_yaml_file(input_content)
    output_path_1 = input_path + ".out1"
    output_path_2 = input_path + ".out2"
    
    script_path = get_script_path()
    
    # First run
    result1 = subprocess.run(
        ["python", script_path, input_path, output_path_1],
        capture_output=True,
        text=True
    )
    assert result1.returncode == 0, f"First run failed: {result1.stderr}"
    
    # Second run - use output of first run as input
    result2 = subprocess.run(
        ["python", script_path, output_path_1, output_path_2],
        capture_output=True,
        text=True
    )
    assert result2.returncode == 0, f"Second run failed: {result2.stderr}"
    
    # Read both outputs
    with open(output_path_1, 'r') as f:
        output1 = f.read()
    
    with open(output_path_2, 'r') as f:
        output2 = f.read()
    
    # The outputs should be identical (idempotent)
    assert output1 == output2, \
        "Running the script twice should produce identical output (idempotency).\n" \
        f"First run output length: {len(output1)}\n" \
        f"Second run output length: {len(output2)}"
    
    # Also verify no duplicate Verified_By in the second run
    lines = output2.split('\n')
    requirement_block = []
    in_requirement = False
    
    for line in lines:
        if line.lstrip().startswith('- Type:') and 'Requirement' in line:
            in_requirement = True
            requirement_block = [line]
        elif in_requirement:
            if line.lstrip().startswith('- Type:'):
                break
            requirement_block.append(line)
    
    verified_by_count = sum(1 for line in requirement_block if 'Verified_By:' in line)
    assert verified_by_count == 1, \
        f"Expected exactly 1 Verified_By field after second run, found {verified_by_count}"
    
    # Cleanup
    for path in [output_path_1, output_path_2]:
        if os.path.exists(path):
            os.remove(path)


def test_multiple_requirements_no_duplicates(temp_yaml_file):
    """
    Test that multiple Requirements each get exactly one Verified_By field.
    """
    input_content = """- Type: Requirement
  ID: REQU.TEST.4
  Name: First Requirement
  Text: |
    The system shall do something.

- Type: Requirement
  ID: REQU.TEST.5
  Name: Second Requirement
  Text: |
    The system shall do another thing.
  Verified_By: EXISTING.VALUE

- Type: Requirement
  ID: REQU.TEST.6
  Name: Third Requirement
  Text: |
    The system shall do a third thing.
"""
    
    input_path = temp_yaml_file(input_content)
    output_path = input_path + ".out"
    
    # Run the script
    script_path = get_script_path()
    result = subprocess.run(
        ["python", script_path, input_path, output_path],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Read the output
    with open(output_path, 'r') as f:
        output_content = f.read()
    
    # Split into items and check each requirement
    lines = output_content.split('\n')
    current_block = []
    requirement_blocks = []
    in_item = False
    
    for line in lines:
        if line.lstrip().startswith('- Type:'):
            if in_item and 'Requirement' in current_block[0]:
                requirement_blocks.append(current_block)
            current_block = [line]
            in_item = True
        elif in_item:
            current_block.append(line)
    
    # Don't forget the last block
    if in_item and current_block and 'Requirement' in current_block[0]:
        requirement_blocks.append(current_block)
    
    # Each requirement should have exactly one Verified_By
    for idx, block in enumerate(requirement_blocks):
        verified_by_count = sum(1 for line in block if 'Verified_By:' in line)
        assert verified_by_count == 1, \
            f"Requirement {idx + 1} has {verified_by_count} Verified_By fields, expected 1.\n" \
            f"Block:\n" + '\n'.join(block)
    
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)
