# Contributing to MkDocs Quiz Plugin

Thank you for your interest in contributing to the MkDocs Quiz Plugin! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/mkdocs-quiz.git
cd mkdocs-quiz
```

2. Create a virtual environment and install development dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

3. Set up pre-commit hooks:

```bash
pre-commit install
```

4. Test with the example site:

```bash
cd example
mkdocs serve
# Open http://127.0.0.1:8000 in your browser
```

## Code Quality

We use several tools to maintain code quality:

- **Ruff**: Python code formatting and linting
- **Prettier**: JavaScript and CSS formatting
- **MyPy**: Static type checking
- **Pytest**: Testing

### Running Quality Checks

Most checks run automatically via pre-commit hooks. To run manually:

```bash
# Run all checks
pre-commit run --all-files

# Or run individual tools
ruff format mkdocs_quiz tests
ruff check mkdocs_quiz tests
mypy mkdocs_quiz
pytest tests/ -v --cov=mkdocs_quiz
```

### Pre-commit Hooks

This project uses pre-commit hooks to automatically check code quality before committing:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

The hooks will automatically:

- Format Python code with Ruff
- Format JS/CSS with Prettier
- Lint code with Ruff
- Type check with MyPy
- Check for common issues (trailing whitespace, etc.)

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mkdocs_quiz --cov-report=html

# Run specific test file
pytest tests/test_plugin.py

# Run specific test
pytest tests/test_plugin.py::test_single_choice_quiz
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_*.py` pattern
- Use descriptive test function names starting with `test_`
- Include docstrings explaining what each test validates

### Testing with the Example Site

Test your changes with the included example site:

```bash
cd example
mkdocs serve
# Open http://127.0.0.1:8000 in your browser
```

## Building the Package

To build the package locally:

```bash
# Install build tools
pip install build

# Build the package
python -m build

# The distribution files will be in dist/
```

## Publishing

The package is automatically published to PyPI when a new release is created on GitHub. See the comments in [.github/workflows/publish.yml](.github/workflows/publish.yml) for one-time setup instructions.

## Making Changes

1. Create a new branch for your feature or bugfix:

```bash
git checkout -b feature/my-new-feature
```

2. Make your changes and ensure:
   - Pre-commit hooks are installed (they'll check everything automatically)
   - Type hints are added for new code
   - Tests are added/updated for new features
   - All tests pass

3. Commit your changes with clear, descriptive messages:

```bash
git commit -m "Add feature: description of what you added"
```

4. Push to your fork:

```bash
git push origin feature/my-new-feature
```

5. Open a Pull Request on GitHub

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Ensure all CI checks pass
- Update documentation if needed
- Add entries to CHANGELOG.md

## Code Style

- Follow PEP 8 guidelines (enforced by Ruff)
- Use type hints for all function parameters and return values
- Write docstrings for classes and functions
- Keep functions focused and concise
- Use descriptive variable names

Pre-commit hooks will automatically format your code and catch common issues before you commit.

## Reporting Issues

When reporting issues, please include:

- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, OS, MkDocs version)
- Relevant code snippets or error messages

## Questions?

Feel free to open an issue for questions or discussions about contributing!

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
