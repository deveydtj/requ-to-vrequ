#!/usr/bin/env python3
"""
Tests for the "rendering" gerund form detection to prevent double-render insertion.

Issue: Pattern 3 in normalize_quote_in_pattern checks for the gerund form "rendering"
to skip insertion of "is rendered", but this pattern needs to be checked independently
of Pattern 2 (render/renders), not as an elif branch.

These tests verify that:
1. The "rendering" gerund form is correctly detected and skips insertion
2. Pattern 3 is checked independently regardless of Pattern 2 results
3. The fix handles cases where Pattern 2 matches but doesn't trigger skip_insertion
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    normalize_quote_in_pattern,
    transform_text,
    generate_verification_items
)


def test_normalize_quote_in_with_rendering():
    """Test that normalize_quote_in_pattern skips insertion when 'rendering' is present."""
    text = 'The system is rendering the UI button label "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert 'is rendered' because 'rendering' governs the label (gerund form)
    assert '"button" in white' in result, \
        f"Should not insert 'is rendered' when 'rendering' is present, got: {result}"
    assert '"button" is rendered in white' not in result, \
        f"Should not insert 'is rendered' when 'rendering' is present, got: {result}"


def test_normalize_quote_in_with_rendering_alone():
    """Test 'rendering' without any other render verb forms."""
    text = 'While rendering "label" in blue'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert because 'rendering' is present
    assert '"label" in blue' in result, \
        f"Should not insert 'is rendered' when only 'rendering' is present, got: {result}"
    assert '"label" is rendered in blue' not in result, \
        f"Should not insert 'is rendered' when only 'rendering' is present, got: {result}"


def test_normalize_quote_in_with_rendering_and_passive_renders():
    """Test that Pattern 3 (rendering) is checked independently of Pattern 2 (renders).
    
    This is the key test for the control flow bug fix. If 'renders' is found but
    in passive voice (e.g., 'is renders'), Pattern 2 won't set skip_insertion to True.
    Pattern 3 should still check for 'rendering' independently and skip insertion if found.
    """
    # This text has passive "is renders" (Pattern 2 matches but doesn't skip)
    # AND has "rendering" (Pattern 3 should skip)
    text = 'The display is renders and is rendering the button "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # Pattern 3 should catch 'rendering' and skip insertion
    assert '"button" in white' in result, \
        f"Pattern 3 should skip insertion when 'rendering' is present, got: {result}"
    assert '"button" is rendered in white' not in result, \
        f"Pattern 3 should prevent double-render even when Pattern 2 doesn't skip, got: {result}"


def test_normalize_quote_in_with_command_render_and_rendering():
    """Test that Pattern 3 is checked even when Pattern 2 finds command-form 'Render'.
    
    Command-form 'Render' at the start doesn't trigger skip_insertion in Pattern 2,
    but if 'rendering' is also present, Pattern 3 should catch it.
    """
    text = 'Render the UI while rendering "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # Pattern 3 should detect 'rendering' and skip insertion
    assert '"button" in white' in result, \
        f"Pattern 3 should skip insertion when 'rendering' is present, got: {result}"
    assert '"button" is rendered in white' not in result, \
        f"Pattern 3 should work independently of command-form Render detection, got: {result}"


def test_transform_text_with_rendering():
    """Test transform_text with a requirement containing 'rendering'."""
    req_text = 'The system is rendering the UI button label "button" in white.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should have 'rendering' preserved
    assert 'rendering' in result.lower(), f"Should preserve 'rendering', got: {result}"
    
    # Should NOT have duplicate 'is rendered'
    assert '"button" is rendered in white' not in result, \
        f"Should not have duplicate render semantics, got: {result}"
    
    # Should keep label phrase without duplicate 'is rendered'
    assert '"button" in white' in result, \
        f"Should keep label phrase without duplicate 'is rendered', got: {result}"


def test_rendering_case_insensitive():
    """Test that 'rendering' detection is case-insensitive."""
    text = 'The system is Rendering the UI button label "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert 'is rendered' (case-insensitive match)
    assert '"button" in white' in result, \
        f"Should handle 'Rendering' (capitalized), got: {result}"
    assert '"button" is rendered in white' not in result, \
        f"Should handle 'Rendering' (capitalized), got: {result}"


def test_rendering_word_boundary():
    """Test that 'rendering' must be a complete word (word boundary check)."""
    # Text with 'rendering' as part of another word should NOT skip insertion
    text = 'The prerendering system displays "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # SHOULD insert because 'prerendering' is not the same as 'rendering'
    # (word boundary \b should prevent matching 'rendering' inside 'prerendering')
    assert '"button" is rendered in white' in result, \
        f"Should insert 'is rendered' when 'rendering' is part of another word, got: {result}"


def test_end_to_end_with_rendering():
    """End-to-end test with a requirement containing 'rendering'."""
    req_item = {
        'Type': 'Requirement',
        'ID': 'REQU.TEST.RENDERING.1',
        'Name': 'The system is rendering the UI button label "button" in white',
        'Text': 'The system is rendering the UI button label "button" in white.',
        'Verified_By': '',
        'Traced_To': '',
        '_order': [('key', 'ID'), ('key', 'Name'), ('key', 'Text')]
    }
    
    result = generate_verification_items([req_item])
    
    # Find the verification item
    ver_item = None
    for item in result:
        if item.get('Type') == 'Verification':
            ver_item = item
            break
    
    assert ver_item is not None, "Should generate a verification item"
    
    # Check Text field - should NOT have duplicate 'is rendered'
    text = ver_item['Text']
    assert '"button" is rendered in white' not in text.lower(), \
        f"Should not have duplicate render semantics in Text, got: {text}"
    
    # Should preserve the rendering context
    assert 'rendering' in text.lower(), \
        f"Should preserve 'rendering' in Text, got: {text}"


def test_multiple_patterns_independence():
    """Test that all three patterns are checked independently.
    
    This test verifies the fix for the control flow bug where Pattern 3
    was only checked when Pattern 2's render_match was False.
    """
    # Text with all patterns: "shall render", "renders", and "rendering"
    text = 'The system shall render and renders while rendering "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # Any one of the patterns should trigger skip_insertion
    assert '"button" in white' in result, \
        f"Should skip insertion when any render pattern is present, got: {result}"
    assert '"button" is rendered in white' not in result, \
        f"Should not insert when multiple render patterns are present, got: {result}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
