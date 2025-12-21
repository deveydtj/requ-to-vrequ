#!/usr/bin/env python3
"""
Generate automated Verification entries from Requirement entries
in a simple YAML-like file, without third-party libraries.

This script is designed to satisfy the authoring rules described in the
"authoring requirements and guidelines" document, including:

- Recognizing Requirement items by ID (must start with "REQU")
- Setting Verification Type based on domain:
  * "DMGR Verification Requirement" for IDs containing ".DMGR."
  * "BRDG Verification Requirement" for IDs containing ".BRDG."
  * "Verification" for all other IDs
- Applying special wording rules for IDs containing ".BRDG." (Bridge) or
  ".DMGR." (Data Manager)
- Case-sensitive handling of the tokens "Set", "to", "The", and "shall set"
- Generating a Verification item with fields:
  Type, Parent_Req, ID, Name, Text, Verified_By, Traced_To (if present)
- Setting Parent_Req of the Verification to blank
- Copying Traced_To from the Requirement to the Verification (scalar only)
- Preserving multiline values using YAML block scalar syntax (Key: |)
- Capturing and re-emitting all comments in the original order, adjacent to
  the related item blocks.

SUPPORTED TOP-LEVEL ITEM FORMAT:
Top-level items must start with "- " (hyphen followed by space), optionally
preceded by leading whitespace. The script supports:
  - Leading whitespace before "- " (e.g., "  - Type: Requirement")
  - Variable spacing after the hyphen (e.g., "- Type:" or "-  Type:")
  - Inline key-value on the same line as "- " (e.g., "- Type: Requirement")
  - Any key can appear first (e.g., "- ID: REQU.1" or "- Type: Requirement")

The parser uses lstrip() to detect item starts via "- " prefix, making it
tolerant of leading whitespace and formatting variations. Patchers maintain
this same tolerance to ensure consistent behavior.

USAGE:
python generate_verification_yaml.py input.yaml output.yaml
python generate_verification_yaml.py --no-sequence input.yaml output.yaml
python generate_verification_yaml.py --sequence-log input.yaml output.yaml

FLAGS:
  --no-sequence    Disable ID sequencing (placeholder IDs like .X will remain unchanged)
  --sequence-log   Print a summary of ID renumbering operations to stdout
"""

import argparse
import re
import os
import tempfile
from typing import List, Dict, Optional, Tuple

# Base key order for output. Additional keys discovered in the file will be
# appended after these in alphabetical order.
BASE_KEY_ORDER = [
    "Type", "Parent_Req", "ID", "Name", "Text", "Verified_By", "Traced_To"
]

# Compiled regex pattern for BRDG render issue detection
# Matches "render", "renders", "rendered", "rendering" as whole words (case-insensitive)
BRDG_RENDER_PATTERN = re.compile(r"\brender(?:s|ed|ing)?\b", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Item Detection Helpers
# ---------------------------------------------------------------------------


def is_item_start(line: str) -> bool:
    """
    Check if a line represents the start of a top-level item.
    
    Consistent with parse_items(), this function detects item starts by:
    - Stripping leading whitespace with lstrip()
    - Checking if the result starts with "- "
    
    This makes the detection tolerant of:
    - Leading whitespace before the hyphen
    - Any key appearing first (Type, ID, Name, etc.)
    
    Args:
        line: The line to check (should not have trailing newline)
    
    Returns:
        True if the line starts a new item, False otherwise
    
    Examples:
        >>> is_item_start("- Type: Requirement")
        True
        >>> is_item_start("  - Type: Requirement")
        True
        >>> is_item_start("- ID: REQU.1")
        True
        >>> is_item_start("  ID: REQU.1")
        False
    """
    stripped = line.lstrip()
    return stripped.startswith("- ")


def parse_first_line_kv(line: str) -> Optional[Tuple[str, str]]:
    """
    Parse key-value pair from the first line of an item.
    
    Handles variable spacing after the hyphen and extracts the key and value
    from lines like "- Type: Requirement" or "-  ID: REQU.1".
    
    Args:
        line: A line that starts with "- " (after lstrip)
    
    Returns:
        (key, value) tuple if a key-value pair is found, None otherwise
    
    Examples:
        >>> parse_first_line_kv("- Type: Requirement")
        ('Type', 'Requirement')
        >>> parse_first_line_kv("  -  ID: REQU.1")
        ('ID', 'REQU.1')
        >>> parse_first_line_kv("- ")
        None
    """
    stripped = line.lstrip()
    if not stripped.startswith("- "):
        return None
    
    # Skip "- " and any additional whitespace
    rest = stripped[2:].lstrip()
    if not rest or ":" not in rest:
        return None
    
    key, value = rest.split(":", 1)
    return (key.strip(), value.strip())

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_items(path: str) -> List[Dict[str, str]]:
    """
    Very small YAML-like parser for the expected flat structure.

    Supports:
    - Top-level items beginning with '- '
    - Key: Value pairs
    - Multiline block scalars for any key: 'Key: |' or 'Key: |-'
      with indentation-based termination rules.
    - Captures any comment lines ('# ...') anywhere in the file:
      * Outside items: stored as standalone entries with '_comment'
      * Inside items (outside of block scalars): appended to the item's '_order'
        to preserve relative position among keys.

    Note: This is not a full YAML parser; it only supports what is needed
    for these requirement / verification records.
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    items: List[Dict[str, str]] = []
    current: Optional[Dict[str, str]] = None
    i = 0
    n = len(lines)

    while i < n:
        raw_line = lines[i].rstrip("\n")

        # Skip completely blank lines (preserved only within block scalars)
        if not raw_line.strip():
            i += 1
            continue

        stripped = raw_line.lstrip()

        # Standalone comment (outside any current item)
        if current is None and stripped.startswith("#"):
            items.append({"_comment": raw_line})
            i += 1
            continue

        # New item starts with "- "
        if stripped.startswith("- "):
            if current is not None:
                items.append(current)
            current = {"_order": []}
            rest = stripped[2:].strip()
            if rest and ":" in rest:
                key, value = rest.split(":", 1)
                key = key.strip()
                val = value.strip()
                current[key] = val
                current["_order"].append(("key", key))
            i += 1
            continue

        if current is None:
            # Lines before the first "- " that are not comments are ignored
            i += 1
            continue

        # Determine indentation and content after indentation
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        content = raw_line[indent:]

        # Handle "Key: ..." with optional block scalar indicator generically
        if ":" in content:
            key, value = content.split(":", 1)
            key = key.strip()
            after = value.lstrip()

            # Multiline block scalar (supports any key): "Key: |" or "Key: |-"
            if after in ("|", "|-"):
                block_lines: List[str] = []
                indent_base = indent
                i += 1
                while i < n:
                    nxt_raw = lines[i].rstrip("\n")
                    nxt_stripped = nxt_raw.strip()

                    # Preserve completely blank lines inside the block
                    if nxt_stripped == "":
                        block_lines.append("")
                        i += 1
                        continue

                    nxt_indent = len(nxt_raw) - len(nxt_raw.lstrip(" "))
                    nxt_content = nxt_raw[nxt_indent:]

                    # New item? Only if '- ' appears at the same or less indent
                    # as the key line (i.e., a top-level list item).
                    if nxt_indent <= indent_base and nxt_content.startswith("- "):
                        break

                    # New key at same or less indent (e.g., " Name: ...")
                    if nxt_indent <= indent_base and ":" in nxt_content:
                        break

                    # Otherwise this is part of the block content
                    block_indent = indent_base + 2
                    if nxt_indent >= block_indent:
                        block_lines.append(nxt_raw[block_indent:])
                    else:
                        block_lines.append(nxt_raw.lstrip())

                    i += 1

                current[key] = "\n".join(block_lines)
                current["_order"].append(("key", key))

                # Maintain existing behavior: mark only Text as coming from a block scalar
                if key == "Text":
                    current["_Text_block"] = True

                continue

            # Single-line value; split inline comments from the value
            # Detect an inline comment '#' anywhere in the raw line after the colon
            hash_idx_in_raw = raw_line.find("#")
            if hash_idx_in_raw != -1:
                # Compute where the value starts within the raw line
                colon_idx_in_raw = raw_line.find(":")
                # Value portion is the substring after the colon up to the hash
                value_part = raw_line[colon_idx_in_raw +
                    1:hash_idx_in_raw].strip()
                # preserve original indentation/content
                comment_part = raw_line[hash_idx_in_raw:]
                current[key] = value_part
                current["_order"].append(("key", key))
                current["_order"].append(("comment", comment_part))
            else:
                current[key] = after
                current["_order"].append(("key", key))

            if key == "Text":
                current["_Text_block"] = False

            i += 1
            continue

        # Comment line (outside of block scalars): capture and preserve in-item order
        if stripped.startswith("#"):
            current["_order"].append(("comment", raw_line))
            i += 1
            continue

        # If we get here, increment to avoid infinite loop
        i += 1

    if current is not None:
        items.append(current)

    return items

# ---------------------------------------------------------------------------
# Transformation helpers
# ---------------------------------------------------------------------------


def split_leading_classification(s: str) -> tuple[str, str]:
    """
    If the string begins with one or more parenthetical classification tags,
    return (prefix_with_space_preserved, remainder_without_leading_spaces),
    otherwise return ("", s).
    """
    m = re.match(r"^(\s*(?:\([^)]+\)\s*)+)(.*)$", s)
    if not m:
        return "", s
    prefix = m.group(1)
    remainder = m.group(2).lstrip()
    return prefix, remainder


def generate_verification_id(req_id: str) -> str:
    """
    Generate a Verification ID from a Requirement ID.

    Examples:
    REQU.DIS.UI.1 -> VREQU.DIS.UI.1
    REQU.DMGR.STATE.2.DMGR.MODE -> VREQU.DMGR.STATE.2.DMGR.MODE
    """
    return "V" + req_id.strip()


def has_standalone_set(name: str) -> bool:
    """
    Return True if the Name contains the standalone token 'Set'
    (case-sensitive, word boundary).
    """
    return re.search(r"\bSet\b", name) is not None


def is_plural_subject_phrase(phrase: str) -> bool:
    """
    Minimal plurality heuristic (purposefully lightweight, no NLP dependencies):
    - If the phrase includes a coordination ('and'/'or') or a comma list, treat as plural.
    - If it begins with a numeric count, treat >1 as plural.
    - Otherwise, pick a likely "head" token near the end of the phrase and decide plural
      based on simple morphology.

    Important: tokens inside quotes must NOT influence plurality detection.
    """
    if not phrase:
        return False

    def _strip_quoted(text: str) -> str:
        """Remove quoted substrings so quoted tokens don't affect plurality."""
        # Double-quoted segments (supports simple escaped quotes)
        text = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', " ", text)
        # Single-quoted segments (supports simple escaped quotes)
        text = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", " ", text)
        return text

    p = _strip_quoted(phrase.strip())
    p_low = p.lower()

    # Lists and coordination are strong signals of plurality
    if "," in p_low:
        return True
    if re.search(r"\b(and|or)\b", p_low):
        return True

    # Leading numeric count
    m_num = re.match(r"^(\d+)\b", p_low)
    if m_num:
        try:
            return int(m_num.group(1)) != 1
        except ValueError:
            pass

    tokens = re.findall(r"[a-z0-9']+", p_low)
    if not tokens:
        return False

    determiners = {"the", "a", "an", "this", "that"}
    idx = 0
    while idx < len(tokens) and tokens[idx] in determiners:
        idx += 1
    if idx >= len(tokens):
        return False

    # Choose a head-ish token from the end, skipping common trailing stopwords.
    stopwords = {
        # articles/determiners
        "the", "a", "an", "this", "that", "these", "those",
        # coordination
        "and", "or",
        # common prepositions/conjunctions
        "in", "on", "at", "to", "from", "with", "without", "by", "for", "of", "as",
        "into", "onto", "over", "under", "between", "within", "across", "through",
        # common trailing adverbs
        "here", "there",
    }

    head = None
    for t in reversed(tokens[idx:]):
        if t in stopwords:
            continue
        head = t
        break

    if not head:
        return False

    # Common singular nouns ending in 's' (avoid obvious false pluralization)
    singular_s_endings = {
        "status", "news", "chassis",
    }
    if head in singular_s_endings:
        return False

    # Simple morphological checks
    if head.endswith("ies"):          # e.g., "policies" -> plural
        return True
    if head.endswith("s") and not head.endswith("ss"):
        return True

    return False


def choose_be_verb(phrase: str) -> str:
    """Return 'are' if the phrase looks plural, otherwise 'is'."""
    return "are" if is_plural_subject_phrase(phrase) else "is"


def choose_present_verb(base_verb: str, phrase: str) -> str:
    """
    Return the correct present-tense verb form for the given phrase:
    - Singular subject => 'renders' / 'sets'
    - Plural subject   => 'render' / 'set'
    Works for 'render', 'set', and other regular verbs.
    """
    plural = is_plural_subject_phrase(phrase)
    if base_verb == "render":
        return "render" if plural else "renders"
    # Fallback: default singular adds 's'
    return base_verb if plural else (base_verb + "s")


def transform_name_general(req_name: str) -> str:
    """
      General behavior (non-setting semantics):

      - If the Name begins with 'Render ', convert to passive and prefix with 'Verify' or 'Verify the ':
        'Render X in Y' -> 'Verify the X in Y is rendered'
        If X already begins with 'the ' or 'The ', do not add an extra 'the'.
      - Otherwise: 'Verify <Name>'
      """
    if req_name.startswith("Render "):
        rest = req_name[len("Render "):].strip()
        # Avoid double 'the' if the rest already begins with an article
        if rest.startswith("the ") or rest.startswith("The "):
            subject_phrase = rest
            be = choose_be_verb(subject_phrase)
            return f"Verify {rest} {be} rendered"
        else:
            # Include a space so the determiner is tokenized correctly.
            subject_phrase = "the " + rest
            be = choose_be_verb(subject_phrase)
            return f"Verify the {rest} {be} rendered"
    return f"Verify {req_name}"


def transform_name_setting(req_name: str) -> str:
    """
    Setting semantics for Requirements whose Name contains 'Set' as a standalone word.

    Rules:
    - If the Name begins with 'Set ', remove that leading token.
    - Replace the last standalone 'to' with '<is/are> set to' depending on plurality.
    - If there is no standalone 'to', append '<is/are> set' at the end depending on plurality.
    - Prefix with 'Verify the ' unless the base already begins with 'The ' or 'the '.
    """
    base = req_name

    # Remove leading 'Set ' if present (case-sensitive)
    if base.startswith("Set "):
        base = base[len("Set "):]

    be = choose_be_verb(base)

    # Find the last standalone 'to' (case-sensitive, word boundary)
    matches = list(re.finditer(r"\bto\b", base))
    if matches:
        start, end = matches[-1].span()
        new_base = base[:start] + f"{be} set to" + base[end:]
    else:
        new_base = base + f" {be} set"

    # Prefix with 'Verify the ', unless the base already starts with 'The ' or 'the '
    prefix = "Verify the "
    if base.startswith("The ") or base.startswith("the "):
        prefix = "Verify "

    return (prefix + new_base.strip())


def extract_subject_phrase(line: str) -> str:
    """
    Extract the likely subject phrase from the first line by removing any leading
    classification tags '(...)', then removing a leading article ('The'/'the'),
    and taking everything up to the first modal/aux verb ('shall', 'is', 'are', 'will', 'must', 'should').
    """
    s = line.strip()
    # Strip leading classification tags
    _, s = split_leading_classification(s)

    # Remove leading 'The ' / 'the '
    if s.startswith("The "):
        s = s[4:]
    elif s.startswith("the "):
        s = s[4:]

    m = re.search(r"\b(shall|is|are|will|must|should)\b", s)
    return s[:m.start()].strip() if m else s


def normalize_verification_text(text: str) -> str:
    """
    Apply verification-specific text normalization.
    
    This function handles:
    1. Insert 'is rendered' between closing quote and ' in' pattern ('" in')
       to fix grammar for color specifications like: label "fruit" in white
       -> label "fruit" is rendered in white
    2. Avoids duplication by checking for 'is rendered' in the 15 characters
       before the opening quote for each '" in' occurrence. Only skips
       insertion if 'is rendered' appears in this window, indicating it is
       already part of the surrounding grammar structure rather than inside
       the quoted text itself.
    
    Args:
        text: The verification text to normalize
        
    Returns:
        Normalized text with patterns fixed
    """
    if not text:
        return text
    
    # Pattern: '" in' (double quote followed by space and the word 'in')
    # Process each occurrence independently to handle mixed content correctly
    # Strategy: Replace '" in' with '" is rendered in' only where not already present
    
    # Use a loop to process each occurrence, checking locally for duplication
    result = text
    search_pattern = '" in'
    replace_pattern = '" is rendered in'
    
    # Process from start to end, adjusting position after each replacement
    # to avoid index shifting issues
    pos = 0
    while True:
        pos = result.find(search_pattern, pos)
        if pos == -1:
            break
        
        # Find the matching opening quote for this closing quote
        # We search backwards from the closing quote position
        opening_quote_pos = -1
        for i in range(pos - 1, -1, -1):
            if result[i] == '"':
                opening_quote_pos = i
                break
        
        if opening_quote_pos == -1:
            # No opening quote found, skip this occurrence
            pos += len(search_pattern)
            continue
        
        # Check the context BEFORE the opening quote (not inside the quoted text)
        # to see if "is rendered" is already part of the grammar structure
        check_start = max(0, opening_quote_pos - 15)
        context_before_opening = result[check_start:opening_quote_pos]
        
        # Only treat "is rendered" as already present if it appears before
        # the opening quote (i.e., as part of the grammar structure)
        # If "is rendered" is inside the quoted text, we should still insert it
        if 'is rendered' not in context_before_opening:
            result = result[:pos] + replace_pattern + result[pos + len(search_pattern):]
            pos += len(replace_pattern)
        else:
            pos += len(search_pattern)
    
    return result


def transform_text(req_text: str, is_advanced: bool, is_setting: bool) -> str:
    """
    Transform Requirement Text into Verification Text.

    General rules:
    - If the first line begins with classification tags '(...)', keep them at the front,
      then insert 'Verify ' after them.
    - If the remainder begins with 'The ', rewrite as 'Verify the ...'.
      If it begins with 'Verify ', keep it.
      Otherwise, prefix with 'Verify '.
    - Plurality is determined from the remainder (ignoring classification prefix).

    Verb normalization (applied to the post-rewrite text for consistency):
    - Replace 'shall render' with 'render/renders' depending on subject plurality.
    - For advanced (.BRDG./.DMGR.) setting semantics, and when applicable,
      replace 'shall set' with 'set/sets' depending on subject plurality.
    
    All replacement checks and operations are performed on the rewritten text (after
    first-line normalization) to ensure consistency and avoid edge cases where
    first-line rewriting might change context.
    """
    if not req_text:
        return "Verify that the requirement is satisfied."

    lines = req_text.split("\n")
    first = lines[0]

    # Split out any leading classification prefix, and determine subject plurality from remainder
    class_prefix, remainder = split_leading_classification(first)
    subject_phrase = extract_subject_phrase(remainder)
    be = choose_be_verb(subject_phrase)
    render_present = choose_present_verb("render", subject_phrase)
    set_present = choose_present_verb("set", subject_phrase)

    # Build the rewritten first line
    # Normalize first-word article capitalization after 'Verify'
    if remainder.startswith("The "):
        new_remainder = "Verify the " + remainder[len("The "):]
    elif remainder.startswith("Verify "):
        new_remainder = remainder
    else:
        # Also handle 'the ' (already lowercase) gracefully
        if remainder.startswith("the "):
            new_remainder = "Verify " + remainder
        else:
            new_remainder = "Verify " + remainder

    if class_prefix:
        # Ensure exactly one space between the classification and the rewritten remainder
        lines[0] = class_prefix.rstrip() + " " + new_remainder
    else:
        lines[0] = new_remainder

    joined = "\n".join(lines)

    # Normalize 'shall render' -> 'render'/'renders' (active voice)
    # Check the post-rewrite text (joined) for consistency
    if "shall render" in joined:
        joined = joined.replace("shall render", render_present)

    # Advanced Bridge / DMGR + setting semantics
    if is_advanced and is_setting:
        # Handle 'shall set to' first to avoid 'to to' duplication
        # Check the post-rewrite text (joined) for consistency
        if "shall set to" in joined:
            joined = joined.replace("shall set to", f"{set_present} to")
        elif "shall set" in joined:
            joined = joined.replace("shall set", set_present)

    # Apply verification-specific normalization (e.g., '" in' pattern fix)
    joined = normalize_verification_text(joined)

    return joined


# ---------------------------------------------------------------------------
# ID Sequencing
# ---------------------------------------------------------------------------

def build_id_sequence_map(items: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Build a mapping from placeholder IDs (ending in .X or .x) to their sequenced replacements.
    
    Since multiple items can have the same placeholder ID, this function returns a mapping
    that includes a position suffix to differentiate them. The key format is:
    "ORIGINAL_ID@INDEX" where INDEX is the 0-based position of that item in the items list.
    
    Sequencing rules:
    - Only applies to Requirement items (IDs starting with "REQU")
    - Groups items by domain (DMGR, BRDG, OTHER) and stem (everything up to the last dot)
    - For each (domain, stem) group:
      * First numbered ID (ending in .<digit> or .<digit>+) becomes the anchor
      * Subsequent .X or .x IDs in that group are sequenced starting from anchor + 1
      * Already-numbered IDs are skipped (not renumbered)
      * Sequencing stops when an ID's stem diverges from the group stem
    - If no numbered anchor exists for a stem, .X/.x IDs are left unchanged
    
    Args:
        items: List of parsed item dictionaries
        
    Returns:
        Dictionary mapping "ORIGINAL_ID@INDEX" to their sequenced replacements
    """
    id_map: Dict[str, str] = {}
    
    # Track anchors and counters per (domain, stem)
    # Key: (domain, stem), Value: (anchor_number, next_sequence_number)
    domain_stem_state: Dict[Tuple[str, str], Tuple[int, int]] = {}
    
    for idx, item in enumerate(items):
        # Skip non-item entries like standalone comments
        if "_comment" in item and len(item) == 1:
            continue
            
        req_id = item.get("ID", "").strip()
        
        # Only process Requirement IDs
        if not is_requirement_id(req_id):
            continue
        
        # Classify domain
        domain = classify_domain(req_id)
        
        # Extract stem (everything up to the last dot)
        if "." not in req_id:
            continue
        
        last_dot_idx = req_id.rfind(".")
        stem = req_id[:last_dot_idx]
        suffix = req_id[last_dot_idx + 1:]
        
        key = (domain, stem)
        
        # Check if this is a numbered ID (anchor or already-numbered)
        if suffix.isdigit():
            # This is a numbered ID
            num = int(suffix)
            
            # If no anchor exists for this (domain, stem), this becomes the anchor
            if key not in domain_stem_state:
                domain_stem_state[key] = (num, num + 1)
            # If anchor exists but this is a different number, update next sequence if needed
            # Note: The anchor (first numbered ID) remains constant; only next_sequence_number updates
            elif num >= domain_stem_state[key][1]:
                anchor_num, _ = domain_stem_state[key]
                domain_stem_state[key] = (anchor_num, num + 1)
        
        # Check if this is a placeholder (.X or .x)
        elif suffix in ("X", "x"):
            # Only sequence if we have an anchor for this (domain, stem)
            if key in domain_stem_state:
                anchor_num, next_num = domain_stem_state[key]
                # Create the sequenced ID
                sequenced_id = f"{stem}.{next_num}"
                # Use item index to make the key unique
                map_key = f"{req_id}@{idx}"
                id_map[map_key] = sequenced_id
                # Update the next sequence number
                domain_stem_state[key] = (anchor_num, next_num + 1)
            # If no anchor, leave .X/.x unchanged (don't add to map)
    
    return id_map


def apply_id_sequence_patch(original_text: str, id_map: Dict[str, str]) -> str:
    """
    Replace placeholder IDs (.X/.x) in the original text with their sequenced values.
    
    This function preserves all formatting and comments while updating only the ID fields
    for Requirement items that have placeholder IDs.
    
    Note: Item indexing must match the order produced by parse_items(), which:
    - Creates a standalone comment item for comments appearing before the first "- " line
    - Does NOT create standalone items for comments appearing between structured items
      (those are stored in the item's _order field instead)
    
    Args:
        original_text: The original file content as a string
        id_map: Mapping from "ORIGINAL_ID@INDEX" to sequenced IDs
        
    Returns:
        Updated text with sequenced IDs
    """
    if not id_map:
        return original_text
    
    lines = original_text.splitlines()
    result: List[str] = []
    
    # Track which item we're in (by counting ALL items as parse_items() does)
    item_index = -1
    in_item = False
    # Track whether we've seen any structured item (starting with '- ')
    # to distinguish preamble comments (before first structured item) from
    # inter-item comments (which are stored in the previous item's _order)
    seen_structured_item = False
    
    for line in lines:
        # Detect start of new item (including standalone comments)
        stripped = line.lstrip()
        
        # Standalone comment before the first structured item
        # Note: Comments between structured items are NOT standalone items -
        # they're stored in the previous item's _order field by parse_items()
        # Each preamble comment line is treated as a separate item by parse_items()
        if not seen_structured_item and stripped.startswith("#"):
            item_index += 1
            result.append(line)
            continue
        
        # Start of a structured item - use is_item_start() for consistency
        if is_item_start(line):
            item_index += 1
            in_item = True
            seen_structured_item = True
            
            # Check if the first line contains an ID that needs sequencing
            # Format: "- ID: REQU.TEST.X" or "  - ID: REQU.TEST.X" or "-  ID: ..."
            kv = parse_first_line_kv(line)
            if kv and kv[0] == "ID":
                id_val = kv[1]
                map_key = f"{id_val}@{item_index}"
                if map_key in id_map:
                    new_id = id_map[map_key]
                    # Preserve all original spacing by finding and replacing only the ID value
                    id_pos = line.find("ID:")
                    if id_pos != -1:
                        # Portion after "ID:"
                        suffix = line[id_pos + 3:]
                        # Replace only the old ID value within the suffix
                        val_pos = suffix.find(id_val)
                        if val_pos != -1:
                            new_suffix = suffix[:val_pos] + new_id + suffix[val_pos + len(id_val):]
                            new_line = line[:id_pos + 3] + new_suffix
                            result.append(new_line)
                            continue
                    # Fallback: if structure is unexpected, use simple replacement
                    indent = line[:len(line) - len(line.lstrip())]
                    result.append(f"{indent}- ID: {new_id}")
                    continue
            
            result.append(line)
            continue
        
        # Check if this is an ID line within an item
        if in_item and stripped.startswith("ID:"):
            # Extract the ID value
            id_val = stripped[len("ID:"):].strip()
            
            # Build the map key with current item index
            map_key = f"{id_val}@{item_index}"
            
            # If this ID is in our mapping, replace it
            if map_key in id_map:
                # Preserve indentation
                indent = line[:len(line) - len(line.lstrip())]
                new_id = id_map[map_key]
                result.append(f"{indent}ID: {new_id}")
                continue
        
        # Not an ID line or not in map, keep as-is
        result.append(line)
    
    return "\n".join(result)


def sequence_requirement_ids(items: List[Dict[str, str]], id_map: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    """
    Apply ID sequencing to the structured items list.
    
    This creates a new list with updated IDs for items that have placeholder IDs.
    
    Args:
        items: List of parsed item dictionaries
        id_map: Optional pre-computed ID mapping. If None, will be computed.
        
    Returns:
        New list with sequenced IDs applied
    """
    # Build the ID mapping if not provided
    if id_map is None:
        id_map = build_id_sequence_map(items)
    
    if not id_map:
        return items
    
    # Create updated items list
    result: List[Dict[str, str]] = []
    
    for idx, item in enumerate(items):
        # Pass through comments unchanged
        if "_comment" in item and len(item) == 1:
            result.append(item)
            continue
        
        # Check if this item's ID needs sequencing
        req_id = item.get("ID", "").strip()
        map_key = f"{req_id}@{idx}"
        
        if map_key in id_map:
            # Create a shallow copy and update the ID
            # Shallow copy is safe here because we only modify the ID field,
            # and no other code will modify the _order list after this point
            updated_item = dict(item)
            updated_item["ID"] = id_map[map_key]
            result.append(updated_item)
        else:
            result.append(item)
    
    return result


# ---------------------------------------------------------------------------
# Verification generation
# ---------------------------------------------------------------------------

def is_requirement_id(req_id: str) -> bool:
    """
    Return True if the given ID represents a Requirement.
    
    A valid Requirement ID starts with "REQU" (case-sensitive).
    This includes IDs like "REQU.DMGR.TEST.1", "REQU.BRDG.X", or even "REQU".
    """
    req_id = req_id.strip()
    return req_id.startswith("REQU")


def classify_domain(req_id: str) -> str:
    """
    Classify the domain of a Requirement based on its ID.
    
    Returns:
    - "DMGR" if the ID contains ".DMGR."
    - "BRDG" if the ID contains ".BRDG."
    - "OTHER" otherwise
    """
    req_id = req_id.strip()
    if ".DMGR." in req_id:
        return "DMGR"
    elif ".BRDG." in req_id:
        return "BRDG"
    else:
        return "OTHER"


def is_standard_name(req_name: str) -> bool:
    """
    Check if a Requirement Name follows standard formatting.
    
    A standard Name starts with "Render " or "Set " (case-sensitive).
    
    Returns:
    - True if the Name starts with "Render " or "Set "
    - False otherwise
    """
    req_name = req_name.strip()
    return req_name.startswith("Render ") or req_name.startswith("Set ")


def is_standard_text(req_text: str, domain: str) -> bool:
    """
    Check if a Requirement Text follows domain-specific standard formatting.
    
    Domain-specific standards:
    - DMGR: Text should contain "shall render"
    - BRDG: Text should contain "shall set"
    - OTHER: No specific Text standard required, but text must be non-empty
    
    Empty text is always considered non-standard regardless of domain.
    
    Args:
        req_text: The Text field from the Requirement
        domain: The domain classification ("DMGR", "BRDG", or "OTHER")
    
    Returns:
        True if the Text meets the domain-specific standard, False otherwise
    """
    if not req_text:
        return False
    
    if domain == "DMGR":
        return "shall render" in req_text
    elif domain == "BRDG":
        return "shall set" in req_text
    else:
        # OTHER domain has no specific Text standard, but text must be non-empty
        return True


def has_brdg_render_issue(ver_name: str, ver_text: str) -> bool:
    """
    Detect if a BRDG Verification item incorrectly contains "render" terminology.
    
    BRDG items should use "set" semantics, not "render" semantics.
    This performs case-insensitive, word-boundary-aware detection.
    
    Args:
        ver_name: The Name field from the Verification item
        ver_text: The Text field from the Verification item
    
    Returns:
        True if a whole-word "render", "renders", "rendered", or "rendering"
        is found (case-insensitive), False otherwise.
    """
    name_to_check = ver_name or ""
    text_to_check = ver_text or ""
    return bool(BRDG_RENDER_PATTERN.search(name_to_check)) or bool(BRDG_RENDER_PATTERN.search(text_to_check))


def generate_verification_items(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    For each Requirement item that matches the scope rules, generate a
    corresponding Verification item and update the Requirement's Verified_By.

    Scope rules:
    - ID must start with 'REQU' (Type is no longer used for detection)

    Verification Type assignment:
    - If '.DMGR.' is in the ID, Type is set to "DMGR Verification Requirement"
    - If '.BRDG.' is in the ID, Type is set to "BRDG Verification Requirement"
    - Otherwise, Type is set to "Verification"

    Name & Text transformations follow the authoring guidelines:
    - Non-setting: 'Verify <Name>', and Text with 'Verify the' or 'Verify '.
    - Setting semantics: special wording for Name and 'shall set' -> 'sets' in Text
      when applicable.

    Parent_Req and Traced_To:
    - Verification.Parent_Req is left blank.
    - If Requirement.Traced_To is present, it is copied as-is to the
      Verification (scalar only in this script).
    """
    result: List[Dict[str, str]] = []
    ver_items: List[Dict[str, str]] = []

    for item in items:
        # Pass through standalone comments untouched
        if "_comment" in item and len(item) == 1:
            result.append(item)
            continue

        req_id = item.get("ID", "").strip()
        
        # Use ID-based detection: process only items with IDs starting with "REQU"
        if not is_requirement_id(req_id):
            result.append(item)
            continue

        req_name = item.get("Name", "")
        req_text = item.get("Text", "")

        # Classify the domain based on ID
        domain = classify_domain(req_id)
        is_brdg = (domain == "BRDG")
        is_dmgr = (domain == "DMGR")
        is_advanced = is_brdg or is_dmgr

        # Setting semantics if Name contains 'Set' as a standalone word
        is_setting = has_standalone_set(req_name)

        ver_id = generate_verification_id(req_id)

        # --- Update the Requirement itself (set Verified_By) ---
        updated_req = dict(item)  # shallow copy to preserve other fields
        updated_req["Verified_By"] = ver_id
        result.append(updated_req)

        # --- Create the Verification item ---
        ver_item: Dict[str, str] = {}

        # Set Type based on domain
        if domain == "DMGR":
            ver_item["Type"] = "DMGR Verification Requirement"
        elif domain == "BRDG":
            ver_item["Type"] = "BRDG Verification Requirement"
        else:
            ver_item["Type"] = "Verification"
        
        # Set Parent_Req to blank
        ver_item["Parent_Req"] = ""
        ver_item["ID"] = ver_id

        # --- Option B: Check for non-standard fields ---
        non_standard_fields = []
        
        # Check if Name is non-standard (doesn't start with "Render " or "Set ")
        name_is_standard = is_standard_name(req_name)
        if not name_is_standard:
            non_standard_fields.append("Name")
        
        # Check if Text is non-standard based on domain
        text_is_standard = is_standard_text(req_text, domain)
        if not text_is_standard:
            non_standard_fields.append("Text")
        
        # Add comment if there are any non-standard fields
        if non_standard_fields:
            comment_text = f"# FIX - Non-Standard {', '.join(non_standard_fields)}"
            ver_items.append({"_comment": comment_text})
        
        # Apply Name transformation based on whether Name is standard
        if not name_is_standard:
            # Option B: Minimal transformation for non-standard Name
            ver_item["Name"] = "Verify " + req_name.strip()
        else:
            # Standard Name: apply existing transformations
            if is_setting:
                ver_item["Name"] = transform_name_setting(req_name)
            else:
                ver_item["Name"] = transform_name_general(req_name)

        # Apply Text transformation based on whether Text is standard
        if not text_is_standard:
            # Option B: Minimal transformation for non-standard Text (copy verbatim)
            ver_item["Text"] = req_text
        else:
            # Standard Text: apply existing transformation
            ver_item["Text"] = transform_text(
                req_text,
                is_advanced=is_advanced,
                is_setting=is_setting,
            )

        # Verified_By starts empty for the Verification
        ver_item["Verified_By"] = ""

        # Copy Traced_To exactly if present (scalar-only support)
        if "Traced_To" in item:
            ver_item["Traced_To"] = item["Traced_To"]

        # Preserve the fact that Text was a block scalar so we can rewrite it
        if "_Text_block" in item:
            ver_item["_Text_block"] = item["_Text_block"]

        # --- Additional check: BRDG render issue ---
        if domain == "BRDG" and has_brdg_render_issue(ver_item["Name"], ver_item["Text"]):
            # Insert comment entry before this Verification item.
            # If there is an immediately preceding non-standard comment for this
            # verification (added at line 681), combine it into a single, prioritized comment.
            # Note: This is safe because nothing else is added to ver_items between
            # the non-standard comment insertion (line 681) and this check.
            combined_comment = "# FIX - BRDG must not render"
            if ver_items and isinstance(ver_items[-1], dict) and "_comment" in ver_items[-1]:
                last_comment = ver_items[-1].get("_comment", "")
                if last_comment.startswith("# FIX - Non-Standard"):
                    # Extract the non-standard fields from the previous comment
                    # Format: "# FIX - Non-Standard Name" or "# FIX - Non-Standard Name, Text"
                    non_standard_part = last_comment.replace("# FIX - Non-Standard ", "")
                    # Remove the prior non-standard comment and combine into one
                    ver_items.pop()
                    combined_comment = f"# FIX - BRDG must not render; Non-Standard {non_standard_part}"
            ver_items.append({"_comment": combined_comment})

        ver_items.append(ver_item)

    # Append all generated Verifications at the bottom
    result.extend(ver_items)
    return result

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def build_global_key_order(items: List[Dict[str, str]]) -> List[str]:
    """
    Build a global key order for output:

    - Start with BASE_KEY_ORDER
    - Append any additional keys found across all items (except
      internal keys starting with '_'), sorted alphabetically.
    """
    all_keys = set()
    for item in items:
        for key in item.keys():
            if not key.startswith("_"):
                all_keys.add(key)

    key_order: List[str] = BASE_KEY_ORDER.copy()
    extra_keys = sorted(k for k in all_keys if k not in key_order)
    key_order.extend(extra_keys)
    return key_order


def write_items(path: str, items: List[Dict[str, str]]) -> None:
    """
    Write items back out in the simple YAML-like format.

    Behavior:
    - A blank line is written between item blocks and before standalone comments
      (except at the start of the file).
    - Standalone comments appear directly adjacent to their following item with
      no blank line in between.
    - Keys that appear in the parsed order ('_order') are written in that exact order,
      interleaved with comments. Then any remaining keys are appended using the global key order.
    - For Verification items, all keys in the global key order are written (some may be blank).
    - For non-Verification items, only keys actually present are written.
    - If any key's value is multiline, it is written back out using 'Key: |'
      with the content indented by 2 spaces more than the key indentation.

    Indentation:
    - Keys under '- Type:' are indented by 2 spaces.
    - Multiline block lines are indented by 4 spaces (2 more than the key line).

    Comments:
    - Standalone comment entries (dicts with '_comment') are written as-is in place.
    - In-item comments recorded in '_order' are emitted in the same relative position.
    """
    key_order = build_global_key_order(items)

    def write_key_value(f, key: str, value: str) -> None:
        if isinstance(value, str) and "\n" in value:
            f.write(f"  {key}: |\n")
            for line in value.split("\n"):
                f.write(f"    {line}\n")
        else:
            f.write(f"  {key}: {value}\n")

    with open(path, "w", encoding="utf-8") as f:
        first_block = True
        prev_was_comment = False

        for item in items:
            # Standalone comment entry: write exactly as it appeared
            if "_comment" in item and len(item) == 1:
                if not first_block:
                    f.write("\n")
                first_block = False
                prev_was_comment = True
                f.write(f"{item['_comment']}\n")
                continue

            # Only add blank line if previous wasn't a standalone comment
            if not first_block and not prev_was_comment:
                f.write("\n")
            first_block = False
            prev_was_comment = False

            item_type = item.get("Type", "")
            is_verification = item_type in {
                "Verification",
                "DMGR Verification Requirement",
                "BRDG Verification Requirement"
            }

            # Top-level item marker
            f.write(f"- Type: {item_type}\n")

            # Emit keys/comments in the parsed order if available
            emitted_keys = set()
            order = item.get("_order", [])

            if order:
                for kind, payload in order:
                    if kind == "comment":
                        # Write the comment line as-is to preserve formatting
                        f.write(f"{payload}\n")
                    elif kind == "key":
                        key = payload
                        if key == "Type" or key.startswith("_"):
                            continue
                        if key not in item:
                            continue
                        write_key_value(f, key, item.get(key, ""))
                        emitted_keys.add(key)

            # Emit remaining keys
            for key in key_order:
                if key == "Type" or key.startswith("_"):
                    continue
                # For non-Verification items, only write keys that actually exist
                if not is_verification and key not in item:
                    continue
                if key in emitted_keys:
                    continue
                write_key_value(f, key, item.get(key, ""))


def render_items_to_string(items: List[Dict[str, str]]) -> str:
    """Render a list of items to the YAML-like text format used by this script.

    This helper uses write_items() on a temporary file and returns its contents
    so that the caller can append the rendered items to an existing file
    without re-emitting the original requirements section.
    
    Returns:
        A string with trailing newlines removed to avoid double blank lines
        when appending to an existing file.
    """
    if not items:
        return ""
    tmp_path: Optional[str] = None
    try:
        tmp = tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8")
        tmp_path = tmp.name
        tmp.close()
        write_items(tmp_path, items)
        with open(tmp_path, "r", encoding="utf-8") as f:
            return f.read().rstrip("\n")
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                # Best-effort cleanup; ignore failure
                pass


def apply_verified_by_patch(original_text: str, req_verified_map: Dict[str, str]) -> str:
    """
    Update the Verified_By field for in-scope Requirement items directly in the
    original text, with minimal disturbance to formatting and comments.

    We:
    - Detect top-level items using is_item_start() for consistency with the parser
    - Track the Requirement ID for items whose ID starts with "REQU".
    - For those, either replace an existing "Verified_By:" line or insert a new
      one near the other key/value lines.

    This avoids re-writing the whole file via write_items(), which can move
    comments, while still guaranteeing that each Requirement has an up-to-date
    Verified_By value.
    """
    if not req_verified_map:
        return original_text

    lines = original_text.splitlines()
    result: List[str] = []

    in_item = False
    item_lines: List[str] = []
    current_type: Optional[str] = None
    current_req_id: Optional[str] = None

    def flush_item():
        nonlocal item_lines, current_type, current_req_id, in_item
        if not in_item:
            return
        # Only patch items whose ID starts with REQU and are in the mapping
        if (
            current_req_id
            and is_requirement_id(current_req_id)
            and current_req_id in req_verified_map
        ):
            ver_id = req_verified_map[current_req_id]

            # --- Patch this block's Verified_By line(s) ---
            patched: List[str] = []
            has_verified_by = False

            # Some heuristics for where to insert if missing
            last_key_index = -1
            name_key_index = -1

            # First pass: we just scan and patch/remember positions
            for idx, line in enumerate(item_lines):
                stripped = line.lstrip()

                # Top-level "- Key: ..." line is always kept as-is
                if idx == 0:
                    patched.append(line)
                    continue

                # Existing Verified_By: line -> replace value
                m_ver = re.match(r"^(\s*)Verified_By\s*:", line)
                if m_ver:
                    indent = m_ver.group(1)
                    patched.append(f"{indent}Verified_By: {ver_id}")
                    has_verified_by = True
                    continue

                # Track positions of other keys for insertion ordering
                # We only look at simple "Key: value" patterns at this level.
                m_key = re.match(r"^(\s*)([A-Za-z0-9_]+)\s*:", line)
                if m_key:
                    key_name = m_key.group(2)
                    # Always track the last key we see (even if it's a block scalar start)
                    last_key_index = len(patched)
                    if key_name == "Name":
                        name_key_index = len(patched)

                patched.append(line)

            if not has_verified_by:
                # Compute indentation: prefer Name's indent, then last key's, then a default
                indent = "  "
                if name_key_index != -1:
                    m = re.match(r"^(\s*)", patched[name_key_index])
                    if m:
                        indent = m.group(1) or indent
                elif last_key_index != -1:
                    m = re.match(r"^(\s*)", patched[last_key_index])
                    if m:
                        indent = m.group(1) or indent

                insert_line = f"{indent}Verified_By: {ver_id}"

                # Insert at the end of the item to avoid breaking multiline blocks
                if last_key_index != -1:
                    patched.append(insert_line)
                else:
                    # No keys found, insert after '- ...:' line
                    patched.insert(1, insert_line)

            result.extend(patched)
        else:
            # Not a Requirement in scope; just copy block as-is
            result.extend(item_lines)

        # Reset state
        in_item = False
        item_lines = []
        current_type = None
        current_req_id = None

    for line in lines:
        # Detect top-level item start using is_item_start() for consistency
        if is_item_start(line):
            # Flush previous block if any
            if in_item:
                flush_item()
            in_item = True
            item_lines = [line]
            # Try to parse Type or ID if they appear on the first line
            # Format can be "- Type: FOO" or "-  ID: BAR" etc.
            current_type = None
            current_req_id = None
            kv = parse_first_line_kv(line)
            if kv:
                if kv[0] == "Type":
                    current_type = kv[1]
                elif kv[0] == "ID":
                    current_req_id = kv[1]
            continue

        if in_item:
            item_lines.append(line)
            stripped = line.lstrip()
            # Look for the ID line (e.g., "  ID: REQU.DIS.UI...")
            if stripped.startswith("ID:"):
                req_id_val = stripped[len("ID:"):].strip()
                current_req_id = req_id_val
            # Also look for Type if not found on first line
            if current_type is None and stripped.startswith("Type:"):
                current_type = stripped[len("Type:"):].strip()
            continue

        # Not inside an item; passthrough
        result.append(line)

    # Flush the last item if file ended while inside it
    if in_item:
        flush_item()

    return "\n".join(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Verification entries from Requirement entries in a YAML-like file."
    )
    parser.add_argument(
        "input_file", help="Path to input YAML-like requirements file.")
    parser.add_argument("output_file", help="Path to output YAML-like file.")
    parser.add_argument(
        "--no-sequence",
        action="store_true",
        help="Disable ID sequencing (placeholder IDs like .X will remain unchanged)"
    )
    parser.add_argument(
        "--sequence-log",
        action="store_true",
        help="Print a summary of ID renumbering operations to stdout"
    )
    args = parser.parse_args()

    # 1) Parse the input file for structured items (Requirements + any existing
    #    Verification items).
    items = parse_items(args.input_file)

    # 2) Conditionally apply ID sequencing based on --no-sequence flag
    if args.no_sequence:
        # Skip sequencing: use original items as-is
        id_map = {}
        sequenced_items = items
    else:
        # Compute ID sequence mapping for placeholder IDs (.X/.x)
        id_map = build_id_sequence_map(items)
        
        # Log sequencing operations if requested
        if args.sequence_log and id_map:
            print("ID Sequencing Summary:")
            print("=" * 60)
            for map_key, new_id in sorted(id_map.items()):
                # Extract original ID from map_key format "ORIGINAL_ID@INDEX"
                # The @INDEX suffix is added by build_id_sequence_map() to ensure
                # uniqueness when multiple items have the same placeholder ID.
                # Use rsplit to strip the synthetic @INDEX suffix (valid IDs do not contain '@').
                old_id = map_key.rsplit("@", 1)[0]
                print(f"  {old_id} -> {new_id}")
            print("=" * 60)
        
        # Apply sequencing to structured items (for verification generation)
        # Pass id_map to avoid rebuilding it
        sequenced_items = sequence_requirement_ids(items, id_map)

    # 3) Read original text (needed for both sequenced and non-sequenced paths)
    with open(args.input_file, "r", encoding="utf-8") as f:
        original_text = f.read()
    
    # 4) Apply ID sequencing patch to original text (only if sequencing is enabled)
    if args.no_sequence:
        sequenced_text = original_text
    else:
        sequenced_text = apply_id_sequence_patch(original_text, id_map)

    # 5) Generate verification items from the sequenced (or original) items
    items_with_verifications = generate_verification_items(sequenced_items)

    # 6) Build a map of Requirement ID -> Verified_By (Verification ID)
    #    Using the sequenced (updated) IDs
    req_verified_map: Dict[str, str] = {}
    for item in items_with_verifications:
        req_id = item.get("ID", "").strip()
        # Use ID-based detection instead of Type
        if not is_requirement_id(req_id):
            continue
        ver_id = item.get("Verified_By", "").strip()
        if ver_id:
            req_verified_map[req_id] = ver_id

    # Collect IDs of any existing Verification items so we don't duplicate them
    # if the script is run multiple times.
    # Check against the original (pre-sequencing) items to see what was already there
    existing_ver_ids = {
        item.get("ID", "").strip()
        for item in items
        if item.get("Type", "").strip() in {
            "Verification",
            "DMGR Verification Requirement",
            "BRDG Verification Requirement"
        }
    }

    # Filter out only the *new* Verification items that were created by
    # generate_verification_items (i.e., those whose ID does not already
    # exist in the original file).
    # Also include comment entries that immediately precede new verifications.
    new_ver_items: List[Dict[str, str]] = []
    pending_comments: List[Dict[str, str]] = []
    
    for item in items_with_verifications:
        # Standalone comment entry - hold it temporarily
        if "_comment" in item and len(item) == 1:
            pending_comments.append(item)
            continue
        
        item_type = item.get("Type", "").strip()
        # If this is a verification item
        if item_type in {
            "Verification",
            "DMGR Verification Requirement",
            "BRDG Verification Requirement"
        }:
            ver_id = item.get("ID", "").strip()
            # If it's a new verification, include any pending comments and the item
            if ver_id and ver_id not in existing_ver_ids:
                new_ver_items.extend(pending_comments)
                new_ver_items.append(item)
            # Clear pending comments either way
            pending_comments = []
        else:
            # Not a verification, so clear pending comments (they were for requirements)
            pending_comments = []

    # 7) Apply Verified_By patch to the sequenced text (using updated IDs from sequencing)
    updated_text = apply_verified_by_patch(sequenced_text, req_verified_map)

    # 8) If there are no new Verification items to add, we're done after updating
    #    the Verified_By fields in-place.
    if not new_ver_items:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(updated_text)
        return

    # Otherwise, render only the new Verification items and append them.
    extra_text = render_items_to_string(new_ver_items)

    with open(args.output_file, "w", encoding="utf-8") as f:
        # Preserve the original content (with updated IDs and Verified_By) exactly,
        # then add a blank line and the new Verification section.
        f.write(updated_text.rstrip("\n"))
        f.write("\n\n")
        f.write(extra_text)
        f.write("\n")


if __name__ == "__main__":
    main()
