#!/usr/bin/env python3
"""
End-to-end integration test for the " in <color>" pattern fix in Name fields.

This test validates the complete workflow from requirement input to verification output,
focusing on Name field transformations.
"""

import tempfile
import os
import sys
import subprocess

# Add parent directory to path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import parse_items


def test_end_to_end_name_quote_in_pattern():
    """End-to-end test with Name field containing '" in' patterns."""
    
    # Create input YAML with various Name field test cases
    input_content = """- Type: Requirement
  Parent_Req: 
  ID: REQU.TEST.1
  Name: Render label "fruit" in white
  Text: |
    The system shall render the label.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.TEST.2
  Name: Render labels "fruit" in white and "vegetable" in green
  Text: |
    The system shall render multiple labels.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.TEST.3
  Name: Set button label "ok" in green to value
  Text: |
    The Display Bridge shall set the button label.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.TEST.4
  Name: Button label "warning" in yellow displays
  Text: |
    The button label displays correctly.
  Verified_By: 
  Traced_To: 
"""
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as input_file:
        input_path = input_file.name
        input_file.write(input_content)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as output_file:
        output_path = output_file.name
    
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
        
        # Verify we have 4 verification items
        assert len(verifications) == 4, f"Expected 4 verification items, got {len(verifications)}"
        
        # Test case 1: Render with single label
        ver1 = verifications[0]
        assert ver1['ID'] == 'VREQU.TEST.1', f"Expected VREQU.TEST.1, got {ver1['ID']}"
        expected_name_1 = 'Verify the label "fruit" is rendered in white'
        assert ver1['Name'].strip() == expected_name_1, \
            f"Name test 1 failed.\nExpected: {expected_name_1}\nGot: {ver1['Name'].strip()}"
        # Should not have duplicate "is rendered"
        assert ver1['Name'].count('is rendered') == 1, \
            f"Name should have exactly one 'is rendered', got: {ver1['Name']}"
        
        # Test case 2: Render with multiple labels
        ver2 = verifications[1]
        assert ver2['ID'] == 'VREQU.TEST.2', f"Expected VREQU.TEST.2, got {ver2['ID']}"
        # Both labels should have pattern fixed
        assert '"fruit" is rendered in white' in ver2['Name'], \
            f"Name should have '\"fruit\" is rendered in white', got: {ver2['Name']}"
        assert '"vegetable" is rendered in green' in ver2['Name'], \
            f"Name should have '\"vegetable\" is rendered in green', got: {ver2['Name']}"
        
        # Test case 3: Set with BRDG domain
        ver3 = verifications[2]
        assert ver3['ID'] == 'VREQU.BRDG.TEST.3', f"Expected VREQU.BRDG.TEST.3, got {ver3['ID']}"
        expected_name_3 = 'Verify the button label "ok" is rendered in green is set to value'
        assert ver3['Name'].strip() == expected_name_3, \
            f"Name test 3 failed.\nExpected: {expected_name_3}\nGot: {ver3['Name'].strip()}"
        # Should have both "is rendered in" and "is set to"
        assert '"ok" is rendered in green' in ver3['Name'], \
            f"Name should have pattern fixed, got: {ver3['Name']}"
        assert 'is set to' in ver3['Name'], \
            f"Name should have 'is set to', got: {ver3['Name']}"
        
        # Test case 4: Non-standard Name
        ver4 = verifications[3]
        assert ver4['ID'] == 'VREQU.TEST.4', f"Expected VREQU.TEST.4, got {ver4['ID']}"
        expected_name_4 = 'Verify Button label "warning" is rendered in yellow displays'
        assert ver4['Name'].strip() == expected_name_4, \
            f"Name test 4 failed.\nExpected: {expected_name_4}\nGot: {ver4['Name'].strip()}"
        
        # Verify the original requirements' Name fields were not modified
        requirements = [item for item in items if item.get('Type', '').strip() == 'Requirement']
        assert len(requirements) == 4, f"Expected 4 requirement items, got {len(requirements)}"
        
        req1 = requirements[0]
        assert 'Render label "fruit" in white' in req1['Name'], \
            "Original requirement Name should not be modified"
        assert req1['Verified_By'] == 'VREQU.TEST.1', "Verified_By should be set"
        
        req2 = requirements[1]
        assert 'Render labels "fruit" in white and "vegetable" in green' in req2['Name'], \
            "Original requirement Name should not be modified"
        
        req3 = requirements[2]
        assert 'Set button label "ok" in green to value' in req3['Name'], \
            "Original requirement Name should not be modified"
        
        # Verify that Text fields also have the pattern fixed (existing functionality)
        # This ensures consistency between Name and Text transformations
        for ver in verifications:
            text = ver.get('Text', '')
            # If Text contains '" in', it should be transformed
            if '" in' in text:
                # Check that it's been transformed
                assert '" is rendered in' in text or text.count('" in') == 0, \
                    f"Text should also have pattern fixed: {text}"
        
    finally:
        # Cleanup
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


def test_end_to_end_name_idempotency():
    """Test that running the script multiple times doesn't duplicate pattern fixes in Names."""
    
    input_content = """- Type: Requirement
  Parent_Req: 
  ID: REQU.TEST.1
  Name: Render label "fruit" in white
  Text: |
    The system shall render the label "fruit" in white.
  Verified_By: 
  Traced_To: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as input_file:
        input_path = input_file.name
        input_file.write(input_content)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'generate_verification_yaml.py'
        )
        
        # Run the script once
        result1 = subprocess.run(
            ['python', script_path, input_path, output_path],
            capture_output=True,
            text=True
        )
        assert result1.returncode == 0, f"First run failed: {result1.stderr}"
        
        # Read the first output
        with open(output_path, 'r') as f:
            first_output = f.read()
        
        # Run the script again using the output as input
        result2 = subprocess.run(
            ['python', script_path, output_path, output_path],
            capture_output=True,
            text=True
        )
        assert result2.returncode == 0, f"Second run failed: {result2.stderr}"
        
        # Read the second output
        with open(output_path, 'r') as f:
            second_output = f.read()
        
        # The outputs should be identical (idempotency)
        # Parse both to compare verification items
        items1 = parse_items(output_path)
        
        # For idempotency, find the verification item from first run
        verifications = [item for item in items1 if item.get('Type', '').strip() == 'Verification']
        assert len(verifications) >= 1, "Should have at least one verification"
        
        ver_name = verifications[0]['Name']
        
        # Should not have duplicate "is rendered"
        assert 'is rendered is rendered' not in ver_name, \
            f"Idempotency failed: duplicate 'is rendered' found in Name: {ver_name}"
        
        # Should have exactly one "is rendered"
        assert ver_name.count('is rendered') == 1, \
            f"Idempotency failed: should have exactly one 'is rendered', got: {ver_name}"
        
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == '__main__':
    test_end_to_end_name_quote_in_pattern()
    test_end_to_end_name_idempotency()
    print("✓ All end-to-end Name field tests passed!")
