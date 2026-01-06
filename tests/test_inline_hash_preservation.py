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
import tempfile

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import parse_items


def test_single_line_name_with_hash():
    """
    Test that a single-line Name field containing '#' is preserved intact.
    """
    print("Testing single-line Name with hash...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Show deveydtj/requ-to-vrequ#1 indicator
  Text: |
    Test text.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
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
        
        print(f"✓ Name preserved correctly: '{name}'")
        
    finally:
        os.remove(temp_path)


def test_single_line_text_with_hash_pattern():
    """
    Test that a single-line Text field containing '###.###' is preserved intact.
    """
    print("\nTesting single-line Text with hash pattern...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.2
  Name: Display version
  Text: The system shall display ###.### in the header
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
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
        
        print(f"✓ Text preserved correctly: '{text}'")
        
    finally:
        os.remove(temp_path)


def test_fullline_comment_still_captured():
    """
    Test that full-line comments (starting with '#') are still captured correctly.
    """
    print("\nTesting full-line comment capture...")
    
    test_yaml = """# This is a full-line comment
- Type: Requirement
  ID: REQU.TEST.3
  Name: Test
  # This is an in-item comment
  Text: Test text
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
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
        
        print("✓ Full-line comments preserved correctly")
        
    finally:
        os.remove(temp_path)


def test_hash_in_name_not_comment():
    """
    Regression test: ensure '#' in Name is not treated as a comment delimiter.
    """
    print("\nTesting hash in Name is not comment delimiter...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.4
  Name: Issue #123 fix
  Text: Test
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
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
        
        print(f"✓ Hash in Name not treated as comment: '{name}'")
        
    finally:
        os.remove(temp_path)


def test_multiple_hashes_preserved():
    """
    Test that multiple '#' characters in a single line are all preserved.
    """
    print("\nTesting multiple hashes preserved...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.5
  Name: Display #1, #2, and #3 items
  Text: Render items #1 and #2 with color #FFFFFF
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
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
        
        print(f"✓ Multiple hashes preserved in Name: '{name}'")
        print(f"✓ Multiple hashes preserved in Text: '{text}'")
        
    finally:
        os.remove(temp_path)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running inline hash preservation tests")
    print("=" * 60)
    
    try:
        test_single_line_name_with_hash()
        test_single_line_text_with_hash_pattern()
        test_fullline_comment_still_captured()
        test_hash_in_name_not_comment()
        test_multiple_hashes_preserved()
        
        print("\n" + "=" * 60)
        print("All inline hash preservation tests passed! ✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
