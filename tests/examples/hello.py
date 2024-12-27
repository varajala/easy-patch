def greet(name: str = "World") -> str:
    """A simple greeting function"""
    return f"Hello, {name}!"

def main():
    print(greet())
    print(greet("Python"))

if __name__ == "__main__":
    main()