# easy-patch
A simple, LLM-friendly CLI tool to apply patches in a custom format.

## Usage

The tool reads patch instructions from standard input and applies them to the specified files:

```bash
cat your_changes.patch | easy-patch
```

or

```bash
easy-patch < your_changes.patch
```

## Patch Format

The patch format supports four main operations:

1. **Replace** existing code
2. **Add before** a specific block
3. **Add after** a specific block
4. **Delete** a block

Each operation requires a context block (`FIND:`) to locate where the change should be applied.

### Example

Here's a complete example using files from the tests/examples directory:

```
FILE: tests/examples/hello.py
FIND:
def greet(name: str = "World") -> str:
    """A simple greeting function"""
    return f"Hello, {name}!"

REPLACE WITH:
def greet(name: str = "World", greeting: str = "Hello") -> str:
    """A customizable greeting function

    Args:
        name (str): Name to greet
        greeting (str): Custom greeting to use
    """
    return f"{greeting}, {name}!"

FIND:
def main():

ADD AFTER:
    # Add some extra greetings
    print(greet(greeting="Hi"))
    print(greet("Everyone", "Good morning"))
```

This patch makes two changes to the `hello.py` file:
1. Updates the `greet()` function to support custom greetings
2. Adds additional example greetings to the main function

See the `SPEC.md` for more detailed specification of the format.
This can be given to the LLM of your choice.