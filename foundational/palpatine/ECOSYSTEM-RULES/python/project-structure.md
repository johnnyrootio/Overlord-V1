# Python Project Structure

Recommended project structure for Python projects.

## Standard Structure

```
project-name/
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── main.py
│       ├── models.py
│       └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   └── test_utils.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── scripts/
│   └── check.sh
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml          # Optional but recommended
├── README.md
├── CLAUDE.md
└── .gitignore
```

## Alternative: Flat Structure (for simple projects)

```
project-name/
├── project_name.py
├── tests/
│   └── test_project_name.py
├── requirements.txt
└── README.md
```

## Directory Descriptions

- **`src/`**: Source code (use `src/` layout for packages)
- **`tests/`**: Test files mirroring source structure
- **`.github/workflows/`**: CI/CD configuration
- **`scripts/`**: Utility scripts (e.g., `check.sh`)
- **`requirements.txt`**: Production dependencies
- **`requirements-dev.txt`**: Development dependencies
- **`pyproject.toml`**: Modern Python project configuration

## Package Structure

For packages, use `src/` layout:

```
src/
└── package_name/
    ├── __init__.py          # Package initialization
    ├── module1.py
    ├── module2.py
    └── subpackage/
        ├── __init__.py
        └── module3.py
```

## Test Structure

Mirror source structure in tests:

```
tests/
├── __init__.py
├── test_module1.py
├── test_module2.py
└── test_subpackage/
    ├── __init__.py
    └── test_module3.py
```
