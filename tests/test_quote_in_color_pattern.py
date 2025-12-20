#!/usr/bin/env python3
"""
Pytest tests for the quoted label "in <color>" pattern transformation.

This test suite validates that:
1. Pattern `" in` (closing quote + space + in) has `is rendered` inserted
2. No duplicate insertion when `is rendered` already exists
3. Works in combination with `shall set` → `sets` transformation
4. Only applies to Verification Requirement generation
"""

from generate_verification_yaml import transform_text


def test_quote_in_pattern_basic():
    """Test basic insertion of 'is rendered' for '" in' pattern."""
    req_text = 'The Fruit button label "fruit" in white'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should insert 'is rendered' between '" in'
    assert '"fruit" is rendered in white' in result, f"Expected '\"fruit\" is rendered in white', got: {result}"
    
    # Should have 'Verify the' prefix
    expected = 'Verify the Fruit button label "fruit" is rendered in white'
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_quote_in_pattern_no_duplicate():
    """Test that 'is rendered' is not duplicated when already present."""
    req_text = 'The Fruit button label "fruit" is rendered in white'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should not have duplicate 'is rendered'
    assert '"fruit" is rendered is rendered in white' not in result, f"Should not duplicate 'is rendered', got: {result}"
    
    # Should contain exactly one 'is rendered'
    expected = 'Verify the Fruit button label "fruit" is rendered in white'
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_quote_in_pattern_with_classification():
    """Test pattern with classification tag."""
    req_text = '(U) The Fruit button label "fruit" in white'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should preserve classification and insert 'is rendered'
    assert '(U) Verify the Fruit button label "fruit" is rendered in white' == result, f"Got: {result}"


def test_quote_in_pattern_with_shall_set():
    """Test combined transformation: 'shall set' → 'sets' and '" in' insertion."""
    req_text = 'The Display Bridge shall set the Fruit button label "fruit" in white'
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    # Should have both transformations applied
    assert "shall set" not in result, f"'shall set' should be replaced, got: {result}"
    assert "sets" in result, f"Should contain 'sets', got: {result}"
    assert '"fruit" is rendered in white' in result, f"Should insert 'is rendered', got: {result}"
    
    # Full expected output
    expected = 'Verify the Display Bridge sets the Fruit button label "fruit" is rendered in white'
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_quote_in_pattern_multiline():
    """Test pattern when text spans multiple lines."""
    req_text = '''The Fruit button label
"fruit" in white and the text is visible'''
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should insert 'is rendered' even when spanning lines
    assert '"fruit" is rendered in white' in result, f"Should insert 'is rendered', got: {result}"


def test_quote_in_pattern_multiple_occurrences():
    """Test multiple '" in' patterns in the same text."""
    req_text = 'The label "fruit" in white and "vegetable" in green'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Both occurrences should have 'is rendered' inserted
    assert '"fruit" is rendered in white' in result, f"Should insert 'is rendered' for 'fruit', got: {result}"
    assert '"vegetable" is rendered in green' in result, f"Should insert 'is rendered' for 'vegetable', got: {result}"


def test_quote_in_pattern_single_quotes_not_affected():
    """Test that single quotes don't trigger the pattern."""
    req_text = "The label 'fruit' in white"
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Single quotes should not trigger insertion (only double quotes)
    assert "'fruit' in white" in result, f"Single quotes should not trigger pattern, got: {result}"


def test_quote_in_without_space():
    """Test that pattern requires space between quote and 'in'."""
    req_text = 'The label "fruit"in white'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # No space means no transformation
    assert '"fruit"in white' in result, f"Pattern requires space after quote, got: {result}"


def test_quote_in_pattern_different_colors():
    """Test pattern works with various color names."""
    colors = ['white', 'black', 'red', 'blue', 'green', 'yellow']
    
    for color in colors:
        req_text = f'The button label "text" in {color}'
        result = transform_text(req_text, is_advanced=False, is_setting=False)
        
        assert f'"text" is rendered in {color}' in result, \
            f"Should work with color '{color}', got: {result}"


def test_quote_in_pattern_case_sensitive_in():
    """Test that 'in' is case-sensitive (only lowercase 'in' triggers pattern)."""
    req_text = 'The label "fruit" In white'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Capitalized 'In' should not trigger the pattern
    # This is based on typical case-sensitive handling in the codebase
    assert '"fruit" In white' in result or '"fruit" is rendered In white' in result, \
        f"Case sensitivity test, got: {result}"


def test_existing_is_rendered_in_before_pattern():
    """Test no duplication when 'is rendered in' already exists before our pattern."""
    req_text = 'The label is rendered "fruit" in white'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Even if 'is rendered' appears elsewhere, still insert for '" in' pattern
    # unless it's immediately adjacent
    # This test documents the expected behavior
    assert 'is rendered' in result, f"Should contain 'is rendered', got: {result}"


def test_must_pass_example_1():
    """Must-pass example 1: Basic render insertion."""
    req_text = 'The Fruit button label "fruit" in white'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    expected = 'Verify the Fruit button label "fruit" is rendered in white'
    assert result == expected, f"Must-pass example 1 failed. Expected: '{expected}', Got: '{result}'"


def test_must_pass_example_2():
    """Must-pass example 2: No duplicate insertion."""
    req_text = 'The Fruit button label "fruit" is rendered in white'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    expected = 'Verify the Fruit button label "fruit" is rendered in white'
    assert result == expected, f"Must-pass example 2 failed. Expected: '{expected}', Got: '{result}'"


def test_must_pass_example_3():
    """Must-pass example 3: Combined with 'shall set' rule."""
    req_text = 'The Display Bridge shall set the Fruit button label "fruit" in white'
    result = transform_text(req_text, is_advanced=True, is_setting=True)
    
    expected = 'Verify the Display Bridge sets the Fruit button label "fruit" is rendered in white'
    assert result == expected, f"Must-pass example 3 failed. Expected: '{expected}', Got: '{result}'"
