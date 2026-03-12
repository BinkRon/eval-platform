"""Tests for project_file_service: validation and file type checks."""
import pytest

from app.services.project_file_service import _sanitize_filename, _validate_file, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from app.exceptions import ValidationError


class TestValidateFile:
    def test_allowed_extensions(self):
        for ext in ALLOWED_EXTENSIONS:
            result = _validate_file(f"test{ext}", 1024)
            assert result == ext

    def test_rejected_extension(self):
        with pytest.raises(ValidationError, match="不支持的文件类型"):
            _validate_file("test.exe", 1024)

    def test_rejected_no_extension(self):
        with pytest.raises(ValidationError, match="不支持的文件类型"):
            _validate_file("noextension", 1024)

    def test_file_size_limit(self):
        with pytest.raises(ValidationError, match="文件大小超过限制"):
            _validate_file("test.pdf", MAX_FILE_SIZE + 1)

    def test_file_size_at_limit(self):
        # Should not raise
        _validate_file("test.pdf", MAX_FILE_SIZE)

    def test_case_insensitive_extension(self):
        result = _validate_file("test.PDF", 1024)
        assert result == ".pdf"


class TestSanitizeFilename:
    def test_strips_path_traversal(self):
        assert _sanitize_filename("../../etc/passwd.pdf") == "passwd.pdf"

    def test_strips_directory_prefix(self):
        assert _sanitize_filename("/tmp/uploads/test.txt") == "test.txt"

    def test_normal_filename_unchanged(self):
        assert _sanitize_filename("report.pdf") == "report.pdf"

    def test_empty_after_strip_raises(self):
        with pytest.raises(ValidationError, match="文件名非法"):
            _sanitize_filename("")

    def test_only_dots_raises(self):
        with pytest.raises(ValidationError, match="文件名非法"):
            _sanitize_filename("..")
