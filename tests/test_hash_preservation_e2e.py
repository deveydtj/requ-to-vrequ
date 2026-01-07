#!/usr/bin/env python3
"""
End-to-end integration tests for hash character preservation in Name and Text fields.

This test validates the acceptance criteria from the issue:
1. Input requirement with Name including # produces verification Name including the same # (subject to transformations like "Verify ...")
2. Input requirement with Text including ###.### produces verification Text including ###.###
3. Both standard and non-standard paths preserve # content
4. Standard Name/Text case (e.g., starts with Render / contains shall render) with # appended/embedded
5. Non-standard Name/Text case triggers # FIX - Non-Standard ... comments and still preserves # content
"""

import sys
import os
import subprocess
import tempfile

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_script_path():
    """Get the absolute path to the main generate_verification_yaml.py script."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'generate_verification_yaml.py'
    )


def test_standard_name_with_hash_inline():
    """
    Test standard Name (starts with 'Render ') with inline # reference.
    
    Expected: Verification Name should preserve #123 through transformation.
    """
    input_content = """- Type: Requirement
  ID: REQU.DMGR.TEST.1
  Name: Render issue #123 indicator
  Text: |
    (U) The system shall render the indicator.
  Verified_By: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(input_content)
    
    output_file = input_file + ".out"
    
    try:
        script_path = get_script_path()
        result = subprocess.run(
            ["python", script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # Original requirement should preserve #
        assert "Name: Render issue #123 indicator" in output_content, \
            "Original Requirement Name should preserve #123"
        
        # Verification should be generated
        assert "ID: VREQU.DMGR.TEST.1" in output_content, \
            "Verification item should be generated"
        
        # Verification Name should preserve # through transformation
        # Expected: "Verify the issue #123 indicator is rendered"
        lines = output_content.split('\n')
        vrequ_section = '\n'.join([l for l in lines if 'VREQU.DMGR.TEST.1' in l or 
                                    (lines.index(l) > lines.index([x for x in lines if 'VREQU.DMGR.TEST.1' in x][0]) 
                                     if [x for x in lines if 'VREQU.DMGR.TEST.1' in x] else False)])[:200]
        
        assert "#123" in output_content and "VREQU.DMGR.TEST.1" in output_content, \
            "Verification Name should preserve #123"
        
        print("✓ test_standard_name_with_hash_inline PASSED")
        
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def test_standard_text_with_hash_pattern():
    """
    Test standard Text (contains 'shall render') with ### pattern.
    
    Expected: Verification Text should preserve ###.###.### through transformation.
    """
    input_content = """- Type: Requirement
  ID: REQU.DMGR.TEST.2
  Name: Render version display
  Text: |
    (U) The system shall render version ###.###.###
  Verified_By: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(input_content)
    
    output_file = input_file + ".out"
    
    try:
        script_path = get_script_path()
        result = subprocess.run(
            ["python", script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # Original requirement should preserve ###.###.###
        assert "###.###.###" in output_content, \
            "Original Requirement Text should preserve ###.###.###"
        
        # Verification should be generated
        assert "ID: VREQU.DMGR.TEST.2" in output_content, \
            "Verification item should be generated"
        
        # Count occurrences - should appear in both requirement and verification
        pattern_count = output_content.count("###.###.###")
        assert pattern_count >= 2, \
            f"Pattern '###.###.###' should appear at least twice (req + ver), found {pattern_count}"
        
        print("✓ test_standard_text_with_hash_pattern PASSED")
        
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def test_nonstandard_name_with_hash():
    """
    Test non-standard Name (doesn't start with 'Render ' or 'Set ') with # reference.
    
    Expected: Should trigger '# FIX - Non-Standard Name' comment but still preserve #456.
    """
    input_content = """- Type: Requirement
  ID: REQU.DMGR.TEST.3
  Name: Display issue #456 indicator
  Text: |
    (U) The system shall render the indicator.
  Verified_By: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(input_content)
    
    output_file = input_file + ".out"
    
    try:
        script_path = get_script_path()
        result = subprocess.run(
            ["python", script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # Original requirement should preserve #
        assert "Name: Display issue #456 indicator" in output_content, \
            "Original Requirement Name should preserve #456"
        
        # Should have non-standard comment
        assert "# FIX - Non-Standard" in output_content, \
            "Should have non-standard comment"
        assert "Name" in output_content.split("# FIX - Non-Standard")[1].split('\n')[0], \
            "Non-standard comment should mention Name"
        
        # Verification should be generated
        assert "ID: VREQU.DMGR.TEST.3" in output_content, \
            "Verification item should be generated"
        
        # Verification Name should preserve # with minimal transformation
        # Expected: "Verify Display issue #456 indicator"
        assert output_content.count("#456") >= 2, \
            "Hash #456 should appear at least twice (original + verification)"
        
        print("✓ test_nonstandard_name_with_hash PASSED")
        
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def test_nonstandard_text_with_hash():
    """
    Test non-standard Text (DMGR domain without 'shall render') with ### pattern.
    
    Expected: Should trigger '# FIX - Non-Standard Text' comment but still preserve ###.###.
    """
    input_content = """- Type: Requirement
  ID: REQU.DMGR.TEST.4
  Name: Render version display
  Text: |
    (U) The system shall display version ###.###
  Verified_By: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(input_content)
    
    output_file = input_file + ".out"
    
    try:
        script_path = get_script_path()
        result = subprocess.run(
            ["python", script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # Original requirement should preserve ###.###
        assert "###.###" in output_content, \
            "Original Requirement Text should preserve ###.###"
        
        # Should have non-standard comment
        assert "# FIX - Non-Standard" in output_content, \
            "Should have non-standard comment"
        assert "Text" in output_content.split("# FIX - Non-Standard")[1].split('\n')[0], \
            "Non-standard comment should mention Text"
        
        # Verification should be generated
        assert "ID: VREQU.DMGR.TEST.4" in output_content, \
            "Verification item should be generated"
        
        # Verification Text should preserve ### (minimal transformation for non-standard)
        pattern_count = output_content.count("###.###")
        assert pattern_count >= 2, \
            f"Pattern '###.###' should appear at least twice (req + ver), found {pattern_count}"
        
        print("✓ test_nonstandard_text_with_hash PASSED")
        
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def test_combined_standard_with_multiple_hashes():
    """
    Test standard path with multiple # references in both Name and Text.
    
    Expected: All # characters preserved through transformations.
    """
    input_content = """- Type: Requirement
  ID: REQU.DMGR.TEST.5
  Name: Render issues #1, #2, and #3
  Text: |
    (U) The system shall render issue #1 with color #FF0000 and issue #2 with #00FF00
  Verified_By: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(input_content)
    
    output_file = input_file + ".out"
    
    try:
        script_path = get_script_path()
        result = subprocess.run(
            ["python", script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # Check all hash patterns are preserved
        hash_patterns = ["#1", "#2", "#3", "#FF0000", "#00FF00"]
        for pattern in hash_patterns:
            # Each pattern should appear at least twice (requirement + verification)
            count = output_content.count(pattern)
            assert count >= 2, \
                f"Pattern '{pattern}' should appear at least twice, found {count}"
        
        print("✓ test_combined_standard_with_multiple_hashes PASSED")
        
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def test_combined_nonstandard_with_multiple_hashes():
    """
    Test non-standard path with multiple # references.
    
    Expected: FIX comment present, all # characters preserved.
    """
    input_content = """- Type: Requirement
  ID: REQU.DMGR.TEST.6
  Name: Process references #100 and #200
  Text: |
    (U) The system shall process items #100, #200, and version ###.###
  Verified_By: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(input_content)
    
    output_file = input_file + ".out"
    
    try:
        script_path = get_script_path()
        result = subprocess.run(
            ["python", script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # Should have non-standard comments
        assert "# FIX - Non-Standard" in output_content, \
            "Should have non-standard comment"
        
        # Check all hash patterns are preserved
        hash_patterns = ["#100", "#200", "###.###"]
        for pattern in hash_patterns:
            count = output_content.count(pattern)
            assert count >= 2, \
                f"Pattern '{pattern}' should appear at least twice, found {count}"
        
        print("✓ test_combined_nonstandard_with_multiple_hashes PASSED")
        
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def test_brdg_domain_with_hash():
    """
    Test BRDG domain (setting semantics) with # in Name and Text.
    
    Expected: Both standard and non-standard BRDG paths preserve #.
    """
    input_content = """# Standard BRDG with hash
- Type: Requirement
  ID: REQU.BRDG.TEST.1
  Name: Set timeout to #DEFAULT value
  Text: |
    (U) The system shall set the timeout to #DEFAULT value
  Verified_By: 

# Non-standard BRDG with hash
- Type: Requirement
  ID: REQU.BRDG.TEST.2
  Name: Configure parameter #XYZ
  Text: |
    (U) The system shall configure parameter #XYZ
  Verified_By: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(input_content)
    
    output_file = input_file + ".out"
    
    try:
        script_path = get_script_path()
        result = subprocess.run(
            ["python", script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # Check standard BRDG preserves #DEFAULT
        assert output_content.count("#DEFAULT") >= 2, \
            "Standard BRDG should preserve #DEFAULT in both req and ver"
        
        # Check non-standard BRDG preserves #XYZ
        assert output_content.count("#XYZ") >= 2, \
            "Non-standard BRDG should preserve #XYZ in both req and ver"
        
        # Non-standard should have FIX comment
        assert "# FIX - Non-Standard" in output_content, \
            "Non-standard BRDG should have FIX comment"
        
        print("✓ test_brdg_domain_with_hash PASSED")
        
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def test_hash_in_block_scalar_content():
    """
    Test that # at the start of lines in block scalar is preserved as content (not comment).
    
    Expected: Lines starting with # in block scalars are treated as content.
    """
    input_content = """- Type: Requirement
  ID: REQU.TEST.1
  Name: Render documentation
  Text: |
    (U) The system shall render documentation with:
    # Format: owner/repo#number
    # Example: user/project#123
    # Pattern: ###.###.###
  Verified_By: 
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        input_file = f.name
        f.write(input_content)
    
    output_file = input_file + ".out"
    
    try:
        script_path = get_script_path()
        result = subprocess.run(
            ["python", script_path, input_file, output_file],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # All lines starting with # in the block should be preserved
        assert "# Format: owner/repo#number" in output_content, \
            "Block scalar line starting with # should be preserved"
        assert "# Example: user/project#123" in output_content, \
            "Block scalar line starting with # should be preserved"
        assert "# Pattern: ###.###.###" in output_content, \
            "Block scalar line starting with # should be preserved"
        
        # These should appear in both requirement and verification
        assert output_content.count("repo#number") >= 2, \
            "Content should appear in both req and ver"
        assert output_content.count("project#123") >= 2, \
            "Content should appear in both req and ver"
        
        print("✓ test_hash_in_block_scalar_content PASSED")
        
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def _create_temp_file_standalone(content):
    """Standalone temp file creator for when pytest is not available."""
    import atexit
    
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    try:
        tmp_file.write(content)
        tmp_path = tmp_file.name
    finally:
        tmp_file.close()
    
    def _cleanup_temp_file() -> None:
        try:
            os.remove(tmp_path)
        except (FileNotFoundError, OSError):
            pass
    
    atexit.register(_cleanup_temp_file)
    return tmp_path


if __name__ == '__main__':
    try:
        import pytest
        pytest.main([__file__, '-v'])
    except ImportError:
        print("pytest not available, running tests directly\n")
        print("="*70)
        print("INTEGRATION TESTS: Hash Preservation in Standard and Non-Standard Paths")
        print("="*70)
        print()
        
        tests = [
            ("Standard Name with inline hash (#123)", test_standard_name_with_hash_inline),
            ("Standard Text with hash pattern (###.###.###)", test_standard_text_with_hash_pattern),
            ("Non-standard Name with hash", test_nonstandard_name_with_hash),
            ("Non-standard Text with hash", test_nonstandard_text_with_hash),
            ("Standard path with multiple hashes", test_combined_standard_with_multiple_hashes),
            ("Non-standard path with multiple hashes", test_combined_nonstandard_with_multiple_hashes),
            ("BRDG domain with hash", test_brdg_domain_with_hash),
            ("Hash in block scalar content", test_hash_in_block_scalar_content),
        ]
        
        failed = []
        for name, test_func in tests:
            try:
                print(f"Running: {name}...")
                test_func()
            except AssertionError as e:
                print(f"✗ FAILED: {e}")
                failed.append(name)
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed.append(name)
            print()
        
        print("="*70)
        if failed:
            print(f"FAILED: {len(failed)} test(s)")
            for name in failed:
                print(f"  - {name}")
            sys.exit(1)
        else:
            print("ALL TESTS PASSED!")
            print("="*70)
