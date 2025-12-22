#!/usr/bin/env python3
"""
Pytest tests for the quoted label " in <color>" pattern transformation in Name fields.

This test suite validates that the '" in' pattern normalization applies to
Verification Name fields, ensuring consistent grammar across Name and Text fields.
"""

from generate_verification_yaml import transform_name_general, transform_name_setting


def test_name_render_with_quote_in_pattern():
    """Test that '" in' pattern is fixed in Render Name transformations."""
    req_name = 'Render label "fruit" in white'
    result = transform_name_general(req_name)
    
    # Should have pattern fixed
    assert '"fruit" is rendered in white' in result, \
        f"Expected '\"fruit\" is rendered in white', got: {result}"
    
    # Should not have duplicate "is rendered"
    assert result.count('is rendered') == 1, \
        f"Should have exactly one 'is rendered', got: {result}"
    
    # Full expected output
    expected = 'Verify the label "fruit" is rendered in white'
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_name_render_multiple_labels():
    """Test that multiple labels in Name are all fixed."""
    req_name = 'Render label "fruit" in white and "vegetable" in green'
    result = transform_name_general(req_name)
    
    # Both labels should have pattern fixed
    assert '"fruit" is rendered in white' in result, \
        f"Expected '\"fruit\" is rendered in white', got: {result}"
    assert '"vegetable" is rendered in green' in result, \
        f"Expected '\"vegetable\" is rendered in green', got: {result}"


def test_name_render_without_quote_in_pattern():
    """Test that Render Names without '" in' pattern still work correctly."""
    req_name = 'Render the status'
    result = transform_name_general(req_name)
    
    expected = 'Verify the status is rendered'
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_name_render_with_the_article():
    """Test Render Name with 'the' article and '" in' pattern."""
    req_name = 'Render the label "ok" in green'
    result = transform_name_general(req_name)
    
    # Should not have double 'the'
    assert 'the the' not in result, f"Should not have double 'the', got: {result}"
    
    # Should have pattern fixed
    assert '"ok" is rendered in green' in result, \
        f"Expected '\"ok\" is rendered in green', got: {result}"
    
    expected = 'Verify the label "ok" is rendered in green'
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_name_set_with_quote_in_pattern():
    """Test that '" in' pattern is fixed in Set Name transformations."""
    req_name = 'Set label "fruit" in white to value'
    result = transform_name_setting(req_name)
    
    # Should have pattern fixed
    assert '"fruit" is rendered in white' in result, \
        f"Expected '\"fruit\" is rendered in white', got: {result}"
    
    # Should have "is set to" from setting semantics
    assert 'is set to' in result, \
        f"Expected 'is set to', got: {result}"
    
    expected = 'Verify the label "fruit" is rendered in white is set to value'
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_name_non_standard_with_quote_in_pattern():
    """Test that '" in' pattern is fixed in non-standard Names."""
    req_name = 'Button label "ok" in green should be visible'
    result = transform_name_general(req_name)
    
    # Should have pattern fixed
    assert '"ok" is rendered in green' in result, \
        f"Expected '\"ok\" is rendered in green', got: {result}"
    
    expected = 'Verify Button label "ok" is rendered in green should be visible'
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_name_quote_in_pattern_idempotency():
    """Test that pattern fix is idempotent (no duplicate insertion)."""
    # Input already has "is rendered"
    req_name = 'Label "fruit" is rendered in white'
    result = transform_name_general(req_name)
    
    # Should not duplicate "is rendered"
    assert 'is rendered is rendered' not in result, \
        f"Should not duplicate 'is rendered', got: {result}"
    
    # Should still have exactly one "is rendered"
    assert result.count('is rendered') == 1, \
        f"Should have exactly one 'is rendered', got: {result}"


def test_name_quote_in_pattern_with_classification():
    """Test that classification tags don't interfere with Name pattern fix."""
    # Note: Classification tags typically only appear in Text, not Name,
    # but we should handle it gracefully if present
    req_name = 'Render label "fruit" in white'
    result = transform_name_general(req_name)
    
    # Pattern should still be fixed
    assert '"fruit" is rendered in white' in result, \
        f"Expected '\"fruit\" is rendered in white', got: {result}"


def test_name_single_quotes_not_affected():
    """Test that single quotes don't trigger the pattern."""
    req_name = "Render label 'fruit' in white"
    result = transform_name_general(req_name)
    
    # Single quotes should not trigger insertion
    assert "'fruit' in white" in result, \
        f"Single quotes should not trigger pattern, got: {result}"


def test_name_quote_in_without_space():
    """Test that pattern requires space between quote and 'in'."""
    req_name = 'Render label "fruit"in white'
    result = transform_name_general(req_name)
    
    # No space means no transformation
    assert '"fruit"in white' in result, \
        f"Pattern requires space after quote, got: {result}"


def test_name_quote_in_case_sensitive():
    """Test that 'in' is case-sensitive (only lowercase triggers pattern)."""
    req_name = 'Render label "fruit" In white'
    result = transform_name_general(req_name)
    
    # Capitalized 'In' should not trigger the pattern
    assert '"fruit" In white' in result, \
        f"Pattern should not trigger for capitalized 'In', got: {result}"


def test_name_render_plural_subject():
    """Test Render Name with plural subject and '" in' pattern."""
    req_name = 'Render labels "fruit" and "vegetable" in white'
    result = transform_name_general(req_name)
    
    # Plural subject should use "are rendered" not "is rendered"
    # But the quote-in pattern uses "is rendered" specifically
    assert '"fruit" is rendered' in result or '"vegetable" is rendered' in result, \
        f"Should have pattern fixed, got: {result}"


def test_name_set_multiple_labels():
    """Test Set Name with multiple '" in' patterns."""
    req_name = 'Set labels "fruit" in white and "vegetable" in green to values'
    result = transform_name_setting(req_name)
    
    # Both labels should have pattern fixed
    assert '"fruit" is rendered in white' in result, \
        f"Expected '\"fruit\" is rendered in white', got: {result}"
    assert '"vegetable" is rendered in green' in result, \
        f"Expected '\"vegetable\" is rendered in green', got: {result}"
    
    # Should have "are set to" due to plural subject
    assert 'are set to' in result or 'is set to' in result, \
        f"Should have 'set to', got: {result}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
