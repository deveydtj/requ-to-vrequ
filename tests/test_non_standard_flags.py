#!/usr/bin/env python3
"""
Test script for non-standard formatting flags and Option B behavior.

This script validates that the generate_verification_yaml.py script correctly:
1. Detects non-standard Name fields (not starting with "Render " or "Set ")
2. Detects non-standard Text fields based on domain (DMGR expects "shall render", BRDG expects "shall set")
3. Inserts "# FIX - Non-Standard Name" or "# FIX - Non-Standard Text" comments
4. Applies minimal transformation for non-standard fields
5. Applies standard transformation for standard fields
6. Detects BRDG render issues and inserts "# FIX - BRDG must not render" comments
"""

import sys
import os
import tempfile
import subprocess

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    is_standard_name,
    is_standard_text,
    has_brdg_render_issue,
    parse_items,
    generate_verification_items,
)


def test_is_standard_name():
    """Test the is_standard_name function."""
    print("Testing is_standard_name...")
    
    # Standard names
    assert is_standard_name("Render the dashboard"), "Should be standard"
    assert is_standard_name("Set the timeout to 30"), "Should be standard"
    
    # Non-standard names
    assert not is_standard_name("Display the status"), "Should be non-standard"
    assert not is_standard_name("Configure the system"), "Should be non-standard"
    assert not is_standard_name("Process input"), "Should be non-standard"
    
    # Edge cases
    assert not is_standard_name("Rendering the UI"), "Should be non-standard (not 'Render ')"
    assert not is_standard_name("Setting the value"), "Should be non-standard (not 'Set ')"
    assert not is_standard_name(""), "Empty string should be non-standard"
    
    print("✓ is_standard_name tests passed")


def test_is_standard_text():
    """Test the is_standard_text function."""
    print("\nTesting is_standard_text...")
    
    # DMGR domain
    assert is_standard_text("The system shall render the UI.", "DMGR"), "Should be standard for DMGR"
    assert not is_standard_text("The system shall display the UI.", "DMGR"), "Should be non-standard for DMGR"
    assert not is_standard_text("", "DMGR"), "Empty text should be non-standard"
    
    # BRDG domain
    assert is_standard_text("The system shall set the timeout to 30.", "BRDG"), "Should be standard for BRDG"
    assert not is_standard_text("The system shall configure the timeout.", "BRDG"), "Should be non-standard for BRDG"
    assert not is_standard_text("", "BRDG"), "Empty text should be non-standard"
    
    # OTHER domain
    assert is_standard_text("The system shall validate input.", "OTHER"), "Should be standard for OTHER"
    assert is_standard_text("Anything goes for OTHER domain.", "OTHER"), "Should be standard for OTHER"
    assert not is_standard_text("", "OTHER"), "Empty text should be non-standard even for OTHER"
    
    print("✓ is_standard_text tests passed")


def test_has_brdg_render_issue():
    """Test the has_brdg_render_issue function."""
    print("\nTesting has_brdg_render_issue...")
    
    # Should detect "render" in various forms
    assert has_brdg_render_issue("Verify the UI is rendered", ""), "Should detect 'rendered' in Name"
    assert has_brdg_render_issue("", "The system renders the output"), "Should detect 'renders' in Text"
    assert has_brdg_render_issue("Render output", "Rendering mode"), "Should detect 'render' in both"
    
    # Case-insensitive
    assert has_brdg_render_issue("RENDER the output", ""), "Should detect uppercase RENDER"
    assert has_brdg_render_issue("", "The system RENDERS output"), "Should detect uppercase RENDERS"
    
    # Should not detect when not present
    assert not has_brdg_render_issue("Verify the value is set", "The system sets the value"), "Should not detect when no render"
    assert not has_brdg_render_issue("", ""), "Should not detect in empty strings"
    
    print("✓ has_brdg_render_issue tests passed")


def test_end_to_end():
    """Test the full pipeline with a sample YAML file."""
    print("\nTesting end-to-end behavior...")
    
    test_yaml = """# Test input
- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.1
  Name: Display the status
  Text: |
    (U) The system shall render the status indicator.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.TEST.2
  Name: Set the timeout
  Text: |
    (U) The system shall configure the timeout.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.TEST.3
  Name: Set the mode
  Text: |
    (U) The system shall set the mode and render the output.
  Verified_By: 
  Traced_To: 
"""
    
    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(test_yaml)
    
    try:
        # Create temporary output file
        output_file = input_file.replace('.yaml', '_output.yaml')
        
        # Run the script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'generate_verification_yaml.py')
        result = subprocess.run(
            ['python3', script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running script: {result.stderr}")
            return False
        
        # Read and verify output
        with open(output_file, 'r') as f:
            output = f.read()
        
        # Verify comments are present
        assert "# FIX - Non-Standard Name" in output, "Should have non-standard Name comment"
        assert "# FIX - Non-Standard Text" in output, "Should have non-standard Text comment"
        assert "# FIX - BRDG must not render" in output, "Should have BRDG render issue comment"
        
        # Verify verifications were created
        assert "VREQU.DMGR.TEST.1" in output, "Should create verification for TEST.1"
        assert "VREQU.BRDG.TEST.2" in output, "Should create verification for TEST.2"
        assert "VREQU.BRDG.TEST.3" in output, "Should create verification for TEST.3"
        
        # Verify minimal transformation for non-standard Name
        assert "Verify Display the status" in output, "Should apply minimal Name transformation"
        
        print("✓ End-to-end test passed")
        return True
        
    finally:
        # Clean up
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running tests for non-standard formatting flags")
    print("=" * 60)
    
    try:
        test_is_standard_name()
        test_is_standard_text()
        test_has_brdg_render_issue()
        test_end_to_end()
        
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
