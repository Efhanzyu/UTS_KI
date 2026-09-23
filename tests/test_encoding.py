"""Tests for strict standard Base64 encoding helpers."""
import pytest

from app.utils.encoding import safe_b64decode, safe_b64encode


@pytest.mark.parametrize("size", [0, 1, 2, 3, 4, 5, 31, 256])
def test_base64_roundtrip_for_binary_bytes(size):
    original = bytes(range(256))[:size]
    encoded = safe_b64encode(original)

    assert encoded.isascii()
    assert safe_b64decode(encoded) == original


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        ("YQ==", b"a"),
        ("YQ", b"a"),
        ("YWI=", b"ab"),
        ("YWI", b"ab"),
        ("YWJj", b"abc"),
        ("  YW Jj\r\n", b"abc"),
        ("", b""),
    ],
)
def test_base64_decode_accepts_valid_padding_and_ascii_whitespace(encoded, expected):
    assert safe_b64decode(encoded) == expected


@pytest.mark.parametrize(
    "encoded",
    ["A", "YQ=", "YQ===", "Y=Q=", "YQ==!", "YWJj$", "YR==", "____", "é"],
)
def test_base64_decode_rejects_malformed_or_noncanonical_input(encoded):
    with pytest.raises(ValueError, match="Base64 tidak valid"):
        safe_b64decode(encoded)


@pytest.mark.parametrize("value", [None, b"YQ==", 123])
def test_base64_decode_rejects_non_string_input(value):
    with pytest.raises(ValueError, match="Base64 tidak valid"):
        safe_b64decode(value)
