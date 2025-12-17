# Copilot Instructions for requ-to-vrequ

## Project Overview

This repository contains a Python utility that automatically generates Verification entries from Requirement entries in YAML-like files. The tool is designed for requirements engineering workflows where each Requirement needs a corresponding Verification item to confirm compliance.

**Purpose:** Transform Requirement items (identified by IDs starting with "REQU") into Verification items (IDs starting with "VREQU") with specific naming and text transformations based on domain-specific rules.

## Tech Stack

- **Language:** Python 3
- **Dependencies:** None (uses only Python standard library)
- **File Format:** Custom YAML-like format (not full YAML, simplified parser)

## Repository Structure

```
.
├── generate_verification_yaml.py  # Main script for requirement-to-verification transformation
├── README.MD                       # Basic repository description
└── .gitignore                      # Python-standard gitignore
```

## How to Use

### Running the Script

```bash
python generate_verification_yaml.py input.yaml output.yaml
```

- **input.yaml:** Path to the input file containing Requirement items
- **output.yaml:** Path where the output file with updated Requirements and new Verifications will be written

### Script Behavior

The script:
1. Parses a YAML-like file containing Requirement items
2. Identifies Requirements by IDs starting with "REQU"
3. Generates corresponding Verification items with IDs starting with "VREQU"
4. Updates the original Requirements with `Verified_By` fields
5. Appends new Verification items to the output file
6. Preserves all comments and formatting from the input file

## Domain-Specific Rules

### Requirement Classification

Requirements are classified by their ID patterns:
- **DMGR (Data Manager):** IDs containing `.DMGR.` → Type: "DMGR Verification Requirement"
- **BRDG (Bridge):** IDs containing `.BRDG.` → Type: "BRDG Verification Requirement"
- **Other:** All other REQU IDs → Type: "Verification"

### Transformation Rules

**Name Transformations:**
- **Non-setting semantics:** Prefix with "Verify"
  - Special case for "Render X": Converts to "Verify the X is/are rendered." when X doesn't start with "the"/"The", or "Verify X is/are rendered." when it does (avoids double article)
- **Setting semantics** (when Name contains standalone word "Set"):
  - Remove leading "Set " if present
  - Replace last standalone "to" with "is/are set to" (plurality-aware)
  - Prefix with "Verify the " (unless already starts with "The")

**Text Transformations:**
- Prefix with "Verify " or "Verify the " based on original text
- Replace "shall render" with "render/renders" (plurality-aware)
- For DMGR/BRDG + setting semantics: Replace "shall set" with "is/are set" (plurality-aware)
- Preserve classification tags like "(U)" at the beginning

## Coding Guidelines

### Code Style

- Follow standard Python conventions (PEP 8)
- Use type hints for function signatures
- Document complex functions with docstrings
- Use descriptive variable names

### Key Implementation Details

1. **Parser:** Custom YAML-like parser (`parse_items()`) that supports:
   - Top-level items starting with `- `
   - Key-value pairs
   - Multiline block scalars with `Key: |` syntax
   - Comment preservation

2. **Plurality Detection:** Uses `is_plural_subject_phrase()` to determine singular/plural for verb conjugation
   - Checks for coordinations ("and"/"or")
   - Detects comma-separated lists
   - Ignores quoted text
   - Uses morphological heuristics

3. **ID Detection:** Requirements are identified by IDs starting with "REQU" (case-sensitive), including "REQU" itself or "REQU." prefixes

4. **Formatting Preservation:** 
   - Uses `apply_verified_by_patch()` to update existing Requirements in-place
   - Uses `render_items_to_string()` to append only new Verification items
   - Preserves all comments and blank lines from original file

### Testing

Currently, there are no automated tests in this repository. When adding tests:
- Create a `tests/` directory
- Use Python's `unittest` or `pytest` framework
- Test both transformation logic and file I/O operations
- Include test fixtures with sample YAML-like input files

### Adding New Features

When extending the script:
1. Maintain backward compatibility with existing YAML-like format
2. Preserve the comment-preservation behavior
3. Ensure plurality detection remains accurate
4. Update docstrings to reflect new behavior
5. Consider edge cases (empty values, special characters, nested structures)

## Important Notes

- The parser is **not** a full YAML parser—it only supports the specific flat structure needed for requirements/verification records
- All transformations are case-sensitive for keywords like "Set", "to", "The"
- The script can be run multiple times on the same file; it will only append new Verification items and update Verified_By fields
- Classification tags in parentheses (e.g., "(U)") are preserved at the beginning of Text fields

## Common Patterns

### Requirement Item Structure
```yaml
- Type: Requirement
  Parent_Req: PARENT.ID
  ID: REQU.DOMAIN.FEATURE.1
  Name: Requirement name
  Text: |
    (Classification) The system shall do something.
  Verified_By: 
  Traced_To: TRACE.ID
```

### Generated Verification Structure
```yaml
- Type: Verification
  Parent_Req: 
  ID: VREQU.DOMAIN.FEATURE.1
  Name: Verify the requirement name
  Text: |
    (Classification) Verify the system does something.
  Verified_By: 
  Traced_To: TRACE.ID
```

## References

- The script header references authoring requirements and guidelines that define the transformation rules
- See `generate_verification_yaml.py` docstring for detailed transformation rules and examples
