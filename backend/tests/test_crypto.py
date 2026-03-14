"""Tests for the crypto utility module."""

import pytest
from cryptography.fernet import Fernet

from app.utils.crypto import decrypt, encrypt, init_fernet


@pytest.fixture(autouse=True)
def setup_fernet():
    """Initialize Fernet with a test key for each test."""
    key = Fernet.generate_key().decode()
    init_fernet(key)
    yield
    # Reset global state
    import app.utils.crypto as crypto_mod
    crypto_mod._fernet = None


class TestEncryptDecrypt:
    def test_roundtrip(self):
        plaintext = "sk-test-api-key-12345"
        ciphertext = encrypt(plaintext)
        assert ciphertext != plaintext
        assert decrypt(ciphertext) == plaintext

    def test_different_plaintexts_produce_different_ciphertexts(self):
        c1 = encrypt("key-one")
        c2 = encrypt("key-two")
        assert c1 != c2

    def test_same_plaintext_produces_different_ciphertexts(self):
        """Fernet uses random IV, so same input → different output."""
        c1 = encrypt("same-key")
        c2 = encrypt("same-key")
        assert c1 != c2
        assert decrypt(c1) == decrypt(c2)

    def test_empty_string_passthrough(self):
        assert encrypt("") == ""
        assert decrypt("") == ""

    def test_none_like_falsy_passthrough(self):
        assert encrypt("") == ""
        assert decrypt("") == ""

    def test_unicode_content(self):
        plaintext = "密钥：这是一个中文API密钥🔑"
        assert decrypt(encrypt(plaintext)) == plaintext


class TestInvalidKey:
    def test_invalid_key_raises(self):
        import app.utils.crypto as crypto_mod
        crypto_mod._fernet = None
        with pytest.raises(ValueError, match="Invalid EVAL_ENCRYPTION_KEY"):
            init_fernet("not-a-valid-fernet-key")

    def test_decrypt_with_wrong_key(self):
        ciphertext = encrypt("secret")
        # Re-init with a different key
        new_key = Fernet.generate_key().decode()
        init_fernet(new_key)
        with pytest.raises(ValueError, match="Failed to decrypt"):
            decrypt(ciphertext)


class TestUninitializedFernet:
    def test_encrypt_without_init_raises(self):
        import app.utils.crypto as crypto_mod
        crypto_mod._fernet = None
        with pytest.raises(RuntimeError, match="Encryption not initialized"):
            encrypt("test")

    def test_decrypt_without_init_raises(self):
        import app.utils.crypto as crypto_mod
        crypto_mod._fernet = None
        with pytest.raises(RuntimeError, match="Encryption not initialized"):
            decrypt("test")
