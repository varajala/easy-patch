import pytest
from easy_patch import (
    parse_patch_file,
    PatchOperation,
    OperationType,
    Error,
    ParserState,
    parse_file_directive,
    parse_find_block,
    parse_operation
)

def test_parse_simple_replace():
    content = """FILE: test.py
FIND:
def old_function():
    pass

REPLACE WITH:
def new_function():
    return True
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 0
    assert len(operations) == 1
    assert operations[0].file_path == "test.py"
    assert operations[0].find_content == "def old_function():\n    pass"
    assert operations[0].operation == OperationType.REPLACE
    assert operations[0].new_content == "def new_function():\n    return True"


def test_parse_multiple_operations():
    content = """FILE: test.py
FIND:
import os

ADD BEFORE:
import sys

FIND:
def main():

REPLACE WITH:
def main() -> None:
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 0
    assert len(operations) == 2

    assert operations[0].operation == OperationType.ADD_BEFORE
    assert operations[0].find_content == "import os"
    assert operations[0].new_content == "import sys"

    assert operations[1].operation == OperationType.REPLACE
    assert operations[1].find_content == "def main():"
    assert operations[1].new_content == "def main() -> None:"


def test_parse_delete_operation():
    content = """FILE: test.py
FIND:
# TODO: Remove this later
print("debug")

DELETE
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 0
    assert len(operations) == 1
    assert operations[0].operation == OperationType.DELETE
    assert operations[0].new_content is None


def test_parse_multiple_files():
    content = """FILE: test1.py
FIND:
old1
REPLACE WITH:
new1

FILE: test2.py
FIND:
old2
REPLACE WITH:
new2
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 0
    assert len(operations) == 2
    assert operations[0].file_path == "test1.py"
    assert operations[1].file_path == "test2.py"


def test_parse_windows_path():
    content = "FILE: src\\test\\file.py\nFIND:\nold\nREPLACE WITH:\nnew"
    operations, errors = parse_patch_file(content)

    assert len(errors) == 0
    assert operations[0].file_path == "src/test/file.py"


def test_parse_missing_file():
    content = """FIND:
test
REPLACE WITH:
new
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 1
    assert "Expected 'FILE:'" in errors[0].message


def test_parse_missing_find():
    content = """FILE: test.py
REPLACE WITH:
new
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 1
    assert "Expected 'FIND:'" in errors[0].message


def test_parse_missing_operation():
    content = """FILE: test.py
FIND:
test
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 1
    assert "Expected operation" in errors[0].message


def test_parse_empty_file_path():
    content = "FILE:\nFIND:\ntest\nREPLACE WITH:\nnew"
    operations, errors = parse_patch_file(content)

    assert len(errors) == 1
    assert "Empty file path" in errors[0].message


def test_parse_recovery_after_error():
    content = """FILE: test1.py
INVALID

FILE: test2.py
FIND:
test
REPLACE WITH:
new
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 1
    assert len(operations) == 1
    assert operations[0].file_path == "test2.py"


def test_parse_whitespace_preservation():
    content = """FILE: test.py
FIND:
def test():
    return True  # Note the two spaces here

REPLACE WITH:
def test():
    return False  # Should preserve two spaces
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 0
    assert "  #" in operations[0].find_content
    assert "  #" in operations[0].new_content


def test_parser_state():
    state = ParserState("test\ncontent", 0, 1)

    assert state.current() == "t"
    assert state.peek(4) == "test"

    state.advance()
    assert state.current() == "e"
    assert state.line == 1

    # Advance to newline
    state.advance(3)
    assert state.current() == "\n"
    state.advance()
    assert state.line == 2


def test_parse_operation_all_types():
    test_cases = [
        ("REPLACE WITH:\nnew", OperationType.REPLACE, "new"),
        ("ADD BEFORE:\nnew", OperationType.ADD_BEFORE, "new"),
        ("ADD AFTER:\nnew", OperationType.ADD_AFTER, "new"),
        ("DELETE:", OperationType.DELETE, None),
    ]

    for content, expected_type, expected_content in test_cases:
        state = ParserState(content, 0, 1)
        op_type, content = parse_operation(state)

        assert op_type == expected_type
        assert content == expected_content


def test_parse_with_trailing_whitespace():
    content = """FILE: test.py
FIND:
old
REPLACE WITH:
new
"""
    operations, errors = parse_patch_file(content)

    assert len(errors) == 0
    assert operations[0].file_path == "test.py"
    assert operations[0].find_content == "old"
    assert operations[0].new_content == "new"