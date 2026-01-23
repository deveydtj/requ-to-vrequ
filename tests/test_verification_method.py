#!/usr/bin/env python3
"""
Pytest tests for Verification_Method field functionality.

This test suite validates that the generate_verification_yaml.py script correctly:
1. Adds Verification_Method: Test to newly generated Verification items
2. Positions Verification_Method as the last key in generated Verification blocks
3. Preserves non-duplication behavior (doesn't add Verification_Method to existing Verifications)
4. Doesn't add Verification_Method to Requirement items

Target Python version: 3.10.0+
"""

import sys
import os
import subprocess

from generate_verification_yaml import (
    parse_items,
    generate_verification_items,
    build_global_key_order,
)

from conftest import get_script_path


def test_verification_method_added_to_new_items(temp_yaml_file):
    """Test that Verification_Method: Test is added to newly generated Verification items."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Render the dashboard
  Text: |
    (U) The system shall render the dashboard.
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    result = generate_verification_items(items)
    
    # Find the generated Verification item
    verification = None
    for item in result:
        if item.get("Type") in ["Verification", "DMGR Verification Requirement", "BRDG Verification Requirement"]:
            verification = item
            break
    
    assert verification is not None, "Should generate a Verification item"
    assert "Verification_Method" in verification, "Verification item should have Verification_Method field"
    assert verification["Verification_Method"] == "Test", "Verification_Method should be 'Test'"


def test_verification_method_is_last_key(temp_yaml_file):
    """Test that Verification_Method is positioned as the last key in the global key order."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Render the dashboard
  Text: |
    (U) The system shall render the dashboard.
  Traced_To: TRACE.1
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    result = generate_verification_items(items)
    key_order = build_global_key_order(result)
    
    # Verification_Method should be in key_order
    assert "Verification_Method" in key_order, "Verification_Method should be in key order"
    
    # Verification_Method should be the last key
    assert key_order[-1] == "Verification_Method", f"Verification_Method should be last, but got: {key_order}"


def test_verification_method_end_to_end(temp_yaml_file):
    """Test end-to-end that Verification_Method appears in output and is positioned last."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Render the dashboard
  Text: |
    (U) The system shall render the dashboard.
  Verified_By: 
  Traced_To: TRACE.1
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    # Run the script
    script_path = get_script_path()
    result = subprocess.run(
        [sys.executable, script_path, input_path, output_path],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Read output and verify
    with open(output_path, 'r', encoding='utf-8') as f:
        output_content = f.read()
    
    # Parse output to check structure
    output_items = parse_items(output_path)
    
    # Find the Verification item
    verification = None
    for item in output_items:
        if item.get("Type") in ["Verification", "DMGR Verification Requirement", "BRDG Verification Requirement"]:
            verification = item
            break
    
    assert verification is not None, "Should have a Verification item in output"
    assert "Verification_Method" in verification, "Verification should have Verification_Method field"
    assert verification["Verification_Method"] == "Test", "Verification_Method should be 'Test'"
    
    # Check that Verification_Method appears in the output content
    assert "Verification_Method: Test" in output_content, "Output should contain 'Verification_Method: Test'"
    
    # Verify that Verification_Method appears after Traced_To in the output
    # Extract the Verification block from the output
    verification_start = output_content.find("- Type: Verification")
    if verification_start == -1:
        verification_start = output_content.find("- Type: DMGR Verification Requirement")
    if verification_start == -1:
        verification_start = output_content.find("- Type: BRDG Verification Requirement")
    
    assert verification_start != -1, "Should find Verification block in output"
    
    # Find the next item or end of file
    next_item = output_content.find("\n- Type:", verification_start + 1)
    if next_item == -1:
        verification_block = output_content[verification_start:]
    else:
        verification_block = output_content[verification_start:next_item]
    
    # Find positions of Traced_To and Verification_Method
    traced_to_pos = verification_block.find("Traced_To:")
    verification_method_pos = verification_block.find("Verification_Method:")
    
    assert traced_to_pos != -1, "Verification block should contain Traced_To"
    assert verification_method_pos != -1, "Verification block should contain Verification_Method"
    assert verification_method_pos > traced_to_pos, "Verification_Method should appear after Traced_To"
    
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_dmgr_verification_has_verification_method(temp_yaml_file):
    """Test that DMGR Verification Requirements also get Verification_Method."""
    test_yaml = """- Type: Requirement
  ID: REQU.DMGR.FEATURE.1
  Name: Render the status
  Text: |
    (U) The system shall render the status.
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    result = generate_verification_items(items)
    
    # Find the DMGR Verification item
    dmgr_verification = None
    for item in result:
        if item.get("Type") == "DMGR Verification Requirement":
            dmgr_verification = item
            break
    
    assert dmgr_verification is not None, "Should generate a DMGR Verification Requirement"
    assert "Verification_Method" in dmgr_verification, "DMGR Verification should have Verification_Method field"
    assert dmgr_verification["Verification_Method"] == "Test", "Verification_Method should be 'Test'"


def test_brdg_verification_has_verification_method(temp_yaml_file):
    """Test that BRDG Verification Requirements also get Verification_Method."""
    test_yaml = """- Type: Requirement
  ID: REQU.BRDG.CONFIG.1
  Name: Set timeout to 30
  Text: |
    (U) The system shall set timeout to 30.
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    result = generate_verification_items(items)
    
    # Find the BRDG Verification item
    brdg_verification = None
    for item in result:
        if item.get("Type") == "BRDG Verification Requirement":
            brdg_verification = item
            break
    
    assert brdg_verification is not None, "Should generate a BRDG Verification Requirement"
    assert "Verification_Method" in brdg_verification, "BRDG Verification should have Verification_Method field"
    assert brdg_verification["Verification_Method"] == "Test", "Verification_Method should be 'Test'"


def test_requirement_does_not_get_verification_method(temp_yaml_file):
    """Test that Requirement items do NOT get Verification_Method field."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Render the dashboard
  Text: |
    (U) The system shall render the dashboard.
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    result = generate_verification_items(items)
    
    # Find the Requirement item
    requirement = None
    for item in result:
        if item.get("Type") == "Requirement":
            requirement = item
            break
    
    assert requirement is not None, "Should have a Requirement item"
    assert "Verification_Method" not in requirement, "Requirement should NOT have Verification_Method field"


def test_non_duplication_preserved(temp_yaml_file):
    """Test that existing Verification items are not duplicated and don't get Verification_Method."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Render the dashboard
  Text: |
    (U) The system shall render the dashboard.
  Verified_By: VREQU.TEST.1
  Traced_To: TRACE.1

- Type: Verification
  Parent_Req: 
  ID: VREQU.TEST.1
  Name: Verify the dashboard is rendered
  Text: |
    (U) Verify the system renders the dashboard.
  Verified_By: 
  Traced_To: TRACE.1
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    # Run the script
    script_path = get_script_path()
    result = subprocess.run(
        [sys.executable, script_path, input_path, output_path],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Read output
    with open(output_path, 'r', encoding='utf-8') as f:
        output_content = f.read()
    
    # Count how many Verification blocks exist
    verification_count = output_content.count("- Type: Verification")
    
    # Should have exactly 1 Verification item (not duplicated)
    assert verification_count == 1, f"Should have exactly 1 Verification item, got {verification_count}"
    
    # The existing Verification should NOT have Verification_Method added to it
    # (since it already existed in the input)
    output_items = parse_items(output_path)
    verifications = [item for item in output_items if item.get("Type") == "Verification"]
    
    assert len(verifications) == 1, f"Should have 1 Verification item, got {len(verifications)}"
    
    # The existing verification should not have Verification_Method 
    # (since the script preserves existing items as-is via patching)
    existing_verification = verifications[0]
    
    # Assert that existing Verification does NOT have Verification_Method field added
    assert "Verification_Method" not in existing_verification, \
        "Existing Verification should NOT have Verification_Method field added"
    
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_verification_method_in_base_key_order():
    """Test that Verification_Method is included in BASE_KEY_ORDER."""
    from generate_verification_yaml import BASE_KEY_ORDER
    
    assert "Verification_Method" in BASE_KEY_ORDER, "Verification_Method should be in BASE_KEY_ORDER"
    assert BASE_KEY_ORDER[-1] == "Verification_Method", "Verification_Method should be the last key in BASE_KEY_ORDER"
