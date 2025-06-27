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
git clone https://github.com/your-username/bell-system-sim.git
cd bell-system-sim

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
- **Line length**: 88 characters maximum
- **Type hints**: Use for function parameters and returns
- **Docstrings**: Required for all public functions and classes

### Formatting Tools
```bash
# Install development tools
pip install black flake8

# Format code
black src/ tests/ bin/

# Check style
flake8 src/ tests/ bin/
```

### Pre-commit Checks
```bash
# Run before committing
black --check src/ tests/ bin/
flake8 src/ tests/ bin/
python -m pytest tests/
```

## Running Tests Locally

### Test Suite Execution
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/comprehensive_test_suite.py

# Run with coverage
python -m pytest --cov=src tests/

# Test CLI functionality
bell-system --test
```

### Test Requirements
- **Historical accuracy validation** for all Bell System commands
- **Role-based access control** testing
- **Error handling** verification
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
src/                    # Source code modules
├── __init__.py        # Package initialization
├── bell.py            # Main 12-role simulation
├── unix_terminal.py   # Simplified 4-role interface  
├── bell_system_tutorial.py  # Interactive tutorial
├── logging_enhancements.py  # Professional logging
├── performance_profiling.py # Optimization tools
└── ux_command_enhancements.py  # UX improvements

tests/                  # Test suites
├── comprehensive_test_suite.py  # Main test framework
└── test_*.py          # Additional test modules

docs/                   # Documentation
├── overview.md        # Architecture documentation
├── api.md            # API reference
├── contributing.md   # This file
├── changelog.md      # Version history
└── faq.md           # Troubleshooting guide

bin/                   # CLI entry points
└── bell-system       # Main executable

examples/              # Usage demonstrations
└── *.py              # Example scripts
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
- **Profile performance** using included tools

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