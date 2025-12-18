#!/usr/bin/env python3
"""
Test script for transform_text() replacement consistency.

This script validates that:
1. Replacement checks and operations both work on the post-rewrite text (joined).
2. Multi-line texts with "shall render" or "shall set" on non-first lines are handled.
3. Case-sensitive replacement rules are maintained.
4. No regressions to existing transformation behavior.
"""

import sys
import os

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import transform_text


def test_shall_render_single_line():
    """Test 'shall render' replacement on a single line."""
    print("Testing shall render on single line...")
    
    req_text = "(U) The system shall render the display."
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should not contain 'shall render' after transformation
    assert "shall render" not in result, f"Expected 'shall render' to be replaced, got: {result}"
    
    # Should contain 'renders' (singular form based on "the system")
    assert "renders" in result, f"Expected 'renders' in output, got: {result}"
    
    # Should start with classification and 'Verify'
    assert result.startswith("(U) Verify"), f"Expected to start with '(U) Verify', got: {result}"
    
    print(f"  Input:  {req_text}")
    print(f"  Output: {result}")
    print("  ✓ Passed")


def test_shall_render_multiline():
    """Test 'shall render' replacement when it appears on a non-first line."""
    print("\nTesting shall render on multi-line text...")
    
    req_text = """(U) The system
shall render the status indicator."""
    
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should not contain 'shall render' after transformation
    assert "shall render" not in result, f"Expected 'shall render' to be replaced, got: {result}"
    
    # Should contain 'renders' (singular form)
    assert "renders" in result, f"Expected 'renders' in output, got: {result}"
    
    print(f"  Input:  {repr(req_text)}")
    print(f"  Output: {repr(result)}")
    print("  ✓ Passed")


def test_shall_set_single_line_advanced():
    """Test 'shall set' replacement for advanced (BRDG/DMGR) items."""
    print("\nTesting shall set on single line (advanced + setting)...")
    
    req_text = "(U) The system shall set the timeout to 30."
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should not contain 'shall set' after transformation
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    
    # Should contain 'is set' (singular form based on "the system")
    assert "is set" in result, f"Expected 'is set' in output, got: {result}"
    
    print(f"  Input:  {req_text}")
    print(f"  Output: {result}")
    print("  ✓ Passed")


def test_shall_set_to_replacement():
    """Test 'shall set to' replacement to avoid duplication."""
    print("\nTesting shall set to replacement...")
    
    req_text = "(U) The configuration shall set to active mode."
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should not contain 'shall set to' or 'shall set'
    assert "shall set to" not in result, f"Expected 'shall set to' to be replaced, got: {result}"
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    
    # Should contain 'is set to' (not 'is set to to')
    assert "is set to" in result, f"Expected 'is set to' in output, got: {result}"
    assert "to to" not in result, f"Should not have duplicate 'to', got: {result}"
    
    print(f"  Input:  {req_text}")
    print(f"  Output: {result}")
    print("  ✓ Passed")


def test_shall_set_multiline():
    """Test 'shall set' replacement when it appears on a non-first line."""
    print("\nTesting shall set on multi-line text...")
    
    req_text = """(U) The configurations
shall set the mode to active."""
    
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should not contain 'shall set' after transformation
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    
    # Should contain 'are set' (plural form based on "configurations")
    assert "are set" in result, f"Expected 'are set' in output, got: {result}"
    
    print(f"  Input:  {repr(req_text)}")
    print(f"  Output: {repr(result)}")
    print("  ✓ Passed")


def test_case_sensitivity():
    """Test that replacement rules are case-sensitive."""
    print("\nTesting case sensitivity...")
    
    # 'Shall render' (capital S) should NOT be replaced
    # (Though in practice, requirement texts use lowercase 'shall')
    req_text = "(U) The system Shall render the display."
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should still contain 'Shall render' (capital S not replaced)
    # This validates case-sensitivity
    assert "Shall render" in result, f"Case-sensitive: 'Shall render' should not be replaced, got: {result}"
    
    print(f"  Input:  {req_text}")
    print(f"  Output: {result}")
    print("  ✓ Passed - case sensitivity maintained")


def test_no_replacement_when_not_present():
    """Test that text without 'shall render' or 'shall set' is handled correctly."""
    print("\nTesting text without shall render/set...")
    
    req_text = "(U) The system processes the input correctly."
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should just add 'Verify' prefix, no verb replacement
    assert result.startswith("(U) Verify"), f"Expected to start with '(U) Verify', got: {result}"
    assert "processes" in result, f"Original verb should be preserved, got: {result}"
    
    print(f"  Input:  {req_text}")
    print(f"  Output: {result}")
    print("  ✓ Passed")


def test_verify_prefix_already_present():
    """Test that text already starting with 'Verify' is handled correctly."""
    print("\nTesting text already starting with 'Verify'...")
    
    req_text = "Verify the system shall render the output."
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should keep 'Verify' and still replace 'shall render'
    assert result.startswith("Verify"), f"Expected to keep 'Verify' prefix, got: {result}"
    assert "shall render" not in result, f"Expected 'shall render' to be replaced, got: {result}"
    assert "renders" in result, f"Expected 'renders' in output, got: {result}"
    
    print(f"  Input:  {req_text}")
    print(f"  Output: {result}")
    print("  ✓ Passed")


def test_empty_text():
    """Test handling of empty text."""
    print("\nTesting empty text...")
    
    result = transform_text("", is_advanced=False, is_setting=False)
    
    # Should return a default verification message
    assert "Verify" in result, f"Expected default verification message, got: {result}"
    
    print(f"  Input:  (empty)")
    print(f"  Output: {result}")
    print("  ✓ Passed")


def test_advanced_non_setting():
    """Test advanced domain without setting semantics."""
    print("\nTesting advanced (DMGR) without setting semantics...")
    
    req_text = "(U) The system shall render the dashboard."
    result = transform_text(req_text, is_advanced=True, is_setting=False)
    
    # Should replace 'shall render' even in advanced mode when not setting
    assert "shall render" not in result, f"Expected 'shall render' to be replaced, got: {result}"
    assert "renders" in result, f"Expected 'renders' in output, got: {result}"
    
    # Should NOT replace with 'is set' since is_setting=False
    assert "is set" not in result, f"Should not contain 'is set', got: {result}"
    
    print(f"  Input:  {req_text}")
    print(f"  Output: {result}")
    print("  ✓ Passed")


def main():
    """Run all tests."""
    print("=" * 70)
    print("Testing transform_text() replacement consistency")
    print("=" * 70)
    
    try:
        test_shall_render_single_line()
        test_shall_render_multiline()
        test_shall_set_single_line_advanced()
        test_shall_set_to_replacement()
        test_shall_set_multiline()
        test_case_sensitivity()
        test_no_replacement_when_not_present()
        test_verify_prefix_already_present()
        test_empty_text()
        test_advanced_non_setting()
        
        print("\n" + "=" * 70)
        print("All transform_text() consistency tests passed! ✓")
        print("=" * 70)
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
