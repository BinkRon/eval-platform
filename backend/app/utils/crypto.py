"""Symmetric encryption utilities for sensitive data (API keys, auth tokens).

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the cryptography library.
Encryption key must be set via EVAL_ENCRYPTION_KEY environment variable.
"""

from cryptography.fernet import Fernet, InvalidToken


_fernet: Fernet | None = None


def init_fernet(key: str) -> None:
    """Initialize the Fernet instance with the given key. Called at app startup."""
    global _fernet
    try:
        _fernet = Fernet(key.encode())
    except Exception as e:
        raise ValueError(
            f"Invalid EVAL_ENCRYPTION_KEY: {e}. "
            "Generate a valid key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        ) from e


def _get_fernet() -> Fernet:
    if _fernet is None:
        raise RuntimeError("Encryption not initialized. Set EVAL_ENCRYPTION_KEY and call init_fernet().")
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string, returning a base64-encoded ciphertext string."""
    if not plaintext:
        return plaintext
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext string back to plaintext."""
    if not ciphertext:
        return ciphertext
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Failed to decrypt: invalid ciphertext or wrong key") from e
