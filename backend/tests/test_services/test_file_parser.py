"""Tests for file_parser: text extraction from various file types."""
import csv
import os
import tempfile

import pytest

from app.services.file_parser import parse_file


class TestParseTxt:
    def test_plain_text_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello world\nSecond line")
            f.flush()
            result = parse_file(f.name, "txt")
        os.unlink(f.name)
        assert "Hello world" in result
        assert "Second line" in result

    def test_markdown_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Title\n\nSome **bold** text")
            f.flush()
            result = parse_file(f.name, "md")
        os.unlink(f.name)
        assert "# Title" in result
        assert "**bold**" in result


class TestParseCsv:
    def test_csv_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Age"])
            writer.writerow(["Alice", "30"])
            f.flush()
            result = parse_file(f.name, "csv")
        os.unlink(f.name)
        assert "Name | Age" in result
        assert "Alice | 30" in result


class TestParseUnsupported:
    def test_unsupported_type_returns_empty(self):
        assert parse_file("/nonexistent/file.xyz", "xyz") == ""

    def test_missing_file_returns_empty(self):
        assert parse_file("/nonexistent/file.txt", "txt") == ""


class TestParsePdf:
    def test_pdf_parser_exists(self):
        """Verify pypdf is importable and parser is registered."""
        from app.services.file_parser import _PARSERS
        assert "pdf" in _PARSERS


class TestParseDocx:
    def test_docx_parser_exists(self):
        from app.services.file_parser import _PARSERS
        assert "docx" in _PARSERS


class TestParseXlsx:
    def test_xlsx_file(self):
        from openpyxl import Workbook

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            wb = Workbook()
            ws = wb.active
            ws.title = "Data"
            ws.append(["Name", "Score"])
            ws.append(["Bob", 95])
            wb.save(f.name)
            wb.close()
            result = parse_file(f.name, "xlsx")
        os.unlink(f.name)
        assert "Name | Score" in result
        assert "Bob | 95" in result
        assert "[Sheet: Data]" in result
