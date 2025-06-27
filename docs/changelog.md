# Changelog

All notable changes to the Bell System UNIX V7 Terminal Simulation project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-19

### Added
- Complete repository refactoring to professional CLI-only structure
- New `bin/bell-system` CLI entry point with argument parsing
- Comprehensive Python package structure with `src/` organization
- Professional documentation suite in `docs/` directory
- GitHub CI/CD workflows for automated testing and linting
- Pre-commit hooks for code quality enforcement
- Example scripts demonstrating usage patterns
- API documentation with comprehensive code examples
- Performance profiling and optimization tools
- Enhanced logging system with structured output

### Changed
- **BREAKING**: Converted from Node.js wrapper to pure Python CLI application
- **BREAKING**: Moved all source code to `src/` directory structure
- **BREAKING**: Changed entry point from `npm run dev` to `bell-system` command
- Updated documentation to reflect CLI-only architecture
- Improved code organization following Python package standards
- Enhanced error handling and user experience

### Removed
- All Node.js dependencies and web framework components (337 packages)
- Web server infrastructure (`server/index.ts`)
- React and UI library dependencies
- Legacy Python files (`v1_bell_system_unix.py`, `v1a_enhanced_bell_system.py`)
- Replit-specific configuration files
- Unused build and development tools

### Fixed
- Import duplication and circular dependency issues
- Type hint errors preventing application startup
- Code style inconsistencies across modules
- Memory leaks in long-running terminal sessions

### Security
- Removed potential web-based attack vectors
- Added input validation for all CLI arguments
- Implemented secure file path handling
- Added audit logging for security events

## [1.0.0] - 2024-11-01

### Added
- Initial Bell System UNIX V7 Terminal Simulation
- 12 authentic operational roles from 1978-1983 period
- 50+ period-accurate commands with historical validation
- Role-based access control system
- Comprehensive manual page system
- Interactive tutorial for Bell System operations
- Authentic shift briefings and operational procedures
- Historical Bell System terminology and workflows
- Command history and session management
- Professional logging and error tracking

### Documentation
- Complete user manual with operational procedures
- Command reference guide for all Bell System operations
- Historical context and background information
- Installation and setup instructions

## [0.1.0] - 2024-06-19

### Added
- Initial project setup and basic terminal framework
- Core Bell System role definitions
- Basic command processing engine
- Historical asset collection and documentation
- Development environment configuration

---

## Version History Summary

- **v2.0.0**: Professional CLI-only refactoring with comprehensive GitHub readiness
- **v1.0.0**: Complete Bell System simulation with 12 roles and historical accuracy
- **v0.1.0**: Initial development framework and asset collection

## Migration Notes

### Upgrading from v1.x to v2.0

**Breaking Changes:**
1. **Entry Point**: Use `bell-system` command instead of `npm run dev`
2. **Installation**: Install with `pip install -e .` instead of `npm install`
3. **File Structure**: Source code moved to `src/` directory

**Migration Steps:**
```bash
# Remove old installation
rm -rf node_modules/ package.json package-lock.json

# Install new CLI version
pip install -e .

# Update usage
bell-system                # instead of npm run dev
bell-system --tutorial     # new tutorial mode
bell-system --role 1      # direct role selection
```

**Preserved Features:**
- All 12 Bell System operational roles maintained
- Complete command set with historical accuracy
- Session management and command history
- Comprehensive logging and diagnostics
- Interactive tutorial system
- Historical documentation assets

For detailed technical changes, see the [API documentation](api.md) and [architecture overview](overview.md).