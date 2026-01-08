#!/usr/bin/env python3
"""
Test script for the modal verb rule table refactoring.

This test validates that:
1. The rule table supports all modal verbs (render, overlay, set)
2. Rule ordering is correct (shall set to before shall set)
3. The refactored implementation produces the same output as before
4. Adding new modal verbs only requires updating the rule table
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
    MODAL_VERB_RULES,
)


def test_rule_table_structure():
    """Test that the MODAL_VERB_RULES table is properly structured."""
    print("Testing MODAL_VERB_RULES structure...")
    
    # Rules should be sorted by priority (highest first)
    priorities = [rule["priority"] for rule in MODAL_VERB_RULES]
    assert priorities == sorted(priorities, reverse=True), \
        "Rules should be sorted by priority (highest first)"
    
    # Check that all required rules are present
    triggers = [rule["trigger"] for rule in MODAL_VERB_RULES]
    required_triggers = ["shall render", "shall overlay", "shall set", "shall set to"]
    for trigger in required_triggers:
        assert trigger in triggers, f"Missing required trigger: {trigger}"
    
    # Check that "shall set to" has higher priority than "shall set"
    set_to_priority = None
    set_priority = None
    for rule in MODAL_VERB_RULES:
        if rule["trigger"] == "shall set to":
            set_to_priority = rule["priority"]
        elif rule["trigger"] == "shall set":
            set_priority = rule["priority"]
    
    assert set_to_priority is not None, "Missing 'shall set to' rule"
    assert set_priority is not None, "Missing 'shall set' rule"
    assert set_to_priority > set_priority, \
        "'shall set to' must have higher priority than 'shall set'"
    
    print("✓ Rule table structure tests passed")


def test_rule_table_supports_render_and_overlay():
    """Test that the rule table supports both render and overlay transformations."""
    print("\nTesting render and overlay support in rule table...")
    
    # Find render rule
    render_rule = None
    for rule in MODAL_VERB_RULES:
        if rule["trigger"] == "shall render":
            render_rule = rule
            break
    
    assert render_rule is not None, "Missing 'shall render' rule"
    assert render_rule["base_verb"] == "render", "Render rule should have base_verb='render'"
    assert "DMGR" in render_rule["domains"], "Render should be standard for DMGR"
    
    # Find overlay rule
    overlay_rule = None
    for rule in MODAL_VERB_RULES:
        if rule["trigger"] == "shall overlay":
            overlay_rule = rule
            break
    
    assert overlay_rule is not None, "Missing 'shall overlay' rule"
    assert overlay_rule["base_verb"] == "overlay", "Overlay rule should have base_verb='overlay'"
    assert "DMGR" in overlay_rule["domains"], "Overlay should be standard for DMGR"
    
    print("✓ Render and overlay support tests passed")


def test_ordering_shall_set_to_before_shall_set():
    """Test that 'shall set to' is handled before 'shall set' to avoid duplication."""
    print("\nTesting 'shall set to' ordering...")
    
    # Test DMGR with "shall set to"
    req_text = "(U) The Data Manager shall set the timeout to 30 seconds."
    result = transform_text(req_text, is_advanced=True, is_setting=True, is_dmgr=True)
    
    # Should transform "shall set to" to "sets to" (not "sets to to")
    assert "shall set to" not in result, f"Expected 'shall set to' to be replaced, got: {result}"
    assert "sets the timeout to 30" in result, f"Expected 'sets the timeout to 30' in output, got: {result}"
    assert "to to" not in result, f"Should not contain 'to to' duplication, got: {result}"
    
    expected = "(U) Verify the Data Manager sets the timeout to 30 seconds."
    assert result == expected, f"Expected '{expected}', got: '{result}'"
    
    # Test plural subject
    req_text_plural = "(U) The Data Managers shall set the timeouts to 30 seconds."
    result_plural = transform_text(req_text_plural, is_advanced=True, is_setting=True, is_dmgr=True)
    
    assert "shall set to" not in result_plural, f"Expected 'shall set to' to be replaced, got: {result_plural}"
    assert "set the timeouts to 30" in result_plural, f"Expected 'set the timeouts to 30' in output, got: {result_plural}"
    assert "to to" not in result_plural, f"Should not contain 'to to' duplication, got: {result_plural}"
    
    print("✓ Ordering tests passed")


def test_is_standard_text_uses_rule_table():
    """Test that is_standard_text correctly uses the rule table."""
    print("\nTesting is_standard_text with rule table...")
    
    # DMGR should accept all triggers in the rule table with "DMGR" in domains
    assert is_standard_text("The system shall render the UI.", "DMGR"), \
        "DMGR should accept 'shall render'"
    assert is_standard_text("The system shall overlay the indicator.", "DMGR"), \
        "DMGR should accept 'shall overlay'"
    assert is_standard_text("The system shall set the value.", "DMGR"), \
        "DMGR should accept 'shall set'"
    assert is_standard_text("The system shall set the value to 10.", "DMGR"), \
        "DMGR should accept 'shall set to'"
    
    # BRDG should only accept "shall set" triggers
    assert not is_standard_text("The bridge shall render the UI.", "BRDG"), \
        "BRDG should not accept 'shall render'"
    assert not is_standard_text("The bridge shall overlay the indicator.", "BRDG"), \
        "BRDG should not accept 'shall overlay'"
    assert is_standard_text("The bridge shall set the value.", "BRDG"), \
        "BRDG should accept 'shall set'"
    assert is_standard_text("The bridge shall set the value to 10.", "BRDG"), \
        "BRDG should accept 'shall set to'"
    
    # OTHER should accept any non-empty text
    assert is_standard_text("The system shall configure the value.", "OTHER"), \
        "OTHER should accept any non-empty text"
    
    print("✓ is_standard_text tests passed")


def test_transform_text_uses_rule_table():
    """Test that transform_text correctly uses the rule table for all transformations."""
    print("\nTesting transform_text with rule table...")
    
    # Test render transformation
    result = transform_text(
        "(U) The system shall render the UI.",
        is_advanced=False,
        is_setting=False
    )
    assert "renders the UI" in result, f"Expected render transformation, got: {result}"
    
    # Test overlay transformation
    result = transform_text(
        "(U) The system shall overlay the indicator.",
        is_advanced=False,
        is_setting=False
    )
    assert "overlays the indicator" in result, f"Expected overlay transformation, got: {result}"
    
    # Test set transformation (DMGR)
    result = transform_text(
        "(U) The Data Manager shall set the value.",
        is_advanced=True,
        is_setting=True,
        is_dmgr=True
    )
    assert "sets the value" in result, f"Expected set transformation, got: {result}"
    
    # Test set to transformation (DMGR)
    result = transform_text(
        "(U) The Data Manager shall set the value to 10.",
        is_advanced=True,
        is_setting=True,
        is_dmgr=True
    )
    assert "sets the value to 10" in result, f"Expected set to transformation, got: {result}"
    assert "to to" not in result, f"Should not have 'to to' duplication, got: {result}"
    
    # Test multiple verbs in one text
    result = transform_text(
        "(U) The system shall render the UI and shall overlay the indicator.",
        is_advanced=False,
        is_setting=False
    )
    assert "renders the UI" in result, f"Expected render transformation, got: {result}"
    assert "overlays the indicator" in result, f"Expected overlay transformation, got: {result}"
    
    print("✓ transform_text tests passed")


def test_end_to_end_rule_table():
    """Test the full pipeline uses the rule table correctly."""
    print("\nTesting end-to-end rule table behavior...")
    
    test_yaml = """# Test multiple modal verbs with rule table
- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.1
  Name: Render the UI
  Text: |
    (U) The display shall render the status indicator.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.2
  Name: Overlay the warning
  Text: |
    (U) The display shall overlay the warning icon.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.3
  Name: Set the timeout
  Text: |
    (U) The Data Manager shall set the timeout to 30 seconds.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.4
  Name: Render and overlay
  Text: |
    (U) The system shall render the UI and shall overlay the icon.
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
        
        # All requirements should be standard (no non-standard flags)
        assert "# FIX - Non-Standard Text" not in output, \
            "All DMGR requirements with modal verbs should be standard"
        
        # Verify transformations
        assert "renders the status indicator" in output, \
            "Should transform 'shall render' to 'renders'"
        assert "overlays the warning icon" in output, \
            "Should transform 'shall overlay' to 'overlays'"
        assert "sets the timeout to 30 seconds" in output, \
            "Should transform 'shall set to' to 'sets to'"
        assert "renders the UI and overlays the icon" in output, \
            "Should transform multiple verbs correctly"
        
        # Ensure no remnants of modal phrases
        lines = output.split('\n')
        verification_lines = []
        in_verification = False
        for line in lines:
            if 'Type: DMGR Verification Requirement' in line or 'Type: Verification' in line:
                in_verification = True
            if in_verification:
                verification_lines.append(line)
                if line.strip().startswith('- Type:'):
                    in_verification = False
        
        verification_text = '\n'.join(verification_lines)
        assert "shall render" not in verification_text, \
            "Verifications should not contain 'shall render'"
        assert "shall overlay" not in verification_text, \
            "Verifications should not contain 'shall overlay'"
        assert "shall set" not in verification_text, \
            "Verifications should not contain 'shall set'"
        
        print("✓ End-to-end test passed")
        
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
    print("Testing modal verb rule table refactoring")
    print("=" * 60)
    
    try:
        test_rule_table_structure()
        test_rule_table_supports_render_and_overlay()
        test_ordering_shall_set_to_before_shall_set()
        test_is_standard_text_uses_rule_table()
        test_transform_text_uses_rule_table()
        test_end_to_end_rule_table()
        
        print("\n" + "=" * 60)
        print("All rule table tests passed! ✓")
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
