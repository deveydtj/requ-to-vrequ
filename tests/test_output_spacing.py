#!/usr/bin/env python3
"""
Test script for output spacing consistency.

This script validates that:
1. Standalone comment entries (like "# FIX ...") appear directly above their
   associated verification items with no extra blank lines.
2. Unrelated blocks are separated by exactly one blank line.
3. Appending verification items doesn't create double blank lines.
"""

import sys
import os
import tempfile

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    parse_items,
    generate_verification_items,
    write_items,
    render_items_to_string,
)


def test_comment_adjacency():
    """
    Test that FIX comments appear directly above their verification items.
    """
    print("Testing comment adjacency...")
    
    # Create items with a comment followed by a verification
    items = [
        {"_comment": "# FIX - Non-Standard Name"},
        {
            "Type": "DMGR Verification Requirement",
            "Parent_Req": "",
            "ID": "VREQU.DMGR.TEST.1",
            "Name": "Verify Display the status",
            "Text": "(U) Verify the system renders the status.",
            "Verified_By": "",
            "Traced_To": "",
            "_order": [
                ("key", "Parent_Req"),
                ("key", "ID"),
                ("key", "Name"),
                ("key", "Text"),
                ("key", "Verified_By"),
                ("key", "Traced_To"),
            ],
        }
    ]
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
    
    try:
        write_items(temp_path, items)
        
        with open(temp_path, 'r') as f:
            output = f.read()
        
        lines = output.split('\n')
        
        # Find the comment line
        comment_idx = None
        for i, line in enumerate(lines):
            if '# FIX - Non-Standard Name' in line:
                comment_idx = i
                break
        
        assert comment_idx is not None, "Comment not found in output"
        
        # The next non-empty line should be the verification item (starting with "- Type:")
        next_line_idx = comment_idx + 1
        while next_line_idx < len(lines) and not lines[next_line_idx].strip():
            next_line_idx += 1
        
        # There should be NO blank lines between comment and verification
        blank_lines_between = next_line_idx - comment_idx - 1
        assert blank_lines_between == 0, \
            f"Expected 0 blank lines between comment and verification, got {blank_lines_between}"
        
        assert lines[next_line_idx].startswith("- Type:"), \
            f"Expected verification item after comment, got: {lines[next_line_idx]}"
        
        print("✓ Comment adjacency test passed")
        
    finally:
        os.remove(temp_path)


def test_multiple_comments_and_items():
    """
    Test spacing with multiple comments and verification items.
    """
    print("\nTesting multiple comments and items...")
    
    items = [
        {"_comment": "# FIX - Non-Standard Name"},
        {
            "Type": "DMGR Verification Requirement",
            "Parent_Req": "",
            "ID": "VREQU.DMGR.TEST.1",
            "Name": "Verify Display the status",
            "Text": "(U) Verify the system renders the status.",
            "Verified_By": "",
            "Traced_To": "",
            "_order": [("key", "Parent_Req"), ("key", "ID"), ("key", "Name"), 
                      ("key", "Text"), ("key", "Verified_By"), ("key", "Traced_To")],
        },
        {"_comment": "# FIX - Non-Standard Text"},
        {
            "Type": "BRDG Verification Requirement",
            "Parent_Req": "",
            "ID": "VREQU.BRDG.TEST.2",
            "Name": "Verify the timeout is set",
            "Text": "(U) The system shall configure the timeout.",
            "Verified_By": "",
            "Traced_To": "",
            "_order": [("key", "Parent_Req"), ("key", "ID"), ("key", "Name"), 
                      ("key", "Text"), ("key", "Verified_By"), ("key", "Traced_To")],
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
    
    try:
        write_items(temp_path, items)
        
        with open(temp_path, 'r') as f:
            output = f.read()
        
        lines = output.split('\n')
        
        # Check first comment -> first verification
        comment1_idx = None
        for i, line in enumerate(lines):
            if '# FIX - Non-Standard Name' in line:
                comment1_idx = i
                break
        assert comment1_idx is not None
        
        # Next non-empty should be verification
        next_idx = comment1_idx + 1
        while next_idx < len(lines) and not lines[next_idx].strip():
            next_idx += 1
        assert next_idx - comment1_idx - 1 == 0, "Comment 1 should be directly adjacent"
        assert 'VREQU.DMGR.TEST.1' in '\n'.join(lines[next_idx:next_idx+10])
        
        # Check second comment -> second verification
        comment2_idx = None
        for i, line in enumerate(lines):
            if '# FIX - Non-Standard Text' in line:
                comment2_idx = i
                break
        assert comment2_idx is not None
        
        next_idx = comment2_idx + 1
        while next_idx < len(lines) and not lines[next_idx].strip():
            next_idx += 1
        assert next_idx - comment2_idx - 1 == 0, "Comment 2 should be directly adjacent"
        assert 'VREQU.BRDG.TEST.2' in '\n'.join(lines[next_idx:next_idx+10])
        
        # Verify there IS a blank line between the two verification blocks
        # (between end of first verification and second comment)
        first_ver_end = comment2_idx - 1
        # Walk back to find last non-empty line of first verification
        while first_ver_end > 0 and not lines[first_ver_end].strip():
            first_ver_end -= 1
        
        blank_lines_between_blocks = comment2_idx - first_ver_end - 1
        assert blank_lines_between_blocks == 1, \
            f"Expected 1 blank line between verification blocks, got {blank_lines_between_blocks}"
        
        print("✓ Multiple comments and items test passed")
        
    finally:
        os.remove(temp_path)


def test_render_items_to_string_no_double_blanks():
    """
    Test that render_items_to_string doesn't create double blank lines.
    """
    print("\nTesting render_items_to_string trailing newlines...")
    
    items = [
        {"_comment": "# FIX - Test Comment"},
        {
            "Type": "Verification",
            "Parent_Req": "",
            "ID": "VREQU.TEST.1",
            "Name": "Verify something",
            "Text": "Verify that it works.",
            "Verified_By": "",
            "Traced_To": "",
            "_order": [("key", "Parent_Req"), ("key", "ID"), ("key", "Name"), 
                      ("key", "Text"), ("key", "Verified_By"), ("key", "Traced_To")],
        }
    ]
    
    output = render_items_to_string(items)
    
    # The output should not have double newlines at the end
    assert not output.endswith('\n\n'), "Should not have double newlines at end"
    
    # The output should not start with a newline
    assert not output.startswith('\n'), "Should not start with a newline"
    
    # When appended to a file with "\n\n" + output + "\n", we should get
    # exactly one blank line before the comment
    simulated_append = "previous content\n\n" + output + "\n"
    lines = simulated_append.split('\n')
    
    # Find the comment
    comment_idx = None
    for i, line in enumerate(lines):
        if '# FIX - Test Comment' in line:
            comment_idx = i
            break
    
    assert comment_idx is not None
    
    # There should be exactly 1 blank line before the comment
    # (line before should be empty, line before that should have content)
    assert comment_idx >= 2, "Not enough lines before comment"
    assert lines[comment_idx - 1] == "", "Line before comment should be blank"
    assert lines[comment_idx - 2].strip() != "", "Two lines before should have content"
    
    print("✓ render_items_to_string test passed")


def test_end_to_end_spacing():
    """
    Test full pipeline to ensure proper spacing in final output.
    """
    print("\nTesting end-to-end spacing...")
    
    test_yaml = """- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.1
  Name: Display the status
  Text: |
    (U) The system shall render the status.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.TEST.2
  Name: Process input
  Text: |
    (U) The system shall set the value.
  Verified_By: 
  Traced_To: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    output_path = None
    try:
        output_path = input_path.replace('.yaml', '_output.yaml')
        
        # Parse and generate
        items = parse_items(input_path)
        items_with_ver = generate_verification_items(items)
        
        # Get only new verification items
        existing_ver_ids = set()
        new_ver_items = []
        pending_comments = []
        
        for item in items_with_ver:
            if "_comment" in item and len(item) == 1:
                pending_comments.append(item)
                continue
            
            item_type = item.get("Type", "").strip()
            if item_type in {"Verification", "DMGR Verification Requirement", "BRDG Verification Requirement"}:
                ver_id = item.get("ID", "").strip()
                if ver_id and ver_id not in existing_ver_ids:
                    new_ver_items.extend(pending_comments)
                    new_ver_items.append(item)
                pending_comments = []
            else:
                pending_comments = []
        
        # Render to string
        ver_text = render_items_to_string(new_ver_items)
        
        # Write output simulating main()
        with open(output_path, 'w') as f:
            f.write(test_yaml.rstrip("\n"))
            f.write("\n\n")
            f.write(ver_text)
            f.write("\n")
        
        with open(output_path, 'r') as f:
            output = f.read()
        
        lines = output.split('\n')
        
        # Verify each FIX comment is directly above its verification
        for i, line in enumerate(lines):
            if line.strip().startswith("# FIX"):
                # Next non-empty line should be a verification item
                next_idx = i + 1
                while next_idx < len(lines) and not lines[next_idx].strip():
                    next_idx += 1
                
                blank_count = next_idx - i - 1
                assert blank_count == 0, \
                    f"FIX comment at line {i} has {blank_count} blank lines before verification (expected 0)"
                assert lines[next_idx].startswith("- Type:"), \
                    f"FIX comment at line {i} not followed by verification item"
        
        print("✓ End-to-end spacing test passed")
        
    finally:
        os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running output spacing tests")
    print("=" * 60)
    
    try:
        test_comment_adjacency()
        test_multiple_comments_and_items()
        test_render_items_to_string_no_double_blanks()
        test_end_to_end_spacing()
        
        print("\n" + "=" * 60)
        print("All spacing tests passed! ✓")
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
