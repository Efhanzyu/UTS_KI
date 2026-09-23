"""Strict Base64 helpers that also accept unpadded input."""
import base64
import binascii


_ASCII_WHITESPACE = b" \t\r\n\v\f"


def safe_b64encode(data: bytes) -> str:
    """Encode bytes as standard, padded Base64 ASCII."""
    return base64.b64encode(data).decode("ascii")


def safe_b64decode(value: str) -> bytes:
    """Decode standard Base64, accepting omitted padding and ASCII whitespace.

    Invalid alphabet characters, malformed padding, non-ASCII input, and
    non-canonical pad bits are rejected instead of being silently ignored.

    Raises:
        ValueError: If ``value`` is not valid standard Base64 text.
    """
    if not isinstance(value, str):
        raise ValueError("Base64 tidak valid.")

    try:
        encoded = value.encode("ascii").translate(None, _ASCII_WHITESPACE)
    except UnicodeEncodeError as exc:
        raise ValueError("Base64 tidak valid.") from exc

    padding = len(encoded) - len(encoded.rstrip(b"="))
    if padding:
        if padding > 2 or len(encoded) % 4 != 0:
            raise ValueError("Base64 tidak valid.")
        if b"=" in encoded[:-padding]:
            raise ValueError("Base64 tidak valid.")
    else:
        remainder = len(encoded) % 4
        if remainder == 1:
            raise ValueError("Base64 tidak valid.")
        if remainder:
            encoded += b"=" * (4 - remainder)

    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Base64 tidak valid.") from exc

    # Reject alternate encodings with non-zero unused pad bits.
    if base64.b64encode(decoded).rstrip(b"=") != encoded.rstrip(b"="):
        raise ValueError("Base64 tidak valid.")
    return decoded
