# Contributing to Bell System UNIX V7 Terminal Simulation

Thank you for your interest in contributing to this historical recreation of Bell System operations! This project aims to maintain historical accuracy while providing an educational and nostalgic experience.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Node.js 20+ (for development environment)
- Basic understanding of UNIX systems and telecommunications history
- Familiarity with Bell System operations (helpful but not required)

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/bell-system-unix-v7.git
   cd bell-system-unix-v7
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Test the application:
   ```bash
   npm run dev
   ```

## Contributing Guidelines

### Historical Accuracy

This project prioritizes historical authenticity. When contributing:

- **Research First**: Use authentic Bell System documentation from the 1978-1983 period
- **Verify Terminology**: Ensure all technical terms match historical usage
- **Check Command Syntax**: Commands should reflect actual UNIX V7 and Bell System practices
- **Maintain Context**: Keep the operational environment authentic to the period

### Code Standards

#### Python Code
- Follow PEP 8 style guidelines
- Use descriptive variable names that reflect Bell System terminology
- Include docstrings for all functions and classes
- Maintain consistent indentation (4 spaces)

#### File Organization
- Keep related functionality in appropriate modules
- Maintain the existing file structure
- Document any new files in the project README

### Types of Contributions

#### 1. Historical Enhancements
- Adding authentic Bell System commands
- Expanding role-specific functionality
- Including period-accurate documentation
- Improving operational workflows

#### 2. Technical Improvements
- Bug fixes and error handling
- Performance optimizations
- Code refactoring for maintainability
- Enhanced logging and diagnostics

#### 3. Documentation
- User manual improvements
- Command reference updates
- Historical context additions
- Installation and setup guides

#### 4. Testing
- Unit tests for command functionality
- Integration tests for role workflows
- Historical accuracy validation
- Performance benchmarking

### Contribution Process

1. **Issue First**: For major changes, create an issue to discuss the proposal
2. **Branch Naming**: Use descriptive names like:
   - `feature/add-switching-commands`
   - `fix/role-authentication-bug`
   - `docs/update-installation-guide`
3. **Commit Messages**: Use clear, descriptive commit messages:
   - `Add authentic trunk testing commands for SARTS role`
   - `Fix command history persistence across sessions`
   - `Update manual with crossbar switching procedures`

### Testing Your Changes

Before submitting a pull request:

1. Run the test suite:
   ```bash
   python3 comprehensive_test_suite.py
   ```

2. Test your changes with multiple roles:
   ```bash
   python3 bell.py
   ```

3. Verify performance impact:
   ```bash
   python3 performance_profiling.py
   ```

4. Check logging functionality:
   ```bash
   # Review logs after testing
   cat logs/bell_system.log
   ```

### Pull Request Guidelines

#### PR Title Format
- Use clear, descriptive titles
- Include the type of change: `[FEATURE]`, `[FIX]`, `[DOCS]`, `[TEST]`
- Example: `[FEATURE] Add microwave link monitoring commands for Radio/Microwave Technician role`

#### PR Description Template
```
## Description
Brief description of changes and their purpose.

## Historical Context
How these changes maintain or enhance historical accuracy.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] I have tested these changes locally
- [ ] I have run the test suite
- [ ] I have tested with multiple user roles
- [ ] I have verified historical accuracy

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
```

### Historical Resources

When researching for contributions, consider these authentic sources:

- Bell System Technical Journal archives
- UNIX V7 system documentation
- AT&T Bell Laboratories technical manuals
- Historical telecommunications engineering documents
- Period-appropriate training materials

### Code Review Process

All contributions go through code review to ensure:

1. **Historical Accuracy**: Changes align with Bell System practices
2. **Code Quality**: Follows project standards and best practices
3. **Functionality**: New features work correctly across all roles
4. **Documentation**: Changes are properly documented
5. **Testing**: Adequate test coverage is maintained

### Questions and Support

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for general questions
- **Historical Questions**: Include relevant documentation sources when asking about Bell System practices

### Recognition

Contributors who make significant improvements to the project will be recognized in the project README and changelog. We particularly value contributions that enhance historical accuracy and educational value.

## Thank You

Your contributions help preserve and share the fascinating history of Bell System operations and early UNIX systems. Every authentic detail you add helps create a more immersive and educational experience for users interested in telecommunications and computing history.