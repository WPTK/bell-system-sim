# Bell System UNIX V7 Terminal Simulation

## Overview

This repository contains a historically accurate recreation of AT&T Bell System internal operations workstations from the transformative period of 1978-1983. The simulation provides an authentic terminal-based experience of Bell System operations, featuring 12 operational roles, 50+ period-accurate commands, and comprehensive Bell System workflows.

The application is primarily built in Python with a focus on terminal-based interaction, maintaining historical authenticity while providing modern enhancements like command history, structured logging, and comprehensive error handling.

## System Architecture

### Core Components
- **Python-based Terminal Simulation**: Main application built with Python 3.6+ using terminal-based interaction
- **Multi-role Authentication System**: 12 authentic Bell System operational roles with role-based command access
- **Command Processing Engine**: Comprehensive command system with aliases, validation, and historical accuracy
- **Event and Ticket Management**: Authentic Bell System trouble ticket and shift event systems
- **Logging and Diagnostics**: Professional-grade logging with rotation and error tracking

### Development Environment
- **Replit Configuration**: Node.js 20 environment with direct Python execution through server wrapper
- **Terminal-Only Interface**: No web interface - direct terminal interaction only
- **Python Execution**: Node.js wrapper spawns Python 3 process with inherited stdio for terminal access

## Key Components

### Primary Application Files
- `bell.py`: Main Bell System terminal simulation with complete functionality
- `main.py`: Alternative Unix terminal implementation
- `unix_terminal.py`: Four-role simplified Bell System terminal
- `bell_system_tutorial.py`: Interactive tutorial system for new users

### Enhancement Modules
- `logging_enhancements.py`: Advanced logging system with structured output and rotation
- `performance_profiling.py`: Performance analysis and optimization tools
- `ux_command_enhancements.py`: User experience improvements and command assistance
- `comprehensive_test_suite.py`: Automated testing framework for command validation

### Documentation and Reference
- `manual.txt`: Complete user manual and documentation
- `command_reference.txt`: Command reference cheat sheet
- `changelog.txt`: Detailed version history and improvements
- Various historical Bell System documentation in `attached_assets/`

## Data Flow

### Command Processing Flow
1. User input received through terminal interface
2. Command parsing and alias resolution
3. Role-based permission validation
4. Command execution with error handling
5. Structured logging and performance tracking
6. Response formatting and display

### Session Management
1. Role selection and authentication
2. Session initialization with unique ID generation
3. Command history tracking with readline integration
4. Structured logging throughout session
5. Graceful session termination and cleanup

### Event and Ticket System
1. Dynamic shift event generation based on Bell System operations
2. Authentic trouble ticket creation and management
3. Role-specific workflow integration
4. Historical data persistence and reporting

## External Dependencies

### Python Requirements
- **Core**: Python 3.6+ with standard library modules
- **Terminal Features**: readline module for command history and line editing
- **Logging**: Built-in logging with handlers for file rotation
- **System Integration**: os, sys, time, datetime for system interaction

### Node.js Environment (Development)
- **React Ecosystem**: Modern React with hooks, context, and routing
- **UI Components**: Radix UI component library for consistent interface
- **Styling**: Tailwind CSS with Vite integration
- **Database**: Drizzle ORM with potential PostgreSQL integration
- **Session Management**: Connect-pg-simple for session storage

### Development Tools
- **Build Tools**: Vite for development and production builds
- **TypeScript**: Full TypeScript support with type checking
- **Testing**: Comprehensive test suite with automated validation
- **Code Quality**: ESBuild for fast compilation and bundling

## Deployment Strategy

### Replit Autoscale Deployment
- **Target**: Autoscale deployment for automatic scaling
- **Build Command**: `npm run build` for production assets
- **Runtime**: `npm run start` for production execution
- **Development**: `npm run dev` for development mode with hot reload

### Application Architecture
- **Development Mode**: Python simulation runs independently on port 5000
- **Production Mode**: Integrated with Node.js backend for enhanced features
- **Database Integration**: Optional PostgreSQL integration for data persistence
- **Session Management**: Redis or PostgreSQL-based session storage

### Configuration Management
- **Environment Variables**: Separate development and production configurations
- **Port Management**: Automatic port mapping from 5000 to 80 for external access
- **Process Management**: Parallel workflow execution for development efficiency

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- June 19, 2025. Initial setup