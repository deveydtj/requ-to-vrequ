#!/usr/bin/env python3
"""
Pytest tests for the double render bug fix.

This test suite validates that when "shall render" appears before a label
with the '" in <color>' pattern, the transformation does not produce both
"renders" (active voice) and "is rendered" (passive voice).

The correct behavior is to use only the passive voice "is rendered" that is
inserted by the normalize_quote_in_pattern() function.
"""

from generate_verification_yaml import transform_text


def test_shall_render_with_quote_in_pattern():
    """Test that 'shall render' before '" in' pattern doesn't cause double render."""
    req_text = '(CUI) The Display Format shall render the UI button label "button" in white.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should NOT have both "renders" and "is rendered"
    has_renders = 'renders' in result
    has_is_rendered = 'is rendered' in result
    
    assert not (has_renders and has_is_rendered), \
        f"Should not have both 'renders' and 'is rendered', got: {result}"
    
    # Should have "is rendered" (passive voice) from the pattern normalization
    assert 'is rendered' in result, \
        f"Should have 'is rendered' from pattern normalization, got: {result}"
    
    # Should NOT have "renders" (active voice)
    assert 'renders' not in result, \
        f"Should not have 'renders' (active voice), got: {result}"
    
    # The expected output should have the label pattern properly fixed
    assert '"button" is rendered in white' in result, \
        f"Expected '\"button\" is rendered in white', got: {result}"


def test_shall_render_with_quote_in_pattern_plural():
    """Test plural subject with 'shall render' before '" in' pattern."""
    req_text = 'The Display Formats shall render the UI button labels "ok" and "cancel" in white.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should NOT have both "render" and "is rendered"
    has_render = ' render ' in result
    has_is_rendered = 'is rendered' in result
    
    assert not (has_render and has_is_rendered), \
        f"Should not have both 'render' and 'is rendered', got: {result}"
    
    # Should have "is rendered" from pattern normalization
    assert 'is rendered' in result, \
        f"Should have 'is rendered', got: {result}"


def test_shall_render_without_quote_in_pattern():
    """Test that 'shall render' without '" in' pattern still works correctly."""
    req_text = 'The Display Format shall render the status.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Without the '" in' pattern, we should have "renders" (active voice)
    assert 'renders' in result, \
        f"Should have 'renders' when no pattern to normalize, got: {result}"
    
    # Should NOT have "is rendered" since there's no pattern
    assert 'is rendered' not in result, \
        f"Should not have 'is rendered' without pattern, got: {result}"
    
    expected = 'Verify the Display Format renders the status.'
    assert result == expected, f"Expected '{expected}', got: '{result}'"


def test_shall_render_multiple_labels():
    """Test 'shall render' with multiple '" in' patterns."""
    req_text = 'The Display shall render label "fruit" in white and "vegetable" in green.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should NOT have "renders"
    assert 'renders' not in result, \
        f"Should not have 'renders', got: {result}"
    
    # Should have "is rendered" for both labels
    assert '"fruit" is rendered in white' in result, \
        f"Should have '\"fruit\" is rendered in white', got: {result}"
    assert '"vegetable" is rendered in green' in result, \
        f"Should have '\"vegetable\" is rendered in green', got: {result}"


def test_shall_render_with_classification():
    """Test that classification tags don't interfere with the fix."""
    req_text = '(U) The Component shall render the label "test" in red.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should start with classification tag
    assert result.startswith('(U) '), \
        f"Should preserve classification tag, got: {result}"
    
    # Should NOT have both "renders" and "is rendered"
    has_renders = 'renders' in result
    has_is_rendered = 'is rendered' in result
    
    assert not (has_renders and has_is_rendered), \
        f"Should not have both 'renders' and 'is rendered', got: {result}"


def test_shall_render_with_quote_in_pattern_mixed_content():
    """Test text with 'shall render' and '" in' pattern plus other content."""
    req_text = 'The UI shall render the button label "OK" in green when active.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should NOT have "renders"
    assert 'renders' not in result, \
        f"Should not have 'renders', got: {result}"
    
    # Should have the pattern fixed
    assert '"OK" is rendered in green' in result, \
        f"Should have '\"OK\" is rendered in green', got: {result}"
    
    # Should preserve the trailing content
    assert 'when active' in result, \
        f"Should preserve 'when active', got: {result}"


def test_shall_render_case_sensitivity():
    """Test that 'Shall Render' (capitalized) is not affected by the fix."""
    req_text = 'The Display Shall Render the label "test" in white.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # 'Shall Render' should NOT be replaced (case-sensitive)
    assert 'Shall Render' in result, \
        f"Should preserve 'Shall Render' (case mismatch), got: {result}"
    
    # The pattern should still be fixed though
    assert 'is rendered' in result, \
        f"Pattern should still be fixed, got: {result}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
