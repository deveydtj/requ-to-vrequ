#!/usr/bin/env python3
"""
End-to-end integration test for the " in <color>" pattern fix.

This test validates the complete workflow from requirement input to verification output
using the actual script execution, covering all must-pass examples from the issue.
"""

import tempfile
import os
import sys
import subprocess

# Add parent directory to path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import parse_items


def test_end_to_end_quote_in_pattern():
    """End-to-end test with all must-pass examples from the issue."""
    
    # Create input YAML with all must-pass examples
    input_content = """- Type: Requirement
  Parent_Req: 
  ID: REQU.TEST.1
  Name: Render Fruit button label
  Text: |
    The Fruit button label "fruit" in white
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.TEST.2
  Name: Render Fruit button label (already has is rendered)
  Text: |
    The Fruit button label "fruit" is rendered in white
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.TEST.3
  Name: Set Fruit button label
  Text: |
    The Display Bridge shall set the Fruit button label "fruit" in white
  Verified_By: 
  Traced_To: 
"""
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as input_file:
        input_path = input_file.name
        input_file.write(input_content)
    
    output_path = tempfile.mktemp(suffix='.yaml')
    
    try:
        # Run the script
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'generate_verification_yaml.py'
        )
        result = subprocess.run(
            ['python', script_path, input_path, output_path],
            capture_output=True,
            text=True
        )
        
        # Check script execution was successful
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        # Parse the output
        items = parse_items(output_path)
        
        # Find verification items
        verifications = [item for item in items if item.get('Type', '').strip() in {
            'Verification',
            'DMGR Verification Requirement',
            'BRDG Verification Requirement'
        }]
        
        # Verify we have 3 verification items
        assert len(verifications) == 3, f"Expected 3 verification items, got {len(verifications)}"
        
        # Must-pass example 1: Basic render insertion
        ver1 = verifications[0]
        assert ver1['ID'] == 'VREQU.TEST.1', f"Expected VREQU.TEST.1, got {ver1['ID']}"
        expected_text_1 = 'Verify the Fruit button label "fruit" is rendered in white'
        assert ver1['Text'].strip() == expected_text_1, \
            f"Example 1 failed.\nExpected: {expected_text_1}\nGot: {ver1['Text'].strip()}"
        
        # Must-pass example 2: No duplicate insertion
        ver2 = verifications[1]
        assert ver2['ID'] == 'VREQU.TEST.2', f"Expected VREQU.TEST.2, got {ver2['ID']}"
        expected_text_2 = 'Verify the Fruit button label "fruit" is rendered in white'
        # Should not have duplicate 'is rendered'
        assert '"fruit" is rendered is rendered' not in ver2['Text'], \
            "Should not duplicate 'is rendered'"
        assert ver2['Text'].strip() == expected_text_2, \
            f"Example 2 failed.\nExpected: {expected_text_2}\nGot: {ver2['Text'].strip()}"
        
        # Must-pass example 3: Combined with "shall set" rule
        ver3 = verifications[2]
        assert ver3['ID'] == 'VREQU.BRDG.TEST.3', f"Expected VREQU.BRDG.TEST.3, got {ver3['ID']}"
        expected_text_3 = 'Verify the Display Bridge sets the Fruit button label "fruit" is rendered in white'
        assert 'shall set' not in ver3['Text'], "'shall set' should be replaced with 'sets'"
        assert 'sets' in ver3['Text'], "Should contain 'sets'"
        assert '"fruit" is rendered in white' in ver3['Text'], "Should insert 'is rendered'"
        assert ver3['Text'].strip() == expected_text_3, \
            f"Example 3 failed.\nExpected: {expected_text_3}\nGot: {ver3['Text'].strip()}"
        
        # Verify the original requirements were not modified (only Verified_By added)
        requirements = [item for item in items if item.get('Type', '').strip() == 'Requirement']
        assert len(requirements) == 3, f"Expected 3 requirement items, got {len(requirements)}"
        
        req1 = requirements[0]
        assert 'The Fruit button label "fruit" in white' in req1['Text'], \
            "Original requirement text should not be modified"
        assert req1['Verified_By'] == 'VREQU.TEST.1', "Verified_By should be set"
        
        req2 = requirements[1]
        assert 'The Fruit button label "fruit" is rendered in white' in req2['Text'], \
            "Original requirement text should not be modified"
        
        req3 = requirements[2]
        assert 'shall set' in req3['Text'], \
            "Original requirement text should not be modified (should still contain 'shall set')"
        assert '"fruit" in white' in req3['Text'], \
            "Original requirement text should not be modified"
        
    finally:
        # Cleanup
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == '__main__':
    test_end_to_end_quote_in_pattern()
    print("✓ All end-to-end tests passed!")
