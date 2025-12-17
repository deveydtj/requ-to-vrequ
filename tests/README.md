# Tests for generate_verification_yaml.py

This directory contains tests for the verification YAML generator.

## Running Tests

To run the test suite:

```bash
python3 tests/test_non_standard_flags.py
```

## Test Coverage

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

## Expected Behavior

When a Requirement has non-standard Name or Text:

1. A comment is inserted before the Verification: `# FIX - Non-Standard Name` or `# FIX - Non-Standard Text`
2. Non-standard fields receive minimal transformation:
   - Name: Just "Verify " prefix
   - Text: Verbatim copy
3. Standard fields receive full transformation as usual

When a BRDG Verification contains "render" (case-insensitive):
- A comment is inserted: `# FIX - BRDG must not render`

## Example

Input:
```yaml
- Type: Requirement
  ID: REQU.DMGR.TEST.1
  Name: Display the status
  Text: |
    (U) The system shall render the status.
```

Output:
```yaml
# FIX - Non-Standard Name

- Type: DMGR Verification Requirement
  Parent_Req:
  ID: VREQU.DMGR.TEST.1
  Name: Verify Display the status
  Text: |
    (U) Verify the system renders the status.
  Verified_By:
  Traced_To:
```
