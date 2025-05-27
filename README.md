# Bell System UNIX V7 Terminal Simulation

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Unix%2FLinux%2FmacOS-lightgrey.svg)](https://github.com/)
[![Historical Accuracy](https://img.shields.io/badge/Historical%20Accuracy-1978--1983-green.svg)](https://github.com/)

> An authentic recreation of AT&T Bell System internal operations workstations from the transformative period of 1978-1983

## Table of Contents

- [Overview](#overview)
- [Historical Context](#historical-context)
- [Installation](#installation)
- [Enhanced Features (Version 2.1)](#enhanced-features-version-21)
- [Quick Start](#quick-start)
- [Operational Roles](#operational-roles)
- [Command Reference](#command-reference)
- [Bell System Practices](#bell-system-practices)
- [Project Documentation](#project-documentation)
- [Technical Architecture](#technical-architecture)
- [Contributing](#contributing)
- [Historical References](#historical-references)

## Overview

The Bell System UNIX V7 Terminal Simulation provides a historically accurate recreation of AT&T Bell System internal operations workstations from 1978-1983. This terminal-based simulation reproduces the experience of using original UNIX Version 7 systems with period-accurate commands, workflows, trouble tickets, and role-specific operations based on extensive Bell System Technical Journal documentation and authentic AT&T internal procedures.

### Key Features

- **12 Authentic Bell System Roles** with realistic daily workflows
- **50+ Period-Accurate Commands** with comprehensive functionality
- **Enhanced Terminal Experience** with professional UX improvements (Version 2.1)
- **Command History Navigation** with up/down arrow support
- **Smart Command Aliases** for improved efficiency (h=help, st=status, rad=radio)
- **Intelligent Error Handling** with helpful suggestions and examples
- **Professional Logging System** with dynamic verbosity control
- **Authentic Equipment Simulation** including 3A Central Control, 5ESS, TH-3 microwave, TNDS
- **Historical Bell System Practices** integration with real BSP procedures
- **Comprehensive Documentation** with authentic technical specifications
- **Terminal-Only Interface** maintaining period authenticity

## Historical Context

This simulation represents Bell System operations during the critical period of 1978-1983, when the company was:

- Transitioning from electromechanical to electronic switching systems
- Deploying the revolutionary 5ESS Electronic Switching System
- Operating the world's largest telecommunications network
- Preparing for the landmark 1984 divestiture
- Advancing UNIX development through the Programmer's Workbench (PWB)

The simulation incorporates authentic Bell System equipment, procedures, and terminology from this transformative period in telecommunications history.

## Installation

### Requirements

- **Python 3.6 or higher**
- **Terminal emulator** supporting ANSI escape sequences
- **Unix-like operating system** (Linux, macOS, BSD) or Windows with WSL

### Setup

1. **Clone or download the repository:**
   ```bash
   git clone <repository-url>
   cd bell-system-unix-simulation
   ```

2. **Verify Python installation:**
   ```bash
   python3 --version
   ```

3. **Run the simulation:**
   ```bash
   # Standard version
   python3 bell.py
   
   # Enhanced version (recommended)
   python3 enhanced_bell_system.py
   
   # Interactive tutorial
   python3 bell_system_tutorial.py
   ```

No additional dependencies or configuration files are required.

## Enhanced Features (Version 2.1)

The enhanced version includes professional-grade improvements while maintaining complete historical authenticity:

### User Experience Enhancements
- **Command History Navigation**: Use up/down arrows to browse previous commands
- **Smart Command Aliases**: Quick shortcuts like `h` for help, `st` for status, `rad` for radio
- **Intelligent Error Recovery**: "Did you mean..." suggestions for typos and unknown commands
- **Enhanced Error Messages**: Detailed suggestions with examples and troubleshooting tips
- **Command Line Editing**: Full readline support with left/right arrow movement and backspace

### Professional Logging System
- **Structured Logging**: Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Dynamic Verbosity Control**: Change logging detail with `verbosity DEBUG/INFO/WARNING` command
- **Automatic Log Rotation**: Size-based rotation (10MB main, 5MB errors) with backup files
- **Session Analytics**: Comprehensive command timing and usage statistics
- **Error Summaries**: Use `errors` command to see recent issues with solutions

### Advanced Features
- **Automatic Changelog**: System tracks significant events and system changes
- **Performance Monitoring**: Command execution timing and session metrics
- **JSON Structured Logs**: Machine-readable session logs for analysis
- **Professional Cleanup**: Automatic log compression and state management

### New Commands
- **`errors`**: Display recent error summary with solutions and troubleshooting guidance
- **`verbosity [LEVEL]`**: Dynamically change logging detail level at runtime
- **`history [N]`**: Show command history with optional count limit
- **Enhanced `help`**: Reorganized with role-specific guidance and better categorization

## Quick Start

### Standard Version
1. **Start the original simulation:**
   ```bash
   python3 bell.py
   ```

### Enhanced Version (Recommended)
1. **Start the enhanced terminal with professional features:**
   ```bash
   python3 enhanced_bell_system.py
   ```

### Interactive Tutorial (For New Users)
1. **Learn the system with guided tutorial:**
   ```bash
   python3 bell_system_tutorial.py
   ```

### Using the Simulation
2. **Select your Bell System role** from the menu (1-12)

3. **Review your shift briefing** with role-specific procedures

4. **Enter commands** at the Unix-style prompt:
   ```
   sysop@bell-ops:/usr/users/sysop$ help              # Show available commands
   sysop@bell-ops:/usr/users/sysop$ man trunk         # Display manual page for trunk command
   sysop@bell-ops:/usr/users/sysop$ trunk status      # Check trunk group status
   sysop@bell-ops:/usr/users/sysop$ 3a diagnostics    # Run 3A Central Control diagnostics
   ```

5. **Use enhanced features (Enhanced Version only):**
   ```
   sysop@bell-ops:/usr/users/sysop$ h                 # Quick help (alias)
   sysop@bell-ops:/usr/users/sysop$ st                # Status (alias)
   sysop@bell-ops:/usr/users/sysop$ errors            # View error summary
   sysop@bell-ops:/usr/users/sysop$ verbosity DEBUG   # Change logging level
   sysop@bell-ops:/usr/users/sysop$ history 20        # Show command history
   ```

6. **Exit the simulation:**
   ```
   sysop@bell-ops:/usr/users/sysop$ quit
   ```
   or press `Ctrl+C`

## Operational Roles

The simulation offers 12 authentic Bell System operational roles, each with specific responsibilities and command access:

### 1. UNIX Systems Operator
**Primary Responsibilities:**
- System maintenance and monitoring
- UUCP network operations  
- Programmer's Workbench (PWB) environment management
- User account administration

**Key Commands:** `ps`, `df`, `who`, `uucp`, `mail`, `pwb`, `rje`

**Daily Tasks:**
- Monitor system performance and resource utilization
- Manage UUCP mail queues and file transfers
- Coordinate with development teams using PWB tools
- Perform system backups and maintenance procedures

### 2. Switching Station Technician  
**Primary Responsibilities:**
- Telephone switching equipment management
- Electronic and electromechanical system maintenance
- Alarm monitoring and response
- System cutover coordination

**Key Commands:** `trunk`, `switch`, `testboard`, `toll`, `crossbar`, `alarm`, `5ess`, `3a`

**Daily Tasks:**
- Monitor switching system performance and alarms
- Perform routine diagnostic tests on 3A Central Control
- Coordinate equipment maintenance windows
- Analyze traffic patterns and system utilization

### 3. Field Support Liaison
**Primary Responsibilities:**
- Coordinate field technicians and central office operations
- Emergency response coordination
- Service provisioning support
- Customer service issue escalation

**Key Commands:** `trace`, `dialtone`, `emergency`, `ticket`, `provision`, `sarts`

**Daily Tasks:**
- Dispatch field technicians for service calls
- Coordinate emergency response procedures
- Track trouble ticket resolution progress
- Interface between field operations and central office

### 4. National NOC Analyst
**Primary Responsibilities:**
- Network operations center monitoring
- Critical incident management
- Inter-office trunk coordination
- National network status reporting

**Key Commands:** `trunk`, `emergency`, `switch`, `ticket`, `traffic`, `tnds`, `satellite`

**Daily Tasks:**
- Monitor national network status and performance
- Coordinate response to major service outages
- Analyze inter-office traffic patterns
- Generate network performance reports

### 5. Traffic Service Position System (TSPS) Operator
**Primary Responsibilities:**
- Operator-assisted call completion
- Directory assistance services
- Collect call processing
- Customer billing verification

**Key Commands:** `tsps`, `operator`, `directory`, `collect`, `billing`

**Daily Tasks:**
- Handle operator-assisted domestic and international calls
- Provide directory assistance and information services
- Process collect and third-party billing calls
- Monitor TSPS system performance and position utilization

### 6. Database Administrator
**Primary Responsibilities:**
- Customer records and network configuration data
- Database maintenance and optimization
- Service order data management
- Billing system coordination

**Key Commands:** `dbquery`, `custdb`, `billing`, `netdb`, `service`

**Daily Tasks:**
- Maintain customer database integrity and performance
- Process service order database updates
- Coordinate with billing systems for accuracy
- Generate customer and network configuration reports

### 7. Network Planning Engineer
**Primary Responsibilities:**
- Network design and capacity planning
- Traffic forecasting and analysis
- Route optimization studies
- Economic analysis of network investments

**Key Commands:** `netplan`, `traffic`, `routing`, `capacity`, `billing`, `tnds`

**Daily Tasks:**
- Analyze traffic growth patterns and capacity requirements
- Develop network expansion and optimization plans
- Conduct economic studies for capital investments
- Coordinate with engineering teams on network design

### 8. Customer Service Interface Technician
**Primary Responsibilities:**
- Service order processing and management
- Customer provisioning coordination
- Service installation tracking
- Customer billing support

**Key Commands:** `service`, `provision`, `billing`, `custdb`, `directory`

**Daily Tasks:**
- Process new service orders and service changes
- Coordinate service installation with field technicians
- Track service order completion and customer notification
- Resolve customer billing inquiries and service issues

### 9. Radio/Microwave Technician
**Primary Responsibilities:**
- TH-3 microwave system monitoring and maintenance
- Radio path performance analysis
- Satellite communication link management
- Propagation analysis and optimization

**Key Commands:** `radio`, `microwave`, `propagation`, `antenna`, `fade`, `satellite`

**Daily Tasks:**
- Monitor TH-3 microwave network performance
- Analyze radio path fade events and diversity switching
- Perform preventive maintenance on radio equipment
- Coordinate satellite link operations and performance

### 10. Total Network Data System (TNDS) Analyst
**Primary Responsibilities:**
- Network traffic data collection and analysis
- Performance measurement and reporting
- Capacity planning data preparation
- Traffic forecasting model development

**Key Commands:** `tnds`, `netdata`, `analysis`, `forecast`, `modeling`, `traffic`

**Daily Tasks:**
- Collect and process network traffic measurement data
- Generate traffic analysis reports for network planning
- Develop traffic forecasting models and projections
- Monitor network performance against engineering objectives

### 11. SARTS (Special Service Testing) Technician
**Primary Responsibilities:**
- Remote testing of special service circuits
- T1 carrier and data circuit validation
- Customer circuit troubleshooting
- Special service provisioning support

**Key Commands:** `sarts`, `remote`, `special`, `testing`, `circuits`, `provision`

**Daily Tasks:**
- Perform remote testing of customer special service circuits
- Validate T1 carrier and digital circuit performance
- Troubleshoot circuit problems and coordinate repairs
- Support special service order provisioning and turn-up

### 12. Document Preparation Specialist
**Primary Responsibilities:**
- Technical documentation preparation using UNIX tools
- Bell System Practices (BSP) development and maintenance
- Training material creation
- Engineering documentation support

**Key Commands:** `nroff`, `troff`, `tbl`, `eqn`, `pic`, `refer`, `pwb`

**Daily Tasks:**
- Prepare technical documentation using UNIX text processing tools
- Develop and maintain Bell System Practices procedures
- Create training materials and technical illustrations
- Support engineering teams with documentation requirements

## Command Reference

### Core Network Operations Commands

#### Switching Systems
- **`3a`** - 3A Central Control switching system operations
- **`5ess`** - 5ESS Electronic Switching System operations  
- **`crossbar`** - Crossbar switching system controls
- **`switch`** - General switching center management

#### Network Monitoring
- **`trunk`** - Trunk group monitoring and management
- **`traffic`** - Network traffic analysis and monitoring
- **`tnds`** - Total Network Data System operations
- **`alarm`** - Central office alarm monitoring

#### Testing and Maintenance
- **`sarts`** - Special service remote testing
- **`testboard`** - Line testing equipment operations
- **`lmos`** - Loop Maintenance Operations System
- **`coer`** - Central Office Equipment Reports

#### Transmission Systems
- **`radio`** - TH-3 microwave radio system management
- **`microwave`** - Microwave propagation analysis
- **`satellite`** - Satellite communication links

#### Service Operations
- **`tsps`** - Traffic Service Position System
- **`operator`** - Operator services management
- **`directory`** - Directory assistance operations
- **`billing`** - Customer billing and toll charges

#### Network Planning
- **`netplan`** - Network planning and optimization
- **`capacity`** - Capacity planning and utilization
- **`routing`** - Call routing and path analysis
- **`forecast`** - Traffic and capacity forecasting

### Document Preparation Commands

#### Text Processing
- **`nroff`** - Document formatting (terminal output)
- **`troff`** - Typesetting (phototypesetter output)
- **`tbl`** - Table formatting preprocessor
- **`eqn`** - Mathematical equation formatting
- **`pic`** - Picture drawing language
- **`refer`** - Bibliography and reference management

### System Commands

#### UNIX Utilities
- **`ps`** - Display running processes
- **`who`** - Show logged-in users
- **`df`** - Display filesystem usage
- **`ls`** - List directory contents
- **`pwd`** - Print working directory
- **`date`** - Display system date and time

#### Communication
- **`uucp`** - UNIX-to-UNIX Copy operations
- **`mail`** - Electronic mail system

#### Help and Documentation
- **`help`** - Display available commands
- **`man`** - Display manual pages
- **`bsp`** - Bell System Practices reference

### Example Usage

```bash
# Check switching system status
bell$ 3a status
bell$ 5ess diagnostics

# Monitor network traffic
bell$ trunk status
bell$ traffic analysis
bell$ tnds collect

# Perform testing procedures
bell$ sarts test T1-001
bell$ lmos test 555-1234

# Network planning activities
bell$ netplan project NP-8301
bell$ capacity planning
bell$ forecast traffic

# Document preparation
bell$ nroff -ms document.ms
bell$ tbl table.tbl | nroff -ms
bell$ pic diagram.pic | troff -ms
```

## Bell System Practices

The simulation incorporates authentic Bell System Practices (BSP) numbering and procedures:

### BSP Section Organization
- **BSP 100-000 series** - Bell System Fundamentals
- **BSP 200-000 series** - Switching Systems  
- **BSP 300-000 series** - Transmission Systems
- **BSP 400-000 series** - Network Operations
- **BSP 500-000 series** - Customer Services
- **BSP 600-000 series** - UNIX and Computing Systems
- **BSP 700-000 series** - Electronic Switching (5ESS)
- **BSP 800-000 series** - TSPS Operations
- **BSP 900-000 series** - TNDS and Data Systems

### Project Numbering System
- **NP-XXXX** - Network Planning projects
- **TP-XXXX** - Technical/Technology projects  
- **OP-XXXX** - Operations projects
- **AC-XXXX** - Area Code implementation projects
- **RE-XXXX** - Route Enhancement projects
- **CP-XXXX** - Capacity Planning projects

### Work Order System
Work orders use format **WO-XXXXX** for tracking operational activities:
- WO-83047 - Route diversity analysis NYC-WAS corridor
- WO-83048 - Electronic switching capacity planning
- WO-83049 - Rural exchange modernization study

## Project Documentation

### Shift Events and Workflows

The simulation generates authentic Bell System operational events including:

- **Equipment Alarms** - Major/minor alarms with appropriate response procedures
- **Traffic Overloads** - Seasonal and special event traffic management
- **Service Outages** - Coordinated response and restoration procedures  
- **Maintenance Windows** - Scheduled equipment maintenance coordination
- **Emergency Situations** - Disaster response and business continuity
- **Training Activities** - Ongoing education and skill development

### Historical Equipment Integration

#### Electronic Switching Systems
- **1ESS** - First generation electronic switching (legacy)
- **2ESS** - Toll electronic switching system
- **3ESS** - Local electronic switching system
- **4ESS** - Long distance toll switching
- **5ESS** - Advanced electronic switching (new deployment)

#### Transmission Systems
- **TH-3 Microwave** - 6GHz digital radio system
- **T1 Carrier** - Digital transmission system
- **Satellite Links** - Domestic satellite communications
- **Crossbar Systems** - Electromechanical switching (legacy support)

#### Support Systems
- **3A Central Control** - Common control processor
- **TNDS** - Total Network Data System
- **SARTS** - Special Service Testing System
- **TSPS** - Traffic Service Position System

## Technical Architecture

### Code Organization

```
Project Structure:
├── bell.py                        # Original Bell System terminal simulation
├── enhanced_bell_system.py        # Enhanced version with UX improvements (v2.1)
├── bell_system_tutorial.py        # Interactive tutorial for new users
├── logging_enhancements.py        # Professional logging system module
├── ux_command_enhancements.py     # Advanced UX enhancement engine
├── performance_profiling.py       # Performance monitoring tools
├── logging_diagnostics.py         # Diagnostics and analysis tools
├── command_reference.txt          # Complete command cheat sheet
├── changelog.txt                  # Version history and changes
├── manual.txt                     # Comprehensive user manual
├── security_audit.md              # Security guidelines and audit
├── ux_improvements.md             # UX enhancement documentation
└── logs/                          # Generated log files and session data
    ├── bell_system_main.log       # Main application logs
    ├── bell_system_errors.log     # Error-specific logs
    ├── session_*.log              # Individual session logs
    └── bell_system_history.txt    # Command history

Core Components:
├── BellSystemTerminal             # Primary simulation class
├── BellSystemEnhancedTerminal     # Enhanced version with UX features
├── BellSystemLogger               # Professional logging system
├── CommandEnhancementEngine       # Smart command assistance
├── Role Management                # 12 authentic Bell System roles
├── Command Processing             # 50+ period-accurate commands
├── Event Generation               # Realistic operational events
├── Documentation System           # Comprehensive man pages
└── Historical Data                # Authentic Bell System procedures
```

### Key Design Principles

1. **Historical Accuracy** - All commands, procedures, and data based on authentic Bell System documentation
2. **Terminal Authenticity** - Pure text-based interface maintaining 1978-1983 period accuracy
3. **Role-Based Access** - Commands and functionality appropriate to specific Bell System roles
4. **Comprehensive Documentation** - Complete man page system with cross-references
5. **Realistic Operations** - Authentic work flows, project numbers, and procedures

### Development Standards

- **Python 3.6+** compatibility for broad platform support
- **ANSI Terminal** support for authentic display formatting
- **Modular Design** with clear separation of concerns
- **Comprehensive Testing** of all commands and sub-commands
- **Documentation-Driven** development with authentic references

## Contributing

### Guidelines for Enhancement

1. **Historical Accuracy** - All additions must be based on authentic Bell System documentation
2. **Period Appropriateness** - Technology and procedures must be consistent with 1978-1983 timeframe
3. **Documentation Standards** - All new commands require comprehensive man pages
4. **Code Quality** - Follow existing patterns and maintain Python coding standards

### Suggested Improvements

- Additional authentic Bell System roles (e.g., Engineering Administrator, Training Coordinator)
- Enhanced UNIX V7 command implementations
- Additional Bell System Practices integration
- Expanded trouble ticket workflows
- Enhanced network planning tools

### Documentation Sources

Contributions should reference authentic Bell System documentation including:
- Bell System Technical Journal articles
- Engineering and Operations in the Bell System
- Bell System Repair Specifications
- UNIX System documentation from Bell Labs
- Western Electric equipment specifications

## Historical References

This simulation is based on extensive authentic Bell System documentation:

### Primary Sources
- **Bell System Technical Journal** - Technical articles 1976-1983
- **Engineering and Operations in the Bell System** (2nd ed, 1984)
- **Bell System Repair Specifications** (BSRS 104.011)
- **UNIX System documentation** - Bell Laboratories versions
- **3A Central Control circuit descriptions** (SD-1C900-01)

### Technical Documentation
- **Crossbar System Fundamentals** - Western Electric documentation
- **5ESS Electronic Switching System** - AT&T technical specifications
- **TH-3 Microwave Radio System** - Transmission engineering guides
- **TNDS System Specifications** - Network data collection procedures
- **SARTS Testing Procedures** - Special service circuit testing

### Operational Procedures
- **Bell System Practices** - Standard operating procedures
- **TSPS Operations Manual** - Traffic Service Position System
- **Network Operations Center** - NOC procedures and workflows
- **Emergency Response Procedures** - Disaster recovery and business continuity

### Historical Context
- **Telecommunications History** - Pre-divestiture Bell System operations
- **UNIX Development** - Bell Labs software development environment
- **Electronic Switching Evolution** - Transition from electromechanical systems
- **Network Planning Methodologies** - 1970s-1980s engineering practices

---

**Bell System UNIX V7 Terminal Simulation**  
*Version 2.0 - November 2024*

*Based on authentic AT&T Bell System documentation 1978-1983*

*For educational and historical preservation purposes*