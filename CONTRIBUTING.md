# Contributing to compose-status

Thank you for your interest in contributing to compose-status! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/compose-status.git
   cd compose-status
   ```
3. **Set up the upstream remote**:
   ```bash
   git remote add upstream https://github.com/cdhouch/compose-status.git
   ```

## Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Test your changes**:
   ```bash
   python3 compose-status.py
   ```

## Making Changes

### Code Style

- Follow **PEP 8** Python style guidelines
- Use **type hints** for function parameters and return values
- Keep functions **focused and single-purpose**
- Add **docstrings** to all functions (Google or NumPy style)
- Include **inline comments** for complex logic

### Documentation

- Update docstrings when modifying functions
- Update README.md if adding new features or changing behavior
- Add examples for new features

### Commit Messages

Write clear, descriptive commit messages:

```
Add support for custom compose file paths

- Allow users to specify compose file via command-line argument
- Update README with usage examples
- Add tests for new functionality
```

## Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test thoroughly

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub with:
   - Clear description of changes
   - Reference to any related issues
   - Screenshots/examples if applicable

## Areas for Contribution

We welcome contributions in these areas:

### Features
- Support for multiple compose files
- JSON output mode
- Filtering and sorting options
- Resource usage display
- Auto-refresh mode

### Improvements
- Better error handling
- Performance optimizations
- Cross-platform compatibility fixes
- Documentation improvements

### Bug Fixes
- Report bugs via GitHub Issues
- Include steps to reproduce
- Describe expected vs actual behavior

## Code Review

All contributions go through code review. Reviewers will check for:
- Code quality and style
- Test coverage
- Documentation completeness
- Backward compatibility

## Questions?

Feel free to open an issue for questions or discussions about potential contributions.

Thank you for contributing! 🎉

