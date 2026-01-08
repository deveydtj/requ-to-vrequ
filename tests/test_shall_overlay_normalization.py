#!/usr/bin/env python3
"""
Test script for 'shall overlay' verb normalization in Verification generation.

This test validates that requirements with "shall overlay" in the Text field:
1. Are considered standard for DMGR domain
2. Get transformed to "overlay" (plural) or "overlays" (singular) with correct subject-verb agreement
3. Work correctly in normalize_quote_in_pattern() context detection
4. Generate proper end-to-end output
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
    normalize_quote_in_pattern,
    choose_present_verb,
)


def test_is_standard_text_with_shall_overlay():
    """Test that DMGR with 'shall overlay' is considered standard."""
    print("Testing is_standard_text for DMGR with 'shall overlay'...")
    
    # DMGR with "shall overlay" should be standard
    assert is_standard_text("The display shall overlay the indicator.", "DMGR"), \
        "DMGR with 'shall overlay' should be standard"
    
    # DMGR with "shall render" should still be standard
    assert is_standard_text("The display shall render the indicator.", "DMGR"), \
        "DMGR with 'shall render' should be standard"
    
    # DMGR with "shall set" should still be standard
    assert is_standard_text("The system shall set the timeout.", "DMGR"), \
        "DMGR with 'shall set' should be standard"
    
    # DMGR with multiple standard verbs should be standard
    assert is_standard_text("The system shall overlay the UI and shall render the status.", "DMGR"), \
        "DMGR with both 'shall overlay' and 'shall render' should be standard"
    
    # DMGR with none of the standard verbs should be non-standard
    assert not is_standard_text("The system shall configure the timeout.", "DMGR"), \
        "DMGR without 'shall render', 'shall set', or 'shall overlay' should be non-standard"
    
    # BRDG with "shall overlay" should NOT be standard (BRDG only accepts "shall set")
    assert not is_standard_text("The bridge shall overlay the indicator.", "BRDG"), \
        "BRDG with 'shall overlay' should be non-standard"
    
    # OTHER domain with "shall overlay" should be standard (OTHER accepts any non-empty text)
    assert is_standard_text("The system shall overlay the indicator.", "OTHER"), \
        "OTHER domain with 'shall overlay' should be standard"
    
    print("✓ is_standard_text tests passed")


def test_choose_present_verb_overlay():
    """Test that choose_present_verb handles 'overlay' correctly."""
    print("\nTesting choose_present_verb for 'overlay'...")
    
    # Singular subject should get "overlays"
    assert choose_present_verb("overlay", "display") == "overlays", \
        "Singular subject should use 'overlays'"
    
    assert choose_present_verb("overlay", "the display") == "overlays", \
        "Singular subject 'the display' should use 'overlays'"
    
    # Plural subject should get "overlay"
    assert choose_present_verb("overlay", "displays") == "overlay", \
        "Plural subject should use 'overlay'"
    
    assert choose_present_verb("overlay", "the displays") == "overlay", \
        "Plural subject 'the displays' should use 'overlay'"
    
    assert choose_present_verb("overlay", "display and indicator") == "overlay", \
        "Coordinated subjects should use 'overlay'"
    
    print("✓ choose_present_verb tests passed")


def test_transform_text_shall_overlay_singular():
    """Test that transform_text converts 'shall overlay' to 'overlays' for singular subjects."""
    print("\nTesting transform_text for 'shall overlay' with singular subject...")
    
    req_text = "(U) The display shall overlay the indicator on the screen."
    result = transform_text(req_text, is_advanced=True, is_setting=False, is_dmgr=True)
    
    # Should transform "shall overlay" to "overlays" (singular)
    assert "shall overlay" not in result, f"Expected 'shall overlay' to be replaced, got: {result}"
    assert "overlays" in result, f"Expected 'overlays' in output, got: {result}"
    
    expected = "(U) Verify the display overlays the indicator on the screen."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
    
    print("✓ Singular subject transformation test passed")


def test_transform_text_shall_overlay_plural():
    """Test that transform_text converts 'shall overlay' to 'overlay' for plural subjects."""
    print("\nTesting transform_text for 'shall overlay' with plural subject...")
    
    req_text = "(U) The displays shall overlay the indicators on the screen."
    result = transform_text(req_text, is_advanced=True, is_setting=False, is_dmgr=True)
    
    # Should transform "shall overlay" to "overlay" (plural)
    assert "shall overlay" not in result, f"Expected 'shall overlay' to be replaced, got: {result}"
    assert "overlay the indicators" in result, f"Expected 'overlay the indicators' in output, got: {result}"
    
    expected = "(U) Verify the displays overlay the indicators on the screen."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
    
    print("✓ Plural subject transformation test passed")


def test_transform_text_shall_overlay_without_classification():
    """Test 'shall overlay' transformation without classification tags for DMGR."""
    print("\nTesting transform_text for 'shall overlay' without classification (DMGR)...")
    
    req_text = "The system shall overlay the status indicator."
    # Must set is_dmgr=True for overlay transformation to happen
    result = transform_text(req_text, is_advanced=True, is_setting=False, is_dmgr=True)
    
    # Should transform "shall overlay" to "overlays" (DMGR only)
    assert "shall overlay" not in result, f"Expected 'shall overlay' to be replaced, got: {result}"
    assert "overlays" in result, f"Expected 'overlays' in output, got: {result}"
    
    expected = "Verify the system overlays the status indicator."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
    
    print("✓ Transformation without classification test passed")


def test_transform_text_multiple_verbs():
    """Test that both 'shall render' and 'shall overlay' are transformed correctly."""
    print("\nTesting transform_text with multiple verb normalizations...")
    
    req_text = "(CUI) The display shall render the UI and shall overlay the indicator."
    result = transform_text(req_text, is_advanced=True, is_setting=False, is_dmgr=True)
    
    # Both verbs should be transformed
    assert "shall render" not in result, f"Expected 'shall render' to be replaced, got: {result}"
    assert "shall overlay" not in result, f"Expected 'shall overlay' to be replaced, got: {result}"
    assert "renders" in result, f"Expected 'renders' in output, got: {result}"
    assert "overlays" in result, f"Expected 'overlays' in output, got: {result}"
    
    expected = "(CUI) Verify the display renders the UI and overlays the indicator."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
    
    print("✓ Multiple verb normalization test passed")


def test_normalize_quote_in_with_shall_overlay():
    """Test that normalize_quote_in_pattern skips insertion when 'shall overlay' is present."""
    print("\nTesting normalize_quote_in_pattern with 'shall overlay'...")
    
    text = 'The Display Format shall overlay the UI label "status" in white'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert 'is rendered' because 'shall overlay' governs the label
    assert '"status" in white' in result, \
        f"Should not insert 'is rendered' when 'shall overlay' is present, got: {result}"
    assert '"status" is rendered in white' not in result, \
        f"Should not insert 'is rendered' when 'shall overlay' is present, got: {result}"
    
    print("✓ normalize_quote_in_pattern test passed")


def test_normalize_quote_in_with_overlays():
    """Test that normalize_quote_in_pattern skips insertion when 'overlays' is present."""
    print("\nTesting normalize_quote_in_pattern with 'overlays'...")
    
    text = 'The Display Format overlays the UI label "status" in white'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert 'is rendered' because 'overlays' governs the label
    assert '"status" in white' in result, \
        f"Should not insert 'is rendered' when 'overlays' is present, got: {result}"
    assert '"status" is rendered in white' not in result, \
        f"Should not insert 'is rendered' when 'overlays' is present, got: {result}"
    
    print("✓ normalize_quote_in_pattern with 'overlays' test passed")


def test_normalize_quote_in_with_overlay():
    """Test that normalize_quote_in_pattern skips insertion when 'overlay' is present."""
    print("\nTesting normalize_quote_in_pattern with 'overlay'...")
    
    text = 'The formats overlay the UI label "status" in white'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert 'is rendered' because 'overlay' governs the label
    assert '"status" in white' in result, \
        f"Should not insert 'is rendered' when 'overlay' is present, got: {result}"
    assert '"status" is rendered in white' not in result, \
        f"Should not insert 'is rendered' when 'overlay' is present, got: {result}"
    
    print("✓ normalize_quote_in_pattern with 'overlay' test passed")


def test_normalize_quote_in_with_overlaying():
    """Test that normalize_quote_in_pattern skips insertion when 'overlaying' gerund is present."""
    print("\nTesting normalize_quote_in_pattern with 'overlaying'...")
    
    text = 'When overlaying the UI label "status" in white'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert 'is rendered' because 'overlaying' governs the label
    assert '"status" in white' in result, \
        f"Should not insert 'is rendered' when 'overlaying' is present, got: {result}"
    assert '"status" is rendered in white' not in result, \
        f"Should not insert 'is rendered' when 'overlaying' is present, got: {result}"
    
    print("✓ normalize_quote_in_pattern with 'overlaying' test passed")


def test_transform_text_shall_overlay_brdg_no_transform():
    """Test that transform_text does NOT transform 'shall overlay' for BRDG domain."""
    print("\nTesting transform_text for 'shall overlay' with BRDG (should NOT transform)...")
    
    req_text = "(U) The bridge shall overlay the indicator on the screen."
    result = transform_text(req_text, is_advanced=True, is_setting=False, is_dmgr=False)
    
    # Should NOT transform "shall overlay" for BRDG
    assert "shall overlay" in result, f"Expected 'shall overlay' to remain unchanged for BRDG, got: {result}"
    assert "overlays" not in result, f"Should not transform to 'overlays' for BRDG, got: {result}"
    
    expected = "(U) Verify the bridge shall overlay the indicator on the screen."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
    
    print("✓ BRDG no-transform test passed")


def test_transform_text_shall_overlay_other_no_transform():
    """Test that transform_text does NOT transform 'shall overlay' for OTHER domain."""
    print("\nTesting transform_text for 'shall overlay' with OTHER (should NOT transform)...")
    
    req_text = "(U) The system shall overlay the indicator."
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should NOT transform "shall overlay" for OTHER domain
    assert "shall overlay" in result, f"Expected 'shall overlay' to remain unchanged for OTHER, got: {result}"
    assert "overlays" not in result, f"Should not transform to 'overlays' for OTHER, got: {result}"
    
    expected = "(U) Verify the system shall overlay the indicator."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
    
    print("✓ OTHER no-transform test passed")


def test_end_to_end_dmgr_shall_overlay():
    """Test the full pipeline with DMGR requirements containing 'shall overlay'."""
    print("\nTesting end-to-end DMGR 'shall overlay' behavior...")
    
    test_yaml = """# Test DMGR with shall overlay
- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.1
  Name: Render the status overlay
  Text: |
    (U) The display shall overlay the status indicator.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.2
  Name: Render multiple indicators
  Text: |
    (U) The displays shall overlay the status indicators.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.3
  Name: Render and overlay UI
  Text: |
    (U) The system shall render the UI and shall overlay the warning icon.
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
            "TEST.1 (DMGR with 'shall overlay') should NOT be flagged as non-standard Text"
        
        # Check lines before TEST.2 verification (should NOT have non-standard comment)
        lines_before_test2 = '\n'.join(lines[max(0, test2_ver_idx-3):test2_ver_idx])
        assert "# FIX - Non-Standard Text" not in lines_before_test2, \
            "TEST.2 (DMGR with 'shall overlay', plural) should NOT be flagged as non-standard Text"
        
        # Check lines before TEST.3 verification (should NOT have non-standard comment)
        lines_before_test3 = '\n'.join(lines[max(0, test3_ver_idx-3):test3_ver_idx])
        assert "# FIX - Non-Standard Text" not in lines_before_test3, \
            "TEST.3 (DMGR with both 'shall render' and 'shall overlay') should NOT be flagged as non-standard Text"
        
        # Verify the transformation is correct for TEST.1 (singular)
        # Should have "overlays" (active voice, singular)
        test1_section = '\n'.join(lines[test1_ver_idx:test1_ver_idx+20])
        assert "overlays the status indicator" in test1_section, \
            f"TEST.1 should transform 'shall overlay' to 'overlays', got: {test1_section}"
        assert "shall overlay" not in test1_section, \
            f"TEST.1 should not contain 'shall overlay' in verification, got: {test1_section}"
        
        # Verify the transformation is correct for TEST.2 (plural)
        # Should have "overlay" (active voice, plural)
        test2_section = '\n'.join(lines[test2_ver_idx:test2_ver_idx+20])
        assert "overlay the status indicators" in test2_section, \
            f"TEST.2 should transform 'shall overlay' to 'overlay', got: {test2_section}"
        assert "shall overlay" not in test2_section, \
            f"TEST.2 should not contain 'shall overlay' in verification, got: {test2_section}"
        
        # Verify the transformation is correct for TEST.3 (multiple verbs)
        # Should have both "renders" and "overlays"
        test3_section = '\n'.join(lines[test3_ver_idx:test3_ver_idx+20])
        assert "renders the UI" in test3_section, \
            f"TEST.3 should transform 'shall render' to 'renders', got: {test3_section}"
        assert "overlays the warning icon" in test3_section, \
            f"TEST.3 should transform 'shall overlay' to 'overlays', got: {test3_section}"
        assert "shall render" not in test3_section and "shall overlay" not in test3_section, \
            f"TEST.3 should not contain 'shall render' or 'shall overlay' in verification, got: {test3_section}"
        
        print("✓ End-to-end test passed")
        
    finally:
        # Clean up temporary files
        try:
            os.remove(input_file)
        except OSError:
            # Ignore cleanup errors (e.g., file already deleted or not found)
            pass
        if output_file is not None:
            try:
                os.remove(output_file)
            except OSError:
                # Ignore cleanup errors for optional output file
                pass


def test_end_to_end_brdg_shall_overlay_non_standard():
    """Test that BRDG requirements with 'shall overlay' are flagged as non-standard."""
    print("\nTesting end-to-end BRDG 'shall overlay' non-standard behavior...")
    
    test_yaml = """# Test BRDG with shall overlay (non-standard)
- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.TEST.1
  Name: Set the display mode
  Text: |
    (U) The bridge shall overlay the status indicator.
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
        
        lines = output.split('\n')
        
        # Find the verification section
        test1_ver_idx = None
        for i, line in enumerate(lines):
            if 'ID: VREQU.BRDG.TEST.1' in line:
                test1_ver_idx = i
                break
        
        assert test1_ver_idx is not None, "Should create verification for BRDG TEST.1"
        
        # Check lines before TEST.1 verification (should have non-standard comment)
        lines_before_test1 = '\n'.join(lines[max(0, test1_ver_idx-3):test1_ver_idx])
        assert "# FIX - Non-Standard Text" in lines_before_test1, \
            "BRDG with 'shall overlay' should be flagged as non-standard Text"
        
        # Verify that "shall overlay" is NOT transformed
        test1_section = '\n'.join(lines[test1_ver_idx:test1_ver_idx+20])
        assert "shall overlay the status indicator" in test1_section, \
            f"BRDG should NOT transform 'shall overlay', got: {test1_section}"
        assert "overlays" not in test1_section, \
            f"BRDG should not contain 'overlays' (no transformation), got: {test1_section}"
        
        print("✓ End-to-end BRDG non-standard test passed")
        
    finally:
        # Clean up temporary files
        try:
            os.remove(input_file)
        except OSError:
            pass
        if output_file is not None:
            try:
                os.remove(output_file)
            except OSError:
                pass


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing 'shall overlay' verb normalization")
    print("=" * 60)
    
    try:
        test_is_standard_text_with_shall_overlay()
        test_choose_present_verb_overlay()
        test_transform_text_shall_overlay_singular()
        test_transform_text_shall_overlay_plural()
        test_transform_text_shall_overlay_without_classification()
        test_transform_text_multiple_verbs()
        test_transform_text_shall_overlay_brdg_no_transform()
        test_transform_text_shall_overlay_other_no_transform()
        test_normalize_quote_in_with_shall_overlay()
        test_normalize_quote_in_with_overlays()
        test_normalize_quote_in_with_overlay()
        test_normalize_quote_in_with_overlaying()
        test_end_to_end_dmgr_shall_overlay()
        test_end_to_end_brdg_shall_overlay_non_standard()
        
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
