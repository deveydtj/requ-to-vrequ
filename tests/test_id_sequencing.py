#!/usr/bin/env python3
"""
Test script for ID sequencing functionality.

This script validates that the generate_verification_yaml.py script correctly:
1. Sequences .X/.x placeholder IDs based on anchored numbering
2. Applies sequencing independently for DMGR, BRDG, and OTHER domains
3. Skips sequencing when no numbered anchor exists
4. Does not renumber already-numbered IDs
5. Stops sequencing when suffix diverges from stem
"""

import sys
import os
import tempfile

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    parse_items,
    build_id_sequence_map,
    apply_id_sequence_patch,
    sequence_requirement_ids,
)


def test_basic_sequencing():
    """Test basic ID sequencing with a single domain."""
    print("Testing basic ID sequencing...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First requirement
  
- Type: Requirement
  ID: REQU.TEST.X
  Name: Second requirement
  
- Type: Requirement
  ID: REQU.TEST.X
  Name: Third requirement
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(temp_path)
        id_map = build_id_sequence_map(items)
        
        # Check that we have exactly 2 mappings (for the two .X placeholders)
        assert len(id_map) == 2, f"Should have 2 mappings, got {len(id_map)}"
        
        # Apply sequencing
        sequenced_items = sequence_requirement_ids(items, id_map)
        
        # Get IDs from sequenced items
        ids = [item.get("ID") for item in sequenced_items if item.get("ID", "").startswith("REQU.TEST.")]
        
        # Should have .1, .2, .3
        assert "REQU.TEST.1" in ids, "Should have REQU.TEST.1"
        assert "REQU.TEST.2" in ids, "Should have REQU.TEST.2"
        assert "REQU.TEST.3" in ids, "Should have REQU.TEST.3"
        
        # Should not have .X
        assert "REQU.TEST.X" not in ids, "Should not have .X in output"
        
        # Apply to text
        sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
        
        # Count occurrences
        assert sequenced_text.count("REQU.TEST.2") >= 1, "Should have REQU.TEST.2 in output"
        assert sequenced_text.count("REQU.TEST.3") >= 1, "Should have REQU.TEST.3 in output"
        assert "REQU.TEST.X" not in sequenced_text, "Should not have .X in output"
        
        print("✓ Basic sequencing test passed")
        
    finally:
        os.remove(temp_path)


def test_independent_domain_sequencing():
    """Test that DMGR and BRDG domains sequence independently."""
    print("\nTesting independent domain sequencing...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.DMGR.TEST.1
  Name: DMGR requirement 1

- Type: Requirement
  ID: REQU.BRDG.TEST.1
  Name: BRDG requirement 1

- Type: Requirement
  ID: REQU.DMGR.TEST.X
  Name: DMGR requirement 2

- Type: Requirement
  ID: REQU.BRDG.TEST.X
  Name: BRDG requirement 2

- Type: Requirement
  ID: REQU.DMGR.TEST.X
  Name: DMGR requirement 3
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(temp_path)
        sequenced_items = sequence_requirement_ids(items)
        
        # Extract IDs from sequenced items
        dmgr_ids = [item.get("ID") for item in sequenced_items if ".DMGR." in item.get("ID", "")]
        brdg_ids = [item.get("ID") for item in sequenced_items if ".BRDG." in item.get("ID", "")]
        
        # DMGR should have .1, .2, .3
        assert "REQU.DMGR.TEST.1" in dmgr_ids, "Should have DMGR.1"
        assert "REQU.DMGR.TEST.2" in dmgr_ids, "Should have DMGR.2"
        assert "REQU.DMGR.TEST.3" in dmgr_ids, "Should have DMGR.3"
        
        # BRDG should have .1, .2
        assert "REQU.BRDG.TEST.1" in brdg_ids, "Should have BRDG.1"
        assert "REQU.BRDG.TEST.2" in brdg_ids, "Should have BRDG.2"
        
        print("✓ Independent domain sequencing test passed")
        
    finally:
        os.remove(temp_path)


def test_no_anchor_skips_sequencing():
    """Test that .X/.x IDs without a numbered anchor are left unchanged."""
    print("\nTesting sequencing skip when no anchor exists...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.NOANCHOR.X
  Name: No anchor 1

- Type: Requirement
  ID: REQU.NOANCHOR.x
  Name: No anchor 2
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(temp_path)
        id_map = build_id_sequence_map(items)
        
        # Should not create any mappings since there's no anchor
        # Note: id_map keys have format "ID@INDEX"
        has_noanchor_mapping = any("REQU.NOANCHOR." in key for key in id_map.keys())
        assert not has_noanchor_mapping, "Should not sequence IDs without anchor"
        
        sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
        
        # Original text should be unchanged
        assert "REQU.NOANCHOR.X" in sequenced_text, "Should preserve .X without anchor"
        assert "REQU.NOANCHOR.x" in sequenced_text, "Should preserve .x without anchor"
        
        print("✓ No anchor skip test passed")
        
    finally:
        os.remove(temp_path)


def test_already_numbered_not_renumbered():
    """Test that already-numbered IDs are not renumbered."""
    print("\nTesting that numbered IDs are not renumbered...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First

- Type: Requirement
  ID: REQU.TEST.2
  Name: Second (already numbered)

- Type: Requirement
  ID: REQU.TEST.X
  Name: Third (to be sequenced)

- Type: Requirement
  ID: REQU.TEST.5
  Name: Fifth (already numbered)

- Type: Requirement
  ID: REQU.TEST.X
  Name: Sixth (to be sequenced)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(temp_path)
        sequenced_items = sequence_requirement_ids(items)
        
        # Extract IDs
        ids = [item.get("ID") for item in sequenced_items if item.get("ID", "").startswith("REQU.TEST.")]
        
        # Should preserve numbered IDs
        assert "REQU.TEST.1" in ids, "Should preserve .1"
        assert "REQU.TEST.2" in ids, "Should preserve .2"
        assert "REQU.TEST.5" in ids, "Should preserve .5"
        
        # Should sequence .X to .3 and .6
        assert "REQU.TEST.3" in ids, "First .X should become .3"
        assert "REQU.TEST.6" in ids, "Second .X should become .6 (after .5)"
        
        # Should not have any .X
        assert not any(".X" in id for id in ids), "Should not have any .X in output"
        
        print("✓ Numbered IDs preservation test passed")
        
    finally:
        os.remove(temp_path)


def test_different_stems_separate_sequencing():
    """Test that items with different stems have separate sequencing."""
    print("\nTesting separate sequencing for different stems...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.DMGR.ALPHA.1
  Name: Alpha 1

- Type: Requirement
  ID: REQU.DMGR.BETA.1
  Name: Beta 1

- Type: Requirement
  ID: REQU.DMGR.ALPHA.X
  Name: Alpha 2

- Type: Requirement
  ID: REQU.DMGR.BETA.X
  Name: Beta 2
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(temp_path)
        sequenced_items = sequence_requirement_ids(items)
        
        # Extract IDs
        alpha_ids = [item.get("ID") for item in sequenced_items if ".ALPHA." in item.get("ID", "")]
        beta_ids = [item.get("ID") for item in sequenced_items if ".BETA." in item.get("ID", "")]
        
        # Each stem should sequence independently
        assert "REQU.DMGR.ALPHA.1" in alpha_ids, "Should have ALPHA.1"
        assert "REQU.DMGR.ALPHA.2" in alpha_ids, "Should have ALPHA.2"
        
        assert "REQU.DMGR.BETA.1" in beta_ids, "Should have BETA.1"
        assert "REQU.DMGR.BETA.2" in beta_ids, "Should have BETA.2"
        
        print("✓ Different stems test passed")
        
    finally:
        os.remove(temp_path)


def test_mixed_case_x():
    """Test that both .X and .x are handled."""
    print("\nTesting mixed case .X/.x...")
    
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First

- Type: Requirement
  ID: REQU.TEST.X
  Name: Second (uppercase X)

- Type: Requirement
  ID: REQU.TEST.x
  Name: Third (lowercase x)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(temp_path)
        id_map = build_id_sequence_map(items)
        
        # Should have exactly 2 mappings (for .X and .x)
        assert len(id_map) == 2, f"Should have 2 mappings, got {len(id_map)}"
        
        sequenced_items = sequence_requirement_ids(items, id_map)
        ids = [item.get("ID") for item in sequenced_items if item.get("ID", "").startswith("REQU.TEST.")]
        
        # Should have .1, .2, .3
        assert "REQU.TEST.1" in ids, "Should have .1"
        assert "REQU.TEST.2" in ids, "Should have .2"
        assert "REQU.TEST.3" in ids, "Should have .3"
        
        # Should not have .X or .x
        assert "REQU.TEST.X" not in ids, "Should not have .X"
        assert "REQU.TEST.x" not in ids, "Should not have .x"
        
        sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
        
        # Should have .2 and .3
        assert "REQU.TEST.2" in sequenced_text, "Should have .2"
        assert "REQU.TEST.3" in sequenced_text, "Should have .3"
        
        # Should not have .X or .x
        assert "REQU.TEST.X" not in sequenced_text, "Should not have .X"
        assert "REQU.TEST.x" not in sequenced_text, "Should not have .x"
        
        print("✓ Mixed case test passed")
        
    finally:
        os.remove(temp_path)


def test_end_to_end_with_verification():
    """Test full pipeline including verification generation."""
    print("\nTesting end-to-end with verification generation...")
    
    test_yaml = """- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.1
  Name: Render the dashboard
  Text: |
    (U) The system shall render the dashboard.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.X
  Name: Render the status
  Text: |
    (U) The system shall render the status indicator.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.CONFIG.1
  Name: Set the timeout
  Text: |
    (U) The system shall set the timeout to 30 seconds.
  Verified_By: 
  Traced_To: 

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.CONFIG.X
  Name: Set the mode
  Text: |
    (U) The system shall set the mode to active.
  Verified_By: 
  Traced_To: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_path = f.name
        f.write(test_yaml)
    
    output_path = None
    try:
        output_path = input_path.replace('.yaml', '_output.yaml')
        
        # Run the script
        import subprocess
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'generate_verification_yaml.py'
        )
        result = subprocess.run(
            [sys.executable, script_path, input_path, output_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            assert False, "Script execution failed"
        
        with open(output_path, 'r') as f:
            output = f.read()
        
        # Verify sequencing happened
        assert "REQU.DMGR.TEST.1" in output, "Should have DMGR.TEST.1"
        assert "REQU.DMGR.TEST.2" in output, "Should have DMGR.TEST.2 (sequenced from .X)"
        assert "REQU.BRDG.CONFIG.1" in output, "Should have BRDG.CONFIG.1"
        assert "REQU.BRDG.CONFIG.2" in output, "Should have BRDG.CONFIG.2 (sequenced from .X)"
        
        # Verify no .X remain in requirements section
        lines = output.split('\n')
        in_requirements = True
        for i, line in enumerate(lines):
            # Stop when we hit verifications section
            if 'Type: DMGR Verification Requirement' in line or \
               'Type: BRDG Verification Requirement' in line or \
               'Type: Verification' in line:
                in_requirements = False
            
            if in_requirements and 'ID: REQU.' in line:
                assert '.X' not in line, f"Should not have .X in requirements section: {line}"
        
        # Verify verifications were generated with correct IDs
        assert "VREQU.DMGR.TEST.1" in output, "Should have verification for DMGR.TEST.1"
        assert "VREQU.DMGR.TEST.2" in output, "Should have verification for DMGR.TEST.2"
        assert "VREQU.BRDG.CONFIG.1" in output, "Should have verification for BRDG.CONFIG.1"
        assert "VREQU.BRDG.CONFIG.2" in output, "Should have verification for BRDG.CONFIG.2"
        
        # Verify Verified_By fields were updated with sequenced IDs
        assert "Verified_By: VREQU.DMGR.TEST.2" in output, "Should have Verified_By for sequenced ID"
        assert "Verified_By: VREQU.BRDG.CONFIG.2" in output, "Should have Verified_By for sequenced ID"
        
        print("✓ End-to-end test passed")
        
    finally:
        os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)


def test_non_requirement_items_unchanged():
    """Test that non-Requirement items are not affected by sequencing."""
    print("\nTesting non-requirement items are unchanged...")
    
    test_yaml = """- Type: SomeOtherType
  ID: OTHER.TEST.X
  Name: Not a requirement

- Type: Requirement
  ID: REQU.TEST.1
  Name: Real requirement

- Type: Requirement
  ID: REQU.TEST.X
  Name: Another requirement
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(test_yaml)
    
    try:
        items = parse_items(temp_path)
        sequenced_items = sequence_requirement_ids(items)
        
        # The non-requirement item should be unchanged
        other_items = [item for item in sequenced_items if item.get("Type") == "SomeOtherType"]
        assert len(other_items) == 1, "Should have one non-requirement item"
        assert other_items[0].get("ID") == "OTHER.TEST.X", "Non-requirement ID should be unchanged"
        
        # The requirement items should be sequenced
        req_ids = [item.get("ID") for item in sequenced_items if item.get("Type") == "Requirement"]
        assert "REQU.TEST.1" in req_ids, "Should have REQU.TEST.1"
        assert "REQU.TEST.2" in req_ids, "Should have REQU.TEST.2"
        assert "REQU.TEST.X" not in req_ids, "Should not have REQU.TEST.X"
        
        print("✓ Non-requirement items test passed")
        
    finally:
        os.remove(temp_path)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running ID sequencing tests")
    print("=" * 60)
    
    try:
        test_basic_sequencing()
        test_independent_domain_sequencing()
        test_no_anchor_skips_sequencing()
        test_already_numbered_not_renumbered()
        test_different_stems_separate_sequencing()
        test_mixed_case_x()
        test_non_requirement_items_unchanged()
        test_end_to_end_with_verification()
        
        print("\n" + "=" * 60)
        print("All ID sequencing tests passed! ✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
