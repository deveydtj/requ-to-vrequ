#!/usr/bin/env python3
"""
Test that overlay-governed contexts block '" in' pattern insertion.

This test validates the requirement: "we should not allow any overlay insertion with \" in\"."

The normalize_quote_in_pattern() function should:
1. Block insertion when overlay context is detected (all forms)
2. Allow insertion when non-overlay context is present
3. Continue to block for render contexts (regression test)
"""

import sys
import os

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import normalize_quote_in_pattern


def test_overlay_contexts_block_insertion():
    """Test that various overlay forms block '" in' insertion."""
    print("Testing overlay contexts block insertion...")
    
    test_cases = [
        # (name, input, expected_has_in, expected_not_has_rendered_in)
        ("shall overlay", 'The system shall overlay label "fruit" in white', True, True),
        ("overlays singular", 'The system overlays label "fruit" in white', True, True),
        ("overlay plural", 'The systems overlay label "fruit" in white', True, True),
        ("overlaying gerund", 'When overlaying label "fruit" in white', True, True),
        # Command-form at start - should ALSO block insertion per policy
        ("Overlay command at start", 'Overlay label "fruit" in white', True, True),
        # Overlay not at start
        ("overlay mid-sentence", 'The display shall overlay the label "fruit" in white', True, True),
    ]
    
    for name, input_text, should_have_in, should_not_have_rendered_in in test_cases:
        result = normalize_quote_in_pattern(input_text)
        has_in = '"fruit" in white' in result
        not_has_rendered_in = '"fruit" is rendered in white' not in result
        
        passed = has_in == should_have_in and not_has_rendered_in == should_not_have_rendered_in
        
        if passed:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")
            print(f"    Input:    {input_text}")
            print(f"    Output:   {result}")
            print("    Expected: Should preserve '\" in', should NOT insert 'is rendered in'")
            assert False, f"Test failed: {name}"
    
    print("✓ All overlay context tests passed")


def test_non_overlay_contexts_allow_insertion():
    """Test that non-overlay contexts still perform insertion."""
    print("\nTesting non-overlay contexts allow insertion...")
    
    test_cases = [
        # (name, input)
        ("no governing verb", 'The label "fruit" in white'),
        ("display verb", 'Display the label "fruit" in white'),
        ("shows verb", 'System shows label "fruit" in white'),
    ]
    
    for name, input_text in test_cases:
        result = normalize_quote_in_pattern(input_text)
        
        # Should insert "is rendered"
        if '"fruit" is rendered in white' in result:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")
            print(f"    Input:    {input_text}")
            print(f"    Output:   {result}")
            print("    Expected: Should insert 'is rendered in'")
            assert False, f"Test failed: {name}"
    
    print("✓ All non-overlay context tests passed")


def test_render_contexts_still_block_insertion():
    """Regression test: render contexts should continue to block insertion."""
    print("\nTesting render contexts still block insertion (regression)...")
    
    test_cases = [
        ("shall render", 'The system shall render label "fruit" in white'),
        ("renders singular", 'The system renders label "fruit" in white'),
        ("render plural", 'The systems render label "fruit" in white'),
        ("rendering gerund", 'When rendering label "fruit" in white'),
    ]
    
    for name, input_text in test_cases:
        result = normalize_quote_in_pattern(input_text)
        
        # Should NOT insert "is rendered" (render context blocks it)
        has_in = '"fruit" in white' in result
        not_has_rendered_in = '"fruit" is rendered in white' not in result
        
        if has_in and not_has_rendered_in:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")
            print(f"    Input:    {input_text}")
            print(f"    Output:   {result}")
            print("    Expected: Should preserve '\" in', should NOT insert 'is rendered in'")
            assert False, f"Test failed: {name}"
    
    print("✓ All render context regression tests passed")


def test_already_has_is_rendered():
    """Test that when 'is rendered' is already present, no duplication occurs."""
    print("\nTesting no duplication when 'is rendered' already present...")
    
    test_cases = [
        ("overlay with is rendered", 'System overlays label "fruit" is rendered in white'),
        ("render with is rendered", 'System renders label "fruit" is rendered in white'),
    ]
    
    for name, input_text in test_cases:
        result = normalize_quote_in_pattern(input_text)
        
        # Should not duplicate "is rendered"
        if '"fruit" is rendered in white' in result and '"fruit" is rendered is rendered' not in result:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")
            print(f"    Input:    {input_text}")
            print(f"    Output:   {result}")
            print("    Expected: Should not duplicate 'is rendered'")
            assert False, f"Test failed: {name}"
    
    print("✓ All duplication prevention tests passed")


def test_passive_voice_allows_insertion():
    """Test that passive voice (is/are overlaid) allows insertion."""
    print("\nTesting passive voice allows insertion...")
    
    # Passive voice: "is overlaid" or "are overlaid" - these are NOT active overlay verbs
    # Note: The current implementation checks for "is/are/was/were overlay/overlays" not "overlaid"
    # So this test validates that plain "overlaid" (past participle) doesn't block insertion
    
    test_cases = [
        ("passive is overlaid", 'The label "fruit" in white is overlaid on screen'),
        ("passive was overlaid", 'The label "fruit" in white was overlaid yesterday'),
    ]
    
    for name, input_text in test_cases:
        result = normalize_quote_in_pattern(input_text)
        
        # Should insert "is rendered" because "overlaid" is not an active verb form
        if '"fruit" is rendered in white' in result:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")
            print(f"    Input:    {input_text}")
            print(f"    Output:   {result}")
            print("    Expected: Should insert 'is rendered in' (passive voice allows insertion)")
            assert False, f"Test failed: {name}"
    
    print("✓ All passive voice tests passed")


def test_render_vs_overlay_command_form_difference():
    """Test that command-form 'Render' allows insertion but 'Overlay' blocks it.
    
    This validates the key behavioral difference documented in the PR:
    - Command-form "Render" at start: allows insertion (existing behavior)
    - Command-form "Overlay" at start: blocks insertion (new policy)
    """
    print("\nTesting Render vs Overlay command-form difference...")
    
    test_cases = [
        # Command-form "Render" should ALLOW insertion
        (
            "Render command-form",
            'Render label "fruit" in white',
            False  # Should NOT block (allows insertion)
        ),
        # Command-form "Overlay" should BLOCK insertion
        (
            "Overlay command-form",
            'Overlay label "fruit" in white',
            True  # Should block (no insertion)
        ),
    ]
    
    for name, input_text, should_block in test_cases:
        result = normalize_quote_in_pattern(input_text)
        blocks_insertion = '"fruit" is rendered in white' not in result
        allows_insertion = '"fruit" is rendered in white' in result
        
        if blocks_insertion == should_block:
            status = "blocks" if should_block else "allows"
            print(f"  ✓ {name} ({status} insertion)")
        else:
            print(f"  ✗ {name}")
            print(f"    Input:    {input_text}")
            print(f"    Output:   {result}")
            expected = "Block" if should_block else "Allow"
            print(f"    Expected: {expected} insertion")
            assert False, f"Test failed: {name}"
    
    print("✓ Command-form difference validated")


def test_edge_cases_documented_trade_offs():
    """Test edge cases documented in implementation comments.
    
    These tests validate the documented trade-offs where the implementation
    intentionally blocks insertion even in ambiguous cases, prioritizing
    policy compliance over precision.
    """
    print("\nTesting documented edge case trade-offs...")
    
    test_cases = [
        # Edge case 1: Overlay verb has different object
        (
            "different object",
            'System overlays the background. The label "fruit" in white is separate',
            True  # Should block (aggressive policy compliance)
        ),
        # Edge case 2: Overlay in subordinate clause
        (
            "subordinate clause",
            'While we overlay graphics, the label "fruit" in white shows status',
            True  # Should block (aggressive policy compliance)
        ),
        # Edge case 3: Truncated context (overlay appears but context_start > 0)
        (
            "truncated context",
            "The system does many things. " * 5 + 'Then it overlays the label "fruit" in white',
            True  # Should block (aggressive policy compliance)
        ),
    ]
    
    for name, input_text, should_block in test_cases:
        result = normalize_quote_in_pattern(input_text)
        blocks_insertion = '"fruit" is rendered in white' not in result
        
        if blocks_insertion == should_block:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")
            print(f"    Input:    {input_text[:80]}...")
            print(f"    Output:   {result[-80:] if len(result) > 80 else result}")
            print(f"    Expected: {'Block' if should_block else 'Allow'} insertion")
            assert False, f"Test failed: {name}"
    
    print("✓ All edge case tests passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing overlay '\" in' pattern insertion policy")
    print("Policy: 'we should not allow any overlay insertion with \" in\"'")
    print("=" * 60)
    print()
    
    try:
        test_overlay_contexts_block_insertion()
        test_non_overlay_contexts_allow_insertion()
        test_render_contexts_still_block_insertion()
        test_already_has_is_rendered()
        test_passive_voice_allows_insertion()
        test_render_vs_overlay_command_form_difference()
        test_edge_cases_documented_trade_offs()
        
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
