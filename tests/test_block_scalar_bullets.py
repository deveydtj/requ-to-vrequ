#!/usr/bin/env python3
"""
Pytest tests for ID sequencing with block scalar content containing bullets.

This test suite validates that bullet points (lines starting with "- ") inside
block scalars (e.g., Text: |) do not interfere with item indexing during ID sequencing.

This is a regression test for the bug where apply_id_sequence_patch() incorrectly
counted lines starting with "- " inside block scalars as new items, causing
item_index drift and misalignment with the id_map.
"""

from generate_verification_yaml import (
    parse_items,
    build_id_sequence_map,
    apply_id_sequence_patch,
)


def test_block_scalar_bullets_do_not_affect_item_indexing(temp_yaml_file):
    """
    Test that bullet points inside block scalars don't affect item counting.
    
    This is the core regression test for the bug where lines starting with "- "
    inside a Text: | block were incorrectly treated as new items.
    """
    test_yaml = """- Type: Requirement
  ID: REQU.STEM.89
  Name: First requirement
  Text: |
    (U) The system shall render these features:
    - bullet one
    - bullet two
    - bullet three

- Type: Requirement
  ID: REQU.STEM.X
  Name: Second requirement (placeholder)
  Text: |
    (U) Some text without bullets.

- Type: Requirement
  ID: REQU.STEM.X
  Name: Third requirement (placeholder)
  Text: |
    (U) More features:
    - feature A
    - feature B

- Type: Requirement
  ID: REQU.STEM.X
  Name: Fourth requirement (placeholder)
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    
    # Verify parse_items creates exactly 4 items (4 requirements, no comments)
    assert len(items) == 4, f"Expected 4 items (4 requirements), got {len(items)}"
    
    # Build ID sequence map
    id_map = build_id_sequence_map(items)
    
    # Verify the map was built correctly
    # Item 0: REQU.STEM.89 (anchor, no mapping)
    # Item 1: REQU.STEM.X -> should map to REQU.STEM.90
    # Item 2: REQU.STEM.X -> should map to REQU.STEM.91
    # Item 3: REQU.STEM.X -> should map to REQU.STEM.92
    assert len(id_map) == 3, f"Should have 3 mappings for 3 placeholder IDs, got {len(id_map)}"
    
    # Check the map keys contain correct indices
    assert "REQU.STEM.X@1" in id_map, "Should have mapping for item at index 1"
    assert "REQU.STEM.X@2" in id_map, "Should have mapping for item at index 2"
    assert "REQU.STEM.X@3" in id_map, "Should have mapping for item at index 3"
    
    # Check the mapped values
    assert id_map["REQU.STEM.X@1"] == "REQU.STEM.90", "First .X should map to .90"
    assert id_map["REQU.STEM.X@2"] == "REQU.STEM.91", "Second .X should map to .91"
    assert id_map["REQU.STEM.X@3"] == "REQU.STEM.92", "Third .X should map to .92"
    
    # Apply the patch - this is where the bug occurs
    sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
    
    # Verify the output has the sequenced IDs in the correct positions
    assert "ID: REQU.STEM.89" in sequenced_text, "Should preserve REQU.STEM.89"
    assert "ID: REQU.STEM.90" in sequenced_text, "Should have REQU.STEM.90 (sequenced from first .X)"
    assert "ID: REQU.STEM.91" in sequenced_text, "Should have REQU.STEM.91 (sequenced from second .X)"
    assert "ID: REQU.STEM.92" in sequenced_text, "Should have REQU.STEM.92 (sequenced from third .X)"
    
    # Verify no .X remain in ID lines
    lines = sequenced_text.split('\n')
    for line in lines:
        if line.strip().startswith("ID:"):
            assert ".X" not in line, f"Should not have .X in ID line: {line}"
    
    # Verify bullet points are preserved in Text blocks
    assert "- bullet one" in sequenced_text
    assert "- bullet two" in sequenced_text
    assert "- bullet three" in sequenced_text
    assert "- feature A" in sequenced_text
    assert "- feature B" in sequenced_text
    
    # Verify the sequence is in order by checking positions
    pos_89 = sequenced_text.find("ID: REQU.STEM.89")
    pos_90 = sequenced_text.find("ID: REQU.STEM.90")
    pos_91 = sequenced_text.find("ID: REQU.STEM.91")
    pos_92 = sequenced_text.find("ID: REQU.STEM.92")
    
    assert pos_89 < pos_90 < pos_91 < pos_92, "IDs should appear in order: 89, 90, 91, 92"


def test_block_scalar_bullets_multiple_blocks(temp_yaml_file):
    """
    Test with multiple block scalars containing bullets in the same file.
    """
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: First requirement
  Text: |
    Requirements:
    - item 1
    - item 2

- Type: Requirement
  ID: REQU.TEST.X
  Name: Second requirement
  Text: |
    More requirements:
    - item A
    - item B
    - item C

- Type: Requirement
  ID: REQU.TEST.X
  Name: Third requirement
  Text: |
    Final requirements:
    - last item
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    id_map = build_id_sequence_map(items)
    
    # Apply patch
    sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
    
    # Verify sequencing
    assert "ID: REQU.TEST.1" in sequenced_text
    assert "ID: REQU.TEST.2" in sequenced_text
    assert "ID: REQU.TEST.3" in sequenced_text
    assert "ID: REQU.TEST.X" not in sequenced_text
    
    # Verify bullets preserved
    assert "- item 1" in sequenced_text
    assert "- item A" in sequenced_text
    assert "- last item" in sequenced_text


def test_block_scalar_with_name_field(temp_yaml_file):
    """
    Test that block scalars work for fields other than Text (like Name).
    """
    test_yaml = """- Type: Requirement
  ID: REQU.TEST.1
  Name: |
    First requirement with:
    - bullet in name
  Text: Some text

- Type: Requirement
  ID: REQU.TEST.X
  Name: |
    Second requirement with:
    - another bullet
  Text: More text
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    id_map = build_id_sequence_map(items)
    
    sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
    
    # Verify sequencing worked
    assert "ID: REQU.TEST.2" in sequenced_text
    assert "ID: REQU.TEST.X" not in sequenced_text
    
    # Verify bullets in Name field are preserved
    assert "- bullet in name" in sequenced_text
    assert "- another bullet" in sequenced_text


def test_mixed_block_scalars_and_preamble_comments(temp_yaml_file):
    """
    Test that block scalars with bullets work correctly when combined with preamble comments.
    """
    test_yaml = """# Preamble comment 1
# Preamble comment 2

- Type: Requirement
  ID: REQU.TEST.1
  Name: First requirement
  Text: |
    (U) Requirements:
    - bullet 1
    - bullet 2

- Type: Requirement
  ID: REQU.TEST.X
  Name: Second requirement
  Text: |
    (U) More:
    - bullet A

- Type: Requirement
  ID: REQU.TEST.X
  Name: Third requirement
"""
    
    temp_path = temp_yaml_file(test_yaml)
    items = parse_items(temp_path)
    
    # Should have 2 comment items + 3 requirement items = 5 items
    assert len(items) == 5, f"Expected 5 items (2 comments + 3 requirements), got {len(items)}"
    
    id_map = build_id_sequence_map(items)
    
    # Items 0-1 are comments, items 2-4 are requirements
    # Item 2: REQU.TEST.1 (anchor)
    # Item 3: REQU.TEST.X -> .2
    # Item 4: REQU.TEST.X -> .3
    assert "REQU.TEST.X@3" in id_map
    assert "REQU.TEST.X@4" in id_map
    
    sequenced_text = apply_id_sequence_patch(test_yaml, id_map)
    
    # Verify sequencing
    assert "ID: REQU.TEST.1" in sequenced_text
    assert "ID: REQU.TEST.2" in sequenced_text
    assert "ID: REQU.TEST.3" in sequenced_text
    
    # Verify preamble comments preserved
    assert "# Preamble comment 1" in sequenced_text
    assert "# Preamble comment 2" in sequenced_text
    
    # Verify bullets preserved
    assert "- bullet 1" in sequenced_text
    assert "- bullet A" in sequenced_text
