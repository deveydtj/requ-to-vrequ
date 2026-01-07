#!/usr/bin/env python3
"""
Test script to ensure inline '#' characters are preserved in single-line values.

This validates the fix for issue #1: Parser should not strip inline `#` from single-line values.

Test cases:
1. Single-line Name with '#' is preserved
2. Single-line Text with '###.###' is preserved  
3. Full-line comments are still captured as comments
4. Regression test: GitHub issue reference in Name
5. Regression test: Version pattern in Text
"""

import sys
import os

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import parse_items


def test_single_line_name_with_hash(temp_yaml_file):
    """
    Test that a single-line Name field containing '#' is preserved intact.
    """
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Show deveydtj/requ-to-vrequ#1 indicator
  Text: |
    Test text.
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    
    # Find the requirement item
    req_item = None
    for item in items:
        if item.get("ID") == "REQU.TEST.1":
            req_item = item
            break
    
    assert req_item is not None, "Requirement item not found"
    
    # Check that the Name contains the full string including '#1'
    name = req_item.get("Name", "")
    expected_name = "Show deveydtj/requ-to-vrequ#1 indicator"
    assert name == expected_name, \
        f"Expected Name '{expected_name}', got '{name}'"


def test_single_line_text_with_hash_pattern(temp_yaml_file):
    """
    Test that a single-line Text field containing '###.###' is preserved intact.
    """
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.2
  Name: Display version
  Text: The system shall display ###.### in the header
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    
    # Find the requirement item
    req_item = None
    for item in items:
        if item.get("ID") == "REQU.TEST.2":
            req_item = item
            break
    
    assert req_item is not None, "Requirement item not found"
    
    # Check that the Text contains the full string including '###.###'
    text = req_item.get("Text", "")
    expected_text = "The system shall display ###.### in the header"
    assert text == expected_text, \
        f"Expected Text '{expected_text}', got '{text}'"


def test_fullline_comment_still_captured(temp_yaml_file):
    """
    Test that full-line comments (starting with '#') are still captured correctly.
    """
    test_yaml = """# This is a full-line comment
- Type: Requirement
  ID: REQU.TEST.3
  Name: Test
  # This is an in-item comment
  Text: Test text
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    
    # Should have 2 items: 1 standalone comment, 1 requirement
    assert len(items) == 2, f"Expected 2 items, got {len(items)}"
    
    # First item should be a standalone comment
    assert "_comment" in items[0], "First item should be a comment"
    assert items[0]["_comment"] == "# This is a full-line comment", \
        f"Comment text mismatch: {items[0]['_comment']}"
    
    # Second item should be the requirement with an in-item comment in _order
    req_item = items[1]
    assert req_item.get("ID") == "REQU.TEST.3", "Requirement not found"
    
    # Check that the in-item comment is in _order
    order = req_item.get("_order", [])
    comment_found = False
    for kind, payload in order:
        if kind == "comment" and "in-item comment" in payload:
            comment_found = True
            break
    
    assert comment_found, "In-item comment not found in _order"


def test_hash_in_name_not_comment(temp_yaml_file):
    """
    Regression test: ensure '#' in Name is not treated as a comment delimiter.
    """
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.4
  Name: Issue #123 fix
  Text: Test
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    
    req_item = None
    for item in items:
        if item.get("ID") == "REQU.TEST.4":
            req_item = item
            break
    
    assert req_item is not None, "Requirement item not found"
    
    name = req_item.get("Name", "")
    assert "#123" in name, f"Name should contain '#123', got '{name}'"
    assert name == "Issue #123 fix", f"Full Name should be preserved, got '{name}'"
    
    # Check that _order does NOT have a comment entry for this line
    order = req_item.get("_order", [])
    name_entry_count = 0
    for kind, payload in order:
        if kind == "key" and payload == "Name":
            name_entry_count += 1
    
    # Should have exactly one Name entry in _order
    assert name_entry_count == 1, \
        f"Expected 1 Name entry in _order, got {name_entry_count}"


def test_multiple_hashes_preserved(temp_yaml_file):
    """
    Test that multiple '#' characters in a single line are all preserved.
    """
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.5
  Name: Display #1, #2, and #3 items
  Text: Render items #1 and #2 with color #FFFFFF
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    
    req_item = None
    for item in items:
        if item.get("ID") == "REQU.TEST.5":
            req_item = item
            break
    
    assert req_item is not None, "Requirement item not found"
    
    name = req_item.get("Name", "")
    expected_name = "Display #1, #2, and #3 items"
    assert name == expected_name, \
        f"Expected Name '{expected_name}', got '{name}'"
    
    text = req_item.get("Text", "")
    expected_text = "Render items #1 and #2 with color #FFFFFF"
    assert text == expected_text, \
        f"Expected Text '{expected_text}', got '{text}'"


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
        test_single_line_name_with_hash(_create_temp_file_standalone)
        test_single_line_text_with_hash_pattern(_create_temp_file_standalone)
        test_fullline_comment_still_captured(_create_temp_file_standalone)
        test_hash_in_name_not_comment(_create_temp_file_standalone)
        test_multiple_hashes_preserved(_create_temp_file_standalone)
        print("All tests passed!")
