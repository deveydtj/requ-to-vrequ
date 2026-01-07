#!/usr/bin/env python3
"""
End-to-end test for Verified_By patching with hash characters in values.

This test validates the complete workflow:
1. Parse Requirements with '#' in Name/Text
2. Generate Verification items (which also contain '#')
3. Apply Verified_By patch back to original text
4. Verify all '#' characters are preserved and structure is intact

Acceptance Criteria:
- Verified_By patch does not alter or remove '#' from any Name/Text content
- Block scalars containing lines like '#not-a-comment' remain unchanged (as content)
"""

import sys
import os
import subprocess
import tempfile

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_script_path():
    """Get the absolute path to the main generate_verification_yaml.py script."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'generate_verification_yaml.py'
    )


def test_e2e_hash_preservation_in_verified_by_patch(temp_yaml_file):
    """
    End-to-end test: Verify that running the full script preserves '#' in all fields.
    """
    input_content = """# Test input with various hash patterns
- Type: Requirement
  ID: REQU.DISPLAY.1
  Name: Show issue #123 indicator
  Text: |
    (U) The system shall display:
    # Issue format: repo#number
    # Example: project#123
  Verified_By: 
  Traced_To: 

- Type: Requirement
  ID: REQU.VERSION.2
  Name: Display version ###.###.###
  Text: The system shall display version ###.###.### in the header
  Verified_By: 
"""
    
    input_path = temp_yaml_file(input_content)
    output_path = input_path + ".out"
    
    try:
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
        
        # ACCEPTANCE CRITERION 1: Verified_By patch does not alter '#' from Name/Text
        
        # Check Requirements section preserved all '#' characters
        assert "Name: Show issue #123 indicator" in output_content, \
            "Requirement Name with '#123' should be preserved"
        assert "# Issue format: repo#number" in output_content, \
            "Block scalar line starting with '#' should be preserved"
        assert "# Example: project#123" in output_content, \
            "Block scalar line with '#' in content should be preserved"
        assert "Name: Display version ###.###.###" in output_content, \
            "Requirement Name with '###.###.###' should be preserved"
        assert "Text: The system shall display version ###.###.### in the header" in output_content, \
            "Requirement Text with '###.###.###' should be preserved"
        
        # Check that Verified_By fields were added/updated correctly
        assert "Verified_By: VREQU.DISPLAY.1" in output_content, \
            "Verified_By should be added for REQU.DISPLAY.1"
        assert "Verified_By: VREQU.VERSION.2" in output_content, \
            "Verified_By should be added for REQU.VERSION.2"
        
        # Check Verification items section also preserves '#' characters
        assert "ID: VREQU.DISPLAY.1" in output_content, \
            "Verification item should be generated"
        assert "ID: VREQU.VERSION.2" in output_content, \
            "Verification item should be generated"
        
        # Verification items should contain transformed versions with '#' preserved
        # The '#' from original Name/Text should appear in Verification Name/Text
        lines = output_content.split('\n')
        
        # Find VREQU.DISPLAY.1 section
        vrequ_display_start = None
        for i, line in enumerate(lines):
            if "ID: VREQU.DISPLAY.1" in line:
                vrequ_display_start = i
                break
        
        assert vrequ_display_start is not None, "VREQU.DISPLAY.1 section not found"
        
        # Check next ~20 lines for the verification content
        vrequ_display_section = '\n'.join(lines[vrequ_display_start:vrequ_display_start+20])
        assert "#123" in vrequ_display_section, \
            "Verification Name should preserve '#123' from original"
        assert "# Issue format:" in vrequ_display_section or "Issue format:" in vrequ_display_section, \
            "Verification Text should preserve block content (may be transformed)"
        
        # Find VREQU.VERSION.2 section
        vrequ_version_start = None
        for i, line in enumerate(lines):
            if "ID: VREQU.VERSION.2" in line:
                vrequ_version_start = i
                break
        
        assert vrequ_version_start is not None, "VREQU.VERSION.2 section not found"
        
        vrequ_version_section = '\n'.join(lines[vrequ_version_start:vrequ_version_start+10])
        assert "###.###.###" in vrequ_version_section, \
            "Verification content should preserve '###.###.###' pattern"
        
        # ACCEPTANCE CRITERION 2: Block scalars with '#' remain unchanged as content
        
        # The block scalar structure should be intact
        assert "Text: |" in output_content, \
            "Block scalar indicator should be present"
        
        # Count '#' characters to ensure none were lost
        input_hash_count = input_content.count('#')
        output_hash_count = output_content.count('#')
        
        # Output should have at least as many '#' as input (may have more from FIX comments)
        # But the key point is that none should be lost
        # Let's be more specific: check that specific patterns are preserved
        input_patterns = [
            "#123",
            "# Issue format:",
            "# Example:",
            "###.###.###"
        ]
        
        for pattern in input_patterns:
            input_occurrences = input_content.count(pattern)
            output_occurrences = output_content.count(pattern)
            assert output_occurrences >= input_occurrences, \
                f"Pattern '{pattern}' should be preserved (input: {input_occurrences}, output: {output_occurrences})"
        
        print("✓ All acceptance criteria validated")
        print("  - Verified_By patching preserved all '#' characters")
        print("  - Block scalar content with '#' remained intact")
        
    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)


def test_e2e_hash_in_values_not_treated_as_comments(temp_yaml_file):
    """
    Test that '#' appearing in values is never treated as starting a comment.
    """
    input_content = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Color #FF0000 rendering
  Text: Render with hex color #ABCDEF
  Verified_By: 
"""
    
    input_path = temp_yaml_file(input_content)
    output_path = input_path + ".out"
    
    try:
        script_path = get_script_path()
        result = subprocess.run(
            ["python", script_path, input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        with open(output_path, 'r') as f:
            output_content = f.read()
        
        # The Name and Text should be complete, not truncated at '#'
        assert "Name: Color #FF0000 rendering" in output_content, \
            "Name should not be truncated at '#'"
        assert "Text: Render with hex color #ABCDEF" in output_content, \
            "Text should not be truncated at '#'"
        
        # Parse the output to verify structure
        lines = output_content.split('\n')
        name_line = next((line for line in lines if "Name: Color #FF0000" in line), None)
        assert name_line is not None
        assert "rendering" in name_line, \
            "Name should continue after '#FF0000'"
        
        text_line = next((line for line in lines if "Text: Render with hex color" in line), None)
        assert text_line is not None
        assert "#ABCDEF" in text_line, \
            "Text should include '#ABCDEF'"
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_e2e_multiple_runs_preserve_hash_idempotency(temp_yaml_file):
    """
    Test that running the script multiple times preserves '#' characters (idempotency test).
    """
    input_content = """- Type: Requirement
  ID: REQU.IDEMPOTENT.1
  Name: Feature #999 implementation
  Text: |
    Implements feature #999:
    # Step 1: Parse input
    # Step 2: Process data
  Verified_By: 
"""
    
    input_path = temp_yaml_file(input_content)
    output_path_1 = input_path + ".out1"
    output_path_2 = input_path + ".out2"
    
    try:
        script_path = get_script_path()
        
        # First run
        result1 = subprocess.run(
            ["python", script_path, input_path, output_path_1],
            capture_output=True,
            text=True
        )
        assert result1.returncode == 0, f"First run failed: {result1.stderr}"
        
        # Second run (using output from first run as input)
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
        
        # Both outputs should preserve all '#' patterns
        patterns = [
            "#999",
            "# Step 1:",
            "# Step 2:"
        ]
        
        for pattern in patterns:
            count1 = output1.count(pattern)
            count2 = output2.count(pattern)
            assert count1 > 0, f"Pattern '{pattern}' should appear in first output"
            assert count2 > 0, f"Pattern '{pattern}' should appear in second output"
            # The counts should be equal (idempotency)
            assert count1 == count2, \
                f"Pattern '{pattern}' count should be stable across runs (run1: {count1}, run2: {count2})"
        
    finally:
        for path in [output_path_1, output_path_2]:
            if os.path.exists(path):
                os.remove(path)


def _create_temp_file_standalone(content):
    """Standalone temp file creator for when pytest is not available."""
    import atexit
    
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    try:
        tmp_file.write(content)
        tmp_path = tmp_file.name
    finally:
        tmp_file.close()
    
    def _cleanup_temp_file() -> None:
        try:
            os.remove(tmp_path)
        except (FileNotFoundError, OSError):
            pass
    
    atexit.register(_cleanup_temp_file)
    return tmp_path


if __name__ == '__main__':
    try:
        import pytest
        pytest.main([__file__, '-v'])
    except ImportError:
        print("pytest not available, running tests directly\n")
        
        print("="*70)
        print("TEST: E2E hash preservation in Verified_By patch")
        print("="*70)
        test_e2e_hash_preservation_in_verified_by_patch(_create_temp_file_standalone)
        print("\n")
        
        print("="*70)
        print("TEST: E2E hash in values not treated as comments")
        print("="*70)
        test_e2e_hash_in_values_not_treated_as_comments(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("TEST: E2E multiple runs preserve hash (idempotency)")
        print("="*70)
        test_e2e_multiple_runs_preserve_hash_idempotency(_create_temp_file_standalone)
        print("✓ PASSED\n")
        
        print("="*70)
        print("ALL E2E TESTS PASSED!")
        print("="*70)
