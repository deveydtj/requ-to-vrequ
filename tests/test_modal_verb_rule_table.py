#!/usr/bin/env python3
"""
Test script for modal verb rule table extensibility and ordering.

This test validates that:
1. The rule table correctly supports both render and overlay transformations
2. Priority ordering works correctly (shall set to before shall set)
3. Adding new rules follows a predictable pattern
4. Domain-specific gating works correctly
"""

import sys
import os
import tempfile
import subprocess

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    MODAL_VERB_RULES,
    is_standard_text,
    transform_text,
)


def test_rule_table_structure():
    """Test that the rule table has the expected structure."""
    print("Testing rule table structure...")
    
    # Check that we have rules defined
    assert len(MODAL_VERB_RULES) > 0, "MODAL_VERB_RULES should not be empty"
    
    # Check that each rule has required fields
    required_fields = {"trigger", "base_verb", "domains", "priority", "requires_setting"}
    for i, rule in enumerate(MODAL_VERB_RULES):
        for field in required_fields:
            assert field in rule, f"Rule {i} missing required field: {field}"
        
        # Check field types
        assert isinstance(rule["trigger"], str), f"Rule {i} trigger should be string"
        assert isinstance(rule["base_verb"], str), f"Rule {i} base_verb should be string"
        assert isinstance(rule["domains"], set), f"Rule {i} domains should be set"
        assert isinstance(rule["priority"], int), f"Rule {i} priority should be int"
        assert isinstance(rule["requires_setting"], bool), f"Rule {i} requires_setting should be bool"
    
    print("✓ Rule table structure is valid")


def test_rule_table_has_expected_verbs():
    """Test that the rule table includes expected modal verbs."""
    print("\nTesting rule table contains expected verbs...")
    
    # Extract all triggers from rules
    triggers = {rule["trigger"] for rule in MODAL_VERB_RULES}
    
    # Check for expected triggers
    expected_triggers = {
        "shall render",
        "shall overlay",
        "shall set",
        "shall set to",
    }
    
    for expected in expected_triggers:
        assert expected in triggers, f"Expected trigger '{expected}' not found in rule table"
    
    print("✓ Rule table contains all expected verbs")


def test_priority_ordering():
    """Test that 'shall set to' has higher priority than 'shall set'."""
    print("\nTesting priority ordering...")
    
    # Find shall set to rules
    shall_set_to_rules = [r for r in MODAL_VERB_RULES if r["trigger"] == "shall set to"]
    shall_set_rules = [r for r in MODAL_VERB_RULES if r["trigger"] == "shall set"]
    
    assert len(shall_set_to_rules) > 0, "Should have 'shall set to' rules"
    assert len(shall_set_rules) > 0, "Should have 'shall set' rules"
    
    # Check that all 'shall set to' rules have higher priority than 'shall set' rules
    min_set_to_priority = min(r["priority"] for r in shall_set_to_rules)
    max_set_priority = max(r["priority"] for r in shall_set_rules)
    
    assert min_set_to_priority > max_set_priority, \
        f"'shall set to' priority ({min_set_to_priority}) should be higher than 'shall set' priority ({max_set_priority})"
    
    print("✓ Priority ordering is correct")


def test_shall_set_to_processed_before_shall_set():
    """Test that 'shall set to' is processed before 'shall set' to avoid 'to to' duplication."""
    print("\nTesting 'shall set to' vs 'shall set' ordering in transformation...")
    
    # DMGR with "shall set to"
    req_text = "(U) The Data Manager shall set the buffer size to 1024."
    result = transform_text(req_text, is_advanced=True, is_setting=False, is_dmgr=True)
    
    # Should NOT have "sets to to" or "set to to" (duplication bug)
    assert "to to" not in result, f"Should not have 'to to' duplication, got: {result}"
    
    # Should have "sets" and "to 1024" (correct transformation)
    assert "sets the buffer size to 1024" in result, f"Expected 'sets the buffer size to 1024', got: {result}"
    
    # BRDG with setting semantics and "shall set to"
    req_text_brdg = "(U) The Bridge shall set the value to high."
    result_brdg = transform_text(req_text_brdg, is_advanced=True, is_setting=True, is_dmgr=False)
    
    # Should NOT have duplication
    assert "to to" not in result_brdg, f"Should not have 'to to' duplication, got: {result_brdg}"
    assert "sets the value to high" in result_brdg, f"Expected 'sets the value to high', got: {result_brdg}"
    
    print("✓ 'shall set to' processing is correct")


def test_rule_table_supports_render_and_overlay():
    """Test that the rule table supports both render and overlay transformations."""
    print("\nTesting rule table supports both render and overlay...")
    
    # Test render
    req_text_render = "(U) The display shall render the UI."
    result_render = transform_text(req_text_render, is_advanced=False, is_setting=False)
    assert "renders the UI" in result_render, f"Expected 'renders the UI', got: {result_render}"
    
    # Test overlay
    req_text_overlay = "(U) The display shall overlay the indicator."
    result_overlay = transform_text(req_text_overlay, is_advanced=False, is_setting=False)
    assert "overlays the indicator" in result_overlay, f"Expected 'overlays the indicator', got: {result_overlay}"
    
    # Test both in one requirement
    req_text_both = "(U) The display shall render the UI and shall overlay the warning."
    result_both = transform_text(req_text_both, is_advanced=True, is_setting=False, is_dmgr=True)
    assert "renders the UI" in result_both, f"Expected 'renders the UI', got: {result_both}"
    assert "overlays the warning" in result_both, f"Expected 'overlays the warning', got: {result_both}"
    
    print("✓ Rule table supports both render and overlay")


def test_domain_specific_gating():
    """Test that domain-specific gating works correctly."""
    print("\nTesting domain-specific gating...")
    
    # DMGR should always transform "shall set"
    dmgr_text = "(U) The Data Manager shall set the timeout."
    dmgr_result = transform_text(dmgr_text, is_advanced=True, is_setting=False, is_dmgr=True)
    assert "sets the timeout" in dmgr_result, \
        f"DMGR should transform 'shall set' regardless of is_setting, got: {dmgr_result}"
    
    # BRDG should only transform "shall set" when is_setting=True
    brdg_text = "(U) The Bridge shall set the mode."
    brdg_result_with_setting = transform_text(brdg_text, is_advanced=True, is_setting=True, is_dmgr=False)
    assert "sets the mode" in brdg_result_with_setting, \
        f"BRDG with is_setting=True should transform 'shall set', got: {brdg_result_with_setting}"
    
    brdg_result_without_setting = transform_text(brdg_text, is_advanced=True, is_setting=False, is_dmgr=False)
    assert "shall set the mode" in brdg_result_without_setting, \
        f"BRDG with is_setting=False should NOT transform 'shall set', got: {brdg_result_without_setting}"
    
    print("✓ Domain-specific gating works correctly")


def test_standardness_detection():
    """Test that standardness detection uses the rule table correctly."""
    print("\nTesting standardness detection...")
    
    # DMGR with "shall overlay" should be standard
    assert is_standard_text("The display shall overlay the indicator.", "DMGR"), \
        "DMGR with 'shall overlay' should be standard"
    
    # BRDG with "shall overlay" should NOT be standard (only DMGR)
    assert not is_standard_text("The bridge shall overlay the indicator.", "BRDG"), \
        "BRDG with 'shall overlay' should be non-standard"
    
    # DMGR with "shall set" should be standard
    assert is_standard_text("The manager shall set the value.", "DMGR"), \
        "DMGR with 'shall set' should be standard"
    
    # BRDG with "shall set" should be standard
    assert is_standard_text("The bridge shall set the value.", "BRDG"), \
        "BRDG with 'shall set' should be standard"
    
    # DMGR with "shall render" should be standard
    assert is_standard_text("The display shall render the UI.", "DMGR"), \
        "DMGR with 'shall render' should be standard"
    
    # BRDG with "shall render" should be standard
    assert is_standard_text("The bridge shall render the UI.", "BRDG"), \
        "BRDG with 'shall render' should be standard"
    
    # OTHER domain should always be standard (if non-empty)
    assert is_standard_text("The system shall configure the timeout.", "OTHER"), \
        "OTHER domain with any text should be standard"
    
    print("✓ Standardness detection works correctly")


def test_end_to_end_rule_table():
    """Test the full pipeline using the rule table."""
    print("\nTesting end-to-end with rule table...")
    
    test_yaml = """# Test rule table functionality
- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.1
  Name: Render and overlay UI
  Text: |
    (U) The display shall render the UI and shall overlay the indicator.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.2
  Name: Set buffer size
  Text: |
    (U) The Data Manager shall set the buffer size to 1024.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.TEST.3
  Name: Set mode value
  Text: |
    (U) The Bridge shall set the display mode to active.
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
        
        # Check transformations
        # TEST.1 should have both "renders" and "overlays"
        assert "renders the UI" in output, "TEST.1 should transform 'shall render' to 'renders'"
        assert "overlays the indicator" in output, "TEST.1 should transform 'shall overlay' to 'overlays'"
        
        # TEST.2 should have "sets to" (not "sets to to")
        assert "sets the buffer size to 1024" in output, "TEST.2 should transform 'shall set to' correctly"
        assert "to to" not in output, "TEST.2 should not have 'to to' duplication"
        
        # TEST.3 should have "sets to" (BRDG with setting semantics)
        assert "sets the display mode to active" in output, "TEST.3 should transform 'shall set to' correctly"
        
        # No non-standard flags (all should be standard)
        assert "# FIX - Non-Standard Text" not in output, \
            "All requirements should be standard (no FIX comments)"
        
        print("✓ End-to-end test passed")
        
    finally:
        # Clean up temporary files
        try:
            os.remove(input_file)
        except OSError:
            # Best-effort cleanup: ignore errors when removing the temporary input file
            pass
        if output_file is not None:
            try:
                os.remove(output_file)
            except OSError:
                # Best-effort cleanup: ignore errors when removing the temporary output file
                pass


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Modal Verb Rule Table")
    print("=" * 60)
    
    try:
        test_rule_table_structure()
        test_rule_table_has_expected_verbs()
        test_priority_ordering()
        test_shall_set_to_processed_before_shall_set()
        test_rule_table_supports_render_and_overlay()
        test_domain_specific_gating()
        test_standardness_detection()
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
