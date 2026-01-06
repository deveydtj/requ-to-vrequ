#!/usr/bin/env python3
"""
Tests for the fix to prevent double-render insertion in sentence-style requirements.

Issue: When a Requirement Name or Text contains both:
- An explicit render verb phrase (e.g., 'shall render')
- A quoted label with color phrase ('"button" in white')

The generator should produce Verification output with exactly ONE render expression,
not both 'renders' (from shall render normalization) and 'is rendered' (from quote-in
pattern normalization).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    normalize_quote_in_pattern,
    transform_text,
    generate_verification_items
)


def test_normalize_quote_in_with_shall_render():
    """Test that normalize_quote_in_pattern skips insertion when 'shall render' is present."""
    text = 'The Display Format shall render the UI button label "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert 'is rendered' because 'shall render' governs the label
    assert '"button" in white' in result, \
        f"Should not insert 'is rendered' when 'shall render' is present, got: {result}"
    assert '"button" is rendered in white' not in result, \
        f"Should not insert 'is rendered' when 'shall render' is present, got: {result}"


def test_normalize_quote_in_with_renders():
    """Test that normalize_quote_in_pattern skips insertion when 'renders' is present."""
    text = 'The Display Format renders the UI button label "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert 'is rendered' because 'renders' governs the label
    assert '"button" in white' in result, \
        f"Should not insert 'is rendered' when 'renders' is present, got: {result}"
    assert '"button" is rendered in white' not in result, \
        f"Should not insert 'is rendered' when 'renders' is present, got: {result}"


def test_normalize_quote_in_with_render():
    """Test that normalize_quote_in_pattern skips insertion when 'render' is present."""
    text = 'The formats render the UI button label "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # Should NOT insert 'is rendered' because 'render' governs the label
    assert '"button" in white' in result, \
        f"Should not insert 'is rendered' when 'render' is present, got: {result}"
    assert '"button" is rendered in white' not in result, \
        f"Should not insert 'is rendered' when 'render' is present, got: {result}"


def test_normalize_quote_in_without_render_verb():
    """Test that normalize_quote_in_pattern DOES insert when no render verb is present."""
    text = 'The UI button label "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # SHOULD insert 'is rendered' because no render verb governs the label
    assert '"button" is rendered in white' in result, \
        f"Should insert 'is rendered' when no render verb is present, got: {result}"


def test_normalize_quote_in_with_passive_is_rendered():
    """Test that normalize_quote_in_pattern DOES insert when only passive 'is rendered' is present."""
    # This tests that we distinguish active from passive voice
    text = 'The label "fruit" is rendered in white and "vegetable" in green'
    result = normalize_quote_in_pattern(text)
    
    # "fruit" already has "is rendered" - should not be duplicated
    assert '"fruit" is rendered is rendered' not in result
    
    # "vegetable" does not have "is rendered" and "is rendered" for "fruit" is passive,
    # not an active verb governing "vegetable" - should be inserted
    assert '"vegetable" is rendered in green' in result, \
        f"Should insert 'is rendered' for vegetable (passive voice doesn't govern it), got: {result}"


def test_transform_text_shall_render_with_quote_in():
    """Test that transform_text produces only one render expression for 'shall render' + '" in'."""
    req_text = '(CUI) The Display Format shall render the UI button label "button" in white.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should have 'renders' (from 'shall render' normalization)
    assert 'renders' in result, f"Should have 'renders', got: {result}"
    
    # Should NOT have duplicate 'is rendered'
    assert '"button" is rendered in white' not in result, \
        f"Should not have duplicate render semantics, got: {result}"
    
    # Should have exactly one render expression
    assert '"button" in white' in result, \
        f"Should keep label phrase without duplicate 'is rendered', got: {result}"
    
    # Full expected output (from issue)
    expected = '(CUI) Verify the Display Format renders the UI button label "button" in white.'
    assert result == expected, f"Expected: '{expected}', Got: '{result}'"


def test_transform_text_plural_subject_shall_render_with_quote_in():
    """Test plural subject with 'shall render' + '" in' pattern."""
    req_text = 'The Display Formats shall render the UI button labels "button" in white.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # Should have 'render' (plural form)
    assert 'render' in result, f"Should have 'render' (plural), got: {result}"
    
    # Should NOT have duplicate 'is rendered'
    assert '"button" is rendered in white' not in result, \
        f"Should not have duplicate render semantics, got: {result}"


def test_transform_text_without_render_verb_with_quote_in():
    """Test that '" in' normalization still works when no render verb is present."""
    req_text = 'The UI button label "button" in white is visible.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # SHOULD insert 'is rendered' because no render verb governs the label
    assert '"button" is rendered in white' in result, \
        f"Should insert 'is rendered' when no render verb is present, got: {result}"


def test_end_to_end_sentence_style_with_shall_render():
    """End-to-end test with sentence-style requirement containing 'shall render' + '" in'."""
    req_item = {
        'Type': 'Requirement',
        'ID': 'REQU.TEST.1',
        'Name': '(CUI) The Display Format shall render the UI button label "button" in white',
        'Text': '(CUI) The Display Format shall render the UI button label "button" in white.',
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
    
    # Check Name field (non-standard, minimal transformation)
    # It should have 'shall render' preserved (no transformation for non-standard Names)
    assert 'shall render' in ver_item['Name'], \
        f"Non-standard Name should preserve 'shall render', got: {ver_item['Name']}"
    
    # Check Text field (should have exactly one render expression)
    text = ver_item['Text']
    has_renders = 'renders' in text.lower()
    has_is_rendered = '"button" is rendered in white' in text.lower()
    
    # Should have 'renders' (from 'shall render' normalization)
    assert has_renders, f"Should have 'renders' in Text, got: {text}"
    
    # Should NOT have 'is rendered' after the label (double render semantics)
    assert not has_is_rendered, \
        f"Should not have duplicate render semantics in Text, got: {text}"
    
    # Expected Text output
    expected_text = '(CUI) Verify the Display Format renders the UI button label "button" in white.'
    assert text == expected_text, f"Expected: '{expected_text}', Got: '{text}'"


def test_end_to_end_multiple_labels_mixed_verbs():
    """Test with multiple labels where render verb is present.
    
    Note: The current implementation takes a conservative approach - if ANY active
    render verb is found in the preceding context (up to 100 chars), it skips
    insertion for all subsequent labels. This prevents false positives and the
    double-render bug, even if it means some labels might not get 'is rendered'
    when they technically could.
    """
    req_text = 'The system renders "button" in white and displays label "status" in green.'
    result = transform_text(req_text, is_advanced=False, is_setting=False)
    
    # "button" is governed by "renders" - should not get "is rendered"
    assert '"button" in white' in result, \
        f"Should not insert 'is rendered' for button (governed by renders), got: {result}"
    
    # "status" comes after "renders" in the context, so conservative behavior
    # also skips insertion here to avoid complexity in determining precise scope
    assert '"status" in green' in result, \
        f"Conservative behavior: skips insertion when render verb is in context, got: {result}"


def test_idempotency_with_render_verb():
    """Test that names already containing 'is rendered in' remain stable when render verb is present."""
    req_text = 'The system renders "button" is rendered in white'
    result = normalize_quote_in_pattern(req_text)
    
    # Should not duplicate 'is rendered'
    assert 'is rendered is rendered' not in result, \
        f"Should not duplicate 'is rendered', got: {result}"


def test_command_form_render_still_inserts():
    """Test that command-form 'Render' at start still allows insertion (for passive conversion)."""
    text = 'Render the UI button label "button" in white'
    result = normalize_quote_in_pattern(text)
    
    # Command-form 'Render' gets converted to passive, so insertion IS needed
    assert '"button" is rendered in white' in result, \
        f"Should insert 'is rendered' for command-form Render, got: {result}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
