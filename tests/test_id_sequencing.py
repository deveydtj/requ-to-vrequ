#!/usr/bin/env python3
"""
Pytest tests for ID sequencing functionality.

This test suite validates that the generate_verification_yaml.py script correctly:
1. Sequences .X/.x placeholder IDs based on anchored numbering
2. Applies sequencing independently for DMGR, BRDG, and OTHER domains
3. Skips sequencing when no numbered anchor exists
4. Does not renumber already-numbered IDs
5. Stops sequencing when suffix diverges from stem
6. Handles end-to-end verification generation with proper Traced_To copying
7. Respects CLI flags (--no-sequence and --sequence-log)

Target Python version: 3.10.0+
"""

import sys
import os
import tempfile
import subprocess
import pytest

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_verification_yaml import (
    parse_items,
    build_id_sequence_map,
    apply_id_sequence_patch,
    sequence_requirement_ids,
    generate_verification_items,
)



# Fixtures and helper functions

@pytest.fixture
def temp_yaml_file():
    """Fixture to create and cleanup temporary YAML files."""
    temp_files = []
    
    def _create_temp_file(content):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        temp_path = f.name
        f.write(content)
        f.close()
        temp_files.append(temp_path)
        return temp_path
    
    yield _create_temp_file
    
    # Cleanup
    for path in temp_files:
        if os.path.exists(path):
            os.remove(path)


def get_script_path():
    """Get the path to the main script."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'generate_verification_yaml.py'
    )


# Unit tests for build_id_sequence_map()

def test_build_id_sequence_map_basic(temp_yaml_file):
    """Test basic ID sequencing with a single domain."""
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
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    id_map = build_id_sequence_map(items)
    
    # Check that we have exactly 2 mappings (for the two .X placeholders)
    assert len(id_map) == 2, f"Should have 2 mappings, got {len(id_map)}"
    
    # Verify the mapping values (not the keys which include @index)
    mapped_values = set(id_map.values())
    assert "REQU.TEST.2" in mapped_values, "Should map to REQU.TEST.2"
    assert "REQU.TEST.3" in mapped_values, "Should map to REQU.TEST.3"


def test_build_id_sequence_map_dmgr_anchored(temp_yaml_file):
    """Test DMGR anchored sequence with multiple .X/.x placeholders."""
    test_yaml = """- Type: Requirement
  ID: REQU.DMGR.FEATURE.1
  Name: DMGR requirement 1

- Type: Requirement
  ID: REQU.DMGR.FEATURE.X
  Name: DMGR requirement 2

- Type: Requirement
  ID: REQU.DMGR.FEATURE.x
  Name: DMGR requirement 3

- Type: Requirement
  ID: REQU.DMGR.FEATURE.X
  Name: DMGR requirement 4
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    id_map = build_id_sequence_map(items)
    
    # Should have 3 mappings for the three placeholders
    assert len(id_map) == 3, f"Should have 3 mappings, got {len(id_map)}"
    
    # Verify sequential numbering: 2, 3, 4
    mapped_values = set(id_map.values())
    assert "REQU.DMGR.FEATURE.2" in mapped_values
    assert "REQU.DMGR.FEATURE.3" in mapped_values
    assert "REQU.DMGR.FEATURE.4" in mapped_values


def test_build_id_sequence_map_brdg_independent(temp_yaml_file):
    """Test BRDG anchored sequence independent of DMGR."""
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
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    sequenced_items = sequence_requirement_ids(items)
    
    # Extract IDs from sequenced items
    dmgr_ids = [item.get("ID") for item in sequenced_items if ".DMGR." in item.get("ID", "")]
    brdg_ids = [item.get("ID") for item in sequenced_items if ".BRDG." in item.get("ID", "")]
    
    # DMGR should have .1, .2, .3
    assert "REQU.DMGR.TEST.1" in dmgr_ids
    assert "REQU.DMGR.TEST.2" in dmgr_ids
    assert "REQU.DMGR.TEST.3" in dmgr_ids
    
    # BRDG should have .1, .2 (independent sequencing)
    assert "REQU.BRDG.TEST.1" in brdg_ids
    assert "REQU.BRDG.TEST.2" in brdg_ids


def test_build_id_sequence_map_no_anchor_skip(temp_yaml_file):
    """Test that .X/.x IDs without a numbered anchor are left unchanged."""
    test_yaml = """- Type: Requirement
  ID: REQU.NOANCHOR.X
  Name: No anchor 1

- Type: Requirement
  ID: REQU.NOANCHOR.x
  Name: No anchor 2
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    id_map = build_id_sequence_map(items)
    
    # Should not create any mappings since there's no anchor
    has_noanchor_mapping = any("REQU.NOANCHOR." in key for key in id_map.keys())
    assert not has_noanchor_mapping, "Should not sequence IDs without anchor"
    
    # Verify text is unchanged
    sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
    assert "REQU.NOANCHOR.X" in sequenced_text
    assert "REQU.NOANCHOR.x" in sequenced_text


def test_build_id_sequence_map_mixed_stems(temp_yaml_file):
    """Test that items with different stems have separate sequencing (separate counters per stem)."""
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
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    sequenced_items = sequence_requirement_ids(items)
    
    # Extract IDs
    alpha_ids = [item.get("ID") for item in sequenced_items if ".ALPHA." in item.get("ID", "")]
    beta_ids = [item.get("ID") for item in sequenced_items if ".BETA." in item.get("ID", "")]
    
    # Each stem should sequence independently
    assert "REQU.DMGR.ALPHA.1" in alpha_ids
    assert "REQU.DMGR.ALPHA.2" in alpha_ids
    
    assert "REQU.DMGR.BETA.1" in beta_ids
    assert "REQU.DMGR.BETA.2" in beta_ids


# Unit tests for sequence_requirement_ids()

def test_sequence_requirement_ids_basic(temp_yaml_file):
    """Test sequence_requirement_ids() applies ID sequencing correctly."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First

- Type: Requirement
  ID: REQU.TEST.X
  Name: Second

- Type: Requirement
  ID: REQU.TEST.X
  Name: Third
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    sequenced_items = sequence_requirement_ids(items)
    
    # Get IDs from sequenced items
    ids = [item.get("ID") for item in sequenced_items if item.get("ID", "").startswith("REQU.TEST.")]
    
    # Should have .1, .2, .3
    assert "REQU.TEST.1" in ids
    assert "REQU.TEST.2" in ids
    assert "REQU.TEST.3" in ids
    
    # Should not have .X
    assert "REQU.TEST.X" not in ids


def test_sequence_requirement_ids_preserves_numbered(temp_yaml_file):
    """Test that already-numbered IDs are not renumbered."""
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
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    sequenced_items = sequence_requirement_ids(items)
    
    # Extract IDs
    ids = [item.get("ID") for item in sequenced_items if item.get("ID", "").startswith("REQU.TEST.")]
    
    # Should preserve numbered IDs
    assert "REQU.TEST.1" in ids
    assert "REQU.TEST.2" in ids
    assert "REQU.TEST.5" in ids
    
    # Should sequence .X to .3 and .6
    assert "REQU.TEST.3" in ids, "First .X should become .3"
    assert "REQU.TEST.6" in ids, "Second .X should become .6 (after .5)"
    
    # Should not have any .X
    assert not any(".X" in id for id in ids)


def test_sequence_requirement_ids_mixed_case_x(temp_yaml_file):
    """Test that both .X and .x are handled."""
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
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    id_map = build_id_sequence_map(items)
    
    # Should have exactly 2 mappings (for .X and .x)
    assert len(id_map) == 2, f"Should have 2 mappings, got {len(id_map)}"
    
    sequenced_items = sequence_requirement_ids(items, id_map)
    ids = [item.get("ID") for item in sequenced_items if item.get("ID", "").startswith("REQU.TEST.")]
    
    # Should have .1, .2, .3
    assert "REQU.TEST.1" in ids
    assert "REQU.TEST.2" in ids
    assert "REQU.TEST.3" in ids
    
    # Should not have .X or .x
    assert "REQU.TEST.X" not in ids
    assert "REQU.TEST.x" not in ids


def test_sequence_requirement_ids_non_requirement_unchanged(temp_yaml_file):
    """Test that non-Requirement items are not affected by sequencing."""
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
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    sequenced_items = sequence_requirement_ids(items)
    
    # The non-requirement item should be unchanged
    other_items = [item for item in sequenced_items if item.get("Type") == "SomeOtherType"]
    assert len(other_items) == 1
    assert other_items[0].get("ID") == "OTHER.TEST.X", "Non-requirement ID should be unchanged"
    
    # The requirement items should be sequenced
    req_ids = [item.get("ID") for item in sequenced_items if item.get("Type") == "Requirement"]
    assert "REQU.TEST.1" in req_ids
    assert "REQU.TEST.2" in req_ids
    assert "REQU.TEST.X" not in req_ids


# Unit tests for apply_id_sequence_patch()

def test_apply_id_sequence_patch_basic(temp_yaml_file):
    """Test apply_id_sequence_patch() updates IDs in text format."""
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
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    id_map = build_id_sequence_map(items)
    
    # Apply to text
    sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
    
    # Verify text has sequenced IDs
    assert sequenced_text.count("REQU.TEST.2") >= 1, "Should have REQU.TEST.2 in output"
    assert sequenced_text.count("REQU.TEST.3") >= 1, "Should have REQU.TEST.3 in output"
    assert "REQU.TEST.X" not in sequenced_text, "Should not have .X in output"


# End-to-end integration tests

def test_end_to_end_with_verification_and_traced_to(temp_yaml_file):
    """Test full pipeline including verification generation and Traced_To copying."""
    test_yaml = """- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.1
  Name: Render the dashboard
  Text: |
    (U) The system shall render the dashboard.
  Verified_By: 
  Traced_To: TRACE.DMGR.1

- Type: Requirement
  Parent_Req: 
  ID: REQU.DMGR.TEST.X
  Name: Render the status
  Text: |
    (U) The system shall render the status indicator.
  Verified_By: 
  Traced_To: TRACE.DMGR.2

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.CONFIG.1
  Name: Set the timeout
  Text: |
    (U) The system shall set the timeout to 30 seconds.
  Verified_By: 
  Traced_To: TRACE.BRDG.1

- Type: Requirement
  Parent_Req: 
  ID: REQU.BRDG.CONFIG.X
  Name: Set the mode
  Text: |
    (U) The system shall set the mode to active.
  Verified_By: 
  Traced_To: TRACE.BRDG.2
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, get_script_path(), input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        
        with open(output_path, 'r') as f:
            output = f.read()
        
        # Verify sequencing happened
        assert "REQU.DMGR.TEST.1" in output
        assert "REQU.DMGR.TEST.2" in output, "Should have DMGR.TEST.2 (sequenced from .X)"
        assert "REQU.BRDG.CONFIG.1" in output
        assert "REQU.BRDG.CONFIG.2" in output, "Should have BRDG.CONFIG.2 (sequenced from .X)"
        
        # Verify no .X remain in requirements section
        lines = output.split('\n')
        in_requirements = True
        for line in lines:
            # Stop when we hit verifications section
            if 'Type: DMGR Verification Requirement' in line or \
               'Type: BRDG Verification Requirement' in line or \
               'Type: Verification' in line:
                in_requirements = False
            
            if in_requirements and 'ID: REQU.' in line:
                assert '.X' not in line, f"Should not have .X in requirements section: {line}"
        
        # Verify verifications were generated with correct IDs
        assert "VREQU.DMGR.TEST.1" in output
        assert "VREQU.DMGR.TEST.2" in output
        assert "VREQU.BRDG.CONFIG.1" in output
        assert "VREQU.BRDG.CONFIG.2" in output
        
        # Verify Verified_By fields were updated with sequenced IDs
        assert "Verified_By: VREQU.DMGR.TEST.2" in output
        assert "Verified_By: VREQU.BRDG.CONFIG.2" in output
        
        # Verify Traced_To is copied unchanged to Verification items
        assert "Traced_To: TRACE.DMGR.1" in output
        assert "Traced_To: TRACE.DMGR.2" in output
        assert "Traced_To: TRACE.BRDG.1" in output
        assert "Traced_To: TRACE.BRDG.2" in output
        
        # Count Traced_To occurrences: should appear in both Req and Ver for each
        assert output.count("Traced_To: TRACE.DMGR.1") >= 2, "Traced_To should be in both Req and Ver"
        assert output.count("Traced_To: TRACE.DMGR.2") >= 2
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_end_to_end_cli_no_sequence_flag(temp_yaml_file):
    """Test --no-sequence flag disables sequencing."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First requirement
  Text: |
    (U) Test requirement.
  Verified_By: 

- Type: Requirement
  ID: REQU.TEST.X
  Name: Second requirement
  Text: |
    (U) Test requirement.
  Verified_By: 

- Type: Requirement
  ID: REQU.TEST.X
  Name: Third requirement
  Text: |
    (U) Test requirement.
  Verified_By: 
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    try:
        # Run with --no-sequence
        result = subprocess.run(
            [sys.executable, get_script_path(), '--no-sequence', input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        
        with open(output_path, 'r') as f:
            output = f.read()
        
        # Verify sequencing did NOT happen (should still have .X)
        assert "REQU.TEST.1" in output
        assert "REQU.TEST.X" in output, "Should still have .X (not sequenced)"
        
        # Should NOT have .2 or .3
        assert "REQU.TEST.2" not in output, "Should not have .2 (sequencing disabled)"
        assert "REQU.TEST.3" not in output, "Should not have .3 (sequencing disabled)"
        
        # Verification IDs should also use .X
        assert "VREQU.TEST.X" in output, "Verification should also use .X"
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_end_to_end_cli_sequence_log_flag(temp_yaml_file):
    """Test --sequence-log flag prints sequencing information."""
    test_yaml = """- Type: Requirement
  ID: REQU.DMGR.TEST.1
  Name: Render first
  Text: |
    (U) The system shall render the first item.
  Verified_By: 

- Type: Requirement
  ID: REQU.DMGR.TEST.X
  Name: Render second
  Text: |
    (U) The system shall render the second item.
  Verified_By: 

- Type: Requirement
  ID: REQU.BRDG.TEST.5
  Name: Set first
  Text: |
    (U) The system shall set the first value.
  Verified_By: 

- Type: Requirement
  ID: REQU.BRDG.TEST.X
  Name: Set second
  Text: |
    (U) The system shall set the second value.
  Verified_By: 
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    try:
        # Run with --sequence-log
        result = subprocess.run(
            [sys.executable, get_script_path(), '--sequence-log', input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        
        # Check stdout for sequencing information
        stdout = result.stdout
        
        # Should have header
        assert "ID Sequencing Summary:" in stdout, "Should have summary header"
        
        # Should show the sequenced IDs
        assert "REQU.DMGR.TEST.X -> REQU.DMGR.TEST.2" in stdout, "Should show DMGR sequencing"
        assert "REQU.BRDG.TEST.X -> REQU.BRDG.TEST.6" in stdout, "Should show BRDG sequencing"
        
        # Verify output file still has sequenced IDs
        with open(output_path, 'r') as f:
            output = f.read()
        
        assert "REQU.DMGR.TEST.2" in output
        assert "REQU.BRDG.TEST.6" in output
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_end_to_end_cli_no_sequence_with_sequence_log(temp_yaml_file):
    """Test that --sequence-log has no effect when --no-sequence is used."""
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First requirement
  Text: |
    (U) Test requirement.
  Verified_By: 

- Type: Requirement
  ID: REQU.TEST.X
  Name: Second requirement
  Text: |
    (U) Test requirement.
  Verified_By: 
"""
    
    input_path = temp_yaml_file(test_yaml)
    output_path = input_path.replace('.yaml', '_output.yaml')
    
    try:
        # Run with both flags
        result = subprocess.run(
            [sys.executable, get_script_path(), '--no-sequence', '--sequence-log', 
             input_path, output_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        
        # Should not print any sequencing info (since sequencing is disabled)
        stdout = result.stdout
        assert "ID Sequencing Summary:" not in stdout, \
            "Should not show summary when sequencing is disabled"
        
        # Verify output has .X (not sequenced)
        with open(output_path, 'r') as f:
            output = f.read()
        
        assert "REQU.TEST.X" in output
        assert "REQU.TEST.2" not in output
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

