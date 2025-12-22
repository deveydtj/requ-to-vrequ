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
from typing import List

# Add parent directory to path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conftest import get_script_path, temp_yaml_file


def extract_requirement_blocks(output_content: str) -> List[List[str]]:
    """
    Extract all Requirement blocks from the output content.
    
    Returns a list of blocks, where each block is a list of lines
    representing one Requirement item.
    """
    lines = output_content.split('\n')
    requirement_blocks = []
    current_block = []
    in_requirement = False
    
    for line in lines:
        if line.lstrip().startswith('- Type:'):
            # Save previous block if it was a requirement
            if in_requirement and current_block:
                requirement_blocks.append(current_block)
            
            # Check if this is a new requirement
            in_requirement = 'Requirement' in line and 'Verification' not in line
            current_block = [line] if in_requirement else []
        elif in_requirement:
            current_block.append(line)
    
    # Don't forget the last block
    if in_requirement and current_block:
        requirement_blocks.append(current_block)
    
    return requirement_blocks


def count_verified_by_in_block(block: List[str]) -> int:
    """Count the number of Verified_By fields in a block of lines."""
    return sum(1 for line in block if 'Verified_By:' in line)


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
    
    # Extract requirement blocks
    requirement_blocks = extract_requirement_blocks(output_content)
    assert len(requirement_blocks) == 1, f"Expected 1 requirement block, found {len(requirement_blocks)}"
    
    # Count Verified_By occurrences in the requirement block
    verified_by_count = count_verified_by_in_block(requirement_blocks[0])
    
    assert verified_by_count == 1, \
        f"Expected exactly 1 Verified_By field, found {verified_by_count}.\n" \
        f"Requirement block:\n" + '\n'.join(requirement_blocks[0])
    
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
    
    # Extract requirement blocks
    requirement_blocks = extract_requirement_blocks(output_content)
    assert len(requirement_blocks) == 1, f"Expected 1 requirement block, found {len(requirement_blocks)}"
    
    requirement_block = requirement_blocks[0]
    
    # Count Verified_By occurrences in the requirement block
    verified_by_count = count_verified_by_in_block(requirement_block)
    
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
    
    # The outputs should be identical (idempotent), ignoring trailing whitespace
    # Normalize by stripping trailing whitespace from each line
    def normalize_output(text):
        return '\n'.join(line.rstrip() for line in text.splitlines())
    
    normalized1 = normalize_output(output1)
    normalized2 = normalize_output(output2)
    
    assert normalized1 == normalized2, \
        "Running the script twice should produce identical output (idempotency).\n" \
        f"First run output length: {len(output1)}\n" \
        f"Second run output length: {len(output2)}"
    
    # Also verify no duplicate Verified_By in the second run
    requirement_blocks = extract_requirement_blocks(output2)
    assert len(requirement_blocks) >= 1, "Expected at least one requirement block"
    
    verified_by_count = count_verified_by_in_block(requirement_blocks[0])
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
    
    # Extract all requirement blocks
    requirement_blocks = extract_requirement_blocks(output_content)
    
    # Verify we found the expected number of requirements
    assert len(requirement_blocks) == 3, \
        f"Expected 3 requirement blocks, found {len(requirement_blocks)}"
    
    # Each requirement should have exactly one Verified_By
    for idx, block in enumerate(requirement_blocks):
        verified_by_count = count_verified_by_in_block(block)
        assert verified_by_count == 1, \
            f"Requirement {idx + 1} has {verified_by_count} Verified_By fields, expected 1.\n" \
            f"Block:\n" + '\n'.join(block)
    
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)
