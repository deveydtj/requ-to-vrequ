#!/usr/bin/env python3
"""
Tests for fixing verb agreement with trailing modifier phrases.

Issue: Singular subjects with trailing modifier phrases like "with ...", "without ...",
etc. were incorrectly treated as plural because the plurality heuristic was picking
up the last noun in the modifier phrase instead of the true subject.

For example:
  "bay temperature indicator with configured values"
  
The true subject is "indicator" (singular), but the heuristic was picking "values"
(plural) from the modifier phrase "with configured values", leading to incorrect
verb agreement: "are rendered" instead of "is rendered".

These tests verify that:
1. Singular subjects with trailing modifiers use singular verb agreement
2. Plural subjects with trailing modifiers use plural verb agreement
3. Coordination cases still work correctly
4. Quoted labels still work correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    is_plural_subject_phrase,
    choose_be_verb,
    transform_name_general,
    generate_verification_items
)


def test_singular_subject_with_trailing_with():
    """Test that singular subject with 'with ...' modifier uses singular verb."""
    phrase = "the bay temperature indicator with configured values"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    assert result == False, f"Expected singular for '{phrase}', got plural"
    assert verb == "is", f"Expected 'is' for '{phrase}', got '{verb}'"


def test_plural_subject_with_trailing_with():
    """Test that plural subject with 'with ...' modifier uses plural verb."""
    phrase = "the bay temperature indicators with configured values"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    assert result == True, f"Expected plural for '{phrase}', got singular"
    assert verb == "are", f"Expected 'are' for '{phrase}', got '{verb}'"


def test_singular_subject_without_modifier():
    """Baseline test: singular subject without modifier should be singular."""
    phrase = "the bay temperature indicator"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    assert result == False, f"Expected singular for '{phrase}', got plural"
    assert verb == "is", f"Expected 'is' for '{phrase}', got '{verb}'"


def test_singular_with_without_modifier():
    """Test singular subject with 'without ...' modifier."""
    phrase = "the display panel without decorations"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    assert result == False, f"Expected singular for '{phrase}', got plural"
    assert verb == "is", f"Expected 'is' for '{phrase}', got '{verb}'"


def test_singular_with_using_modifier():
    """Test singular subject with 'using ...' modifier."""
    phrase = "the button using default styles"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    assert result == False, f"Expected singular for '{phrase}', got plural"
    assert verb == "is", f"Expected 'is' for '{phrase}', got '{verb}'"


def test_singular_with_including_modifier():
    """Test singular subject with 'including ...' modifier."""
    phrase = "the panel including multiple indicators"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    assert result == False, f"Expected singular for '{phrase}', got plural"
    assert verb == "is", f"Expected 'is' for '{phrase}', got '{verb}'"


def test_singular_with_excluding_modifier():
    """Test singular subject with 'excluding ...' modifier."""
    phrase = "the list excluding disabled items"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    assert result == False, f"Expected singular for '{phrase}', got plural"
    assert verb == "is", f"Expected 'is' for '{phrase}', got '{verb}'"


def test_coordination_still_plural():
    """Test that coordination (and/or) still results in plural."""
    phrase1 = "the label A and label B with styles"
    result1 = is_plural_subject_phrase(phrase1)
    verb1 = choose_be_verb(phrase1)
    
    assert result1 == True, f"Expected plural for coordination, got singular"
    assert verb1 == "are", f"Expected 'are' for coordination, got '{verb1}'"
    
    phrase2 = "the button or switch with values"
    result2 = is_plural_subject_phrase(phrase2)
    verb2 = choose_be_verb(phrase2)
    
    assert result2 == True, f"Expected plural for coordination, got singular"
    assert verb2 == "are", f"Expected 'are' for coordination, got '{verb2}'"


def test_quoted_labels_still_work():
    """Test that quoted labels don't affect plurality detection."""
    phrase1 = 'the label "A" with values'
    result1 = is_plural_subject_phrase(phrase1)
    verb1 = choose_be_verb(phrase1)
    
    # "label" is singular, should be singular verb
    assert result1 == False, f"Expected singular for '{phrase1}', got plural"
    assert verb1 == "is", f"Expected 'is' for '{phrase1}', got '{verb1}'"
    
    phrase2 = 'the labels "A" and "B" with styles'
    result2 = is_plural_subject_phrase(phrase2)
    verb2 = choose_be_verb(phrase2)
    
    # Has "and" coordination, should be plural
    assert result2 == True, f"Expected plural for '{phrase2}', got singular"
    assert verb2 == "are", f"Expected 'are' for '{phrase2}', got '{verb2}'"


def test_render_name_transformation_singular_with_modifier():
    """Test transform_name_general with singular subject and modifier."""
    req_name = "Render the bay temperature indicator with configured values"
    result = transform_name_general(req_name)
    
    # Should use 'is rendered' for singular subject
    assert "is rendered" in result, f"Expected 'is rendered', got: {result}"
    assert "are rendered" not in result, f"Should not have 'are rendered', got: {result}"
    assert result == "Verify the bay temperature indicator with configured values is rendered", \
        f"Incorrect transformation: {result}"


def test_render_name_transformation_plural_with_modifier():
    """Test transform_name_general with plural subject and modifier."""
    req_name = "Render the bay temperature indicators with configured values"
    result = transform_name_general(req_name)
    
    # Should use 'are rendered' for plural subject
    assert "are rendered" in result, f"Expected 'are rendered', got: {result}"
    assert "is rendered" not in result, f"Should not have 'is rendered', got: {result}"
    assert result == "Verify the bay temperature indicators with configured values are rendered", \
        f"Incorrect transformation: {result}"


def test_end_to_end_singular_with_modifier():
    """End-to-end test with a requirement containing singular subject with modifier."""
    req_item = {
        'Type': 'Requirement',
        'ID': 'REQU.TEST.MODIFIER.1',
        'Name': 'Render the bay temperature indicator with configured values',
        'Text': 'The system shall render the bay temperature indicator with configured values.',
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
    
    # Check Name field - should use 'is rendered' for singular subject
    name = ver_item['Name']
    assert "is rendered" in name, f"Expected 'is rendered' in Name, got: {name}"
    assert "are rendered" not in name, f"Should not have 'are rendered' in Name, got: {name}"


def test_end_to_end_plural_with_modifier():
    """End-to-end test with a requirement containing plural subject with modifier."""
    req_item = {
        'Type': 'Requirement',
        'ID': 'REQU.TEST.MODIFIER.2',
        'Name': 'Render the bay temperature indicators with configured values',
        'Text': 'The system shall render the bay temperature indicators with configured values.',
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
    
    # Check Name field - should use 'are rendered' for plural subject
    name = ver_item['Name']
    assert "are rendered" in name, f"Expected 'are rendered' in Name, got: {name}"
    assert "is rendered" not in name, f"Should not have 'is rendered' in Name, got: {name}"


def test_multiple_modifiers():
    """Test subject with multiple trailing modifiers."""
    phrase = "the indicator with values using settings"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    # "indicator" is singular, should ignore both modifiers
    assert result == False, f"Expected singular for '{phrase}', got plural"
    assert verb == "is", f"Expected 'is' for '{phrase}', got '{verb}'"


def test_coordination_in_modifier_ignored():
    """Test that coordination within modifier phrases is correctly ignored.
    
    The implementation strips modifiers BEFORE checking for coordination.
    This ensures that only the core subject determines plurality, not
    coordination that appears within the modifier phrase itself.
    """
    # Singular subject with coordination in the modifier phrase
    phrase = "the indicator with buttons and switches"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    # Should be singular because "indicator" is singular, even though
    # the modifier phrase contains "and" coordination
    assert result == False, f"Expected singular (coordination in modifier ignored), got plural"
    assert verb == "is", f"Expected 'is' for '{phrase}', got '{verb}'"


def test_plural_subject_morphology():
    """Test that plural subjects are detected by morphology (e.g., 's' ending).
    
    This test uses "controls" which is morphologically plural (ends with 's').
    Even though the modifier phrase contains coordination, the test passes
    due to the plural morphology of "controls", not due to coordination.
    """
    phrase = "the controls with indicators and displays"
    result = is_plural_subject_phrase(phrase)
    verb = choose_be_verb(phrase)
    
    # Should be plural because "controls" ends with 's' (morphologically plural)
    assert result == True, f"Expected plural (morphological), got singular"
    assert verb == "are", f"Expected 'are' for '{phrase}', got '{verb}'"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
