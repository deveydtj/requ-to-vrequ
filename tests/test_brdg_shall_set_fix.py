#!/usr/bin/env python3
"""
Pytest tests for BRDG "shall set" transformation fix.

This test suite validates that:
1. "shall set" is replaced with "sets" (singular) or "set" (plural) in active voice
2. "shall set to" is replaced with "sets to" or "set to" (avoiding "to to" duplication)
3. The transformation works correctly for both BRDG and DMGR items with setting semantics
4. Plurality detection works correctly for determining singular vs plural forms
"""

from generate_verification_yaml import transform_text


def test_shall_set_singular_active_voice():
    """Test 'shall set' replacement with singular subject (active voice)."""
    req_text = "(U) The Display Bridge shall set the overlay opacity."
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should not contain 'shall set' after transformation
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    
    # Should contain 'sets' (singular active voice), not 'is set' (passive voice)
    assert "sets" in result, f"Expected 'sets' in output, got: {result}"
    assert "is set" not in result, f"Should not contain passive voice 'is set', got: {result}"
    
    # Full expected output
    expected = "(U) Verify the Display Bridge sets the overlay opacity."
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_shall_set_plural_active_voice():
    """Test 'shall set' replacement with plural subject (active voice)."""
    req_text = "(U) The configurations shall set the timeout values."
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should not contain 'shall set' after transformation
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    
    # Should contain 'set the timeout' (plural active voice), not 'are set' (passive voice)
    assert "set the timeout" in result, f"Expected 'set the timeout' in output, got: {result}"
    assert "are set" not in result, f"Should not contain passive voice 'are set', got: {result}"


def test_shall_set_to_singular():
    """Test 'shall set to' replacement with singular subject."""
    req_text = "(U) The configuration shall set to active mode."
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should not contain 'shall set to' or 'shall set'
    assert "shall set to" not in result, f"Expected 'shall set to' to be replaced, got: {result}"
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    
    # Should contain 'sets to' (not 'sets to to' or 'is set to')
    assert "sets to" in result, f"Expected 'sets to' in output, got: {result}"
    assert "to to" not in result, f"Should not have duplicate 'to', got: {result}"
    assert "is set to" not in result, f"Should not contain passive voice 'is set to', got: {result}"


def test_shall_set_to_plural():
    """Test 'shall set to' replacement with plural subject."""
    req_text = "(U) The modules shall set to default mode."
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should not contain 'shall set to' or 'shall set'
    assert "shall set to" not in result, f"Expected 'shall set to' to be replaced, got: {result}"
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    
    # Should contain 'set to' (plural), not 'are set to'
    assert "set to" in result, f"Expected 'set to' in output, got: {result}"
    assert "to to" not in result, f"Should not have duplicate 'to', got: {result}"
    assert "are set to" not in result, f"Should not contain passive voice 'are set to', got: {result}"


def test_shall_set_multiline():
    """Test 'shall set' replacement when it appears on a non-first line."""
    req_text = """(U) The Display Bridge
shall set the overlay opacity to 50%."""
    
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should not contain 'shall set' after transformation
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    
    # Should contain 'sets' (singular form based on "Display Bridge")
    assert "sets" in result, f"Expected 'sets' in output, got: {result}"
    assert "is set" not in result, f"Should not contain passive voice 'is set', got: {result}"


def test_dmgr_shall_set():
    """Test that DMGR items also use active voice for 'shall set'."""
    req_text = "(U) The Data Manager shall set the buffer size."
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should not contain 'shall set' after transformation
    assert "shall set" not in result, f"Expected 'shall set' to be replaced, got: {result}"
    
    # Should contain 'sets' (singular active voice)
    assert "sets" in result, f"Expected 'sets' in output, got: {result}"
    assert "is set" not in result, f"Should not contain passive voice 'is set', got: {result}"


def test_non_advanced_no_replacement():
    """Test that non-advanced items don't get 'shall set' replacement."""
    req_text = "(U) The system shall set the timeout."
    result = transform_text(req_text, is_advanced=False, is_setting=True)
    
    # For non-advanced items, 'shall set' should remain unchanged
    # (or be handled differently - verifying current behavior)
    # Based on the code, replacement only happens when is_advanced=True
    assert "shall set" in result, f"Expected 'shall set' to remain for non-advanced items, got: {result}"


def test_non_setting_no_replacement():
    """Test that items without setting semantics don't get 'shall set' replacement."""
    req_text = "(U) The Bridge shall set the value."
    result = transform_text(req_text, is_advanced=True, is_setting=False)
    
    # For non-setting items, 'shall set' should remain unchanged
    assert "shall set" in result, f"Expected 'shall set' to remain for non-setting items, got: {result}"


def test_case_sensitivity():
    """Test that replacement is case-sensitive."""
    req_text = "(U) The Bridge Shall Set the value."
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should NOT replace 'Shall Set' (capitalized)
    assert "Shall Set" in result, f"Case-sensitive: 'Shall Set' should not be replaced, got: {result}"


def test_brdg_example_from_issue():
    """Test the exact example from the GitHub issue."""
    req_text = "The Display Bridge shall set the overlay opacity."
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Expected output based on issue description
    expected = "Verify the Display Bridge sets the overlay opacity."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
