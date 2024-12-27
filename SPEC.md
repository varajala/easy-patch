# Patch Format Specification

## Basic Structure
Every patch file contains one or more file blocks. Each file block contains one or more change operations.

### File Block
Start each file block with:
```
FILE: path/to/your/file.ext
```
This file path should be relative to the project root folder.

### Change Operations
There are 4 types of operations:

1. Replace code:
```
FIND:
[code to find]

REPLACE WITH:
[new code]
```

2. Add code before:
```
FIND:
[code to find]

ADD BEFORE:
[code to add]
```

3. Add code after:
```
FIND:
[code to find]

ADD AFTER:
[code to add]
```

4. Delete code:
```
FIND:
[code to delete]

DELETE
```

## Rules

1. The FIND block must match exactly, including whitespace
2. Each FIND block must appear only once in the file
3. File paths use forward slashes, even on Windows
4. Leave one blank line between operations
5. Indentation in the code blocks must match the source file exactly

## Complete Example

Here's a complete patch file example:

```
FILE: src/hello.py
FIND:
def greet():
    print("Hello")

REPLACE WITH:
def greet(name):
    print(f"Hello {name}")

FIND:
def main():

ADD AFTER:
    # Call with default name
    greet("World")

FILE: src/config.py
FIND:
DEBUG = True
TIMEOUT = 30

DELETE

FIND:
HOST = 'localhost'

ADD BEFORE:
# Production settings
DEBUG = False
TIMEOUT = 120
```