#!/usr/bin/env python3
"""
Bell System UNIX V7 Terminal Simulation
========================================

A historically accurate simulation of AT&T Bell System internal operations
workstations from the transformative period of 1978-1983.

This module provides an authentic recreation of Bell System operations based on
extensive documentation from the Bell System Technical Journal, Engineering and
Operations manuals, and authentic AT&T internal procedures from the
pre-divestiture era.

Features:
    - 12 authentic Bell System operational roles
    - 50+ period-accurate commands with comprehensive functionality
    - Authentic shift briefings and operational procedures
    - Historical Bell System terminology and workflows
    - Role-based command access control
    - Comprehensive manual page system
    - Terminal-only interface maintaining period authenticity

Author: Bell System Operations Simulation Project
Version: 2.0
Date: November 2024
"""

import logging
import logging.handlers
import os
import random
import sys
import time
from collections import defaultdict, deque
from datetime import timedelta
from typing import Dict, List, Optional, Any

from .constants import (
    BELL_SYSTEM_ROLES,
    UNIMPLEMENTED_COMMANDS,
)
from .clock import SimClock
from .console import render
from .data import geography
from .data.man_pages import MAN_PAGES
from .progression import (
    DIFFICULTIES,
    QUALIFICATIONS_BY_KEY,
    ROLE_QUALIFICATIONS,
    Career,
    career_path,
)
from .routing import build_default_network
from .screens.customer import CustomerCommands
from .screens.frame import FrameCommands
from .screens.radio import RadioCommands
from .screens.ticket_generation import TicketGeneration
from .screens.unix import UnixCommands
from .screens.bureau import BureauCommands
from .screens.carrier import CarrierCommands
from .screens.documents import DocumentCommands
from .screens.shift import ShiftCommands
from .screens.switching import SwitchingCommands
from .screens.testing import TestingCommands
from .screens.tickets import TicketCommands
from .screens.tnds import TndsCommands
from .screens.toll import TollCommands
from .screens.traffic import TrafficCommands
from .screens.trunks import TrunkCommands
from .screens.tsps import TspsCommands
from .settings import (
    OPTIONS,
    OPTIONS_BY_KEY,
    Settings,
    settings_path,
    state_dir,
)
from .types import (
    Alarm,
    CentralOffice,
    CrossbarSystem,
    SystemHealth,
    TrunkGroup,
)

readline: Optional[Any]
try:
    import readline as _readline  # For command history and line editing

    readline = _readline
    READLINE_AVAILABLE = True
except ImportError:  # pragma: no cover - readline is absent on stock Windows
    readline = None
    READLINE_AVAILABLE = False










class BellSystemTerminal(
    CarrierCommands,
    SwitchingCommands,
    TndsCommands,
    TspsCommands,
    TrafficCommands,
    TicketCommands,
    TrunkCommands,
    TollCommands,
    TestingCommands,
    BureauCommands,
    ShiftCommands,
    DocumentCommands,
    RadioCommands,
    TicketGeneration,
    CustomerCommands,
    FrameCommands,
    UnixCommands,
):
    """
    Main Bell System UNIX V7 Terminal Simulation Class.

    Provides a historically accurate simulation of Bell System operations
    during 1978-1983, including authentic commands, procedures, and workflows.
    """

    # Enhanced command aliases for improved user experience
    COMMAND_ALIASES = {
        # Traditional UNIX aliases
        'h': 'help',
        '?': 'help',
        'q': 'quit',
        'exit': 'quit',
        'logout': 'quit',
        'clear': 'clear',

        # Bell System operation aliases
        'st': 'status',
        'stat': 'status',
        'tst': 'test',
        'chk': 'test',
        'alm': 'alarm',
        'alert': 'alarm',
        'options': 'set',
        'settings': 'set',
        'config': 'set',

        # Repair service bureau
        'rsb': 'report',
        'board': 'report',
        'reports': 'report',
        'career': 'qual',
        'index': 'qual',
        'ow': 'orderwire',
        'tl': 'testline',
        'tc': 'testcall',
        'call': 'testcall',
        'loop': 'mlt',

        # Technical system aliases
        'rad': 'radio',
        'mw': 'microwave',
        't1': 't1carrier',
        'ds1': 't1carrier',
        'lc': 'lcarrier',
        'coax': 'lcarrier',
        'mult': 'multiplex',
        'mux': 'multiplex',
        'regen': 'regenerator',
        'reg': 'regenerator',

        # Directory and file aliases
        'll': 'ls',
        'la': 'ls',
        'dir': 'ls',

        # System monitoring aliases
        'proc': 'ps',
        'users': 'who',
        'w': 'who',
        'disk': 'df',

        # Bell System specific shortcuts
        'bsp': 'bsp',
        'practices': 'bsp',
        'tnds': 'tnds',
        'sarts': 'sarts',
        'tsps': 'tsps',
        'toll': 'toll',
        'trace': 'trace',
        'route': 'routing',
        'cap': 'capacity',
        'traf': 'traffic',
        'bill': 'billing',
        'cust': 'custdb',
        'db': 'dbquery',
        'net': 'netplan',
        'switch': 'switch',
        'trunk': 'trunk',
        'crossbar': 'crossbar',
        'events': 'events',
        'handoff': 'handoff',
        'tariff': 'tariff',
        'train': 'training',
        '5ess': '5ess',
        'western': 'western',
        'coer': 'coer',
        'lmos': 'lmos'
    }

    # Parsed geographic data, shared across instances in a process. It is
    # static reference data and never changes during a run.
    _NANPA_CACHE: Optional[Dict[str, Any]] = None
    _NANPA_DEGRADED: bool = False

    def __init__(self) -> None:
        """Initialize the Bell System terminal simulation environment."""
        # Settings and the clock come first: logging honours a setting, and
        # every piece of state initialised below stamps itself with the time.
        self.settings = Settings(settings_path(state_dir()))
        self.clock = SimClock(self.settings)

        # What the craftsperson carries between shifts, and how hard the
        # shift is. The setting is the authority: the career record stores a
        # copy so a shift resumed from disk starts the way it ended.
        self.career = Career(career_path(state_dir()))
        self.career.set_difficulty(self.settings.get('game.difficulty'))

        # Setup enhanced logging first
        self._setup_logging()
        self.logger = logging.getLogger('BellSystem')

        # Performance monitoring
        self._performance_log: Dict[str, Any] = {}
        self.session_start_time = time.time()
        self.session_id = f"BELL-{int(time.time())}-{os.getpid()}"
        self.failed_command_attempts = 0

        # Enhanced UX features - command history and error tracking
        self.command_history: deque = deque(maxlen=1000)
        self.command_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recent_errors: deque = deque(maxlen=50)
        self.log_verbosity = 'INFO'

        # Build the command dispatch table once, rather than per command.
        self._command_handlers = self._build_command_handlers()

        # Setup command history for readline if available
        if READLINE_AVAILABLE:
            self._setup_readline()

        # System environment
        self.current_directory: str = "/usr/users/sysop"
        self.username: str = "sysop"
        self.hostname: str = "mhuxco"
        self.shell: str = "/bin/sh"
        self.role: Optional[str] = None
        self.role_name: Optional[str] = None
        self.shift_events: List[Dict[str, Any]] = []
        self.current_shift: int = 1

        # Initialize Bell System environment
        # The toll network the routing engine searches.
        self.toll_network = build_default_network()
        self._initialize_frame_state()
        self._initialize_ticket_system()
        self._initialize_project_numbers()
        self._initialize_rate_structures()
        self._initialize_filesystem()
        self._initialize_processes()
        self._initialize_users()
        self._initialize_shift_handoff()
        self.man_pages = self._initialize_man_pages()

        # Initialize realistic system state management
        self._initialize_network_state()
        self._initialize_equipment_state()
        self._initialize_traffic_state()
        self._initialize_alarm_state()

        # Initialize geographic and infrastructure authenticity
        self._initialize_nanpa_data()
        self._initialize_bell_system_infrastructure()
        self._initialize_enhanced_ticket_system()

        # Generate initial shift events
        self.generate_shift_events()

        # The repair service bureau's board, and the other craft on the wire.
        self._initialize_repair_bureau()

    def _initialize_network_state(self) -> None:
        """Initialize dynamic network state for realistic simulation behavior."""

        # Trunk group states with realistic utilization patterns
        self.trunk_groups: Dict[str, TrunkGroup] = {
            "TG-001-NYC": {"capacity": 24, "utilization": random.randint(45, 85), "status": "ACTIVE", "route": "NYC-WAS", "quality": random.uniform(0.995, 0.999)},
            "TG-023-BOS": {"capacity": 96, "utilization": random.randint(60, 90), "status": "ACTIVE", "route": "NYC-BOS", "quality": random.uniform(0.992, 0.998)},
            "TG-045-PHL": {"capacity": 48, "utilization": random.randint(35, 75), "status": "ACTIVE", "route": "NYC-PHL", "quality": random.uniform(0.994, 0.999)},
            "TG-067-WAS": {"capacity": 72, "utilization": random.randint(40, 80), "status": "ACTIVE", "route": "WAS-ATL", "quality": random.uniform(0.996, 0.999)},
            "TG-089-CHI": {"capacity": 24, "utilization": random.randint(20, 60), "status": "ACTIVE", "route": "CHI-NYC", "quality": random.uniform(0.993, 0.998)},
            "TG-104-DET": {"capacity": 48, "utilization": 0, "status": "MAINT", "route": "DET-CHI", "quality": 0.000}
        }

        # Network performance metrics with time-based variation
        hour = self.clock.now().hour
        base_load = 40 + (30 * max(0, min(1, (hour - 8) / 8))) if 8 <= hour <= 16 else 25
        self.network_metrics = {
            "total_load": base_load + random.randint(-5, 15),
            "call_completion": random.uniform(0.975, 0.995),
            "setup_time": random.uniform(1.8, 2.4),
            "blocking_rate": random.uniform(0.001, 0.008),
            "revenue_hour": random.randint(45000, 95000),
            "peak_forecast": random.randint(850, 950)
        }

    def _initialize_equipment_state(self) -> None:
        """Initialize switching equipment states with realistic operational patterns."""
        import random

        # Electronic switching systems. Each machine is sited where its size
        # class belongs and rated within the traffic it could actually carry:
        # a No. 3 ESS was a rural community dial office switch of a few
        # thousand lines, not a metropolitan machine.
        self.switching_systems = {
            "1ESS-NYC-001": {"type": "1ESS", "status": "ACTIVE", "location": "New York, NY",
                             "load": random.randint(65, 85), "lines": random.randint(48000, 62000),
                             "calls_hour": random.randint(38000, 55000), "uptime": random.randint(720, 8760)},
            "1AESS-CHI-002": {"type": "1AESS", "status": "ACTIVE", "location": "Chicago, IL",
                              "load": random.randint(60, 85), "lines": random.randint(84000, 124000),
                              "calls_hour": random.randint(70000, 110000), "uptime": random.randint(720, 6570)},
            "2ESS-SUM-001": {"type": "2ESS", "status": "ACTIVE", "location": "Summit, NJ",
                             "load": random.randint(50, 75), "lines": random.randint(4200, 9400),
                             "calls_hour": random.randint(3400, 8600), "uptime": random.randint(168, 4380)},
            "3ESS-SEN-001": {"type": "3ESS", "status": "ACTIVE", "location": "Seneca, IL",
                             "load": random.randint(55, 80), "lines": random.randint(900, 4200),
                             "calls_hour": random.randint(700, 3800), "uptime": random.randint(336, 2190)},
            "4ESS-CHI-001": {"type": "4ESS", "status": "ACTIVE", "location": "Chicago, IL",
                             "load": random.randint(70, 90), "trunks": random.randint(38000, 52000),
                             "calls_hour": random.randint(180000, 300000), "uptime": random.randint(504, 6570)},
            "5ESS-SEN-002": {"type": "5ESS", "status": random.choice(["TESTING", "ACTIVE"]), "location": "Seneca, IL",
                             "load": random.randint(20, 45), "lines": random.randint(1800, 8000),
                             "calls_hour": random.randint(1500, 7000), "uptime": random.randint(72, 720)}
        }

        # Crossbar systems (legacy equipment)
        self.crossbar_systems: Dict[str, CrossbarSystem] = {
            "XB-NYC-003": {"status": "ACTIVE", "load": random.randint(40, 70), "maintenance_due": random.choice([True, False])},
            "XB-PHL-001": {"status": random.choice(["ACTIVE", "MAINT"]), "load": random.randint(0, 85), "maintenance_due": False},
            "XB-BOS-002": {"status": "ACTIVE", "load": random.randint(35, 65), "maintenance_due": random.choice([True, False])}
        }

    def _initialize_traffic_state(self) -> None:
        """Initialize traffic patterns with realistic time-based variations."""

        hour = self.clock.now().hour
        day_of_week = self.clock.now().weekday()  # 0=Monday, 6=Sunday

        # Business hours traffic multiplier
        if 8 <= hour <= 17 and day_of_week < 5:  # Business hours, weekday
            traffic_multiplier = 1.0 + random.uniform(0.2, 0.4)
        elif 17 <= hour <= 21:  # Evening hours
            traffic_multiplier = 0.7 + random.uniform(0.1, 0.3)
        elif day_of_week >= 5:  # Weekend
            traffic_multiplier = 0.4 + random.uniform(0.1, 0.2)
        else:  # Overnight
            traffic_multiplier = 0.2 + random.uniform(0.05, 0.15)

        base_calls = 850000  # Base daily call volume
        self.traffic_data = {
            "current_calls": int(base_calls * traffic_multiplier / 24),
            "calls_today": random.randint(780000, 920000),
            "peak_hour_calls": random.randint(45000, 65000),
            "avg_duration": random.uniform(3.8, 4.6),
            "completion_rate": random.uniform(0.975, 0.995),
            "revenue_today": random.randint(450000, 650000),
            "international_pct": random.uniform(0.08, 0.15),
            "toll_pct": random.uniform(0.35, 0.45)
        }

        # Regional distribution with realistic patterns
        self.regional_traffic = {
            "northeast": {"calls": int(self.traffic_data["current_calls"] * 0.38), "revenue": random.randint(180000, 250000)},
            "southeast": {"calls": int(self.traffic_data["current_calls"] * 0.28), "revenue": random.randint(120000, 180000)},
            "central": {"calls": int(self.traffic_data["current_calls"] * 0.22), "revenue": random.randint(95000, 140000)},
            "west": {"calls": int(self.traffic_data["current_calls"] * 0.12), "revenue": random.randint(55000, 85000)}
        }

    def _initialize_alarm_state(self) -> None:
        """Initialize alarm system with realistic fault conditions."""
        import random

        # Generate realistic alarm conditions
        possible_alarms = [
            {"id": "AL-4472", "type": "TRUNK_DEGRADED", "severity": "MINOR", "system": "TG-004", "description": "Intermittent failures on trunk group"},
            {"id": "AL-4473", "type": "MEMORY_PARITY", "severity": "MAJOR", "system": "3A-CCU-D", "description": "Central control memory parity errors"},
            {"id": "AL-4474", "type": "CARRIER_LOSS", "severity": "CRITICAL", "system": "T1-PENTAGON", "description": "Loss of carrier signal"},
            {"id": "AL-4475", "type": "POWER_SUPPLY", "severity": "MINOR", "system": "PWR-NYC-002", "description": "Backup power supply voltage low"},
            {"id": "AL-4476", "type": "RADIO_FADE", "severity": "MAJOR", "system": "TH3-CHI-007", "description": "Microwave path experiencing excessive fade"}
        ]

        # Randomly select active alarms based on time and conditions
        self.active_alarms: List[Alarm] = []
        for candidate in possible_alarms:
            if random.random() < 0.3:  # 30% chance each alarm is active
                alarm: Alarm = dict(candidate)  # type: ignore[assignment]
                alarm["timestamp"] = (self.clock.now()
                                      - timedelta(minutes=random.randint(5, 480)))
                alarm["acknowledged"] = random.choice([True, False])
                self.active_alarms.append(alarm)

        # System health metrics
        self.system_health: SystemHealth = {
            "overall_status": "OPERATIONAL" if len(self.active_alarms) < 3 else "DEGRADED",
            "critical_alarms": len([a for a in self.active_alarms if a["severity"] == "CRITICAL"]),
            "major_alarms": len([a for a in self.active_alarms if a["severity"] == "MAJOR"]),
            "minor_alarms": len([a for a in self.active_alarms if a["severity"] == "MINOR"]),
            "uptime_days": random.randint(45, 365),
            "last_outage": self.clock.now() - timedelta(days=random.randint(7, 90))
        }

        # Log successful initialization
        self.logger.info(f"Bell System Terminal initialized - Session {self.session_id}")

    def _setup_logging(self) -> None:
        """Setup comprehensive logging system with rotation."""
        log_dir = state_dir()

        # Setup main logger
        logger = logging.getLogger('BellSystem')
        logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'bell_system.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)

        # Diagnostic records carry ISO timestamps and file:line references,
        # which no 1983 terminal would emit. They go to the log file only
        # unless a player turns the console channel on for debugging.
        console_handler = logging.StreamHandler()
        if self.settings.is_on('display.log_console'):
            console_handler.setLevel(logging.WARNING)
        else:
            console_handler.setLevel(logging.CRITICAL + 1)

        # Detailed formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    def _setup_readline(self) -> None:
        """Setup readline for command history and editing."""
        if readline is None:  # pragma: no cover - readline is present here
            return
        try:
            # Load command history if it exists
            history_file = os.path.join(state_dir(), 'bell_system_history.txt')
            if os.path.exists(history_file):
                readline.read_history_file(history_file)

            # Set history length
            readline.set_history_length(1000)

            # Complete Bell System commands, not host filesystem paths.
            readline.set_completer(self._complete_command)
            readline.set_completer_delims(' \t\n')
            readline.parse_and_bind('tab: complete')

            self.history_file = history_file
            self.logger.debug("Readline setup completed successfully")

        except Exception as e:
            self.logger.warning(f"Could not setup readline: {e}")
            self.history_file = ''

    def _handle_command_error(self, command: str, error_msg: str) -> str:
        """Enhanced error handling with suggestions."""
        self.error_counts[command] += 1
        self.recent_errors.append({
            'command': command,
            'error': error_msg,
            'timestamp': self.clock.now(),
            'count': self.error_counts[command]
        })

        self.logger.warning(f"Command error: {command} - {error_msg}")

        # Generate helpful response
        response = f"Error: {error_msg}\n"

        # Add suggestions based on command
        suggestions = self._get_command_suggestions(command)
        if suggestions:
            response += "\nDid you mean:\n"
            for suggestion in suggestions[:3]:  # Limit to 3 suggestions
                response += f"  • {suggestion}\n"

        # Add general help for repeated errors
        if self.error_counts[command] > 2:
            response += f"\nHint: Type 'help' for available commands or 'man {command}' for detailed help.\n"
            response += "Type 'errors' to see recent error summary.\n"

        return response

    def _get_command_suggestions(self, command: str) -> List[str]:
        """Get command suggestions based on failed command."""
        suggestions = []

        # Check aliases first
        all_commands = list(self.COMMAND_ALIASES.keys())

        # Simple fuzzy matching (commands that start with same letters)
        if len(command) >= 2:
            prefix_matches = [cmd for cmd in all_commands
                             if cmd.startswith(command[:2]) and cmd != command]
            suggestions.extend(prefix_matches[:2])

        # Common typo corrections
        typo_corrections = {
            'hlep': 'help',
            'quti': 'quit',
            'statu': 'status',
            'tets': 'test',
            'laarm': 'alarm',
            'raido': 'radio',
            'swithc': 'switch',
            'trnuk': 'trunk'
        }

        if command in typo_corrections:
            suggestions.insert(0, typo_corrections[command])

        return list(dict.fromkeys(suggestions))  # Remove duplicates









    def select_role(self, preselected: Optional[int] = None) -> None:
        """
        Allow user to select their Bell System operational role.

        Displays authentic Bell System roles and sets up role-specific
        environment and command access.

        Args:
            preselected: Role number 1-12 to apply without prompting. Used by
                the ``--role`` command-line option.
        """
        if preselected is not None and preselected in BELL_SYSTEM_ROLES:
            role_key, role_name = BELL_SYSTEM_ROLES[preselected]
            self._apply_role(role_key, role_name)
            return

        self.emit("\n" + "="*60)
        self.emit("BELL SYSTEM UNIX V7 INTERNAL OPERATIONS TERMINAL")
        self.emit("AT&T Bell Laboratories - Murray Hill, New Jersey")
        self.emit("="*60)
        self.emit("\nSELECT YOUR BELL SYSTEM OPERATIONAL ROLE:")
        self.emit("-" * 45)

        for role_id, (role_key, role_name) in BELL_SYSTEM_ROLES.items():
            self.emit(f"{role_id:2d}. {role_name}")

        self.emit("-" * 45)

        while True:
            try:
                choice = input("\nEnter role number (1-12): ").strip()
                role_num = int(choice)

                if 1 <= role_num <= 12:
                    role_key, role_name = BELL_SYSTEM_ROLES[role_num]
                    self._apply_role(role_key, role_name)
                    break
                else:
                    self.emit("Invalid selection. Please enter a number between 1 and 12.")
            except ValueError:
                self.emit("Invalid input. Please enter a number between 1 and 12.")
            except (EOFError, KeyboardInterrupt):
                self.emit("\nExiting...")
                raise SystemExit(0)

    def _apply_role(self, role_key: str, role_name: str) -> None:
        """
        Activate a Bell System role and configure the session for it.

        Being put at a position carries its own sign-off: the wire chief
        qualified you for the desk you were assigned to. Everything beyond
        that desk is still earned a report at a time.
        """
        self.role = role_key
        self.role_name = role_name
        self.username = role_key
        self.current_directory = f"/usr/users/{role_key}"
        self.emit(f"\nRole selected: {role_name}")
        self.emit(f"User ID: {role_key}")

        assigned = ROLE_QUALIFICATIONS.get(role_key)
        if assigned and not self.career.is_qualified(assigned):
            self.career.qualifications.append(assigned)
            self.career.save()
            qualification = QUALIFICATIONS_BY_KEY[assigned]
            self.emit(f"Position sign-off: {qualification.name}")

        self.emit("Initializing workstation...")



    def _get_sysop_briefing(self) -> str:
        """Get UNIX Systems Operator briefing."""
        return """
UNIX SYSTEMS OPERATOR BRIEFING

Primary Responsibilities:
- System performance monitoring and maintenance
- UUCP network queue management
- PWB development environment support
- User account administration and security

Current Priorities:
- Monitor disk space utilization (currently 73%)
- Process overnight UUCP mail queue (47 files pending)
- Coordinate with development teams on PWB tools
- Review system logs for anomalies

Key Commands: ps, df, who, uucp, mail, pwb, rje
"""

    def _get_switch_briefing(self) -> str:
        """Get Switching Station Technician briefing."""
        return """
SWITCHING STATION TECHNICIAN BRIEFING

Primary Responsibilities:
- Electronic switching system monitoring (3A, 5ESS)
- Crossbar system maintenance and diagnostics
- Central office alarm response
- System cutover coordination

Current Priorities:
- Monitor 3A Central Control processor occupancy (67%)
- Complete scheduled crossbar maintenance at 09:15
- Coordinate 5ESS system test at 14:30
- Review overnight alarm logs (3 minor alarms cleared)

Key Commands: trunk, switch, testboard, toll, crossbar, alarm, 5ess, 3a
"""

    def _get_field_briefing(self) -> str:
        """Get Field Support Liaison briefing."""
        return """
FIELD SUPPORT LIAISON BRIEFING

Primary Responsibilities:
- Field technician coordination and dispatch
- Service installation and repair oversight
- Customer service issue escalation
- Emergency response coordination

Current Priorities:
- Coordinate 12 active field technician assignments
- Monitor service installation completion (47 pending)
- Review trouble ticket escalations (3 pending review)
- Prepare for emergency response drill at 11:00

Key Commands: trace, dialtone, emergency, ticket, provision, sarts
"""

    def _get_noc_briefing(self) -> str:
        """Get National NOC Analyst briefing."""
        return """
NATIONAL NOC ANALYST BRIEFING

Primary Responsibilities:
- National network monitoring and analysis
- Inter-office trunk coordination
- Critical incident management
- Network performance reporting

Current Priorities:
- Monitor inter-office trunk utilization (peak at 84%)
- Coordinate network optimization project NP-8301
- Review traffic analysis reports from TNDS
- Prepare monthly network performance summary

Key Commands: trunk, emergency, switch, ticket, traffic, tnds, satellite
"""


    def _get_dba_briefing(self) -> str:
        """Get Database Administrator briefing."""
        return """
DATABASE ADMINISTRATOR BRIEFING

Primary Responsibilities:
- Customer database maintenance and integrity
- Network configuration data management
- Service order database coordination
- Billing system interface

Current Priorities:
- Complete monthly database integrity checks
- Process service order updates (156 pending)
- Coordinate billing system interface testing
- Review customer database performance metrics

Key Commands: dbquery, custdb, billing, netdb, service
"""

    def _get_netplan_briefing(self) -> str:
        """Get Network Planning Engineer briefing."""
        return """
NETWORK PLANNING ENGINEER BRIEFING

Primary Responsibilities:
- Network design and capacity planning
- Traffic forecasting and analysis
- Route optimization studies
- Economic analysis coordination

Current Priorities:
- Complete NP-8301 Northeast Corridor analysis
- Review traffic growth projections for Q4 1983
- Coordinate capacity planning meeting at 10:00
- Finalize route optimization recommendations

Key Commands: netplan, traffic, routing, capacity, billing, tnds
"""

    def _get_custserv_briefing(self) -> str:
        """Get Customer Service Interface Technician briefing."""
        return """
CUSTOMER SERVICE INTERFACE TECHNICIAN BRIEFING

Primary Responsibilities:
- Service order processing and management
- Customer provisioning coordination
- Installation tracking and completion
- Customer billing inquiry resolution

Current Priorities:
- Process 89 new service orders received overnight
- Coordinate installation completion verification
- Review customer billing inquiries (23 pending)
- Update service order tracking database

Key Commands: service, provision, billing, custdb, directory
"""

    def _get_radio_briefing(self) -> str:
        """Get Radio/Microwave Technician briefing."""
        return """
RADIO/MICROWAVE TECHNICIAN BRIEFING

Primary Responsibilities:
- TH-3 microwave system monitoring
- Radio path performance analysis
- Satellite communication coordination
- Propagation analysis and optimization

Current Priorities:
- Monitor TH-3 path NYC-WAS for fade events
- Complete radio equipment calibration cycle
- Review satellite link performance metrics
- Analyze weather impact on microwave paths

Key Commands: radio, microwave, propagation, antenna, fade, satellite
"""


    def _get_sarts_briefing(self) -> str:
        """Get SARTS Technician briefing."""
        return """
SARTS TECHNICIAN BRIEFING

Primary Responsibilities:
- Special service remote testing operations
- T1 carrier and digital circuit validation
- Customer circuit troubleshooting
- Special service provisioning support

Current Priorities:
- Complete scheduled T1 circuit testing (12 circuits)
- Validate new customer special service installations
- Troubleshoot reported circuit performance issues
- Coordinate with provisioning for circuit turn-up

Key Commands: sarts, remote, special, testing, circuits, provision
"""

    def _get_docprep_briefing(self) -> str:
        """Get Document Preparation Specialist briefing."""
        return """
DOCUMENT PREPARATION SPECIALIST BRIEFING

Primary Responsibilities:
- Technical documentation using UNIX tools
- Bell System Practices development
- Training material creation
- Engineering documentation support

Current Priorities:
- Complete BSP 200-455-100 revision using nroff
- Prepare technical diagrams for NP-8301 project
- Format training materials for TSPS operators
- Support engineering teams with documentation

Key Commands: nroff, troff, tbl, eqn, pic, refer, pwb
"""

    def _build_command_handlers(self) -> Dict[str, Any]:
        """
        Build the command name to handler-method dispatch table.

        Called once during initialisation; the resulting table is reused for
        every command rather than being rebuilt on each keystroke.

        Returns:
            Mapping of command name to the bound method implementing it
        """
        return {
        # Core Bell System commands
        'trunk': self.cmd_trunk,
        'switch': self.cmd_switch,
        'testboard': self.cmd_testboard,
        'toll': self.cmd_toll,
        'trace': self.cmd_trace,
        'dialtone': self.cmd_dialtone,
        'emergency': self.cmd_emergency,
        'ticket': self.cmd_ticket,
        'trouble': self.cmd_trouble,
        'uucp': self.cmd_uucp,
        'traffic': self.cmd_traffic,
        'routing': self.cmd_routing,
        'capacity': self.cmd_capacity,
        'billing': self.cmd_billing,
        'service': self.cmd_service,
        'operator': self.cmd_operator,
        'directory': self.cmd_directory,
        'crossbar': self.cmd_crossbar,
        'netplan': self.cmd_netplan,
        'dbquery': self.cmd_dbquery,
        'custdb': self.cmd_custdb,
        'provision': self.cmd_provision,
        'collect': self.cmd_collect,
        'tsps': self.cmd_tsps,
        'handoff': self.cmd_handoff,
        'tariff': self.cmd_tariff,
        'events': self.cmd_events,
        'training': self.cmd_training,

        # Enhanced Bell System commands
        '3a': self.cmd_3a,
        '5ess': self.cmd_5ess,
        'bsp': self.cmd_bsp,
        'western': self.cmd_western,
        'coer': self.cmd_coer,
        'lmos': self.cmd_lmos,
        'tnds': self.cmd_tnds,
        'sarts': self.cmd_sarts,
        'radio': self.cmd_radio,
        'microwave': self.cmd_microwave,
        'satellite': self.cmd_satellite,
        'alarm': self.cmd_alarm,
        'pwb': self.cmd_pwb,
        'rje': self.cmd_rje,
        'nroff': self.cmd_nroff,
        'troff': self.cmd_troff,
        'tbl': self.cmd_tbl,
        'eqn': self.cmd_eqn,
        'pic': self.cmd_pic,
        'refer': self.cmd_refer,
        'netdata': self.cmd_netdata,
        'analysis': self.cmd_analysis,
        't1carrier': self.cmd_t1carrier,
        'lcarrier': self.cmd_lcarrier,
        'multiplex': self.cmd_multiplex,
        'regenerator': self.cmd_regenerator,
        'antenna': self.cmd_antenna,

        # Enhanced UX commands
        'errors': self.cmd_errors,
        'verbosity': self.cmd_verbosity,
        'history': self.cmd_history,
        'set': self.cmd_set,
        'clli': self.cmd_clli,
        'cosmos': self.cmd_cosmos,

        # Repair service bureau, loop testing and the craft record
        'report': self.cmd_report,
        'mlt': self.cmd_mlt,
        'testline': self.cmd_testline,
        'qual': self.cmd_qual,
        'write': self.cmd_write,
        'mail': self.cmd_mail,
        'orderwire': self.cmd_orderwire,
        'testcall': self.cmd_testcall,

        # Standard UNIX commands
        'ps': self.cmd_ps,
        'who': self.cmd_who,
        'ls': self.cmd_ls,
        'pwd': self.cmd_pwd,
        'date': self.cmd_date,
        'df': self.cmd_df,
        'help': self.cmd_help,
        'man': self.cmd_man,
        'status': self.cmd_status,
        'test': self.cmd_test,
        'quit': self.cmd_quit,
        'clear': self.cmd_clear
        }
    def cmd_set(self, args: Optional[List[str]] = None) -> str:
        """Display and change simulation settings."""
        args = args or []

        if not args:
            return self._show_settings_screen()

        if args[0].lower() == 'reset':
            if len(args) > 1:
                key = args[1].lower()
                try:
                    self.settings.reset(key)
                except KeyError:
                    return self._unknown_setting(key)
                self._apply_setting(key)
                return f"{key} reset to {self.settings.get(key)}"
            self.settings.reset()
            for option in OPTIONS:
                self._apply_setting(option.key)
            return "All settings reset to period-accurate defaults."

        key = args[0].lower()
        if key not in OPTIONS_BY_KEY:
            return self._unknown_setting(key)

        if len(args) == 1:
            return self._describe_setting(key)

        value = ' '.join(args[1:])
        try:
            stored = self.settings.set(key, value)
        except ValueError as exc:
            return f"set: {exc}"

        self._apply_setting(key)
        option = OPTIONS_BY_KEY[key]
        result = f"{key} = {stored}"
        if key == 'game.difficulty':
            difficulty = DIFFICULTIES[stored]
            result += f"\n\n{difficulty.name}: {difficulty.summary}"
            if difficulty.require_test_before_close:
                result += ("\n\nFrom here on, a report cannot be closed until "
                           "the loop has been measured,\nand mechanised loop "
                           "testing will no longer name the fault for you.")
        if option.accurate is not None and stored != option.accurate:
            result += (f"\n\nNote: the period-accurate value is "
                       f"'{option.accurate}'. This setting now departs from "
                       f"1978-1983 behaviour.")
        return result

    def _apply_setting(self, key: str) -> None:
        """Take account of a setting whose change needs more than storage."""
        if key == 'date.epoch':
            self.clock.reset_session()
        elif key == 'display.log_console':
            self._setup_logging()
        elif key == 'game.difficulty':
            self.career.set_difficulty(self.settings.get('game.difficulty'))

    def _unknown_setting(self, key: str) -> str:
        """Report an unrecognised setting name."""
        return (f"set: no such setting '{key}'\n"
                f"Available settings: {', '.join(sorted(OPTIONS_BY_KEY))}\n"
                f"Type 'set' with no arguments for the settings screen.")

    def _describe_setting(self, key: str) -> str:
        """Show one setting in detail."""
        option = OPTIONS_BY_KEY[key]
        current = self.settings.get(key)
        choices = ', '.join(option.choices) if option.choices else '(free text)'
        accurate = option.accurate or 'not applicable'
        lines = [
            f"{option.key}",
            '=' * 50,
            f"Current value:     {current}",
            f"Default:           {option.default}",
            f"Permitted:         {choices}",
            f"Period-accurate:   {accurate}",
            '',
            option.summary + '.',
        ]
        if option.detail:
            lines.append(option.detail)
        lines.append('')
        lines.append(f"Usage: set {option.key} <value>")
        return '\n'.join(lines)

    def _show_settings_screen(self) -> str:
        """Render the full settings screen."""
        deviations = self.settings.deviations()
        width = max(len(option.key) for option in OPTIONS)

        lines = [
            "Bell System Terminal - Simulation Settings",
            '=' * 60,
            '',
            "The simulation runs period-accurate by default. Each setting",
            "below may be moved away from that where a modern terminal makes",
            "the accurate behaviour less playable.",
            '',
            f"{'SETTING'.ljust(width)}  {'CURRENT'.ljust(12)}  OPTIONS",
            '-' * 60,
        ]

        for option in OPTIONS:
            current = self.settings.get(option.key)
            choices = '/'.join(option.choices) if option.choices else 'YYYY-MM-DD'
            marker = ' *' if option.key in deviations else '  '
            lines.append(
                f"{option.key.ljust(width)}  {current.ljust(12)}{marker}{choices}"
            )

        lines.extend([
            '-' * 60,
            '',
        ])

        if deviations:
            lines.append(
                f"* {len(deviations)} setting(s) depart from period-accurate "
                f"behaviour: {', '.join(deviations)}"
            )
        else:
            lines.append("All settings are period-accurate.")

        lines.extend([
            '',
            "Current shift time: " + self.clock.timestamp(),
            '',
            "Commands:",
            "  set <setting>            Explain one setting in detail",
            "  set <setting> <value>    Change a setting",
            "  set reset [<setting>]    Restore period-accurate defaults",
            '',
            "Settings persist between sessions.",
        ])
        return '\n'.join(lines)



    def _subsystem_unavailable(self, command: str, summary: str) -> str:
        """
        Report a command whose interactive subsystem is not in this release.

        These commands are dispatched and documented, but their operational
        screens are not built yet. Saying so plainly is better than emitting a
        placeholder string that reads like real output.

        Args:
            command: The command name, used to point at its manual page
            summary: Short description of what the subsystem does

        Returns:
            A consistent operator-facing notice
        """
        available = sorted(set(self._command_handlers) - UNIMPLEMENTED_COMMANDS)
        wrapped = []
        line = '  '
        for name in available:
            if len(line) + len(name) + 2 > 72:
                wrapped.append(line.rstrip())
                line = '  '
            line += name + ', '
        wrapped.append(line.rstrip().rstrip(','))

        return f"""{summary}
{'=' * 50}

{command}: subsystem not available in this release.

This command is recognised and documented, but its operational screens
have not been implemented. The manual page describes the intended
interface:

  man {command}

Subsystems available in this release:
""" + '\n'.join(wrapped)

    def emit(self, text: str = '', end: str = '\n') -> None:
        """
        Write simulation output under the active character-set setting.

        Args:
            text: The text to display; empty prints a blank line
        """
        print(render(text, self.settings.get('display.charset')))

    def shell_prompt(self) -> str:
        """
        Return the shell prompt in the configured style.

        The Seventh Edition Bourne shell prompted with a bare ``$ ``, or ``# ``
        for the super-user; it carried no user, host or directory. The verbose
        style restores those for players who want the orientation.
        """
        if self.settings.get('display.prompt') == 'verbose':
            return f"{self.username}@{self.hostname}:{self.current_directory}$ "
        return '# ' if self.username == 'root' else '$ '

    def _complete_command(self, text: str, state: int):
        """
        Readline completer offering Bell System command names.

        Replaces readline's default filename completion, which would otherwise
        expose the host filesystem inside the simulated terminal.
        """
        names = sorted(set(self._command_handlers) | set(self.COMMAND_ALIASES))
        matches = [n for n in names if n.startswith(text)]
        return matches[state] if state < len(matches) else None

    def run(self, role: Optional[int] = None) -> None:
        """
        Main Bell System terminal session loop.

        Handles user interaction, command processing, and maintains
        the authentic Bell System terminal experience.

        Args:
            role: Optional role number 1-12 to start with, bypassing the
                interactive role-selection menu.
        """
        try:
            self.select_role(role)
            self.show_shift_briefing()

            while True:
                try:
                    command_line = input(self.shell_prompt()).strip()

                    if not command_line:
                        continue

                    # History is recorded once, inside execute_command().
                    if command_line.lower() in ['exit', 'quit', 'logout']:
                        self.emit("Logging out of Bell System terminal...")
                        self.emit("Session terminated.")
                        break

                    output = self.execute_command(command_line)
                    if output:
                        self.emit(output)

                except KeyboardInterrupt:
                    self.emit("\n^C")
                    choice = input("Really quit Bell System terminal? (y/N): ")
                    if choice.lower().startswith('y'):
                        self.emit("Session terminated.")
                        break
                except EOFError:
                    self.emit("\nSession terminated.")
                    break

        except Exception as e:
            self.emit(f"Terminal error: {e}")
            self.emit("Session terminated.")

    def execute_command(self, command_line: str) -> str:
        """
        Execute Bell System commands with enhanced UX features and logging.

        Args:
            command_line: The complete command line entered by user

        Returns:
            Command output string or enhanced error message
        """
        start_time = time.time()

        # Add to command history
        if command_line.strip():
            self.command_history.append(command_line)

        try:
            parts = command_line.split()
            if not parts:
                return ""

            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            # Log command execution
            self.logger.debug(f"Executing command: {command} with args: {args}")

            # Handle command aliases
            original_command = command
            if command in self.COMMAND_ALIASES:
                # Handle complex aliases like 'll' -> 'list -l'
                alias_expansion = self.COMMAND_ALIASES[command]
                if ' ' in alias_expansion:
                    alias_parts = alias_expansion.split()
                    command = alias_parts[0]
                    args = alias_parts[1:] + args
                else:
                    command = alias_expansion

                self.logger.debug(f"Command alias expanded: {original_command} -> {command} {' '.join(args)}")

            # Map commands to their handler methods
            handlers = self._command_handlers

            # Execute command if it exists
            if command in handlers:
                # Qualification gates what a craftsperson may work on, so a
                # command they are not signed off for is refused by the wire
                # chief rather than run.
                refusal = self._qualification_block(command)
                if refusal is not None:
                    self.command_counts[command] += 1
                    return refusal

                result = handlers[command](args)

                # Log performance metrics
                execution_time = time.time() - start_time
                self.logger.debug(f"Command '{command}' completed in {execution_time:.3f}s")

                # Update command statistics
                self.command_counts[command] += 1

                # The rest of the building gets a word in.
                interruption = self._interrupt()
                if interruption:
                    result = f"{result}\n{interruption}" if result else interruption

                return result
            else:
                # Enhanced error handling with suggestions
                error_msg = f"{command}: command not found"
                return self._handle_command_error(command, error_msg)

        except Exception as e:
            error_msg = f"Command execution error: {e}"
            self.logger.error(f"Exception in command '{command}': {e}")
            return self._handle_command_error(command, error_msg)

    def _initialize_man_pages(self) -> Dict[str, str]:
        """
        Load the manual pages for all Bell System commands.

        The page text lives in :mod:`bell_system.data.man_pages`; a copy is
        returned so a session cannot mutate the shared table.

        Returns:
            dict: Complete man page documentation system
        """
        return dict(MAN_PAGES)

    def _initialize_nanpa_data(self) -> None:
        """
        Load the geographic data the simulated network is placed on.

        The data ships inside the package and is read through
        :mod:`bell_system.data.geography`, not from the working directory.
        That used to be a relative path, which meant an installed copy run
        from anywhere but the source tree fell back to a handful of offices
        without saying so, and every geographic feature degraded with it.

        The parsed result is cached for the life of the process: it is static
        reference data, and re-reading it for every terminal made
        construction take a second apiece.
        """
        cached = BellSystemTerminal._NANPA_CACHE
        if cached is not None:
            self.nanpa_data = cached
            self.bell_system_exchanges: Dict[str, Any] = {}
            self.geography_degraded = BellSystemTerminal._NANPA_DEGRADED
            return

        self.bell_system_exchanges = {}
        try:
            self.nanpa_data = geography.load()
            self.geography_degraded = False
        except geography.GeographyUnavailable as exc:
            # Degraded, and said out loud. The point of this path is that a
            # player and a maintainer both find out immediately.
            self.nanpa_data = {
                npa: {nxx: [dict(place) for place in places]
                      for nxx, places in exchanges.items()}
                for npa, exchanges in geography.FALLBACK.items()
            }
            self.geography_degraded = True
            self.logger.error(f"Geographic data unavailable: {exc}")

        BellSystemTerminal._NANPA_CACHE = self.nanpa_data
        BellSystemTerminal._NANPA_DEGRADED = self.geography_degraded

    def _initialize_bell_system_infrastructure(self) -> None:
        """Initialize authentic Bell System infrastructure based on NANPA data."""

        # Create realistic Bell System central offices and switching centers
        self.central_offices: Dict[str, CentralOffice] = {}
        self.switching_centers = {}
        self.microwave_sites = {}

        # Generate central offices based on NANPA data
        for npa, exchanges in self.nanpa_data.items():
            for nxx, locations in exchanges.items():
                if locations:
                    location = locations[0]  # Use first location for office
                    office_code = f"{npa}{nxx}"

                    # Create central office with authentic Bell System characteristics
                    placement = self._generate_switch_placement(location['city'])
                    self.central_offices[office_code] = {
                        'npa': npa,
                        'nxx': nxx,
                        'city': location['city'],
                        'state': location['state'],
                        'clli': self._office_clli(
                            location['city'], location['state'],
                            placement['switch_type'],
                        ),
                        'switch_type': placement['switch_type'],
                        'switch_name': placement['switch_name'],
                        'capacity': placement['capacity'],
                        'installation_date': placement['installation_date'],
                        'utilization': random.randint(45, 85),
                        'trunk_groups': random.randint(12, 48),
                        'maintenance_status': random.choice(['NORMAL', 'SCHEDULED', 'EMERGENCY']),
                        'coordinates': (location['latitude'], location['longitude'])
                    }

        # Generate major switching centers for key metropolitan areas
        major_metros = [
            ('212', 'New York', 'NY', '4ESS'), ('213', 'Los Angeles', 'CA', '4ESS'),
            ('312', 'Chicago', 'IL', '4ESS'), ('617', 'Boston', 'MA', '4ESS'),
            ('202', 'Washington', 'DC', '4ESS'), ('215', 'Philadelphia', 'PA', '4ESS'),
            ('313', 'Detroit', 'MI', '4ESS'), ('404', 'Atlanta', 'GA', '4ESS'),
            ('713', 'Houston', 'TX', '4ESS'), ('415', 'San Francisco', 'CA', '4ESS')
        ]

        for npa, city, state, switch_type in major_metros:
            center_id = f"TSC-{npa}-001"
            self.switching_centers[center_id] = {
                'npa': npa,
                'city': city,
                'state': state,
                'type': 'TOLL_SWITCHING_CENTER',
                'switch_type': switch_type,
                'capacity': random.randint(100000, 500000),
                'routes': random.randint(45, 125),
                'status': 'OPERATIONAL',
                'traffic_load': random.randint(65, 90)
            }




    @staticmethod
    def _office_label(office: Any) -> str:
        """
        Render an affected office for display.

        Tickets carry the office record itself, not a name, so anything that
        shows one has to render it. Printing the record raw put a Python
        dictionary on a terminal that could not have produced one.
        """
        if isinstance(office, dict):
            name = f"{office.get('city', 'Unknown')}, {office.get('state', '')}"
            clli = office.get('clli')
            return f"{name.rstrip(', ')} ({clli})" if clli else name.rstrip(', ')
        return str(office)


    # Cities large enough to have carried a metropolitan-class machine.
    METROPOLITAN_CITIES = frozenset({
        'New York', 'Brooklyn', 'Chicago', 'Los Angeles', 'Philadelphia',
        'Detroit', 'Houston', 'Boston', 'San Francisco', 'Washington',
        'Dallas', 'Cleveland', 'Baltimore', 'Saint Louis', 'St. Louis',
        'Pittsburgh', 'Milwaukee', 'Atlanta', 'Newark', 'Minneapolis',
        'Seattle', 'Denver', 'Miami', 'Phoenix', 'San Diego',
    })







    # Commands each position works day to day. Every name here is checked
    # against the dispatch table by the test suite: this list once carried
    # two commands that had never existed.
    ROLE_COMMANDS = {
        "sysop": ["ps", "df", "who", "uucp", "pwb", "rje", "date", "ls"],
        "switch": ["trunk", "switch", "toll", "crossbar", "alarm", "5ess",
                   "3a"],
        "field": ["trace", "dialtone", "emergency", "ticket", "provision",
                  "sarts"],
        "noc": ["trunk", "emergency", "switch", "ticket", "traffic", "tnds",
                "satellite"],
        "tsps": ["tsps", "operator", "directory", "collect", "billing"],
        "dba": ["dbquery", "custdb", "billing", "service"],
        "netplan": ["netplan", "traffic", "routing", "capacity", "billing",
                    "tnds"],
        "custserv": ["service", "provision", "billing", "custdb",
                     "directory"],
        "radio": ["radio", "microwave", "satellite", "alarm"],
        "tnds": ["tnds", "netdata", "analysis", "traffic"],
        "sarts": ["sarts", "testline", "testcall", "provision", "trunk"],
        "docprep": ["nroff", "troff", "tbl", "eqn", "pic", "refer", "pwb"],
    }

    # The work itself, which every position has a board of.
    BUREAU_COMMANDS = (
        ('report', 'The pending trouble reports on your board'),
        ('mlt', 'Measure a subscriber loop'),
        ('testboard', 'The test board: loops, test lines, supervision'),
        ('testline', 'Far-end test lines and responders'),
        ('testcall', 'Place a test call through the network'),
        ('qual', 'Your craft record and service index'),
    )

    PEOPLE_COMMANDS = (
        ('who', 'Who is on the system'),
        ('write', 'Write to another terminal'),
        ('mail', 'Read your mail'),
        ('orderwire', 'The maintenance order wire'),
        ('handoff', 'Shift turnover; handoff relieve to sign off'),
    )

    def cmd_help(self, args: Optional[List[str]] = None) -> str:
        """
        Show available commands, marking what this craftsperson may work.

        Qualification governs what may be used, so the listing says so rather
        than offering a command that will be refused.

        Args:
            args: Optional command name for specific help

        Returns:
            Help information formatted for terminal display
        """
        if args and args[0]:
            command = args[0].lower()
            command = self.COMMAND_ALIASES.get(command, command)
            if command not in self.man_pages:
                return (f"No help available for '{args[0]}'. "
                        f"Use 'help' to see available commands.")
            needed = self.career.qualification_for_command(command)
            note = ''
            if needed and not self.career.is_qualified(needed):
                note = (f"\n\nYou are not signed off on "
                        f"{QUALIFICATIONS_BY_KEY[needed].name}. "
                        f"Type 'qual'.")
            first = self.man_pages[command].strip().splitlines()
            summary = first[1].strip() if len(first) > 1 else command
            return (f"{summary}\n\n"
                    f"Use 'man {command}' for complete documentation.{note}")

        pending = len(self.desk.pending())
        lines = [
            f"Bell System UNIX V7 Commands - Role: "
            f"{self.role_name or 'unassigned'}",
            '=' * 66,
            '',
            f"THE WORK   {pending} trouble report(s) on your board, "
            f"{self.shift_time()} into the shift",
            '-' * 66,
        ]
        lines.extend(self._help_rows(self.BUREAU_COMMANDS))

        role_commands = self.ROLE_COMMANDS.get(self.role or '')
        if role_commands:
            lines.extend(['', f"THIS POSITION   {self.role_name}", '-' * 66])
            lines.extend(self._help_rows(
                (name, self._help_summary(name))
                for name in sorted(role_commands)
            ))

        lines.extend(['', 'THE OTHER CRAFT', '-' * 66])
        lines.extend(self._help_rows(self.PEOPLE_COMMANDS))

        lines.extend([
            '',
            'THE SYSTEM',
            '-' * 66,
            "  man <command>     Complete documentation for any command",
            "  set               Settings, including difficulty and ambience",
            "  bsp search <topic>  Bell System Practices",
            "  help <command>    One line on a single command",
            "  ps, df, ls, date, pwd, who    The usual UNIX commands",
            "  exit              Log out",
            '',
        ])

        locked = sorted(
            name for name in self._command_handlers
            if not self.career.may_use(name)
        )
        if locked:
            lines.append("* marks a command you are not signed off on.")
            lines.append(f"Not signed off: {', '.join(locked)}. Type 'qual'.")
        return '\n'.join(lines)

    def _help_rows(self, entries) -> List[str]:
        """Render command rows, marking anything not signed off."""
        rows = []
        for name, summary in entries:
            mark = ' ' if self.career.may_use(name) else '*'
            rows.append(f" {mark}{name:<12} {summary}")
        return rows

    def _help_summary(self, command: str) -> str:
        """Return the one-line description from a command's manual page."""
        page = self.man_pages.get(command)
        if not page:
            return command
        parts = page.strip().splitlines()
        if len(parts) < 2:
            return command
        line = parts[1].strip()
        return line.split(' - ', 1)[1] if ' - ' in line else line


    # Basic UNIX commands






    # Bell System specific commands (implementations would continue...)





    # Bell System Core Commands Implementation





























    # Additional essential commands



















    # Implement remaining critical commands with similar patterns

    def cmd_trace(self, args: List[str]) -> str:
        """Call tracing and routing analysis"""
        return self._subsystem_unavailable("trace", "Call trace operations")



    def cmd_capacity(self, args: List[str]) -> str:
        """Network capacity planning and utilization"""
        return self._subsystem_unavailable("capacity", "Capacity planning")








































    def cmd_training(self, args: List[str]) -> str:
        """Bell System training programs and procedures"""
        return self._subsystem_unavailable("training", "Training programs")

    # Enhanced commands

    def cmd_western(self, args: List[str]) -> str:
        """Western Electric equipment specifications"""
        return self._subsystem_unavailable("western", "Western Electric equipment")

    def cmd_coer(self, args: List[str]) -> str:
        """Central Office Equipment Reports"""
        return self._subsystem_unavailable("coer", "COER reporting")

    def cmd_lmos(self, args: Optional[List[str]] = None) -> str:
        """Loop Maintenance Operations System: line records and reports."""
        return self.lmos_console.command(args)

    def cmd_sarts(self, args: Optional[List[str]] = None) -> str:
        """Switched Access Remote Test System: special services circuits."""
        return self.sarts_console.command(args)







    # Document preparation commands






    def cmd_netdata(self, args: List[str]) -> str:
        """Network data collection tools"""
        return self._subsystem_unavailable("netdata", "Network data tools")

    def cmd_analysis(self, args: List[str]) -> str:
        """Advanced network analysis and modeling"""
        return self._subsystem_unavailable("analysis", "Network analysis")











    # ------------------------------------------------------------------
    # Repair service bureau: the trouble report loop
    # ------------------------------------------------------------------


    # -- helpers ---------------------------------------------------------














    # -- report command --------------------------------------------------









    # -- mechanised loop testing -----------------------------------------


    # -- test lines ------------------------------------------------------


    # -- craft record ----------------------------------------------------



    # -- messaging channels ----------------------------------------------





    # -- test calls ------------------------------------------------------





    def cmd_quit(self, args: Optional[List[str]] = None) -> str:
        """Exit the Bell System terminal session."""
        # Save command history if readline is available
        if readline is not None and getattr(self, 'history_file', None):
            try:
                readline.write_history_file(self.history_file)
            except OSError as exc:
                self.logger.warning(f"Could not save command history: {exc}")

        self.logger.info(f"Session {self.session_id} terminated by user")
        self.emit("\nBell System session terminated.")
        self.emit("Thank you for using Bell System UNIX V7 Operations Terminal.")
        sys.exit(0)



def main() -> None:
    """Main entry point for the Bell System terminal simulation."""
    try:
        terminal = BellSystemTerminal()
        terminal.run()
    except KeyboardInterrupt:
        print("\nSession terminated by user.")
    except Exception as e:
        print(f"Terminal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
