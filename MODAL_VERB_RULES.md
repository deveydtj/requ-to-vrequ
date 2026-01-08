# Modal Verb Normalization - Migration Guide

## Overview

The modal verb normalization system has been refactored to use a centralized rule table (`MODAL_VERB_RULES`). This makes it easy to add new modal verb transformations without modifying core logic.

## Adding a New Modal Verb

To add a new modal verb normalization (e.g., "shall display"):

### 1. Add an entry to MODAL_VERB_RULES

Location: `generate_verification_yaml.py`, after line 80 (in the MODAL_VERB_RULES list)

```python
{
    "trigger": "shall display",           # The phrase to detect and replace
    "base_verb": "display",               # Base form for conjugation (display/displays)
    "domains": {"DMGR"},                  # Which domains use this transformation
    "priority": 0,                        # Higher = processed first (use 10+ for overlapping patterns)
    "requires_setting": False,            # If True, only applies when Name contains "Set"
    "standardness_domains": {"DMGR"},     # Which domains consider this "standard text"
}
```

### 2. Add tests

Create tests in a new file or add to `tests/test_modal_verb_rule_table.py`:

```python
def test_shall_display_transformation():
    """Test that 'shall display' transforms to 'displays' or 'display'."""
    # Singular subject
    req_text = "(U) The system shall display the indicator."
    result = transform_text(req_text, is_advanced=True, is_setting=False, is_dmgr=True)
    assert "displays the indicator" in result
    
    # Plural subject
    req_text_plural = "(U) The systems shall display the indicators."
    result_plural = transform_text(req_text_plural, is_advanced=True, is_setting=False, is_dmgr=True)
    assert "display the indicators" in result_plural
```

### 3. Run tests

```bash
python tests/test_modal_verb_rule_table.py
```

That's it! No changes to `is_standard_text()` or `transform_text()` needed.

## Rule Table Fields

### Required Fields

- **trigger** (str): The modal verb phrase to detect (e.g., "shall render", "shall set to")
- **base_verb** (str): Base form of the verb for conjugation (e.g., "render", "set")
- **domains** (set): Domains where this transformation applies: {"DMGR", "BRDG", "OTHER"}
- **priority** (int): Processing priority (higher = earlier). Use 10+ for overlapping patterns like "shall set to"
- **requires_setting** (bool): If True, only applies when Name contains standalone "Set"

### Optional Fields

- **standardness_domains** (set): Domains where this triggers "standard text" detection. If omitted, uses `domains` value.

## Examples

### Basic Modal Verb (All Domains)

"shall render" applies to all domains for transformation but only DMGR and OTHER consider it standard:

```python
{
    "trigger": "shall render",
    "base_verb": "render",
    "domains": {"DMGR", "BRDG", "OTHER"},
    "priority": 0,
    "requires_setting": False,
    "standardness_domains": {"DMGR", "OTHER"},  # BRDG does not consider this standard
}
```

### Domain-Specific Modal Verb

"shall overlay" transforms in all domains but only DMGR considers it standard:

```python
{
    "trigger": "shall overlay",
    "base_verb": "overlay",
    "domains": {"DMGR", "BRDG", "OTHER"},
    "priority": 0,
    "requires_setting": False,
    "standardness_domains": {"DMGR"},  # Only DMGR
}
```

### High-Priority Pattern

"shall set to" must be processed before "shall set" to avoid "to to" duplication:

```python
{
    "trigger": "shall set to",
    "base_verb": "set",
    "domains": {"DMGR"},
    "priority": 10,  # Higher priority than "shall set" (priority 0)
    "requires_setting": False,
    "standardness_domains": {"DMGR"},
}
```

### Conditional Transformation (BRDG Setting Semantics)

"shall set" for BRDG only applies when Name contains "Set":

```python
{
    "trigger": "shall set",
    "base_verb": "set",
    "domains": {"BRDG"},
    "priority": 0,
    "requires_setting": True,  # Only when Name has "Set"
    "standardness_domains": {"BRDG"},
}
```

## How It Works

### Transformation (`transform_text()`)

1. Determines domain (DMGR, BRDG, or OTHER) from function parameters
2. Sorts rules by priority (descending) and trigger length (descending)
3. For each applicable rule:
   - Checks if domain matches
   - Checks if `requires_setting` condition is met
   - Conjugates `base_verb` based on subject plurality
   - Replaces `trigger` with conjugated form

### Standardness Detection (`is_standard_text()`)

1. Returns True for OTHER domain (any non-empty text is standard)
2. Checks if text contains any trigger phrase where domain is in `standardness_domains`
3. Returns True if any match found

## Priority and Ordering

Rules are processed in order of:
1. **Priority** (descending): Higher numbers first
2. **Trigger length** (descending): Longer phrases first

This ensures overlapping patterns are handled correctly:
- "shall set to" (priority 10) processes before "shall set" (priority 0)
- Prevents "shall set to" → "sets to" → "sets to to" bug

## Testing

The test suite includes:
- `test_modal_verb_rule_table.py`: Validates rule table structure, priority, and transformations
- `test_shall_overlay_normalization.py`: Tests overlay-specific behavior
- `test_dmgr_shall_set_standard.py`: Tests DMGR set behavior
- Other domain-specific tests

Run all tests:
```bash
# Individual test
python tests/test_modal_verb_rule_table.py

# All tests (requires pytest)
pytest tests/
```

## Migration from Old Implementation

The old implementation had hardcoded checks in `is_standard_text()` and `transform_text()`:

```python
# OLD: Hardcoded in is_standard_text()
if domain == "DMGR":
    return "shall render" in req_text or "shall set" in req_text or "shall overlay" in req_text

# OLD: Hardcoded in transform_text()
if "shall render" in joined:
    joined = joined.replace("shall render", render_present)
if "shall overlay" in joined:
    joined = joined.replace("shall overlay", overlay_present)
# ... etc
```

The new implementation uses the rule table for both:

```python
# NEW: Rule table drives everything
for rule in MODAL_VERB_RULES:
    if domain in rule["domains"] and rule["trigger"] in req_text:
        return True  # is_standard_text
        
for rule in sorted_rules:
    if domain in rule["domains"] and rule["trigger"] in joined:
        joined = joined.replace(rule["trigger"], conjugated)  # transform_text
```

## Benefits

1. **Single source of truth**: All modal verb rules in one place
2. **Easy to extend**: Add new verbs by editing the rule table only
3. **Clear priority handling**: Explicit priority field prevents ordering bugs
4. **Separation of concerns**: Standardness vs. transformation can differ per domain
5. **Self-documenting**: Rule table shows all supported verbs at a glance
6. **Testable**: Rule table structure is easily validated

## Future Enhancements

Possible improvements:
- Regular expression support for triggers (e.g., "shall (render|display)")
- Per-rule conjugation overrides (for irregular verbs)
- Rule composition/inheritance (base rules + domain overrides)
- Runtime rule validation on startup
