"""Tests for error_sanitizer: URL/IP/path stripping and truncation."""
from app.utils.error_sanitizer import sanitize_error


class TestSanitizeError:

    def test_strips_urls(self):
        result = sanitize_error("Error at https://example.com/api")
        assert "[URL]" in result
        assert "https://example.com" not in result

    def test_strips_ips(self):
        result = sanitize_error("Connection to 192.168.1.1:8080")
        assert "[IP]" in result
        assert "192.168.1.1" not in result

    def test_strips_paths(self):
        result = sanitize_error("File /usr/local/bin/app failed")
        assert "[path]" in result
        assert "/usr/local/bin/app" not in result

    def test_truncates_long_messages(self):
        long_msg = "A" * 1000
        result = sanitize_error(long_msg)
        assert len(result) <= 500

    def test_preserves_clean_text(self):
        msg = "Simple error"
        result = sanitize_error(msg)
        assert result == "Simple error"
