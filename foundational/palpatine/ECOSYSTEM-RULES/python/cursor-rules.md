# Python Cursor Rules

These rules should be added to `.cursorrules` or `CLAUDE.md` for Python projects.

## Python-Specific Rules

### Code Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 88 characters (Black default)
- Use `ruff` for linting and `black` for formatting
- Use `mypy` for type checking

### Project Structure

- Use `src/` layout (not flat structure)
- Separate tests in `tests/` directory
- Use `__init__.py` files appropriately
- Follow Python package conventions

### Dependencies

- Use `requirements.txt` for dependencies
- Use `requirements-dev.txt` for development dependencies
- Consider `pyproject.toml` for modern projects
- Pin versions in production dependencies

### Testing

- Use `pytest` as the test framework
- Place tests in `tests/` directory mirroring `src/` structure
- Use fixtures for test data and setup
- Aim for high test coverage (80%+)

### Type Checking

- Run `mypy` as part of the gate (`check.sh`)
- Use strict mode when possible
- Add type stubs for third-party libraries if needed

### Documentation

- Use docstrings (Google or NumPy style)
- Document all public functions and classes
- Include type information in docstrings

### Virtual Environments

- Always use virtual environments
- Document in README how to set up venv
- Include `.venv/` in `.gitignore`

### Import Organization

- Standard library imports first
- Third-party imports second
- Local imports last
- Use absolute imports (not relative)

### Error Handling

- Use specific exception types
- Include context in error messages
- Log errors appropriately
- Don't catch generic `Exception` unless necessary

### Performance

- Profile before optimizing
- Use appropriate data structures
- Consider `asyncio` for I/O-bound operations
- Use generators for large datasets
