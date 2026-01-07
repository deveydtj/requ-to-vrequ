#!/usr/bin/env python3
"""
End-to-end acceptance test for inline hash preservation issue.

This test validates all acceptance criteria from the issue:
1. Name with GitHub issue reference preserved
2. Text with version pattern preserved  
3. Full-line comments still captured and emitted
4. Generated Verification items also preserve hash characters
"""

import sys
import os

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import parse_items, generate_verification_items


def test_acceptance_criteria(temp_yaml_file):
    """
    Test all acceptance criteria from the issue.
    """
    # Create test input with all acceptance criteria scenarios
    test_yaml = """# Preamble comment
- Type: Requirement
  Parent_Req: 
  ID: REQU.DISPLAY.1
  Name: Show deveydtj/requ-to-vrequ#1 indicator
  Text: The system shall display ###.### in the header
  Verified_By: 
  Traced_To: 

# Full-line comment before second requirement
- Type: Requirement
  Parent_Req: 
  ID: REQU.PROCESS.2
  Name: Process issue references like #42 and #99
  Text: |
    (U) The system shall process:
    # Reference format: owner/repo#number
    # Examples: user/project#5, org/app#123
  Verified_By: 
  Traced_To: 
"""
    
    temp_path = temp_yaml_file(test_yaml)
    
    # Parse items
    items = parse_items(temp_path)
    
    # Find REQU.DISPLAY.1
    req1 = None
    for item in items:
        if item.get("ID") == "REQU.DISPLAY.1":
            req1 = item
            break
    
    assert req1 is not None, "REQU.DISPLAY.1 not found"
    
    # ACCEPTANCE CRITERION 1: Name with GitHub reference preserved
    name1 = req1.get("Name", "")
    expected_name1 = "Show deveydtj/requ-to-vrequ#1 indicator"
    assert name1 == expected_name1, \
        f"AC1 FAILED: Expected Name '{expected_name1}', got '{name1}'"
    
    # ACCEPTANCE CRITERION 2: Text with version pattern preserved
    text1 = req1.get("Text", "")
    expected_text1 = "The system shall display ###.### in the header"
    assert text1 == expected_text1, \
        f"AC2 FAILED: Expected Text '{expected_text1}', got '{text1}'"
    
    # ACCEPTANCE CRITERION 3: Full-line comments captured
    # Note: Comments before the first item are standalone, but comments between items
    # are stored in the previous item's _order field (per parser design)
    standalone_comment_count = sum(1 for item in items if "_comment" in item and len(item) == 1)
    assert standalone_comment_count >= 1, \
        f"AC3 FAILED: Expected at least 1 standalone comment, got {standalone_comment_count}"
    
    # Check that preamble comment exists
    preamble_found = any(
        item.get("_comment", "") == "# Preamble comment"
        for item in items if "_comment" in item and len(item) == 1
    )
    assert preamble_found, "AC3 FAILED: Preamble comment not found"
    
    # Check that in-document comment exists (in req1's _order field)
    comment_in_order_found = False
    for item in items:
        if item.get("ID") == "REQU.DISPLAY.1":
            for kind, payload in item.get("_order", []):
                if kind == "comment" and "Full-line comment before second requirement" in payload:
                    comment_in_order_found = True
                    break
    assert comment_in_order_found, "AC3 FAILED: Comment before REQU.PROCESS.2 not found in _order"
    
    # Find REQU.PROCESS.2 and check multiline text with hash lines
    req2 = None
    for item in items:
        if item.get("ID") == "REQU.PROCESS.2":
            req2 = item
            break
    
    assert req2 is not None, "REQU.PROCESS.2 not found"
    
    name2 = req2.get("Name", "")
    assert "#42" in name2 and "#99" in name2, \
        f"Name should contain '#42' and '#99', got '{name2}'"
    
    text2 = req2.get("Text", "")
    assert "# Reference format:" in text2, \
        f"Multiline block should preserve lines starting with '#', got '{text2}'"
    assert "owner/repo#number" in text2, \
        f"Multiline block should preserve '#' in content, got '{text2}'"
    
    # Generate verification items
    items_with_ver = generate_verification_items(items)
    
    # Find VREQU.DISPLAY.1
    ver1 = None
    for item in items_with_ver:
        if item.get("ID") == "VREQU.DISPLAY.1":
            ver1 = item
            break
    
    assert ver1 is not None, "VREQU.DISPLAY.1 not generated"
    
    # Verification Name should preserve hash from original
    ver_name1 = ver1.get("Name", "")
    assert "#1" in ver_name1, \
        f"Verification Name should preserve '#1', got '{ver_name1}'"
    
    # Verification Text should preserve hash pattern from original
    ver_text1 = ver1.get("Text", "")
    assert "###.###" in ver_text1, \
        f"Verification Text should preserve '###.###', got '{ver_text1}'"
    
    # Find VREQU.PROCESS.2
    ver2 = None
    for item in items_with_ver:
        if item.get("ID") == "VREQU.PROCESS.2":
            ver2 = item
            break
    
    assert ver2 is not None, "VREQU.PROCESS.2 not generated"
    
    ver_name2 = ver2.get("Name", "")
    assert "#42" in ver_name2 and "#99" in ver_name2, \
        f"Verification Name should preserve multiple hashes, got '{ver_name2}'"
    
    ver_text2 = ver2.get("Text", "")
    assert "# Reference format:" in ver_text2, \
        f"Verification Text should preserve multiline hash lines, got '{ver_text2}'"


def _create_temp_file_standalone(content):
    """Standalone temp file creator for when pytest is not available."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        return f.name


if __name__ == '__main__':
    try:
        import pytest
        pytest.main([__file__, '-v'])
    except ImportError:
        # Fallback to basic test runner if pytest is not available
        print("pytest not available, running tests directly")
        test_acceptance_criteria(_create_temp_file_standalone)
        print("All tests passed!")
