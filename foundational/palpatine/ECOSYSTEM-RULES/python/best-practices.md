# Python Best Practices and Programming Guidelines

## General Principles

- **Readability counts**: Code is read more often than written
- **Explicit is better than implicit**: Be clear about what code does
- **Simple is better than complex**: Prefer straightforward solutions
- **Don't repeat yourself (DRY)**: Extract common patterns

## Code Organization

### Module Structure

- One class or function per module when possible
- Group related functionality together
- Use `__init__.py` to expose public API
- Keep modules focused and cohesive

### Import Organization

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import requests
from typing import Optional

# Local
from .models import User
from .utils import helper_function
```

## Type Hints

- Use type hints for all function signatures
- Use `Optional[T]` for nullable types
- Use `Union[T, U]` for multiple types
- Use `List[T]`, `Dict[K, V]` for collections
- Use `Any` sparingly (prefer specific types)

## Error Handling

- Use specific exception types
- Include context in error messages
- Use `try/except/finally` appropriately
- Don't catch generic `Exception` unless necessary
- Use `raise ... from ...` for exception chaining

## Testing

- Write tests before implementation (TDD)
- Use descriptive test names
- One assertion per test when possible
- Use fixtures for test data
- Mock external dependencies
- Test edge cases and error conditions

## Documentation

- Write docstrings for all public functions and classes
- Use Google or NumPy style docstrings
- Include type information
- Document parameters and return values
- Provide usage examples

## Performance

- Profile before optimizing
- Use appropriate data structures
- Consider `asyncio` for I/O-bound operations
- Use generators for large datasets
- Cache expensive computations
- Avoid premature optimization

## Security

- Validate all inputs
- Use parameterized queries for databases
- Sanitize user input
- Keep dependencies updated
- Use environment variables for secrets
- Don't commit secrets to version control
