#!/usr/bin/env python3
"""
End-to-end test for overlay-governed '" in' pattern - no insertion policy.

This test validates the complete workflow from requirement input to verification
output, ensuring that overlay contexts correctly block '" in' pattern insertion
as specified in the issue: "we should not allow any overlay insertion with \" in\"."
"""

import tempfile
import os
import sys
import subprocess

# Add parent directory to path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import parse_items


def test_end_to_end_overlay_no_insertion():
    """End-to-end test validating overlay contexts block '" in' insertion."""
    
    # Create input YAML with examples from the issue
    input_content = """# Test overlay-governed contexts block insertion
- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.1
  Name: Render fruit label overlay
  Text: |
    The system overlays label "fruit" in white
  Verified_By: 
  Traced_To: 

# Test non-overlay context allows insertion
- Type: Requirement
  Parent_Req: 
  ID: REQU.TEST.2
  Name: Render fruit label display
  Text: |
    The label "fruit" in white is displayed
  Verified_By: 
  Traced_To: 

# Test shall render context continues to block insertion (regression)
- Type: Requirement
  Parent_Req: 
  ID: REQU.TEST.3
  Name: Render fruit label
  Text: |
    The system shall render label "fruit" in white
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
        
        # Verify we have 3 verification items
        assert len(verifications) == 3, f"Expected 3 verification items, got {len(verifications)}"
        
        # Test 1: Overlay context should NOT insert "is rendered"
        ver1 = verifications[0]
        assert ver1['ID'] == 'VREQU.DMGR.TEST.1', f"Expected VREQU.DMGR.TEST.1, got {ver1['ID']}"
        # The transformation preserves "overlays" in active voice and does NOT insert "is rendered in"
        # Expected: "Verify the system overlays label \"fruit\" in white"
        assert '"fruit" in white' in ver1['Text'], \
            f"Overlay context: should preserve '\" in white' without insertion. Got: {ver1['Text']}"
        assert '"fruit" is rendered in white' not in ver1['Text'], \
            f"Overlay context: should NOT insert 'is rendered'. Got: {ver1['Text']}"
        print("✓ Test 1: Overlay context blocks insertion")
        
        # Test 2: Non-overlay context should insert "is rendered"
        ver2 = verifications[1]
        assert ver2['ID'] == 'VREQU.TEST.2', f"Expected VREQU.TEST.2, got {ver2['ID']}"
        assert '"fruit" is rendered in white' in ver2['Text'], \
            f"Non-overlay context: should insert 'is rendered'. Got: {ver2['Text']}"
        print("✓ Test 2: Non-overlay context allows insertion")
        
        # Test 3: Shall render context should NOT insert "is rendered" (regression)
        ver3 = verifications[2]
        assert ver3['ID'] == 'VREQU.TEST.3', f"Expected VREQU.TEST.3, got {ver3['ID']}"
        # The transformation should convert "shall render" to "renders" but NOT insert "is rendered in"
        assert '"fruit" in white' in ver3['Text'], \
            f"Render context: should preserve '\" in white' without insertion. Got: {ver3['Text']}"
        assert '"fruit" is rendered in white' not in ver3['Text'], \
            f"Render context: should NOT insert 'is rendered'. Got: {ver3['Text']}"
        print("✓ Test 3: Render context still blocks insertion (regression test)")
        
        # Verify the original requirements were not modified (only Verified_By added)
        requirements = [item for item in items if item.get('Type', '').strip() == 'Requirement']
        assert len(requirements) == 3, f"Expected 3 requirement items, got {len(requirements)}"
        
        req1 = requirements[0]
        assert 'overlays label "fruit" in white' in req1['Text'], \
            "Original requirement text should not be modified"
        assert req1['Verified_By'] == 'VREQU.DMGR.TEST.1', "Verified_By should be set"
        
        print("\n✓ All end-to-end tests passed!")
        
    finally:
        # Cleanup
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == '__main__':
    test_end_to_end_overlay_no_insertion()
    print("=" * 60)
    print("End-to-end overlay '\" in' pattern policy test completed!")
    print("=" * 60)
