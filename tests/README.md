# Tests for generate_verification_yaml.py

This directory contains pytest tests for the verification YAML generator.

## Requirements

- Python 3.10.0+
- pytest (install with `pip install pytest`)

## Running Tests

To run the entire test suite:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_id_sequencing.py
pytest tests/test_cli_flags.py
```

To run with verbose output:

```bash
pytest -v
```

To run a specific test function:

```bash
pytest tests/test_id_sequencing.py::test_build_id_sequence_map_basic -v
```

## Test Coverage

### test_id_sequencing.py

Focused pytest tests for ID sequencing logic and end-to-end behavior:

#### Unit Tests for `build_id_sequence_map()`:
- **test_build_id_sequence_map_basic**: Basic ID sequencing with single domain
- **test_build_id_sequence_map_dmgr_anchored**: DMGR anchored sequence with multiple .X/.x placeholders
- **test_build_id_sequence_map_brdg_independent**: BRDG sequencing independent of DMGR
- **test_build_id_sequence_map_no_anchor_skip**: Skips sequencing when no numbered anchor exists
- **test_build_id_sequence_map_mixed_stems**: Different stems use separate counters

#### Unit Tests for `sequence_requirement_ids()`:
- **test_sequence_requirement_ids_basic**: Applies ID sequencing correctly
- **test_sequence_requirement_ids_preserves_numbered**: Already-numbered IDs are not renumbered
- **test_sequence_requirement_ids_mixed_case_x**: Both .X and .x placeholders are handled
- **test_sequence_requirement_ids_non_requirement_unchanged**: Non-Requirement items unaffected

#### Unit Tests for `apply_id_sequence_patch()`:
- **test_apply_id_sequence_patch_basic**: Updates IDs in text format

#### End-to-End Integration Tests:
- **test_end_to_end_with_verification_and_traced_to**: Full pipeline with verification generation and Traced_To copying

### test_cli_flags.py

Pytest tests for CLI flags (--no-sequence and --sequence-log):

- **test_default_sequencing**: Default behavior enables sequencing
- **test_no_sequence_flag**: --no-sequence disables ID sequencing
- **test_sequence_log_flag**: --sequence-log prints sequencing information to stdout
- **test_no_sequence_with_sequence_log**: --sequence-log has no effect when --no-sequence is used
- **test_sequence_log_with_no_placeholders**: --sequence-log handles files with no placeholder IDs gracefully

### test_non_standard_flags.py

Tests for non-standard formatting flags and Option B behavior:

- **is_standard_name()**: Tests Name validation (must start with "Render " or "Set ")
- **is_standard_text()**: Tests Text validation based on domain
  - DMGR: Must contain "shall render"
  - BRDG: Must contain "shall set"
  - OTHER: No specific requirement
- **has_brdg_render_issue()**: Tests detection of "render"/"renders" in BRDG verifications (case-insensitive)
- **End-to-end**: Tests complete pipeline including:
  - Comment insertion before non-standard verifications
  - Minimal transformation for non-standard fields
  - Standard transformation for standard fields
  - BRDG render issue detection

### test_output_spacing.py

Tests for output formatting and spacing:

- **test_comment_adjacency**: Comments appear adjacent to their items
- **test_multiple_comments_and_items**: Multiple comments and items are spaced correctly
- **test_render_items_to_string_no_double_blanks**: No double blank lines when appending
- **test_end_to_end_spacing**: End-to-end spacing validation

## Pytest Configuration

The `pytest.ini` file configures:
- Test discovery patterns
- Minimum Python version (3.10)
- Verbose output by default
- Short traceback format

## Expected Behavior

### ID Sequencing
When a Requirement has placeholder IDs (.X or .x):

1. A numbered anchor (e.g., REQU.TEST.1) must exist for that domain and stem
2. Placeholders are sequenced starting from anchor + 1
3. Already-numbered IDs are preserved
4. Different domains (DMGR, BRDG, OTHER) sequence independently
5. Different stems within a domain have separate counters

### CLI Flags
- `--no-sequence`: Disables all ID sequencing (placeholders remain as .X/.x)
- `--sequence-log`: Prints a summary of ID renumbering to stdout
- Both flags can be combined (--sequence-log has no effect with --no-sequence)

### Verification Generation
- Verification IDs match the (possibly sequenced) Requirement IDs with "V" prefix
- Traced_To fields are copied unchanged from Requirement to Verification
- Verified_By fields are updated with the corresponding Verification ID

## Example

Input:
```yaml
- Type: Requirement
  ID: REQU.DMGR.TEST.1
  Name: Render the status
  Text: |
    (U) The system shall render the status.
  Traced_To: TRACE.1

- Type: Requirement
  ID: REQU.DMGR.TEST.X
  Name: Render the dashboard
  Text: |
    (U) The system shall render the dashboard.
  Traced_To: TRACE.2
```

Output:
```yaml
- Type: Requirement
  ID: REQU.DMGR.TEST.1
  Name: Render the status
  Text: |
    (U) The system shall render the status.
  Verified_By: VREQU.DMGR.TEST.1
  Traced_To: TRACE.1

- Type: Requirement
  ID: REQU.DMGR.TEST.2
  Name: Render the dashboard
  Text: |
    (U) The system shall render the dashboard.
  Verified_By: VREQU.DMGR.TEST.2
  Traced_To: TRACE.2

- Type: DMGR Verification Requirement
  Parent_Req: 
  ID: VREQU.DMGR.TEST.1
  Name: Verify the status is rendered
  Text: |
    (U) Verify the system renders the status.
  Verified_By: 
  Traced_To: TRACE.1

- Type: DMGR Verification Requirement
  Parent_Req: 
  ID: VREQU.DMGR.TEST.2
  Name: Verify the dashboard is rendered
  Text: |
    (U) Verify the system renders the dashboard.
  Verified_By: 
  Traced_To: TRACE.2
```

### test_hash_preservation_e2e.py

**NEW** - End-to-end integration tests for hash character preservation in Name and Text fields:

#### Standard Path Tests:
- **test_standard_name_with_hash_inline**: Name starting with "Render " containing #123
  - Validates transformation: "Render issue #123 indicator" → "Verify the issue #123 indicator is rendered"
- **test_standard_text_with_hash_pattern**: Text containing "shall render" with ###.###.###
  - Validates transformation: "shall render version ###.###.###" → "renders version ###.###.###"

#### Non-Standard Path Tests:
- **test_nonstandard_name_with_hash**: Name not starting with "Render " or "Set " containing #456
  - Validates "# FIX - Non-Standard Name" comment is present
  - Validates minimal transformation: "Display issue #456 indicator" → "Verify Display issue #456 indicator"
- **test_nonstandard_text_with_hash**: Text for DMGR domain without "shall render" containing ###.###
  - Validates "# FIX - Non-Standard Text" comment is present
  - Validates text preserved verbatim

#### Combined Tests:
- **test_combined_standard_with_multiple_hashes**: Multiple hash formats in standard transformations
  - Issue references: #1, #2, #3
  - Color codes: #FF0000, #00FF00
  - All preserved through transformations
- **test_combined_nonstandard_with_multiple_hashes**: Multiple hashes with FIX comments
  - Validates all hashes preserved even with non-standard warnings

#### Domain-Specific Tests:
- **test_brdg_domain_with_hash**: BRDG setting semantics with # characters
  - Standard: "Set timeout to #DEFAULT" → "Verify the timeout is set to #DEFAULT"
  - Non-standard: preserves # with FIX comment

#### Edge Cases:
- **test_hash_in_block_scalar_content**: Lines starting with # in block scalars
  - Validates "# Format: owner/repo#number" treated as content, not comment
  - Validates preservation through transformation

**Acceptance Criteria Validated:**
1. ✅ End-to-end run shows no truncation at # anywhere
2. ✅ Standard paths preserve # through transformations
3. ✅ Non-standard paths preserve # with FIX comments
4. ✅ Block scalar lines starting with # treated as content
5. ✅ Existing comment preservation unchanged

