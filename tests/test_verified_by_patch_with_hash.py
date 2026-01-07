#!/usr/bin/env python3
"""
Test suite for Verified_By patching behavior with hash characters in values.

This validates the fix for the issue "Ensure Verified_By patching and item 
boundary detection remain correct with `#` in values".

Test cases:
1. Single-line Name with '#' - Verified_By insertion works correctly
2. Single-line Text with '#' - Verified_By insertion works correctly
3. Block scalar Text with leading '#' lines - Verified_By insertion works correctly
4. Existing Verified_By replacement with '#' in Name
5. Existing Verified_By replacement with '#' in Text (single-line)
6. Existing Verified_By replacement with '#' in Text (block scalar)
7. Multiple Requirements with various '#' patterns
"""

import sys
import os
import tempfile

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import apply_verified_by_patch


def test_single_line_name_with_hash_verified_by_insertion(temp_yaml_file):
    """
    Test that Verified_By is correctly inserted when Name contains '#'.
    The '#' in Name should not be treated as a comment delimiter.
    """
    original_text = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Display issue #123 indicator
  Text: |
    The system shall display indicators.
  Verified_By: 
"""
    
    req_verified_map = {
        "REQU.TEST.1": "VREQU.TEST.1"
    }
    
    result = apply_verified_by_patch(original_text, req_verified_map)
    
    # Check that Name is preserved exactly
    assert "Name: Display issue #123 indicator" in result, \
        "Name with '#' should be preserved exactly"
    
    # Check that Verified_By was updated
    assert "Verified_By: VREQU.TEST.1" in result, \
        "Verified_By should be updated"
    
    # Check that '#' in Name didn't create a comment entry
    lines = result.split('\n')
    name_line = next((line for line in lines if "Name: Display issue #123" in line), None)
    assert name_line is not None, "Name line should exist"
    assert not name_line.lstrip().startswith("#"), "Name line should not be a comment"


def test_single_line_text_with_hash_verified_by_insertion(temp_yaml_file):
    """
    Test that Verified_By is correctly inserted when single-line Text contains '#'.
    """
    original_text = """- Type: Requirement
  ID: REQU.TEST.2
  Name: Display version
  Text: The system shall display version ###.### in the header
  Verified_By: 
"""
    
    req_verified_map = {
        "REQU.TEST.2": "VREQU.TEST.2"
    }
    
    result = apply_verified_by_patch(original_text, req_verified_map)
    
    # Check that Text is preserved exactly
    assert "Text: The system shall display version ###.### in the header" in result, \
        "Text with '###.###' should be preserved exactly"
    
    # Check that Verified_By was updated
    assert "Verified_By: VREQU.TEST.2" in result, \
        "Verified_By should be updated"


def test_block_scalar_text_with_leading_hash_verified_by_insertion(temp_yaml_file):
    """
    Test that Verified_By is correctly inserted when block scalar Text contains lines starting with '#'.
    These '#' lines should remain as content, not be treated as comments.
    """
    original_text = """- Type: Requirement
  ID: REQU.TEST.3
  Name: Process references
  Text: |
    (U) The system shall process:
    # Reference format: owner/repo#number
    # Examples: user/project#5
  Verified_By: 
"""
    
    req_verified_map = {
        "REQU.TEST.3": "VREQU.TEST.3"
    }
    
    result = apply_verified_by_patch(original_text, req_verified_map)
    
    # Check that block scalar Text is preserved with leading '#' lines
    assert "# Reference format: owner/repo#number" in result, \
        "Block scalar lines starting with '#' should be preserved as content"
    assert "# Examples: user/project#5" in result, \
        "Multiple block scalar lines starting with '#' should be preserved"
    
    # Check that Verified_By was updated
    assert "Verified_By: VREQU.TEST.3" in result, \
        "Verified_By should be updated"
    
    # Verify the block scalar structure is intact
    lines = result.split('\n')
    text_line_idx = next((i for i, line in enumerate(lines) if "Text: |" in line), None)
    assert text_line_idx is not None, "Text: | line should exist"
    
    # The next few lines should be the block content (indented)
    # Check that we have the block content lines with proper indentation
    assert any("    # Reference format:" in line for line in lines), \
        "Block scalar content should be indented and preserved"


def test_existing_verified_by_replacement_with_hash_in_name(temp_yaml_file):
    """
    Test that existing Verified_By is correctly replaced when Name contains '#'.
    """
    original_text = """- Type: Requirement
  ID: REQU.TEST.4
  Name: Fix issue #456 bug
  Text: |
    The system shall fix the bug.
  Verified_By: OLD.VALUE.1
"""
    
    req_verified_map = {
        "REQU.TEST.4": "VREQU.TEST.4"
    }
    
    result = apply_verified_by_patch(original_text, req_verified_map)
    
    # Check that Name is preserved
    assert "Name: Fix issue #456 bug" in result, \
        "Name with '#' should be preserved"
    
    # Check that Verified_By was replaced (not duplicated)
    assert "Verified_By: VREQU.TEST.4" in result, \
        "Verified_By should be updated to new value"
    assert "OLD.VALUE.1" not in result, \
        "Old Verified_By value should be replaced, not kept"
    
    # Count Verified_By occurrences - should be exactly one
    verified_by_count = result.count("Verified_By:")
    assert verified_by_count == 1, \
        f"Should have exactly 1 Verified_By field, found {verified_by_count}"


def test_existing_verified_by_replacement_with_hash_in_single_line_text(temp_yaml_file):
    """
    Test that existing Verified_By is correctly replaced when single-line Text contains '#'.
    """
    original_text = """- Type: Requirement
  ID: REQU.TEST.5
  Name: Show color
  Text: The system shall display color #FF0000 prominently
  Verified_By: OLD.VALUE.2
"""
    
    req_verified_map = {
        "REQU.TEST.5": "VREQU.TEST.5"
    }
    
    result = apply_verified_by_patch(original_text, req_verified_map)
    
    # Check that Text is preserved
    assert "Text: The system shall display color #FF0000 prominently" in result, \
        "Text with '#FF0000' should be preserved"
    
    # Check that Verified_By was replaced
    assert "Verified_By: VREQU.TEST.5" in result, \
        "Verified_By should be updated"
    assert "OLD.VALUE.2" not in result, \
        "Old value should be replaced"


def test_existing_verified_by_replacement_with_hash_in_block_text(temp_yaml_file):
    """
    Test that existing Verified_By is correctly replaced when block scalar Text contains '#'.
    """
    original_text = """- Type: Requirement
  ID: REQU.TEST.6
  Name: Parse patterns
  Text: |
    The system shall parse:
    # Pattern 1: #[0-9]+
    # Pattern 2: ##.##.##
    All patterns must be supported.
  Verified_By: OLD.VALUE.3
"""
    
    req_verified_map = {
        "REQU.TEST.6": "VREQU.TEST.6"
    }
    
    result = apply_verified_by_patch(original_text, req_verified_map)
    
    # Check that block scalar content is preserved
    assert "# Pattern 1: #[0-9]+" in result, \
        "Block scalar line with '#' should be preserved"
    assert "# Pattern 2: ##.##.##" in result, \
        "Block scalar line with multiple '#' should be preserved"
    
    # Check that Verified_By was replaced
    assert "Verified_By: VREQU.TEST.6" in result, \
        "Verified_By should be updated"
    assert "OLD.VALUE.3" not in result, \
        "Old value should be replaced"


def test_multiple_requirements_with_various_hash_patterns(temp_yaml_file):
    """
    Test patching multiple Requirements with various '#' patterns simultaneously.
    """
    original_text = """- Type: Requirement
  ID: REQU.A.1
  Name: Issue #1 fix
  Text: Fix for issue #1
  Verified_By: 

- Type: Requirement
  ID: REQU.B.2
  Name: Display ###.###
  Text: |
    Version pattern:
    # Format: ###.###
  Verified_By: OLD.B

- Type: Requirement
  ID: REQU.C.3
  Name: Parse #tags and #hashtags
  Text: The system shall parse #tags like #example
  Verified_By: 
"""
    
    req_verified_map = {
        "REQU.A.1": "VREQU.A.1",
        "REQU.B.2": "VREQU.B.2",
        "REQU.C.3": "VREQU.C.3"
    }
    
    result = apply_verified_by_patch(original_text, req_verified_map)
    
    # Check all Names are preserved
    assert "Name: Issue #1 fix" in result
    assert "Name: Display ###.###" in result
    assert "Name: Parse #tags and #hashtags" in result
    
    # Check all Text fields are preserved
    assert "Text: Fix for issue #1" in result
    assert "# Format: ###.###" in result
    assert "Text: The system shall parse #tags like #example" in result
    
    # Check all Verified_By fields are updated
    assert "Verified_By: VREQU.A.1" in result
    assert "Verified_By: VREQU.B.2" in result
    assert "Verified_By: VREQU.C.3" in result
    
    # Check old value was replaced
    assert "OLD.B" not in result
    
    # Count Verified_By occurrences - should be exactly 3
    verified_by_count = result.count("Verified_By:")
    assert verified_by_count == 3, \
        f"Should have exactly 3 Verified_By fields, found {verified_by_count}"


def test_hash_not_confused_with_comment_in_key_value_line(temp_yaml_file):
    """
    Test that '#' appearing after a colon in a key-value line is preserved as part of the value,
    not treated as starting a comment.
    """
    original_text = """- Type: Requirement
  ID: REQU.TEST.7
  Name: Test #special
  Text: Value with #hash
  Verified_By: 
"""
    
    req_verified_map = {
        "REQU.TEST.7": "VREQU.TEST.7"
    }
    
    result = apply_verified_by_patch(original_text, req_verified_map)
    
    # Parse the result to ensure structure is correct
    lines = result.split('\n')
    
    # Find the Name line and verify it's complete
    name_line = next((line for line in lines if "Name:" in line and "Test" in line), None)
    assert name_line is not None, "Name line should exist"
    assert "#special" in name_line, "Name should contain '#special'"
    
    # Find the Text line and verify it's complete
    text_line = next((line for line in lines if "Text:" in line and "Value" in line), None)
    assert text_line is not None, "Text line should exist"
    assert "#hash" in text_line, "Text should contain '#hash'"
    
    # Verified_By should be updated
    assert "Verified_By: VREQU.TEST.7" in result


def _create_temp_file_standalone(content):
    """Standalone temp file creator for when pytest is not available.
    
    Creates a temporary file and registers cleanup to run on process exit.
    """
    import atexit
    
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    try:
        tmp_file.write(content)
        tmp_path = tmp_file.name
    finally:
        tmp_file.close()
    
    def _cleanup_temp_file() -> None:
        """Remove the standalone temporary file on process exit."""
        try:
            os.remove(tmp_path)
        except (FileNotFoundError, OSError):
            # Best-effort cleanup: ignore errors if the file was already removed
            # or cannot be deleted; this should not interfere with test execution.
            pass
    
    atexit.register(_cleanup_temp_file)
    return tmp_path


if __name__ == '__main__':
    try:
        import pytest
        pytest.main([__file__, '-v'])
    except ImportError:
        # Fallback to basic test runner if pytest is not available
        print("pytest not available, running tests directly")
        print("\n" + "="*70)
        print("TEST: Single-line Name with '#' - Verified_By insertion")
        print("="*70)
        test_single_line_name_with_hash_verified_by_insertion(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("TEST: Single-line Text with '#' - Verified_By insertion")
        print("="*70)
        test_single_line_text_with_hash_verified_by_insertion(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("TEST: Block scalar Text with leading '#' - Verified_By insertion")
        print("="*70)
        test_block_scalar_text_with_leading_hash_verified_by_insertion(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("TEST: Existing Verified_By replacement with '#' in Name")
        print("="*70)
        test_existing_verified_by_replacement_with_hash_in_name(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("TEST: Existing Verified_By replacement with '#' in single-line Text")
        print("="*70)
        test_existing_verified_by_replacement_with_hash_in_single_line_text(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("TEST: Existing Verified_By replacement with '#' in block Text")
        print("="*70)
        test_existing_verified_by_replacement_with_hash_in_block_text(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("TEST: Multiple Requirements with various '#' patterns")
        print("="*70)
        test_multiple_requirements_with_various_hash_patterns(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("TEST: '#' not confused with comment in key-value line")
        print("="*70)
        test_hash_not_confused_with_comment_in_key_value_line(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("ALL TESTS PASSED!")
        print("="*70)
