"""
Simple unit tests for DexKeeper bot helper functions.
Run with: pytest tests/test_helpers.py -v
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "Sources" / "DexKeeper_Bot"))

from dexkeeper_bot import sanitize, _parse_admin_id, _parse_version, _in_docker


def test_sanitize_escapes_html():
    """Test that sanitize properly escapes HTML special characters"""
    result = sanitize("<script>alert('xss')</script>")
    assert "&lt;script&gt;" in result
    assert sanitize(None) == ""
    assert sanitize("Normal text") == "Normal text"
    

def test_sanitize_truncates_long_strings():
    """Test that sanitize enforces max length"""
    long_text = "A" * 2000
    result = sanitize(long_text)
    assert len(result) == 1000  # Truncated to 1000


def test_parse_admin_id_valid():
    """Test parsing valid admin IDs"""
    assert _parse_admin_id("123456") == 123456
    assert _parse_admin_id("0") == 0
    

def test_parse_admin_id_invalid():
    """Test handling of invalid admin IDs"""
    assert _parse_admin_id("abc") == 0
    assert _parse_admin_id("") == 0
    assert _parse_admin_id(None) == 0
    assert _parse_admin_id("  ") == 0


def test_parse_version_comparison():
    """Test version string parsing and comparison"""
    assert _parse_version("v1.2.3") > _parse_version("v1.2.2")
    assert _parse_version("2.0.0") > _parse_version("1.9.9")
    assert _parse_version("1.0.0") == (1, 0, 0)
    assert _parse_version("v0.1.0") == (0, 1, 0)


def test_in_docker_detection():
    """Test Docker environment detection"""
    # This will vary by environment, just ensure it returns bool
    result = _in_docker()
    assert isinstance(result, bool)
