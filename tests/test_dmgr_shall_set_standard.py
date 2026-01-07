#!/usr/bin/env python3
"""
Test script for DMGR "shall set" as standard text.

This test validates that DMGR domain requirements with "shall set" in the
Text field are considered standard (not non-standard), and that the 
transformation produces "sets" in the verification requirement.
"""

import sys
import os
import tempfile
import subprocess

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    is_standard_text,
    transform_text,
)


def test_is_standard_text_dmgr_shall_set():
    """Test that DMGR with 'shall set' is considered standard."""
    print("Testing is_standard_text for DMGR with 'shall set'...")
    
    # DMGR with "shall render" should be standard
    assert is_standard_text("The system shall render the UI.", "DMGR"), \
        "DMGR with 'shall render' should be standard"
    
    # DMGR with "shall set" should also be standard (this is the fix)
    assert is_standard_text("The system shall set the timeout.", "DMGR"), \
        "DMGR with 'shall set' should be standard"
    
    # DMGR with both should be standard
    assert is_standard_text("The system shall set the value and shall render the UI.", "DMGR"), \
        "DMGR with both 'shall set' and 'shall render' should be standard"
    
    # DMGR with neither should be non-standard
    assert not is_standard_text("The system shall configure the timeout.", "DMGR"), \
        "DMGR without 'shall render' or 'shall set' should be non-standard"
    
    print("✓ is_standard_text tests passed")


def test_dmgr_shall_set_transformation():
    """Test that DMGR with 'shall set' transforms correctly to active voice."""
    print("\nTesting DMGR 'shall set' transformation...")
    
    # Test singular subject
    req_text = "(U) The Data Manager shall set the buffer size."
    result = transform_text(req_text, is_advanced=True, is_setting=True, is_dmgr=True)
    
    # Should transform "shall set" to "sets" (active voice, singular)
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    assert "sets" in result, f"Expected 'sets' in output, got: {result}"
    
    expected = "(U) Verify the Data Manager sets the buffer size."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
    
    # Test plural subject
    req_text_plural = "(U) The Data Managers shall set the buffer sizes."
    result_plural = transform_text(req_text_plural, is_advanced=True, is_setting=True, is_dmgr=True)
    
    # Should transform "shall set" to "set" (active voice, plural)
    assert "shall set" not in result_plural, f"Expected 'shall set' to be replaced, got: {result_plural}"
    assert "set the buffer" in result_plural, f"Expected 'set the buffer' in output, got: {result_plural}"
    
    print("✓ Transformation tests passed")


def test_dmgr_shall_set_without_setting_name():
    """
    Test DMGR requirement with 'shall set' in Text but Name doesn't contain 'Set'.
    
    This edge case verifies that DMGR 'shall set' is transformed even when
    is_setting=False (Name doesn't contain "Set"). This ensures consistency
    where DMGR treats "shall set" like "shall render" - always transformed.
    """
    print("\nTesting DMGR 'shall set' with non-setting Name...")
    
    # Name is "Render the UI" (no "Set"), so is_setting=False
    # But Text contains "shall set", which should still be transformed for DMGR
    req_text = "(U) The Data Manager shall set the display mode."
    result = transform_text(req_text, is_advanced=True, is_setting=False, is_dmgr=True)
    
    # Should transform "shall set" even though is_setting=False
    assert "shall set" not in result, f"Expected 'shall set' to be replaced for DMGR, got: {result}"
    assert "sets the display mode" in result, f"Expected 'sets the display mode' in output, got: {result}"
    
    expected = "(U) Verify the Data Manager sets the display mode."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
    
    print("✓ Edge case test passed")


def test_end_to_end_dmgr_shall_set():
    """Test the full pipeline with a DMGR requirement containing 'shall set'."""
    print("\nTesting end-to-end DMGR 'shall set' behavior...")
    
    test_yaml = """# Test DMGR with shall set
- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.1
  Name: Set the buffer size
  Text: |
    (U) The Data Manager shall set the buffer size to 1024 bytes.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.2
  Name: Render the status
  Text: |
    (U) The Data Manager shall render the status indicator.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.3
  Name: Render the display mode
  Text: |
    (U) The Data Manager shall set the display mode to fullscreen.
  Verified_By: 
  Traced_To: 
"""
    
    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(test_yaml)
    
    output_file = None
    
    try:
        # Create temporary output file
        output_file = input_file.replace('.yaml', '_output.yaml')
        
        # Run the script
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'generate_verification_yaml.py'
        )
        result = subprocess.run(
            [sys.executable, script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running script: {result.stderr}")
            raise AssertionError(f"Script failed: {result.stderr}")
        
        # Read and verify output
        with open(output_file, 'r') as f:
            output = f.read()
        
        # All three requirements should be considered standard (no "# FIX - Non-Standard Text" comments)
        lines = output.split('\n')
        
        # Find the verification sections
        test1_ver_idx = None
        test2_ver_idx = None
        test3_ver_idx = None
        for i, line in enumerate(lines):
            if 'ID: VREQU.DMGR.TEST.1' in line:
                test1_ver_idx = i
            if 'ID: VREQU.DMGR.TEST.2' in line:
                test2_ver_idx = i
            if 'ID: VREQU.DMGR.TEST.3' in line:
                test3_ver_idx = i
        
        assert test1_ver_idx is not None, "Should create verification for TEST.1"
        assert test2_ver_idx is not None, "Should create verification for TEST.2"
        assert test3_ver_idx is not None, "Should create verification for TEST.3"
        
        # Check lines before TEST.1 verification (should NOT have non-standard comment)
        lines_before_test1 = '\n'.join(lines[max(0, test1_ver_idx-3):test1_ver_idx])
        assert "# FIX - Non-Standard Text" not in lines_before_test1, \
            "TEST.1 (DMGR with 'shall set') should NOT be flagged as non-standard Text"
        
        # Check lines before TEST.2 verification (should NOT have non-standard comment)
        lines_before_test2 = '\n'.join(lines[max(0, test2_ver_idx-3):test2_ver_idx])
        assert "# FIX - Non-Standard Text" not in lines_before_test2, \
            "TEST.2 (DMGR with 'shall render') should NOT be flagged as non-standard Text"
        
        # Check lines before TEST.3 verification (should NOT have non-standard comment)
        lines_before_test3 = '\n'.join(lines[max(0, test3_ver_idx-3):test3_ver_idx])
        assert "# FIX - Non-Standard Text" not in lines_before_test3, \
            "TEST.3 (DMGR with 'shall set' but Name='Render') should NOT be flagged as non-standard Text"
        
        # Verify the transformation is correct for TEST.1
        # Should have "sets" (active voice, singular)
        test1_section = '\n'.join(lines[test1_ver_idx:test1_ver_idx+20])
        assert "sets the buffer size" in test1_section, \
            f"TEST.1 should transform 'shall set' to 'sets', got: {test1_section}"
        
        # Verify the transformation is correct for TEST.3 (edge case)
        # Name is "Render..." (not setting) but Text has "shall set"
        # Should still transform "shall set" to "sets" for DMGR
        test3_section = '\n'.join(lines[test3_ver_idx:test3_ver_idx+20])
        assert "sets the display mode" in test3_section, \
            f"TEST.3 should transform 'shall set' to 'sets' even with non-setting Name, got: {test3_section}"
        
        print("✓ End-to-end test passed")
        
    finally:
        # Clean up temporary files
        try:
            os.remove(input_file)
        except OSError:
            # Ignore cleanup errors (e.g., file already removed or missing).
            pass
        if output_file is not None:
            try:
                os.remove(output_file)
            except OSError:
                # Ignore cleanup errors for optional output file as they are non-fatal.
                pass


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing DMGR 'shall set' as standard text")
    print("=" * 60)
    
    try:
        test_is_standard_text_dmgr_shall_set()
        test_dmgr_shall_set_transformation()
        test_dmgr_shall_set_without_setting_name()
        test_end_to_end_dmgr_shall_set()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
