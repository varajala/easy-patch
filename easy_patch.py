import sys
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from enum import Enum


class OperationType(Enum):
    REPLACE = "REPLACE WITH"
    ADD_BEFORE = "ADD BEFORE"
    ADD_AFTER = "ADD AFTER"
    DELETE = "DELETE"


@dataclass
class PatchOperation:
    file_path: str
    find_content: str
    operation: OperationType
    new_content: Optional[str] = None


@dataclass
class Error:
    file_path: str
    message: str
    operation_index: int


@dataclass
class ParserState:
    """Keeps track of parser position and content"""
    content: str
    position: int
    line: int

    def current(self) -> str:
        """Get current character or empty string if at end"""
        return self.content[self.position] if self.position < len(self.content) else ''

    def peek(self, n: int = 1) -> str:
        """Look ahead n characters without moving position"""
        end = min(self.position + n, len(self.content))
        return self.content[self.position:end]

    def advance(self, n: int = 1) -> None:
        """Move position forward by n characters"""
        for _ in range(n):
            if self.current() == '\n':
                self.line += 1
            self.position += 1
            if self.position > len(self.content):
                self.position = len(self.content)


def skip_whitespace(state: ParserState) -> None:
    """Skip any whitespace characters"""
    while state.current().isspace():
        state.advance()


def parse_until(state: ParserState, *delimiters) -> str:
    """Parse content until any of the delimiters is found"""
    result = ""

    while state.current():
        # Check for each delimiter
        found_delimiter = False
        for delimiter in delimiters:
            if state.peek(len(delimiter)) == delimiter:
                found_delimiter = True
                break

        if found_delimiter:
            break

        result += state.current()
        state.advance()

    return result


def parse_keyword(state: ParserState, keyword: str) -> bool:
    """Try to parse a specific keyword"""
    if state.peek(len(keyword)) == keyword:
        state.advance(len(keyword))
        return True
    return False


def parse_file_directive(state: ParserState) -> str:
    """Parse FILE: directive and return the file path"""
    skip_whitespace(state)
    if not parse_keyword(state, "FILE:"):
        raise ValueError(f"Expected 'FILE:' at line {state.line}")

    file_path = parse_until(state, "FIND:", "\n").strip()

    # Validate the file path is not empty
    if not file_path:
        raise ValueError("Empty file path")

    # Normalize path separators
    return file_path.replace('\\', '/')


def parse_find_block(state: ParserState) -> str:
    """Parse FIND: block and return the content to find"""
    skip_whitespace(state)
    if not parse_keyword(state, "FIND:"):
        raise ValueError(f"Expected 'FIND:' at line {state.line}")

    skip_whitespace(state)
    content = parse_until(state, "REPLACE WITH:", "ADD BEFORE:", "ADD AFTER:", "DELETE").strip()
    return content


def parse_operation(state: ParserState) -> Optional[Tuple[OperationType, Optional[str]]]:
    """Parse operation type and its content"""
    skip_whitespace(state)

    for op_type in OperationType:
        if parse_keyword(state, op_type.value):
            if op_type == OperationType.DELETE:
                return op_type, None

            if not state.current() == ':':
                continue
            state.advance()  # skip the colon

            skip_whitespace(state)
            content = parse_until(state, "\nFIND:", "\nFILE:").strip()
            return op_type, content

    return None


def parse_patch_file(content: str) -> Tuple[List[PatchOperation], List[Error]]:
    """Parse the entire patch file content"""
    state = ParserState(content, 0, 1)
    operations = []
    errors = []
    operation_index = 0

    while state.position < len(state.content):
        try:
            file_path = parse_file_directive(state)

            while state.position < len(state.content):
                next_pos = state.position
                while next_pos < len(state.content) and state.content[next_pos].isspace():
                    next_pos += 1
                if next_pos < len(state.content) and state.content[next_pos:].startswith("FILE:"):
                    break

                find_content = parse_find_block(state)

                op_result = parse_operation(state)
                if not op_result:
                    raise ValueError(f"Expected operation at line {state.line}")

                op_type, new_content = op_result
                operations.append(PatchOperation(file_path, find_content, op_type, new_content))

                operation_index += 1
                skip_whitespace(state)

        except ValueError as e:
            errors.append(Error("unknown" if not 'file_path' in locals() else file_path, str(e), operation_index))
            parse_until(state, "FILE:")

    return operations, errors


def apply_operation(content: str, operation: PatchOperation) -> str:
    """Apply a single patch operation to the content"""
    # Find the context in the content
    find_index = content.find(operation.find_content)
    if find_index == -1:
        raise ValueError("Context not found in file")

    # Check for multiple occurrences
    if content.find(operation.find_content, find_index + 1) != -1:
        raise ValueError("Context appears multiple times in file")

    # Apply the operation
    if operation.operation == OperationType.REPLACE:
        return content[:find_index] + operation.new_content + content[find_index + len(operation.find_content):]
    elif operation.operation == OperationType.ADD_BEFORE:
        return content[:find_index] + operation.new_content + '\n' + content[find_index:]
    elif operation.operation == OperationType.ADD_AFTER:
        next_pos = find_index + len(operation.find_content)
        return content[:next_pos] + '\n' + operation.new_content + content[next_pos:]
    elif operation.operation == OperationType.DELETE:
        return content[:find_index] + content[find_index + len(operation.find_content):]
    else:
        raise ValueError(f"Unknown operation type: {operation.operation}")


def apply_operations_to_content(content: str, operations: List[PatchOperation]) -> Tuple[str, List[Error]]:
    """Apply all operations to a string content"""
    errors = []
    current_content = content

    for i, operation in enumerate(operations):
        try:
            current_content = apply_operation(current_content, operation)
        except ValueError as e:
            errors.append(Error(operation.file_path, str(e), i))
            # If we hit an error, return original content
            return content, errors

    return current_content, errors


def group_operations_by_file(operations: List[PatchOperation]) -> Dict[str, List[PatchOperation]]:
    """Group operations by their target file path"""
    result: Dict[str, List[PatchOperation]] = {}
    for op in operations:
        if op.file_path not in result:
            result[op.file_path] = []
        result[op.file_path].append(op)
    return result


def main():
    # Read input patch file
    input_content = sys.stdin.read()

    # Parse patches
    operations, parse_errors = parse_patch_file(input_content)
    if parse_errors:
        print("\nParse errors encountered:", file=sys.stderr)
        for error in parse_errors:
            print(f"- {error.file_path}: {error.message}", file=sys.stderr)
        sys.exit(1)

    # Group operations by file
    grouped_operations = group_operations_by_file(operations)
    apply_errors = []

    # Process each file
    for file_path, file_operations in grouped_operations.items():
        if not os.path.exists(file_path):
            apply_errors.append(Error(file_path, f"File not found: {file_path}", -1))
            continue

        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Apply operations
            new_content, errors = apply_operations_to_content(original_content, file_operations)
            if errors:
                apply_errors.extend(errors)
                continue

            # Write modified content only if no errors occurred
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        except Exception as e:
            apply_errors.append(Error(file_path, str(e), -1))

    # Report any errors
    if apply_errors:
        print("\nErrors encountered while applying patches:", file=sys.stderr)
        for error in apply_errors:
            print(f"- {error.file_path}: {error.message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()