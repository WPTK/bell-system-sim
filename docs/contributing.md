# Contributing to Bell System UNIX V7 Terminal Simulation

Thank you for your interest in contributing to this historical recreation of Bell System operations! This project prioritizes historical accuracy while maintaining modern software engineering practices.

## How to Report Issues

### Bug Reports
Create an issue with:
- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (Python version, OS)
- **Historical context** if command behavior seems incorrect

### Feature Requests
For new features:
- **Research first** using authentic Bell System documentation (1978-1983)
- **Provide historical sources** supporting the feature
- **Explain operational context** within Bell System workflows
- **Consider role relevance** - which operational roles would use this feature

## Development Workflow

### Branching Strategy
```bash
# Clone and setup
git clone https://github.com/WPTK/bell-system-sim.git
cd bell-system-sim
pip install -e ".[dev]"

# Create feature branch
git checkout -b feature/add-switching-commands
git checkout -b fix/role-authentication-bug
git checkout -b docs/update-installation-guide
```

### Pull Request Process
1. **Fork** the repository
2. **Create feature branch** with descriptive name
3. **Implement changes** following code style guidelines
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit pull request** with detailed description

## Code Style and Linting

### Python Standards
- **PEP 8 compliance** for all Python code
- **Line length**: 100 characters, configured in `pyproject.toml`
- **Type hints**: Use for function parameters and returns
- **Docstrings**: Required for all public functions and classes

### Linting
Linting is handled by [ruff](https://docs.astral.sh/ruff/), configured under
`[tool.ruff]` in `pyproject.toml`.

```bash
# Install development tools (ruff and pytest)
pip install -e ".[dev]"

# Check style - this is the same command CI runs
ruff check src tests
```

### Pre-commit Checks
```bash
# Run before committing
ruff check src tests
python -m pytest tests
```

## Running Tests Locally

### Test Suite Execution
```bash
# Run all tests
python -m pytest tests

# Run a specific test file
python -m pytest tests/test_terminal.py

# Run a single test by name
python -m pytest tests -k role
```

The suite points logs and command history at a temporary directory, so running
it will not touch your real `~/.local/state/bell-system`.

### Test Requirements
- **Behavioural assertions**: a test must assert on real behaviour, not merely
  execute code and report success
- **Historical accuracy validation** for all Bell System commands
- **Error handling** verification, including unknown and malformed input
- **Command syntax** compliance with period standards

## Historical Accuracy Guidelines

### Research Sources
Use authentic Bell System documentation:
- **Bell System Technical Journal** (1978-1983)
- **AT&T Engineering and Operations** manuals
- **UNIX V7 documentation** and procedures
- **Bell System Practices** (BSP) documents

### Command Implementation
- **Verify terminology** matches historical usage
- **Check command syntax** against period documentation
- **Maintain operational context** appropriate to role
- **Include authentic error messages** from the era

### Documentation Standards
- **Cite sources** for historical claims
- **Include period context** for operational procedures
- **Reference specific BSP numbers** when applicable
- **Maintain authentic terminology** throughout

## Code Organization

### File Structure
```
src/bell_system/        # The installable package
├── __init__.py        # Package exports and version
├── __main__.py        # python -m bell_system
├── cli.py             # Argument parsing, the bell-system console script
├── terminal.py        # Main 12-role simulation (BellSystemTerminal)
├── simple_terminal.py # Simplified 4-role interface (SimpleTerminal)
├── screens/           # One module per subsystem's screens
└── data/              # Manual page text and other static data

tests/                  # pytest suite
├── conftest.py        # Shared fixtures, state isolation
├── test_cli.py        # Command line entry point
├── test_terminal.py   # 12-role terminal behaviour
├── test_simple_terminal.py  # 4-role terminal behaviour
└── test_integrity.py  # Source integrity: imports, aliases, dispatch table

docs/                   # Documentation
├── overview.md        # Architecture documentation
├── api.md            # API reference
├── contributing.md   # This file
├── changelog.md      # Version history
├── faq.md           # Troubleshooting guide
├── manual.txt       # Full user manual
└── command_reference.txt  # Command cheat sheet

pyproject.toml          # Packaging, console script, ruff and pytest config
```

### Naming Conventions
- **Functions**: `snake_case` with descriptive names
- **Classes**: `PascalCase` with clear purpose
- **Constants**: `UPPER_CASE` for Bell System standards
- **Files**: `snake_case.py` for modules

## Security Considerations

### Input Validation
- **Sanitize all user input** to prevent command injection
- **Validate role permissions** before command execution
- **Check file path traversal** in file operations
- **Limit resource usage** to prevent denial of service

### Audit Requirements
- **Log security events** for review
- **Track permission escalations** or failures
- **Monitor unusual command patterns**
- **Document security-relevant changes**

## Performance Guidelines

### Optimization Principles
- **Minimize startup time** for CLI responsiveness
- **Cache command lookups** for frequently used operations
- **Optimize string operations** in command processing
- **Profile performance** with the standard library (`cProfile`, `timeit`); the
  terminal also logs per-command execution times at DEBUG level

### Memory Management
- **Avoid memory leaks** in long-running sessions
- **Limit log file growth** with rotation
- **Clean up temporary resources** after command execution

## Documentation Updates

### Required Documentation
- **Update README.md** for new features
- **Modify API documentation** for interface changes
- **Add examples** demonstrating new functionality
- **Update changelog** following Keep a Changelog format

### Style Guidelines
- **Use clear, concise language** avoiding jargon
- **Include code examples** for complex features
- **Cross-reference related commands** and procedures
- **Maintain consistent formatting** across all documentation

## Getting Help

### Community Support
- **GitHub Issues** for bug reports and feature requests
- **GitHub Discussions** for general questions about Bell System operations
- **Historical Research** assistance for authentic implementation

### Maintainer Contact
For questions about:
- **Historical accuracy** and source verification
- **Technical architecture** and design decisions  
- **Contribution coordination** and roadmap planning

Thank you for helping preserve and share the fascinating history of Bell System operations and early UNIX systems!