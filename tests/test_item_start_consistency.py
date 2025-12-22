#!/usr/bin/env python3
"""
Test script for item-start detection consistency.

This script validates that:
1. Patchers handle leading whitespace before "- " correctly
2. Patchers handle varied spacing after the hyphen
3. Patchers work when keys appear in any order (e.g., "- ID:" before other fields)
4. The is_item_start() helper correctly identifies item starts
"""

import sys
import os
import tempfile

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    is_item_start,
    parse_items,
    build_id_sequence_map,
    apply_id_sequence_patch,
    apply_verified_by_patch,
    generate_verification_items,
)


def test_is_item_start():
    """Test the is_item_start() helper function."""
    print("Testing is_item_start() helper...")
    
    # Should detect item starts
    assert is_item_start("- Type: Requirement")
    assert is_item_start("  - Type: Requirement")
    assert is_item_start("    - ID: REQU.1")
    assert is_item_start("- Name: Test")
    assert is_item_start("-  Type: Requirement")  # Extra space after hyphen
    
    # Should NOT detect as item starts
    assert not is_item_start("  ID: REQU.1")
    assert not is_item_start("  Name: Test")
    assert not is_item_start("# Comment")
    assert not is_item_start("")
    assert not is_item_start("   ")
    
    print("✓ is_item_start() test passed")


def test_parsing_with_leading_whitespace():
    """Test that parsing handles leading whitespace correctly."""
    print("\nTesting parsing with leading whitespace...")
    
    test_yaml = """  - Type: Requirement
    Parent_Req: 
    ID: REQU.TEST.1
    Name: Test requirement
    Text: |
      Test text
    Verified_By: 
    Traced_To: 

  - Type: Requirement
    Parent_Req: 
    ID: REQU.TEST.2
    Name: Another test
    Text: Test text 2
    Verified_By: 
    Traced_To: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(input_path)
        
        # Should have parsed 2 items
        non_comment_items = [item for item in items if '_comment' not in item or len(item) > 1]
        assert len(non_comment_items) == 2, f"Expected 2 items, got {len(non_comment_items)}"
        
        # Verify IDs were parsed correctly
        assert non_comment_items[0].get('ID') == 'REQU.TEST.1'
        assert non_comment_items[1].get('ID') == 'REQU.TEST.2'
        
        print("✓ Parsing with leading whitespace test passed")
        
    finally:
        os.remove(input_path)


def test_id_sequencing_with_leading_whitespace():
    """Test that ID sequencing patch works with leading whitespace."""
    print("\nTesting ID sequencing with leading whitespace...")
    
    test_yaml = """  - Type: Requirement
    Parent_Req: 
    ID: REQU.TEST.1
    Name: First
    Text: First requirement

  - Type: Requirement
    Parent_Req: 
    ID: REQU.TEST.X
    Name: Second
    Text: Second requirement
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(input_path)
        id_map = build_id_sequence_map(items)
        
        # Should have a mapping for REQU.TEST.X
        matching_keys = [k for k in id_map.keys() if 'REQU.TEST.X@' in k]
        assert matching_keys, \
            f"Expected mapping for REQU.TEST.X, but found mappings: {list(id_map.keys())}"
        
        # Apply the patch
        patched_text = apply_id_sequence_patch(test_yaml, id_map)
        
        # Should have replaced REQU.TEST.X with REQU.TEST.2
        assert 'REQU.TEST.2' in patched_text, "Expected REQU.TEST.2 in patched text"
        assert 'REQU.TEST.X' not in patched_text, "REQU.TEST.X should be replaced"
        
        # Should preserve leading whitespace
        assert '  - Type: Requirement' in patched_text, \
            "Leading whitespace should be preserved"
        
        print("✓ ID sequencing with leading whitespace test passed")
        
    finally:
        os.remove(input_path)


def test_verified_by_patch_with_leading_whitespace():
    """Test that Verified_By patching works with leading whitespace."""
    print("\nTesting Verified_By patching with leading whitespace...")
    
    test_yaml = """  - Type: Requirement
    Parent_Req: 
    ID: REQU.TEST.1
    Name: Test requirement
    Text: Test text
    Verified_By: 
    Traced_To: 
"""
    
    req_verified_map = {
        'REQU.TEST.1': 'VREQU.TEST.1'
    }
    
    patched_text = apply_verified_by_patch(test_yaml, req_verified_map)
    
    # Should have updated Verified_By
    assert 'Verified_By: VREQU.TEST.1' in patched_text, \
        "Expected Verified_By to be updated"
    
    # Should preserve leading whitespace
    assert '  - Type: Requirement' in patched_text, \
        "Leading whitespace should be preserved"
    
    print("✓ Verified_By patching with leading whitespace test passed")


def test_alternate_key_ordering():
    """Test patching when keys appear in different order (e.g., ID first)."""
    print("\nTesting alternate key ordering...")
    
    # This simulates a file where ID appears on the first line
    test_yaml = """- ID: REQU.TEST.1
  Type: Requirement
  Parent_Req: 
  Name: Test requirement
  Text: Test text
  Verified_By: 
  Traced_To: 

- ID: REQU.TEST.2
  Type: Requirement
  Parent_Req: 
  Name: Another test
  Text: Test text 2
  Verified_By: 
  Traced_To: 
"""
    
    req_verified_map = {
        'REQU.TEST.1': 'VREQU.TEST.1',
        'REQU.TEST.2': 'VREQU.TEST.2'
    }
    
    patched_text = apply_verified_by_patch(test_yaml, req_verified_map)
    
    # Should have updated both Verified_By fields
    assert 'Verified_By: VREQU.TEST.1' in patched_text
    assert 'Verified_By: VREQU.TEST.2' in patched_text
    
    # Should preserve the key ordering
    lines = patched_text.split('\n')
    
    # Find first item
    for i, line in enumerate(lines):
        if 'ID: REQU.TEST.1' in line:
            # Type should come after ID
            assert any('Type: Requirement' in lines[j] for j in range(i+1, min(i+10, len(lines)))), \
                "Type should appear after ID in the first item"
            break
    
    print("✓ Alternate key ordering test passed")


def test_varied_spacing():
    """Test patching with varied spacing after the hyphen."""
    print("\nTesting varied spacing after hyphen...")
    
    # Multiple spaces after hyphen
    test_yaml = """-  Type: Requirement
  ID: REQU.TEST.1
  Name: Test
  Text: Test text
  Verified_By: 

-   Type: Requirement
  ID: REQU.TEST.2
  Name: Test 2
  Text: Test text 2
  Verified_By: 
"""
    
    req_verified_map = {
        'REQU.TEST.1': 'VREQU.TEST.1',
        'REQU.TEST.2': 'VREQU.TEST.2'
    }
    
    patched_text = apply_verified_by_patch(test_yaml, req_verified_map)
    
    # Should have updated both Verified_By fields
    assert 'Verified_By: VREQU.TEST.1' in patched_text
    assert 'Verified_By: VREQU.TEST.2' in patched_text
    
    # Should preserve the original spacing
    assert '-  Type: Requirement' in patched_text
    assert '-   Type: Requirement' in patched_text
    
    print("✓ Varied spacing test passed")


def test_id_sequencing_with_varied_spacing():
    """Test that ID sequencing preserves varied spacing after the hyphen when ID is on first line."""
    print("\nTesting ID sequencing with varied spacing after hyphen...")
    
    test_yaml = """-  ID: REQU.TEST.1
  Type: Requirement
  Name: First
  Text: First requirement

-   ID: REQU.TEST.X
  Type: Requirement
  Name: Second
  Text: Second requirement
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(input_path)
        id_map = build_id_sequence_map(items)
        
        # Apply the patch
        patched_text = apply_id_sequence_patch(test_yaml, id_map)
        
        # Should have replaced REQU.TEST.X with REQU.TEST.2
        assert 'REQU.TEST.2' in patched_text, "Expected REQU.TEST.2 in patched text"
        assert 'REQU.TEST.X' not in patched_text, "REQU.TEST.X should be replaced"
        
        # Should preserve varied spacing after hyphen
        assert '-  ID: REQU.TEST.1' in patched_text, \
            "Should preserve two spaces after hyphen in first item"
        assert '-   ID: REQU.TEST.2' in patched_text, \
            "Should preserve three spaces after hyphen in second item"
        
        print("✓ ID sequencing with varied spacing test passed")
        
    finally:
        os.remove(input_path)


def test_end_to_end_with_formatting_variations():
    """Test the full pipeline with formatting variations."""
    print("\nTesting end-to-end with formatting variations...")
    
    test_yaml = """  - Type: Requirement
    ID: REQU.TEST.1
    Name: Render the display
    Text: |
      (U) The system shall render the display.
    Verified_By: 

- ID: REQU.TEST.X
  Type: Requirement
  Name: Set the value
  Text: |
    (U) The system shall set the value.
  Verified_By: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    try:
        # Parse items
        items = parse_items(input_path)
        
        # Build ID sequence map
        id_map = build_id_sequence_map(items)
        
        # Apply ID sequencing
        sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
        
        # Generate verifications (using sequenced items)
        from generate_verification_yaml import sequence_requirement_ids
        sequenced_items = sequence_requirement_ids(items, id_map)
        items_with_ver = generate_verification_items(sequenced_items)
        
        # Build Verified_By map from Verification items (not from Requirements)
        req_verified_map = {}
        for item in items_with_ver:
            item_type = item.get('Type', '').strip()
            if item_type in {
                'Verification',
                'DMGR Verification Requirement',
                'BRDG Verification Requirement'
            }:
                ver_id = item.get('ID', '').strip()
                if ver_id.startswith('VREQU'):
                    # Remove the "V" prefix to get the Requirement ID
                    req_id = ver_id[1:]  # "VREQU.TEST.1" -> "REQU.TEST.1"
                    req_verified_map[req_id] = ver_id
        
        # Apply Verified_By patch
        final_text = apply_verified_by_patch(sequenced_text, req_verified_map)
        
        # Verify results
        assert 'REQU.TEST.1' in final_text
        assert 'REQU.TEST.2' in final_text  # X should be sequenced to 2
        assert 'REQU.TEST.X' not in final_text
        
        assert 'Verified_By: VREQU.TEST.1' in final_text
        assert 'Verified_By: VREQU.TEST.2' in final_text
        
        # Verify leading whitespace preserved for first item
        assert '  - Type: Requirement' in final_text
        
        # Verify alternate ordering preserved for second item:
        # when the item starts with "- ID: REQU.TEST.X", it should remain
        # on the first line after sequencing as "- ID: REQU.TEST.2".
        lines = final_text.split('\n')
        found_id_first = False
        for line in lines:
            if line.lstrip().startswith('- ID: REQU.TEST.2'):
                found_id_first = True
                break
        assert found_id_first, "Expected '- ID: REQU.TEST.2' to appear on the first line of the item"
        
        print("✓ End-to-end with formatting variations test passed")
        
    finally:
        os.remove(input_path)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running item-start detection consistency tests")
    print("=" * 60)
    
    try:
        test_is_item_start()
        test_parsing_with_leading_whitespace()
        test_id_sequencing_with_leading_whitespace()
        test_verified_by_patch_with_leading_whitespace()
        test_alternate_key_ordering()
        test_varied_spacing()
        test_id_sequencing_with_varied_spacing()
        test_end_to_end_with_formatting_variations()
        
        print("\n" + "=" * 60)
        print("All item-start consistency tests passed! ✓")
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
