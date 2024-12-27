import pytest
from easy_patch import (
    PatchOperation,
    OperationType,
    Error,
    apply_operation,
    apply_operations_to_content,
    group_operations_by_file
)

def test_apply_replace_operation():
    content = "def old_function():\n    pass"
    operation = PatchOperation(
        file_path="test.py",
        find_content="def old_function():\n    pass",
        operation=OperationType.REPLACE,
        new_content="def new_function():\n    return True"
    )

    result = apply_operation(content, operation)
    assert result == "def new_function():\n    return True"

def test_apply_add_before():
    content = "def test():\n    pass"
    operation = PatchOperation(
        file_path="test.py",
        find_content="def test():",
        operation=OperationType.ADD_BEFORE,
        new_content="# Added comment"
    )

    result = apply_operation(content, operation)
    assert result == "# Added comment\ndef test():\n    pass"

def test_apply_add_after():
    content = "def test():\n    pass"
    operation = PatchOperation(
        file_path="test.py",
        find_content="def test():\n    pass",
        operation=OperationType.ADD_AFTER,
        new_content="# End of function"
    )

    result = apply_operation(content, operation)
    assert result == "def test():\n    pass\n# End of function"

def test_apply_delete():
    content = "# TODO: Remove this\nprint('debug')\nprint('keep this')"
    operation = PatchOperation(
        file_path="test.py",
        find_content="# TODO: Remove this\nprint('debug')",
        operation=OperationType.DELETE
    )

    result = apply_operation(content, operation)
    assert result == "\nprint('keep this')"

def test_apply_multiple_operations():
    content = "import os\n\ndef main():\n    pass"
    operations = [
        PatchOperation(
            file_path="test.py",
            find_content="import os",
            operation=OperationType.ADD_BEFORE,
            new_content="import sys"
        ),
        PatchOperation(
            file_path="test.py",
            find_content="def main():",
            operation=OperationType.REPLACE,
            new_content="def main() -> None:"
        )
    ]

    result, errors = apply_operations_to_content(content, operations)
    assert len(errors) == 0
    assert "import sys\nimport os" in result
    assert "def main() -> None:" in result

def test_operation_context_not_found():
    content = "def existing_function():\n    pass"
    operation = PatchOperation(
        file_path="test.py",
        find_content="def nonexistent_function():",
        operation=OperationType.REPLACE,
        new_content="def new_function():"
    )

    with pytest.raises(ValueError, match="Context not found in file"):
        apply_operation(content, operation)

def test_multiple_matches():
    content = "print('test')\nprint('test')"
    operation = PatchOperation(
        file_path="test.py",
        find_content="print('test')",
        operation=OperationType.REPLACE,
        new_content="print('modified')"
    )

    with pytest.raises(ValueError, match="Context appears multiple times"):
        apply_operation(content, operation)

def test_apply_operations_stops_on_error():
    content = "def test1():\n    pass\n\ndef test2():\n    pass"
    operations = [
        PatchOperation(
            file_path="test.py",
            find_content="def test1():",
            operation=OperationType.REPLACE,
            new_content="def new_test1():"
        ),
        PatchOperation(
            file_path="test.py",
            find_content="nonexistent",
            operation=OperationType.REPLACE,
            new_content="something"
        ),
        PatchOperation(
            file_path="test.py",
            find_content="def test2():",
            operation=OperationType.REPLACE,
            new_content="def new_test2():"
        )
    ]

    result, errors = apply_operations_to_content(content, operations)
    assert len(errors) == 1
    assert "Context not found" in errors[0].message
    assert result == content  # Should be unchanged due to error

def test_group_operations_by_file():
    operations = [
        PatchOperation("file1.py", "old1", OperationType.REPLACE, "new1"),
        PatchOperation("file2.py", "old2", OperationType.REPLACE, "new2"),
        PatchOperation("file1.py", "old3", OperationType.DELETE)
    ]

    grouped = group_operations_by_file(operations)
    assert len(grouped) == 2
    assert len(grouped["file1.py"]) == 2
    assert len(grouped["file2.py"]) == 1
    assert grouped["file1.py"][0].new_content == "new1"
    assert grouped["file2.py"][0].new_content == "new2"

def test_whitespace_preservation():
    content = "def test():    # Four spaces before comment\n    pass"
    operation = PatchOperation(
        file_path="test.py",
        find_content="def test():",
        operation=OperationType.REPLACE,
        new_content="def new_test():"
    )

    result = apply_operation(content, operation)
    assert result == "def new_test():    # Four spaces before comment\n    pass"