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

from .clock import SimClock
from .console import clear_screen, render
from .data.carrier import (
    L3_LINE_ASSEMBLY,
    L_CARRIER_SYSTEMS,
    MULTIPLEX_HIERARCHY,
    MULTIPLEX_PILOTS_KHZ,
)
from .data.clli import (
    ATTESTED_CLLI,
    STATE_CODES,
    build as build_clli,
    describe_entity,
    entity_for_switch,
    parse as parse_clli,
)
from .data.man_pages import MAN_PAGES
from .data.testlines import TEST_LINE_ORDER, TEST_LINES
from .data.trouble import (
    DISPATCH_FORCES,
    DISPOSITIONS,
    FAULTS,
    NSPMP_CATEGORIES,
    NSPMP_WEIGHTS,
)
from .loop_testing import (
    COIN_STATION_CURRENT_MA,
    SUPERVISION_STATES,
    access_test_line,
    design_note,
    distance_to_open,
    measure_loop,
    tone_header,
)
from .npc import CRAFT, Message, Switchroom, render as render_message
from .progression import (
    DIFFICULTIES,
    MISSED_COMMITMENT_WEIGHT,
    REPEAT_REPORT_WEIGHT,
    WRONG_DISPOSITION_WEIGHT,
    QUALIFICATIONS,
    QUALIFICATIONS_BY_KEY,
    ROLE_QUALIFICATIONS,
    Career,
    career_path,
)
from .reports import (
    CLASSES_OF_SERVICE,
    COST_CALLBACK,
    ReportDesk,
    disposition_name,
    valid_force,
)
from .routing import MAX_TRUNKS_IN_CONNECTION, build_default_network
from .data.signaling import (
    MF_FREQUENCIES,
    PROGRESS_TONES,
    SF_FREQUENCY_HZ,
    SF_IDLE_LEVEL_DBM,
    mf_sequence,
    mf_train_duration_ms,
)
from .data.switching import (
    METROPOLITAN_SWITCHES,
    RURAL_SWITCHES,
    SWITCHING_SYSTEMS,
    available_in,
)
from .settings import (
    EPOCH_HOUR,
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
    TndsData,
    TroubleTicket,
    TrunkGroup,
    TspsData,
)

try:
    import readline  # For command history and line editing
    READLINE_AVAILABLE = True
except ImportError:  # pragma: no cover - readline is absent on stock Windows
    readline = None
    READLINE_AVAILABLE = False


# Commands that are dispatched and documented but whose operational screens
# are not built yet. Kept here so the terminal can tell the operator honestly
# what is and is not available, and so a test can hold the list accountable.
UNIMPLEMENTED_COMMANDS = frozenset({
    '5ess', 'analysis', 'capacity', 'coer', 'collect', 'custdb', 'dbquery',
    'eqn', 'lmos', 'microwave', 'netdata', 'nroff', 'pic', 'provision',
    'pwb', 'refer', 'rje', 'sarts', 'satellite', 'tbl', 'toll', 'trace',
    'training', 'troff', 'western',
})


# Bell System Constants
# A tour of duty. Eight hours is the shift the simulation's events are laid
# out across, and the point at which the wire chief expects to be relieved.
SHIFT_LENGTH_MINUTES = 480

BELL_SYSTEM_ROLES = {
    1: ("sysop", "UNIX Systems Operator"),
    2: ("switch", "Switching Station Technician"),
    3: ("field", "Field Support Liaison"),
    4: ("noc", "National NOC Analyst"),
    5: ("tsps", "Traffic Service Position System Operator"),
    6: ("dba", "Database Administrator"),
    7: ("netplan", "Network Planning Engineer"),
    8: ("custserv", "Customer Service Interface Technician"),
    9: ("radio", "Radio/Microwave Technician"),
    10: ("tnds", "Total Network Data System (TNDS) Analyst"),
    11: ("sarts", "SARTS (Switched Access Remote Test) Technician"),
    12: ("docprep", "Document Preparation Specialist")
}

# Bell System Practices (BSP) Categories
BSP_CATEGORIES = {
    "000": "General Information and Master Indexes",
    "074": "Catalogue Information - Tools",
    "100": "Test Equipment",
    "179": "Signaling and Ringing Circuits",
    "309": "Switched Services Networks",
    "311": "Switched Special Services Systems",
    "460": "Customer Equipment - General Information",
    "620": "Outside Plant - General",
    "660": "Test Center Operation",
    "743": "Supply Ordering and Computer Control",
    "760": "Building Engineering",
    "795": "Common Language",
    "800": "Equipment Design Requirements",
    "801": "Common Systems",
    "900": "Outside Plant Engineering",
}

# Practices cited elsewhere in the simulation, with their subjects.
BSP_PRACTICES = {
    "000-000-001": "Master Alphabetical Index - All Divisions",
    "000-000-005": "Master Numerical Index - All Divisions",
    "309-400-004": "Electronic Tandem Network (ETN) Trouble Reporting",
    "660-000-005": "Alphabetical Index, Divisions 660-669",
    "795-100-100": "Common Language Location Identification (CLLI) Code "
                   "Description, Issue 5, October 1982",
}

# Project Numbering Prefixes
PROJECT_PREFIXES = {
    "NP": "Network Planning",
    "TP": "Technical/Technology",
    "OP": "Operations",
    "AC": "Area Code Implementation",
    "RE": "Route Enhancement",
    "CP": "Capacity Planning"
}


class BellSystemTerminal:
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

    # Parsed NANPA data, shared across instances in a process. The source
    # file is large and never changes during a run.
    _NANPA_CACHE: Optional[Dict[str, Any]] = None

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
        for alarm in possible_alarms:
            if random.random() < 0.3:  # 30% chance each alarm is active
                alarm["timestamp"] = self.clock.now() - timedelta(minutes=random.randint(5, 480))
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
            self.history_file = None

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

    def _initialize_ticket_system(self) -> None:
        """Initialize the Bell System trouble ticket management system."""
        self.ticket_system = {
            "open": {},
            "pending": {},
            "closed": {},
            "escalated": {},
            "priorities": {
                "CRITICAL": {"response_time": 15, "escalation": 30},
                "HIGH": {"response_time": 60, "escalation": 120},
                "MEDIUM": {"response_time": 240, "escalation": 480},
                "LOW": {"response_time": 1440, "escalation": 2880}
            },
            "customer_classes": {
                "GOVERNMENT-PRIORITY": {
                    "escalation_multiplier": 0.5,
                    "priority_boost": 1
                },
                "EMERGENCY-SERVICES": {
                    "escalation_multiplier": 0.25,
                    "priority_boost": 2
                },
                "BUSINESS-CRITICAL": {
                    "escalation_multiplier": 0.75,
                    "priority_boost": 1
                },
                "RESIDENTIAL": {
                    "escalation_multiplier": 1.0,
                    "priority_boost": 0
                }
            }
        }

    def _initialize_project_numbers(self) -> None:
        """Initialize Bell System project and work order numbering system."""
        self.project_numbers = {
            "netplan": {
                "current": "NP-8301",
                "name": "Northeast Corridor Expansion Project",
                "budget": "$4.2M",
                "timeline": "Q1-Q4 1983"
            },
            "capacity": {
                "current": "CP-8302",
                "name": "Digital Switching Migration Phase II",
                "budget": "$12.8M",
                "timeline": "1983-1985"
            },
            "crossbar": {
                "current": "XB-8303",
                "name": "Crossbar Modernization Initiative",
                "budget": "$6.5M",
                "timeline": "1983-1984"
            },
            "maintenance": {
                "current": "MT-8304",
                "name": "Preventive Maintenance Program Enhancement",
                "budget": "$2.1M",
                "timeline": "Ongoing"
            },
            "training": {
                "current": "TR-8305",
                "name": "Employee Development and Certification Update",
                "budget": "$890K",
                "timeline": "1983-1984"
            }
        }

    def _initialize_rate_structures(self) -> None:
        """Initialize Bell System tariff and rate structures."""
        self.rate_structures = {
            "interstate": {
                "day": {"first_minute": 0.45, "additional": 0.34},
                "evening": {"first_minute": 0.32, "additional": 0.24},
                "night": {"first_minute": 0.18, "additional": 0.15}
            },
            "intrastate": {
                "day": {"first_minute": 0.28, "additional": 0.22},
                "evening": {"first_minute": 0.21, "additional": 0.17},
                "night": {"first_minute": 0.14, "additional": 0.12}
            },
            "international": {
                "uk": {"first_minute": 2.50, "additional": 1.80},
                "canada": {"first_minute": 0.65, "additional": 0.45},
                "mexico": {"first_minute": 1.20, "additional": 0.85}
            }
        }

    def _initialize_filesystem(self) -> None:
        """Initialize Bell System UNIX V7 filesystem structure."""
        self.filesystem = {
            "/": {
                "type": "dir", "owner": "root", "group": "bell",
                "mode": "drwxr-xr-x", "size": 512,
                "files": ["bin", "dev", "etc", "lib", "tmp", "usr", "var", "att"]
            },
            "/bin": {
                "type": "dir", "owner": "root", "group": "bell",
                "mode": "drwxr-xr-x", "size": 1024,
                "files": ["sh", "ls", "cat", "ps", "who", "uucp", "mail",
                         "wall", "write"]
            },
            "/usr": {
                "type": "dir", "owner": "root", "group": "bell",
                "mode": "drwxr-xr-x", "size": 2048,
                "files": ["bin", "lib", "users", "spool", "att"]
            },
            "/usr/bin": {
                "type": "dir", "owner": "root", "group": "bell",
                "mode": "drwxr-xr-x", "size": 2048,
                "files": ["trunk", "switch", "testboard", "toll", "trace",
                         "dialtone", "emergency", "ticket", "traffic", "routing",
                         "capacity", "billing", "service", "operator", "directory",
                         "crossbar", "netplan", "dbquery", "custdb", "provision",
                         "collect", "tsps", "3a", "5ess", "bsp", "western",
                         "coer", "lmos", "tnds", "sarts", "radio", "satellite",
                         "alarm", "pwb", "rje", "nroff", "troff", "tbl", "eqn",
                         "pic", "refer"]
            },
            "/usr/users": {
                "type": "dir", "owner": "root", "group": "bell",
                "mode": "drwxr-xr-x", "size": 1024,
                "files": ["sysop", "switch", "field", "noc", "tsps", "dba",
                         "netplan", "custserv", "radio", "tnds", "sarts", "docprep"]
            },
            "/usr/users/sysop": {
                "type": "dir", "owner": "sysop", "group": "bell",
                "mode": "drwx------", "size": 512,
                "files": ["mail", "tickets", "logs", ".profile"]
            },
            "/usr/spool": {
                "type": "dir", "owner": "root", "group": "bell",
                "mode": "drwxrwxrwx", "size": 1024,
                "files": ["uucp", "mail", "tickets"]
            },
            "/att": {
                "type": "dir", "owner": "root", "group": "bell",
                "mode": "drwxr-xr-x", "size": 1024,
                "files": ["switch", "network", "maintenance", "tickets"]
            },
            "/att/tickets": {
                "type": "dir", "owner": "root", "group": "bell",
                "mode": "drwxrwxrwx", "size": 2048,
                "files": ["open", "pending", "closed"]
            },
            "/usr/adm": {
                "type": "dir", "owner": "root", "group": "bell",
                "mode": "drwxr-xr-x", "size": 1024,
                "files": ["wtmp", "messages", "sulog", "acct", "uucplog"]
            },
            "/etc/passwd": {
                "type": "file", "owner": "root", "group": "bell",
                "mode": "-rw-r--r--", "size": 245,
                "content": ("root::0:1:System Administrator:/:/bin/sh\n"
                           "sysop::100:10:UNIX Systems Operator:/usr/users/sysop:/bin/sh\n"
                           "switch::101:10:Switching Technician:/usr/users/switch:/bin/sh\n"
                           "field::102:10:Field Support Liaison:/usr/users/field:/bin/sh\n"
                           "noc::103:10:NOC Analyst:/usr/users/noc:/bin/sh\n"
                           "uucp::5:5:UUCP Network:/usr/spool/uucp:/usr/lib/uucp/uucico\n")
            },
            "/etc/motd": {
                "type": "file", "owner": "root", "group": "bell",
                "mode": "-rw-r--r--", "size": 387,
                "content": ("AT&T Bell System UNIX V7\n"
                           "Internal Operations Terminal\n\n"
                           "Restricted to authorized Bell System personnel only.\n"
                           "All activities are logged and monitored.\n\n"
                           "Current system load: moderate\n"
                           "Network status: operational\n"
                           "Switch centers online: 47/48\n\n"
                           "For technical support contact: BTL-MH TECH ASSISTANCE\n"
                           "For emergency escalation use: emergency command\n\n"
                           "Shift briefings available in /att/tickets/briefing\n")
            }
        }

    def _initialize_processes(self) -> None:
        """Initialize authentic Bell System processes."""
        self.processes = [
            {"pid": 0, "command": "swapper", "tty": "?", "time": "0:00", "user": "root"},
            {"pid": 1, "command": "init", "tty": "?", "time": "0:02", "user": "root"},
            {"pid": 23, "command": "update", "tty": "?", "time": "0:01", "user": "root"},
            {"pid": 45, "command": "sh", "tty": "co", "time": "0:00", "user": "root"},
            {"pid": 67, "command": "getty", "tty": "01", "time": "0:00", "user": "root"},
            {"pid": 89, "command": "uucico", "tty": "?", "time": "0:00", "user": "uucp"},
            {"pid": 102, "command": "cron", "tty": "?", "time": "0:00", "user": "root"},
            {"pid": 115, "command": "switchd", "tty": "?", "time": "0:03", "user": "switch"},
            {"pid": 127, "command": "uuxqt", "tty": "?", "time": "0:00", "user": "root"},
            {"pid": 138, "command": "tnds", "tty": "?", "time": "0:01", "user": "tnds"},
            {"pid": 145, "command": "sartsd", "tty": "?", "time": "0:00", "user": "sarts"},
            {"pid": 152, "command": "radiod", "tty": "?", "time": "0:02", "user": "radio"}
        ]

    def _initialize_users(self) -> None:
        """
        Populate the logged-on user list from the craft roster.

        who(1) and write(1) read the same people, so anyone the terminal says
        is logged on can actually be written to.
        """
        logins = ('07:30', '07:45', '08:00', '08:15', '08:30', '09:00')
        self.users = [
            {
                "user": person.login,
                "tty": person.tty,
                "login": logins[index % len(logins)],
                "location": person.location,
            }
            for index, person in enumerate(CRAFT.values())
        ]

    def _initialize_shift_handoff(self) -> None:
        """Initialize authentic Bell System shift handoff data."""
        self.shift_handoff = {
            "previous_shift": {
                "operator": "Johnson, R.",
                "end_time": "07:59",
                "summary": "Routine night operations - 3 tickets transferred",
                "key_issues": [
                    "RIDGE-X1 intermittent alarms - monitoring",
                    "UUCP queue backup - resolved 06:30",
                    "Crossbar maintenance scheduled 09:15"
                ],
                "open_tickets": ["SW-2847", "MX-2156", "FD-1293"],
                "system_status": "All systems operational",
                "special_instructions": "Monitor trunk TG-047 for blocking threshold"
            }
        }

    def generate_shift_events(self) -> None:
        """
        Generate authentic Bell System operational events with ticket numbers.

        Creates realistic operational events based on time of day, season,
        and historical Bell System operations patterns. Each event has an
        assigned ticket number for detailed investigation.
        """
        current_hour = self.clock.now().hour
        current_month = self.clock.now().month

        # Base events that occur during any shift with ticket numbers
        base_events = [
            {
                "id": "EV-8001",
                "time": "08:15",
                "type": "SYSTEM",
                "title": "Routine trunk group monitoring TG-023 to TG-067",
                "priority": "LOW",
                "status": "MONITORING",
                "description": "Daily trunk group performance monitoring cycle initiated",
                "details": "All 45 trunk groups showing normal utilization. TG-023 at 67%, TG-045 at 73%, TG-067 at 58%. No blocking events detected.",
                "actions": ["Review hourly reports", "Monitor for threshold violations", "Document performance metrics"]
            },
            {
                "id": "EV-8002",
                "time": "08:30",
                "type": "SYSTEM",
                "title": "UUCP queue processing - 47 files transferred",
                "priority": "LOW",
                "status": "COMPLETE",
                "description": "UNIX-to-UNIX Copy network file transfer cycle",
                "details": "Overnight UUCP queue processed successfully. 47 files transferred between Bell Labs sites. Queue depth now at normal levels.",
                "actions": ["Verify transfer logs", "Check for failed transfers", "Archive completed jobs"]
            },
            {
                "id": "EV-8003",
                "time": "08:45",
                "type": "TEST",
                "title": "Emergency services test call verification completed",
                "priority": "MEDIUM",
                "status": "COMPLETE",
                "description": "Daily test of emergency service routing",
                "details": "All 911 emergency routing paths tested successfully. Average setup time 1.8 seconds, all within specifications.",
                "actions": ["Document test results", "Report to emergency services coordinator", "Schedule next test cycle"]
            }
        ]

        # Time-specific events
        time_events = []
        if 6 <= current_hour < 14:  # Day shift
            time_events = [
                {
                    "id": "EV-8010",
                    "time": "09:15",
                    "type": "MAINTENANCE",
                    "title": "5ESS system cutover preparation scheduled 14:30",
                    "priority": "HIGH",
                    "status": "PENDING",
                    "description": "Electronic switching system cutover coordination",
                    "details": "5ESS-NYC-002 cutover from test to production. Requires coordination with traffic engineering and field operations.",
                    "actions": ["Verify test results", "Coordinate with NOC", "Prepare rollback procedures", "Brief field technicians"]
                },
                {
                    "id": "EV-8011",
                    "time": "10:00",
                    "type": "MEETING",
                    "title": "Network planning meeting NP-8301 at 10:00",
                    "priority": "MEDIUM",
                    "status": "SCHEDULED",
                    "description": "Northeast Corridor Expansion Project review",
                    "details": "Quarterly review of NP-8301 project milestones. Discussion of capacity requirements and timeline adjustments.",
                    "actions": ["Prepare traffic analysis reports", "Review budget status", "Present capacity forecasts"]
                }
            ]
        elif 14 <= current_hour < 22:  # Evening shift
            time_events = [
                {
                    "id": "EV-8020",
                    "time": "15:30",
                    "type": "TRAFFIC",
                    "title": "Peak traffic period - all trunk groups monitored",
                    "priority": "HIGH",
                    "status": "ACTIVE",
                    "description": "Daily peak traffic management",
                    "details": "Evening calling peak approaching. All trunk groups under enhanced monitoring. TG-023 approaching 85% capacity.",
                    "actions": ["Monitor trunk utilization", "Prepare overflow routing", "Coordinate with traffic engineering"]
                },
                {
                    "id": "EV-8021",
                    "time": "16:00",
                    "type": "TRAINING",
                    "title": "TSPS operator training session 16:00-17:30",
                    "priority": "MEDIUM",
                    "status": "SCHEDULED",
                    "description": "Traffic Service Position System operator certification",
                    "details": "Monthly TSPS operator training on new procedures and emergency protocols.",
                    "actions": ["Prepare training materials", "Coordinate with training department", "Document attendance"]
                }
            ]
        else:  # Night shift
            time_events = [
                {
                    "id": "EV-8030",
                    "time": "02:30",
                    "type": "MAINTENANCE",
                    "title": "Preventive maintenance window 02:00-05:00",
                    "priority": "MEDIUM",
                    "status": "ACTIVE",
                    "description": "Scheduled overnight maintenance procedures",
                    "details": "Crossbar system maintenance at three central offices. Estimated completion 04:30.",
                    "actions": ["Monitor maintenance progress", "Coordinate with field teams", "Verify service restoration"]
                }
            ]

        # Equipment-specific events with authentic Bell System issues
        equipment_events = [
            {
                "id": "EV-8040",
                "time": "09:47",
                "type": "ALARM",
                "title": "TH-3 microwave path NYC-WAS fade event detected",
                "priority": "HIGH",
                "status": "MONITORING",
                "description": "Radio path fade margin below threshold",
                "details": "TH-3 path NYC-WAS-001 experiencing atmospheric fade. Current RSL -65 dBm, fade margin reduced to 12 dB. Space diversity activated.",
                "actions": ["Monitor signal levels", "Check weather conditions", "Verify diversity operation", "Prepare backup routing"]
            },
            {
                "id": "EV-8041",
                "time": "11:23",
                "type": "EQUIPMENT",
                "title": "3A Central Control Unit D diagnostic alert",
                "priority": "HIGH",
                "status": "INVESTIGATING",
                "description": "Central control processor requires attention",
                "details": "3A Central Control Unit D reporting memory parity errors. Unit switched to standby. Diagnostic testing in progress.",
                "actions": ["Run comprehensive diagnostics", "Check memory modules", "Coordinate with maintenance", "Monitor standby unit"]
            },
            {
                "id": "EV-8042",
                "time": "13:15",
                "type": "CUSTOMER",
                "title": "Government priority circuit outage - Pentagon line",
                "priority": "CRITICAL",
                "status": "URGENT",
                "description": "High-priority government customer service interruption",
                "details": "Dedicated Pentagon communication line experiencing total outage. Customer class: GOVERNMENT-PRIORITY. Immediate response required.",
                "actions": ["Dispatch emergency team", "Activate backup circuits", "Notify government liaison", "Escalate to Level 3"]
            }
        ]

        # Seasonal events
        seasonal_events = []
        if current_month in [12, 1, 2]:  # Winter
            seasonal_events = [
                {
                    "id": "EV-8050",
                    "time": "07:30",
                    "type": "WEATHER",
                    "title": "Ice storm impact on microwave paths",
                    "priority": "HIGH",
                    "status": "MONITORING",
                    "description": "Weather affecting radio propagation",
                    "details": "Ice accumulation on microwave antennas in northeast corridor. Multiple paths showing degraded performance.",
                    "actions": ["Monitor all radio paths", "Coordinate ice removal crews", "Implement backup routing", "Track weather conditions"]
                }
            ]
        elif current_month in [6, 7, 8]:  # Summer
            seasonal_events = [
                {
                    "id": "EV-8060",
                    "time": "14:20",
                    "type": "WEATHER",
                    "title": "Thunderstorm fade analysis for radio paths",
                    "priority": "MEDIUM",
                    "status": "MONITORING",
                    "description": "Summer storm impact assessment",
                    "details": "Thunderstorm activity affecting multiple TH-3 paths. Increased fade events expected through evening hours.",
                    "actions": ["Monitor fade events", "Verify diversity switching", "Prepare traffic rerouting", "Document performance"]
                }
            ]

        # Always include base events, then add others based on current conditions
        selected_events = base_events.copy()

        # Add time-appropriate events
        selected_events.extend(time_events)

        # Add 2-3 equipment/customer events randomly
        if equipment_events:
            selected_events.extend(random.sample(equipment_events, min(2, len(equipment_events))))

        # Add seasonal events if applicable
        selected_events.extend(seasonal_events)

        # Sort by time and limit to reasonable number
        selected_events.sort(key=lambda x: x["time"])
        self.shift_events = selected_events[:8]  # Limit to 8 events per shift

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

    def show_shift_briefing(self) -> None:
        """
        Display role-specific shift briefing.

        Provides authentic Bell System shift briefing information
        tailored to the selected operational role.
        """
        current_time = self.clock.now().strftime("%H:%M")
        current_date = self.clock.now().strftime("%B %d, %Y")

        self.emit(f"\n{'='*60}")
        self.emit(f"BELL SYSTEM SHIFT BRIEFING - {current_date}")
        self.emit(f"Shift Start Time: {current_time}")
        # Find the role name for display
        role_name = "Unknown Role"
        for role_id, (role_key, name) in BELL_SYSTEM_ROLES.items():
            if role_key == self.role:
                role_name = name
                break
        self.emit(f"Role: {role_name}")
        self.emit(f"{'='*60}")

        # Role-specific briefings
        role_briefings = {
            "sysop": self._get_sysop_briefing(),
            "switch": self._get_switch_briefing(),
            "field": self._get_field_briefing(),
            "noc": self._get_noc_briefing(),
            "tsps": self._get_tsps_briefing(),
            "dba": self._get_dba_briefing(),
            "netplan": self._get_netplan_briefing(),
            "custserv": self._get_custserv_briefing(),
            "radio": self._get_radio_briefing(),
            "tnds": self._get_tnds_briefing(),
            "sarts": self._get_sarts_briefing(),
            "docprep": self._get_docprep_briefing()
        }

        briefing = role_briefings.get(self.role, "Generic Bell System briefing")
        self.emit(briefing)

        self.emit("\nShift Events:")
        for i, event in enumerate(self.shift_events[:5], 1):
            priority_marker = "*** " if event["priority"] == "CRITICAL" else "** " if event["priority"] == "HIGH" else "* " if event["priority"] == "MEDIUM" else ""
            self.emit(f"  {i}. {event['time']} [{event['type']}] {priority_marker}{event['status']}")
            self.emit(f"     {event['title']}")
            self.emit(f"     ID: {event['id']}")
            self.emit()

        self.emit("\nCurrent System Status:")
        self.emit("  Network Operations: NORMAL")
        self.emit("  Switch Centers: 47/48 operational")
        self.emit("  TNDS Collection: ACTIVE")
        self.emit("  Emergency Services: OPERATIONAL")

        self._emit_board_briefing()

        self.emit("\nType 'help' for available commands or 'man <command>' for detailed help.")
        self.emit(f"{'='*60}")

    def _emit_board_briefing(self) -> None:
        """
        Show the board the shift starts with, and what to do about it.

        Whatever position a craftsperson holds, there is a board of customer
        trouble waiting. Saying so at the start of the shift is the
        difference between a terminal with commands and a terminal with a
        job.
        """
        pending = self.desk.pending()
        difficulty = self._difficulty()

        self.emit("\nRepair Service Bureau:")
        self.emit(f"  Reports on your board: {len(pending)}")
        if pending:
            oldest = pending[0]
            self.emit(f"  Nearest commitment:    {oldest.number} "
                      f"({oldest.record.telephone_number}) in "
                      f"{oldest.age_label()}")
        self.emit(f"  Difficulty:            {difficulty.name}")
        self.emit(f"  Service index:         "
                  f"{self.career.service_index():.1f} of 100 "
                  f"({self.career.index_band()})")
        self.emit(f"  Shift:                 {self.career.shift}")

        held = len(self.career.qualifications)
        self.emit(f"  Qualifications:        {held} of "
                  f"{len(QUALIFICATIONS)} held")

        self.emit("\n  'report' for the board, 'mlt <report>' to measure a "
                  "loop,")
        self.emit("  'qual' for your craft record.")
        if self.career.shift == 1 and not self.career.reports_closed:
            self.emit("  'set game.difficulty craft' if you want the shift "
                      "worked the hard way.")

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

    def _get_tsps_briefing(self) -> str:
        """Get TSPS Operator briefing."""
        return """
TSPS OPERATOR BRIEFING

Primary Responsibilities:
- Traffic Service Position System operations
- Operator-assisted call completion
- Directory assistance coordination
- Collect call processing

Current Priorities:
- Monitor TSPS position utilization (78% busy hour)
- Coordinate operator training session 16:00-17:30
- Review directory assistance accuracy metrics
- Process special billing arrangements

Key Commands: tsps, operator, directory, collect, billing
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

    def _get_tnds_briefing(self) -> str:
        """Get TNDS Analyst briefing."""
        return """
TNDS ANALYST BRIEFING

Primary Responsibilities:
- Total Network Data System operations
- Traffic data collection and analysis
- Network performance measurement
- Capacity planning data preparation

Current Priorities:
- Complete TNDS data collection cycle 1 of 4
- Generate traffic analysis reports for planning
- Monitor network performance against objectives
- Prepare capacity forecasting models

Key Commands: tnds, netdata, analysis, forecast, modeling, traffic
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

    def cmd_clli(self, args: Optional[List[str]] = None) -> str:
        """Decode and look up COMMON LANGUAGE location identifiers."""
        args = args or []

        if not args:
            return f"""COMMON LANGUAGE Location Identification
{'=' * 62}

Every location in the Bell System carries a CLLI code, and every record
that refers to a place refers to it by that code.

STRUCTURE (11 characters)
{'=' * 62}
  Positions  Segment          Encodes                    Characters
  1-4        Geographical     place, town or locality    alphabetic
  5-6        Geopolitical     state, province, country   alphabetic
  7-8        Network site     building within the place  alphanumeric
  9-11       Network entity   equipment or work centre   alphanumeric

The first 8 characters identify a building. All 11 identify a particular
machine or entity within it.

SWITCHING ENTITY CODES
{'=' * 62}
  MG0-MG9    Marker group        crossbar
  SG0-SG9    Step group          step-by-step
  CG0-CG9    Control group       electronic switching, stored program
  DS0        Digital switch      digital time-division (1982 and later)
  nnT        Toll or tandem switching entity
  nnB        Board - operator and switchboard positions
  Letters I, O, U, W and Y are not used in entity codes.

ADMINISTRATION
{'=' * 62}
COMMON LANGUAGE codes are AT&T Co Standard, published in the Bell System
Practices Division 795. The governing practice is BSP 795-100-100,
Issue 5, October 1982.

Commands:
  clli decode <code>       Break a code into its segments
  clli office <npa><nxx>   Show the code for an office
  clli examples            Codes of known offices"""

        action = args[0].lower()

        if action == 'decode' and len(args) > 1:
            code = args[1].upper()
            parsed = parse_clli(code)
            if parsed is None:
                return (f"clli: '{args[1]}' is not a well formed CLLI code.\n"
                        "A code is 11 characters, the first 6 alphabetic.")
            return f"""CLLI Decode: {parsed}
{'=' * 55}
Geographical  {parsed.place}    place, town or locality
Geopolitical  {parsed.state}      state, province or country
Network site  {parsed.building}      building within that place
Entity        {parsed.entity}     {describe_entity(parsed.entity)}

Building code (8 character form): {parsed.building_code()}

{ATTESTED_CLLI.get(code, 'Not among the codes recorded here as attested.')}"""

        if action == 'office' and len(args) > 1:
            key = args[1].replace('-', '')
            office = self.central_offices.get(key)
            if office is None:
                return f"clli: no office {args[1]} in the office records"
            return f"""Office Record: {office['clli']}
{'=' * 55}
CLLI:             {office['clli']}
Building:         {office['clli'][:8]}
Place:            {office['city']}, {office['state']}
Code:             {office['npa']}-{office['nxx']}
Switching system: {office.get('switch_name', office['switch_type'])}
Entity:           {describe_entity(office['clli'][8:])}
In service:       {office['installation_date']}
Line capacity:    {office['capacity']:,}
Utilization:      {office['utilization']}%
Trunk groups:     {office['trunk_groups']}
Maintenance:      {office['maintenance_status']}"""

        if action == 'examples':
            output = f"""Attested CLLI Codes
{'=' * 62}

These codes are recorded from published switching rosters; they denoted
real offices.

"""
            for code, description in ATTESTED_CLLI.items():
                parsed = parse_clli(code)
                output += f"{code}\n"
                output += (f"  {parsed.place} / {parsed.state} / "
                           f"{parsed.building} / {parsed.entity}\n")
                output += f"  {description}\n\n"
            return output.rstrip()

        return (f"clli: Unknown option '{args[0]}'\n"
                "Available commands: decode <code>, office <npanxx>, examples")

    def cmd_cosmos(self, args: Optional[List[str]] = None) -> str:
        """Wire centre administration: frame assignment and load balance."""
        args = args or []

        if not args or args[0].lower() == 'status':
            frame = self.frame_state
            return f"""COSMOS - Computer System for Main Frame Operations
Wire Centre Administration
{self.clock.timestamp()}
{'=' * 62}

The main frame here is the main distributing frame, the manually
operated field of terminations where outside plant cable meets central
office equipment - not a mainframe computer. COSMOS keeps the frame from
congesting and the switching equipment in load balance.

FRAME STATUS
{'=' * 62}
Wire centre:              {frame['clli']}
Frame type:               {frame['frame_type']}
Vertical appearances:     {frame['verticals']:,} (outside plant, protected)
Horizontal appearances:   {frame['horizontals']:,} (office equipment)
Assigned:                 {frame['assigned']:,} ({frame['assigned'] / frame['verticals']:.1%})
Spare:                    {frame['verticals'] - frame['assigned']:,}

JUMPER ADMINISTRATION
{'=' * 62}
Average jumper length:    {frame['avg_jumper_ft']:.1f} feet
Long jumpers (over 40ft): {frame['long_jumpers']} - candidates for rearrangement
Preferential assignments: {frame['preferential']:.1%} of placements this week
Pending frame orders:     {frame['pending_orders']}

LOAD BALANCE
{'=' * 62}
Line link groups:         {frame['line_groups']}
Load balance index:       {frame['balance_index']:.3f}
Worst group deviation:    {frame['worst_deviation']:+.1%}
Assessment:               {'WITHIN OBJECTIVE' if abs(frame['worst_deviation']) < 0.08 else 'REBALANCE RECOMMENDED'}

Commands:
  cosmos assign <number>     Assign office equipment and a frame pair
  cosmos jumper <number>     Show the cross-connect for a line
  cosmos balance             Load balance across line link groups
  cosmos pending             Frame work orders awaiting the frame

Note: COSMOS transaction syntax is not reproduced from any source
available here. These commands are this simulation's own."""

        action = args[0].lower()

        if action == 'assign' and len(args) > 1:
            number = args[1]
            frame = self.frame_state
            vertical = random.randint(1, frame['verticals'])
            horizontal = random.randint(1, frame['horizontals'])
            jumper = abs(vertical - horizontal) / 100 + random.uniform(3, 12)
            return f"""COSMOS Line Assignment
{'=' * 55}
Telephone number:     {number}
Wire centre:          {frame['clli']}

ASSIGNMENT
{'=' * 45}
Cable pair:           {random.randint(1, 900)} pair {random.randint(1, 25)}
Vertical appearance:  {vertical:05d}
Horizontal appearance:{horizontal:05d}
Office equipment:     LEN {random.randint(0, 7)}-{random.randint(0, 19)}-{random.randint(0, 9)}-{random.randint(0, 9)}
Line link group:      {random.randint(1, frame['line_groups'])}

Estimated jumper:     {jumper:.1f} feet
Placement:            {'Preferential - short jumper' if jumper < 20 else 'Standard'}

A frame work order has been printed for the frame technician.
Load balance after assignment: {frame['balance_index'] + random.uniform(-0.004, 0.004):.3f}"""

        if action == 'jumper' and len(args) > 1:
            number = args[1]
            return f"""COSMOS Cross-Connect Record
{'=' * 55}
Telephone number:     {number}
Wire centre:          {self.frame_state['clli']}

CROSS-CONNECT
{'=' * 45}
Vertical (cable):     {random.randint(1, 9999):05d}  tip and ring
Protector unit:       {random.choice(['Carbon block', 'Gas tube'])}, in service
Horizontal (equip):   {random.randint(1, 9999):05d}
Jumper length:        {random.uniform(6, 55):.1f} feet
Jumper run:           Shelf {random.randint(1, 14)}, trough {random.randint(1, 9)}
Placed:               {(self.clock.now() - timedelta(days=random.randint(30, 2400))).strftime('%B %Y')}

Setting the protector unit to its inactive position disconnects the
customer temporarily without disturbing the cross-connection."""

        if action == 'balance':
            frame = self.frame_state
            output = f"""COSMOS Load Balance
{'=' * 62}
Wire centre:          {frame['clli']}
Balance index:        {frame['balance_index']:.3f}

Load balance keeps originating traffic even across the line link groups,
so no group of concentrators carries disproportionate load in the busy
hour.

GROUP        LINES    ORIGINATING CCS   DEVIATION
{'-' * 62}"""
            for group in range(1, frame['line_groups'] + 1):
                lines = random.randint(480, 640)
                ccs = random.randint(18, 32)
                deviation = random.uniform(-0.09, 0.09)
                flag = '  REBALANCE' if abs(deviation) > 0.08 else ''
                output += (f"\n{group:<12} {lines:>5}    {ccs:>10}"
                           f"        {deviation:>+6.1%}{flag}")
            return output + """

Groups outside the objective are rearranged by reassigning line
equipment at the next convenient frame visit."""

        if action == 'pending':
            frame = self.frame_state
            output = f"""COSMOS Frame Work Orders
{'=' * 62}
Wire centre:          {frame['clli']}
Orders pending:       {frame['pending_orders']}

ORDER      TYPE          NUMBER        ACTION
{'-' * 62}"""
            for index in range(frame['pending_orders']):
                order_type = random.choice(['CONNECT', 'DISCONNECT', 'CHANGE', 'TRANSFER'])
                output += (f"\nFWO-{random.randint(1000, 9999)}   {order_type:<13} "
                           f"{random.randint(200, 999)}-{random.randint(1000, 9999)}   "
                           f"{'Run jumper' if order_type == 'CONNECT' else 'Remove jumper' if order_type == 'DISCONNECT' else 'Rearrange'}")
            return output + "\n\nOrders are worked in sequence by the frame technician."

        return (f"cosmos: Unknown option '{args[0]}'\n"
                "Available commands: status, assign, jumper, balance, pending")

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

    def emit(self, text: str = '') -> None:
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
        Load NANPA geographic data for Bell System infrastructure.

        The source file is 48 MB, so the parsed result is cached for the life
        of the process: it is static reference data, and re-reading it for
        every terminal made construction take a second apiece.
        """
        import csv

        cached = BellSystemTerminal._NANPA_CACHE
        if cached is not None:
            self.nanpa_data = cached
            self.bell_system_exchanges = {}
            return

        # Load and process NANPA data for authentic Bell System operations
        self.nanpa_data = {}
        self.bell_system_exchanges = {}

        try:
            # Read NANPA CSV data
            with open('attached_assets/full_dataset_csv.csv', 'r') as csvfile:
                reader = csv.DictReader(csvfile)

                # Sample and process key Bell System service areas from 1978-1983 era
                bell_system_areas = ['202', '212', '213', '214', '215', '216', '301', '302', '303', '305', '312', '313', '314', '401', '404', '412', '413', '414', '415', '416', '501', '502', '503', '504', '505', '507', '509', '512', '513', '515', '516', '517', '518', '601', '602', '603', '605', '606', '607', '608', '609', '612', '614', '615', '616', '617', '618', '701', '702', '703', '704', '712', '713', '714', '715', '716', '717', '801', '802', '803', '804', '805', '806', '807', '808', '812', '813', '814', '815', '816', '817', '901', '902', '904', '906', '907', '912', '913', '914', '915', '916', '918', '919']

                wanted = set(bell_system_areas)
                per_npa_cap = 40

                for row in reader:
                    npa = row['npa']
                    if npa not in wanted:
                        continue
                    if len(self.nanpa_data.get(npa, {})) >= per_npa_cap:
                        continue

                    nxx = row['nxx']
                    city = row['city']
                    state = row['state']

                    # Focus on US Bell System territories
                    if npa in bell_system_areas and row['country'] == 'United States':
                        if npa not in self.nanpa_data:
                            self.nanpa_data[npa] = {}

                        if nxx not in self.nanpa_data[npa]:
                            self.nanpa_data[npa][nxx] = []

                        self.nanpa_data[npa][nxx].append({
                            'city': city,
                            'state': state,
                            'latitude': row.get('latitude', '0'),
                            'longitude': row.get('longitude', '0')
                        })

            BellSystemTerminal._NANPA_CACHE = self.nanpa_data

        except FileNotFoundError:
            # Fallback to core Bell System data if file not accessible
            self.nanpa_data = {
                '212': {'555': [{'city': 'New York', 'state': 'NY', 'latitude': '40.7128', 'longitude': '-74.0060'}]},
                '213': {'555': [{'city': 'Los Angeles', 'state': 'CA', 'latitude': '34.0522', 'longitude': '-118.2437'}]},
                '312': {'555': [{'city': 'Chicago', 'state': 'IL', 'latitude': '41.8781', 'longitude': '-87.6298'}]},
                '617': {'555': [{'city': 'Boston', 'state': 'MA', 'latitude': '42.3601', 'longitude': '-71.0589'}]},
                '202': {'555': [{'city': 'Washington', 'state': 'DC', 'latitude': '38.9072', 'longitude': '-77.0369'}]},
                '301': {'555': [{'city': 'Silver Spring', 'state': 'MD', 'latitude': '38.9907', 'longitude': '-77.0261'}]}
            }

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
                        **placement,
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

    def _initialize_enhanced_ticket_system(self) -> None:
        """Initialize comprehensive ticket management system with realistic scenarios."""

        # Enhanced ticket categories with Bell System authenticity
        self.ticket_categories = {
            'NETWORK_OUTAGE': {
                'priority_weights': {'CRITICAL': 0.15, 'MAJOR': 0.35, 'MINOR': 0.50},
                'typical_duration': {'CRITICAL': (30, 240), 'MAJOR': (60, 480), 'MINOR': (120, 720)},
                'customer_impact': {'CRITICAL': (1000, 50000), 'MAJOR': (100, 5000), 'MINOR': (10, 500)}
            },
            'EQUIPMENT_FAILURE': {
                'priority_weights': {'CRITICAL': 0.20, 'MAJOR': 0.45, 'MINOR': 0.35},
                'typical_duration': {'CRITICAL': (45, 180), 'MAJOR': (90, 360), 'MINOR': (180, 600)},
                'customer_impact': {'CRITICAL': (500, 25000), 'MAJOR': (50, 2500), 'MINOR': (5, 250)}
            },
            'SERVICE_INTERRUPTION': {
                'priority_weights': {'CRITICAL': 0.10, 'MAJOR': 0.30, 'MINOR': 0.60},
                'typical_duration': {'CRITICAL': (15, 120), 'MAJOR': (30, 240), 'MINOR': (60, 480)},
                'customer_impact': {'CRITICAL': (100, 10000), 'MAJOR': (25, 1000), 'MINOR': (1, 100)}
            },
            'MAINTENANCE': {
                'priority_weights': {'CRITICAL': 0.05, 'MAJOR': 0.25, 'MINOR': 0.70},
                'typical_duration': {'CRITICAL': (60, 300), 'MAJOR': (120, 480), 'MINOR': (240, 720)},
                'customer_impact': {'CRITICAL': (0, 5000), 'MAJOR': (0, 500), 'MINOR': (0, 50)}
            },
            'TRAFFIC_ANOMALY': {
                'priority_weights': {'CRITICAL': 0.08, 'MAJOR': 0.32, 'MINOR': 0.60},
                'typical_duration': {'CRITICAL': (20, 90), 'MAJOR': (45, 180), 'MINOR': (90, 360)},
                'customer_impact': {'CRITICAL': (1000, 100000), 'MAJOR': (100, 10000), 'MINOR': (10, 1000)}
            }
        }

        # Initialize dynamic ticket generation
        self.active_tickets: List[TroubleTicket] = []
        self.ticket_counter = 4500  # Start from realistic Bell System ticket numbers
        self.completed_tickets = []

        # Generate initial realistic ticket scenarios
        self._generate_initial_tickets()

    def _generate_initial_tickets(self) -> None:
        """Generate initial realistic trouble tickets for the simulation session."""

        # Generate 8-15 initial tickets for authentic operational load
        initial_ticket_count = random.randint(8, 15)

        for _ in range(initial_ticket_count):
            self._create_realistic_ticket()

    def _create_realistic_ticket(self) -> dict:
        """Create a realistic trouble ticket with authentic Bell System characteristics."""
        import random

        # Select ticket category and priority
        category = random.choice(list(self.ticket_categories.keys()))
        category_data = self.ticket_categories[category]

        # Determine priority based on realistic weights
        priority_choices = list(category_data['priority_weights'].keys())
        priority_weights = list(category_data['priority_weights'].values())
        priority = random.choices(priority_choices, weights=priority_weights)[0]

        # Generate ticket ID
        self.ticket_counter += random.randint(1, 5)
        ticket_id = f"TK-{self.ticket_counter}"

        # Select affected infrastructure from NANPA data
        affected_office = self._select_affected_infrastructure()

        # Generate realistic scenario based on category
        scenario = self._generate_ticket_scenario(category, priority, affected_office)

        # Calculate realistic duration and impact
        duration_range = category_data['typical_duration'][priority]
        estimated_duration = random.randint(*duration_range)

        impact_range = category_data['customer_impact'][priority]
        customer_impact = random.randint(*impact_range)

        # Create comprehensive ticket
        ticket = {
            'id': ticket_id,
            'category': category,
            'priority': priority,
            'title': scenario['title'],
            'description': scenario['description'],
            'affected_office': affected_office,
            'customer_impact': customer_impact,
            'estimated_duration': estimated_duration,
            'status': 'OPEN',
            'assigned_team': scenario['assigned_team'],
            'created_time': self.clock.now() - timedelta(minutes=random.randint(10, 480)),
            'escalation_level': 1,
            'technical_details': scenario['technical_details'],
            'required_actions': scenario['actions'],
            'equipment_involved': scenario.get('equipment', []),
            'geographic_scope': scenario.get('scope', 'LOCAL'),
            'business_impact': self._calculate_business_impact(priority, customer_impact),
            'resolution_steps': []
        }

        self.active_tickets.append(ticket)
        return ticket

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

    def _select_affected_infrastructure(self) -> dict:
        """Select realistic affected infrastructure from Bell System network."""

        if self.central_offices:
            office_code = random.choice(list(self.central_offices.keys()))
            return self.central_offices[office_code]
        else:
            # Fallback to major metropolitan areas
            return {
                'npa': '212',
                'nxx': '555',
                'city': 'New York',
                'state': 'NY',
                'switch_type': '4ESS',
                'capacity': 35000,
                'utilization': 78
            }

    # Cities large enough to have carried a metropolitan-class machine.
    METROPOLITAN_CITIES = frozenset({
        'New York', 'Brooklyn', 'Chicago', 'Los Angeles', 'Philadelphia',
        'Detroit', 'Houston', 'Boston', 'San Francisco', 'Washington',
        'Dallas', 'Cleveland', 'Baltimore', 'Saint Louis', 'St. Louis',
        'Pittsburgh', 'Milwaukee', 'Atlanta', 'Newark', 'Minneapolis',
        'Seattle', 'Denver', 'Miami', 'Phoenix', 'San Diego',
    })

    def _format_carrier_bands(self) -> str:
        """
        Render the L-carrier line bands and the multiplex hierarchy.

        The two are distinct and were previously conflated: 564-3084 kHz is
        the basic mastergroup, an assembly band, not the L4 line spectrum.
        """
        lines = ["  LINE SPECTRUM TRANSMITTED ON COAXIAL"]
        for code, system in L_CARRIER_SYSTEMS.items():
            lines.append(
                f"    {code:<4} {system.line_band():<26}"
                f"{system.channels:>6,} channels  "
                f"{system.repeater_spacing_miles:g} mi repeaters"
            )
        lines.append("")
        lines.append("  MULTIPLEX ASSEMBLY HIERARCHY")
        for level in MULTIPLEX_HIERARCHY:
            pilot = MULTIPLEX_PILOTS_KHZ.get(level.name)
            pilot_text = f"pilot {pilot:,.2f} kHz" if pilot else ""
            lines.append(
                f"    {level.name:<26}{level.band():<22}"
                f"{level.channels:>5,} ch  {pilot_text}"
            )
        lines.append("")
        lines.append("  L3 LINE SIGNAL ASSEMBLY (3 mastergroups + 1 supergroup = 1,860)")
        for name, low, high in L3_LINE_ASSEMBLY:
            lines.append(f"    {name:<20}{low:>7,.0f} - {high:>7,.0f} kHz")
        return "\n".join(lines)

    def _initialize_frame_state(self) -> None:
        """
        Set up the main distributing frame this wire centre works.

        Congestion and long cross-connects on the frame are what COSMOS
        exists to minimise, so the frame carries the numbers those
        objectives are measured against.
        """
        verticals = random.randint(8000, 24000)
        self.frame_state: Dict[str, Any] = {
            'clli': 'MRHLNJ01CG0',
            'frame_type': random.choice([
                'COSMIC II modular', 'COSMIC I modular', 'Low-profile conventional',
            ]),
            'verticals': verticals,
            'horizontals': int(verticals * random.uniform(0.85, 1.05)),
            'assigned': int(verticals * random.uniform(0.62, 0.88)),
            'avg_jumper_ft': random.uniform(14, 34),
            'long_jumpers': random.randint(20, 210),
            'preferential': random.uniform(0.72, 0.95),
            'pending_orders': random.randint(3, 9),
            'line_groups': random.randint(6, 14),
            'balance_index': random.uniform(0.94, 0.995),
            'worst_deviation': random.uniform(-0.11, 0.11),
        }

    def _office_clli(self, city: str, state: str, switch_type: str,
                     is_toll: bool = False, ordinal: int = 0) -> str:
        """
        Return the COMMON LANGUAGE location identifier for an office.

        Falls back to the eight-character building form when a full code
        cannot be built, rather than emitting something malformed.
        """
        code = build_clli(city, STATE_CODES.get(state, state), 'CO',
                          entity_for_switch(switch_type, is_toll, ordinal))
        return str(code) if code is not None else ''

    def _generate_switch_placement(self, city: str) -> Dict[str, Any]:
        """
        Choose a switching machine and a cutover year that could coexist.

        Type and year were previously drawn independently, which produced
        offices like a 5ESS installed in 1965 - seventeen years before the
        first one carried traffic. Here the year is drawn first, only machines
        already in service by then are eligible, and the size class is taken
        from what the machine was actually engineered for.

        Args:
            city: The city the office serves, which decides the size class

        Returns:
            The switch_type, capacity and installation_date fields
        """
        # The simulated present. Offices are cut over some years before it.
        current_year = self.clock.now().year
        installed = random.randint(max(1919, current_year - 40), current_year)

        metropolitan = city in self.METROPOLITAN_CITIES
        pool = METROPOLITAN_SWITCHES if metropolitan else RURAL_SWITCHES
        eligible = available_in(installed, pool)
        if not eligible:
            # Before any machine in the pool existed, step-by-step served.
            eligible = ['SXS']
            installed = max(installed, SWITCHING_SYSTEMS['SXS'].first_service)

        code = random.choice(eligible)
        system = SWITCHING_SYSTEMS[code]
        return {
            'switch_type': code,
            'switch_name': system.name,
            'capacity': random.randint(system.min_lines, system.max_lines),
            'installation_date': str(installed),
        }

    def _generate_ticket_scenario(self, category: str, priority: str, office: dict) -> dict:
        """Generate realistic ticket scenario based on category and Bell System operations."""
        import random

        city = office['city']
        state = office['state']
        switch_type = office['switch_type']
        npa = office['npa']

        scenarios = {
            'NETWORK_OUTAGE': {
                'CRITICAL': [
                    {
                        'title': f"Total service outage - {city} central office",
                        'description': f"Complete loss of dial tone affecting {npa} area code in {city}, {state}",
                        'assigned_team': 'Emergency Response Team Alpha',
                        'technical_details': f"Primary {switch_type} switching system failure. All trunk groups down. Backup power systems operational.",
                        'actions': ['Dispatch emergency technicians', 'Activate backup switching', 'Notify major customers', 'Coordinate with NOC'],
                        'equipment': [f'{switch_type}-MAIN', 'POWER-PRIMARY', 'TRUNK-GROUPS'],
                        'scope': 'REGIONAL'
                    },
                    {
                        'title': f"Inter-office trunk failure - {city} to major hubs",
                        'description': f"Loss of all long-distance connectivity from {city} affecting interstate traffic",
                        'assigned_team': 'Network Operations Emergency',
                        'technical_details': "Fiber optic cable cut on Route 80 corridor. Microwave backup circuits at capacity.",
                        'actions': ['Locate cable fault', 'Deploy emergency repair crew', 'Reroute traffic via alternate paths', 'Customer notifications'],
                        'equipment': ['FIBER-MAIN', 'MICROWAVE-BACKUP', 'ROUTING-SYSTEMS'],
                        'scope': 'INTERSTATE'
                    }
                ],
                'MAJOR': [
                    {
                        'title': f"Partial service degradation - {city} {switch_type} switch",
                        'description': f"50% capacity loss on {switch_type} switch affecting {city} area",
                        'assigned_team': 'Switching Maintenance Team',
                        'technical_details': f"Memory module failure in {switch_type} central processing unit. System running on backup processors.",
                        'actions': ['Replace faulty memory modules', 'Run comprehensive diagnostics', 'Monitor system performance', 'Prepare for cutover if needed'],
                        'equipment': [f'{switch_type}-CPU', 'MEMORY-MODULES', 'BACKUP-SYSTEMS'],
                        'scope': 'LOCAL'
                    }
                ],
                'MINOR': [
                    {
                        'title': f"Intermittent service issues - {city} area",
                        'description': f"Sporadic call setup failures reported in {npa} area code",
                        'assigned_team': 'Local Maintenance',
                        'technical_details': "Line interface circuit experiencing intermittent failures. Error rate: 0.3%",
                        'actions': ['Test line interface circuits', 'Monitor error patterns', 'Schedule preventive maintenance'],
                        'equipment': ['LINE-INTERFACE', 'DIAGNOSTIC-SYSTEMS'],
                        'scope': 'LOCAL'
                    }
                ]
            },
            'EQUIPMENT_FAILURE': {
                'CRITICAL': [
                    {
                        'title': f"Primary power system failure - {city} CO",
                        'description': f"Main power feed lost at {city} central office, running on battery backup",
                        'assigned_team': 'Power Systems Emergency',
                        'technical_details': f"Utility power failure affecting {city} CO. Battery backup operational for 8 hours. Generator startup failed.",
                        'actions': ['Repair generator system', 'Monitor battery levels', 'Coordinate with utility company', 'Prepare for emergency shutdown'],
                        'equipment': ['POWER-MAIN', 'GENERATOR', 'BATTERY-BACKUP'],
                        'scope': 'LOCAL'
                    }
                ],
                'MAJOR': [
                    {
                        'title': f"Crossbar switch mechanical failure - {city}",
                        'description': f"Crossbar switching matrix experiencing mechanical binding in {city} office",
                        'assigned_team': 'Electromechanical Repair',
                        'technical_details': "Contact spring tension loss causing call setup failures. Estimated 25% capacity reduction.",
                        'actions': ['Spring tension adjustment', 'Contact cleaning', 'Lubrication service', 'Performance testing'],
                        'equipment': ['CROSSBAR-MATRIX', 'CONTACT-SPRINGS', 'MECHANICAL-SYSTEMS'],
                        'scope': 'LOCAL'
                    }
                ],
                'MINOR': [
                    {
                        'title': f"Trunk interface card failure - {city}",
                        'description': "Single trunk interface card malfunction affecting 24 circuits",
                        'assigned_team': 'Circuit Maintenance',
                        'technical_details': "T1 interface card showing signal level degradation. BER: 10^-4",
                        'actions': ['Replace interface card', 'Test circuit performance', 'Update maintenance records'],
                        'equipment': ['T1-INTERFACE', 'TRUNK-CIRCUITS'],
                        'scope': 'LOCAL'
                    }
                ]
            },
            'SERVICE_INTERRUPTION': {
                'CRITICAL': [
                    {
                        'title': f"Emergency services circuit down - {city}",
                        'description': f"911 emergency services losing connectivity in {city} area",
                        'assigned_team': 'Emergency Services Team',
                        'technical_details': "Dedicated emergency trunk group failure. Backup circuits activated but limited capacity.",
                        'actions': ['Immediate circuit repair', 'Verify backup operations', 'Notify emergency dispatch', 'Monitor call overflow'],
                        'equipment': ['EMERGENCY-TRUNKS', 'BACKUP-CIRCUITS', 'DISPATCH-SYSTEMS'],
                        'scope': 'REGIONAL'
                    }
                ],
                'MAJOR': [
                    {
                        'title': f"Business customer group outage - {city}",
                        'description': f"Major business district losing phone service in {city}",
                        'assigned_team': 'Business Services',
                        'technical_details': "Serving area interface failure affecting 500+ business lines. PBX connections down.",
                        'actions': ['Repair serving area interface', 'Test PBX connections', 'Customer notifications', 'Service verification'],
                        'equipment': ['SAI-EQUIPMENT', 'PBX-INTERFACES', 'BUSINESS-LINES'],
                        'scope': 'LOCAL'
                    }
                ],
                'MINOR': [
                    {
                        'title': f"Residential area intermittent service - {city}",
                        'description': f"Sporadic dial tone issues in residential area of {city}",
                        'assigned_team': 'Residential Services',
                        'technical_details': "Line concentrator showing intermittent failures. Affects approximately 50 customers.",
                        'actions': ['Test line concentrator', 'Check subscriber loops', 'Monitor service quality'],
                        'equipment': ['LINE-CONCENTRATOR', 'SUBSCRIBER-LOOPS'],
                        'scope': 'LOCAL'
                    }
                ]
            }
        }

        if category in scenarios and priority in scenarios[category]:
            return random.choice(scenarios[category][priority])
        else:
            # Generic fallback scenario
            return {
                'title': f"System issue - {city} area",
                'description': f"Technical issue affecting service in {city}, {state}",
                'assigned_team': 'General Maintenance',
                'technical_details': "System requiring investigation and repair",
                'actions': ['Investigate issue', 'Implement repair', 'Test service'],
                'equipment': ['SYSTEM-COMPONENTS'],
                'scope': 'LOCAL'
            }

    def _calculate_business_impact(self, priority: str, customer_count: int) -> dict:
        """Calculate business impact metrics for trouble tickets."""

        # Revenue impact calculations based on 1983 Bell System rates
        avg_revenue_per_customer_hour = random.uniform(0.85, 2.45)  # 1983 rates

        impact = {
            'revenue_loss_hour': int(customer_count * avg_revenue_per_customer_hour),
            'customer_calls_affected': customer_count * random.randint(2, 8),
            'business_severity': priority,
            'regulatory_exposure': priority == 'CRITICAL',
            'media_attention_risk': customer_count > 10000,
            'service_level_impact': {
                'CRITICAL': 'Severe degradation',
                'MAJOR': 'Moderate impact',
                'MINOR': 'Minimal impact'
            }[priority]
        }

        return impact

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

        role_commands = self.ROLE_COMMANDS.get(self.role)
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

    def cmd_man(self, args: List[str]) -> str:
        """
        Display manual pages for Bell System commands.

        Provides comprehensive documentation for all commands and sub-commands
        with authentic Bell System formatting and terminology.

        Args:
            args: Command arguments [command_name] or [-k keyword]

        Returns:
            Formatted manual page or search results
        """
        if not args:
            return "Usage: man <command> or man -k <keyword>"

        if args[0] == "-k" and len(args) > 1:
            # Keyword search
            keyword = args[1].lower()
            matches = []
            for cmd, content in self.man_pages.items():
                if keyword in content.lower():
                    matches.append(cmd)

            if matches:
                return f"Manual pages containing '{keyword}':\n" + "\n".join(f"  {cmd}(1)" for cmd in matches)
            else:
                return f"No manual pages found for keyword '{keyword}'"

        command = args[0].lower()
        if command in self.man_pages:
            return self.man_pages[command]
        else:
            return f"No manual entry for {command}"

    # Basic UNIX commands
    def cmd_ps(self, args: Optional[List[str]] = None) -> str:
        """
        Display Bell System processes in authentic UNIX V7 format.

        Shows currently running processes on the Bell System workstation
        including system daemons, switching processes, and user sessions.

        Returns:
            Process listing formatted in traditional ps output style
        """
        output = "  PID TTY  TIME COMMAND\n"
        for proc in self.processes:
            output += f"{proc['pid']:5d} {proc['tty']:>3} {proc['time']:>5} {proc['command']}\n"
        return output

    def cmd_who(self, args: Optional[List[str]] = None) -> str:
        """
        Display currently logged-in Bell System users.

        Shows active user sessions on the Bell System workstation with
        login times and terminal locations for operational awareness.

        Returns:
            User listing with terminals and login information
        """
        output = ""
        for user in self.users:
            person = CRAFT.get(user['user'])
            title = f"  {person.title}" if person else ""
            output += (f"{user['user']:<10} tty{user['tty']:<4} "
                       f"{user['login']:<8} ({user['location']}){title}\n")
        return output

    def cmd_ls(self, args: List[str]) -> str:
        """
        List directory contents in the Bell System filesystem.

        Provides basic directory listing functionality for navigating
        the authentic Bell System file structure and operational directories.

        Args:
            args: Command arguments (currently unused, basic implementation)

        Returns:
            Directory contents or error message
        """
        path = self.current_directory
        if path in self.filesystem and "files" in self.filesystem[path]:
            files = self.filesystem[path]["files"]
            return "  ".join(files)
        return "ls: cannot access directory"

    def cmd_pwd(self, args: Optional[List[str]] = None) -> str:
        """Print current working directory."""
        return self.current_directory

    def cmd_date(self, args: Optional[List[str]] = None) -> str:
        """Display current system date and time in the configured layout."""
        return self.clock.date_command()

    def cmd_df(self, args: Optional[List[str]] = None) -> str:
        """Display filesystem disk space usage."""
        return """/dev/hp0a   1814   431
/dev/hp0g  24661  3902
/dev/hp0h  12572  2317"""

    # Bell System specific commands (implementations would continue...)
    def cmd_trunk(self, args: List[str]) -> str:
        """Enhanced trunk status and management with realistic state-aware behavior."""

        # Update trunk states based on time and network conditions
        self._update_trunk_states()

        if not args or args[0] == "status":
            # Dynamic trunk status with real-time variability
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")
            active_count = len([tg for tg in self.trunk_groups.values() if tg["status"] == "ACTIVE"])
            total_count = len(self.trunk_groups)
            avg_utilization = sum(tg["utilization"] for tg in self.trunk_groups.values() if tg["status"] == "ACTIVE") // active_count

            # Add realistic alerts and warnings
            alerts = []
            for tg_name, tg_data in self.trunk_groups.items():
                if tg_data["utilization"] > 85:
                    alerts.append(f"HIGH UTIL: {tg_name} at {tg_data['utilization']}%")
                elif tg_data["quality"] < 0.995:
                    alerts.append(f"QUALITY: {tg_name} below threshold")

            status_output = f"""Bell System Trunk Group Status Summary
{current_time}

Trunk Group      Capacity   Utilization   Status      Route        Quality
-----------      --------   -----------   ------      -----        -------"""

            for tg_name, tg_data in self.trunk_groups.items():
                util_status = "HIGH" if tg_data["utilization"] > 80 else "NORMAL" if tg_data["utilization"] > 30 else "LOW"
                if tg_data["status"] == "MAINT":
                    util_status = "MAINT"
                quality_pct = f"{tg_data['quality']:.3f}" if tg_data["quality"] > 0 else "N/A"
                status_output += f"\n{tg_name:<16} {tg_data['capacity']:<10} {tg_data['utilization']:>3}%        {util_status:<8}    {tg_data['route']:<12} {quality_pct}"

            status_output += f"""

Network Summary:
  Active Trunk Groups:     {active_count}/{total_count}
  Average Utilization:     {avg_utilization}%
  Peak Traffic Period:     {self._get_peak_period()}
  Revenue This Hour:       ${self.network_metrics['revenue_hour']:,}

System Alerts:"""

            if alerts:
                for alert in alerts[:3]:  # Show up to 3 alerts
                    status_output += f"\n  ⚠ {alert}"
            else:
                status_output += "\n  ✓ All systems operating normally"

            status_output += """

Commands:
  trunk detail <TG-xxx>     Detailed analysis and diagnostics
  trunk test <TG-xxx>       Initiate testing sequence
  trunk traffic <TG-xxx>    Real-time traffic monitoring
  trunk maintenance         Scheduled maintenance status"""

            return status_output

        elif args[0] == "detail" and len(args) > 1:
            tg_name = args[1].upper()
            if tg_name not in self.trunk_groups:
                return f"trunk: ERROR - Trunk group {tg_name} not found\nAvailable groups: {', '.join(self.trunk_groups.keys())}"

            tg = self.trunk_groups[tg_name]
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            # Calculate realistic metrics
            active_channels = int(tg["capacity"] * tg["utilization"] / 100) if tg["status"] == "ACTIVE" else 0
            setup_time = random.uniform(0.8, 2.4)
            error_rate = random.uniform(0.0001, 0.01) if tg["quality"] < 0.998 else random.uniform(0.00001, 0.0001)

            detail_output = f"""Detailed Trunk Group Analysis: {tg_name}
Analysis Time: {current_time}

Configuration:
  Trunk Group:        {tg_name}
  Circuit Type:       T1 Digital Carrier System
  Total Capacity:     {tg["capacity"]} voice channels
  Route:              {tg["route"]} Direct
  Equipment:          Western Electric D4 Channel Bank

Current Performance:
  Active Calls:       {active_channels} of {tg["capacity"]} channels
  Utilization:        {tg["utilization"]}% ({'Normal' if 40 <= tg["utilization"] <= 80 else 'High' if tg["utilization"] > 80 else 'Low'} range)
  Answer/Seizure:     {tg["quality"]:.1%} (Target: >95.0%)
  Post-Dial Delay:    {setup_time:.1f} seconds average

Traffic Analysis:
  Busy Hour CCS:      {int(active_channels * 36)} (within capacity)
  Peak Utilization:   {min(100, tg["utilization"] + random.randint(5, 15))}% at {random.randint(14, 16)}:{random.randint(0, 59):02d}
  Average Hold Time:  {random.uniform(2.8, 4.2):.1f} minutes
  Overflow Events:    {random.randint(0, 3)} (last 24 hours)

Quality Metrics:
  Bit Error Rate:     {error_rate:.2e} ({'Excellent' if error_rate < 0.0001 else 'Good' if error_rate < 0.001 else 'Marginal'})
  Noise Level:        {random.randint(-72, -60)} dBm (Good)
  Echo Return Loss:   {random.randint(32, 38)} dB (Acceptable)
  Jitter:             {random.uniform(0.1, 0.8):.1f} ms (Normal)

Maintenance Status:
  Last Test:          {(self.clock.now() - timedelta(days=random.randint(1, 7))).strftime('%B %d, %Y %H:%M')}
  Next Scheduled:     {(self.clock.now() + timedelta(days=random.randint(1, 14))).strftime('%B %d, %Y %H:%M')}
  Known Issues:       {'None' if tg["quality"] > 0.995 else 'Minor performance degradation'}
  Alarm Status:       {'Clear' if tg["status"] == 'ACTIVE' and tg["quality"] > 0.995 else 'Active alarms present'}

Recommendations:"""

            if tg["utilization"] > 85:
                detail_output += f"\n  • URGENT: Monitor closely - utilization at {tg['utilization']}%"
                detail_output += "\n  • Consider immediate capacity upgrade or load balancing"
            elif tg["utilization"] > 75:
                detail_output += f"\n  • Monitor during peak hours - current utilization {tg['utilization']}%"

            if tg["quality"] < 0.995:
                detail_output += "\n  • Quality below standard - investigate circuit issues"
                detail_output += "\n  • Schedule comprehensive testing"

            if tg["status"] == "MAINT":
                detail_output += "\n  • Trunk group in maintenance mode"
                detail_output += "\n  • Verify completion before returning to service"

            if not any([tg["utilization"] > 75, tg["quality"] < 0.995, tg["status"] == "MAINT"]):
                detail_output += "\n  • Continue normal monitoring procedures"
                detail_output += "\n  • Performance within acceptable parameters"

            return detail_output

        elif args[0] == "test" and len(args) > 1:
            tg_name = args[1].upper()
            if tg_name not in self.trunk_groups:
                return f"trunk: ERROR - Trunk group {tg_name} not found"

            tg = self.trunk_groups[tg_name]
            if tg["status"] == "MAINT":
                return f"trunk: Cannot test {tg_name} - trunk group in maintenance mode"

            # Simulate realistic testing sequence with variable results
            test_results = []
            test_start = self.clock.now().strftime("%H:%M:%S")

            # Various test phases with realistic pass/fail rates
            tests = [
                ("Signal continuity", 0.98),
                ("Noise level analysis", 0.95),
                ("Crosstalk measurement", 0.93),
                ("Timing verification", 0.97),
                ("Echo return loss", 0.92),
                ("Digital error rate", 0.90),
                ("Synchronization", 0.96),
                ("Power level check", 0.99)
            ]

            test_output = f"""Initiating comprehensive test sequence for {tg_name}...
Test started: {test_start}

Running Bell System Standard Test Suite BSP-100-120-001:
"""

            overall_pass = True
            for test_name, pass_rate in tests:
                # Degrade pass rate based on trunk quality
                adjusted_pass_rate = pass_rate * tg["quality"]
                passed = random.random() < adjusted_pass_rate
                status = "PASS" if passed else "FAIL"
                if not passed:
                    overall_pass = False

                # Add realistic test values
                if "noise" in test_name.lower():
                    value = f" ({random.randint(-72, -60)} dBm)"
                elif "error" in test_name.lower():
                    value = f" ({random.uniform(0.00001, 0.001):.2e})"
                elif "echo" in test_name.lower():
                    value = f" ({random.randint(30, 40)} dB)"
                else:
                    value = ""

                test_output += f"\nPhase {len(test_results)+1}: {test_name:<20} [{status}]{value}"
                test_results.append(passed)

            test_end = self.clock.now().strftime("%H:%M:%S")

            test_output += f"""

Test completed: {test_end}
Duration: {random.randint(45, 180)} seconds

Results Summary:
  Tests Passed: {sum(test_results)}/{len(test_results)}
  Overall Status: {'PASS' if overall_pass else 'FAIL'}
  Quality Rating: {tg["quality"]:.1%}
"""

            if overall_pass:
                test_output += f"  Recommendation: {tg_name} certified for continued operation"
                # Slightly improve quality on successful test
                tg["quality"] = min(0.999, tg["quality"] + 0.001)
            else:
                test_output += f"  Recommendation: Schedule maintenance for {tg_name}"
                test_output += "\n  Action Required: Investigate failed test phases"
                # Degrade quality on failed test
                tg["quality"] = max(0.980, tg["quality"] - 0.005)

            test_output += f"""

Test log saved: /att/network/tests/{tg_name.lower()}_{self.clock.now().strftime('%m%d_%H%M')}.log
Next test due: {(self.clock.now() + timedelta(days=30)).strftime('%B %d, %Y')}"""

            return test_output

        elif args[0] == "traffic" and len(args) > 1:
            tg_name = args[1].upper()
            if tg_name not in self.trunk_groups:
                return f"trunk: ERROR - Trunk group {tg_name} not found"

            tg = self.trunk_groups[tg_name]
            return self._show_trunk_traffic_monitor(tg_name, tg)

        elif args[0] == "maintenance":
            return self._show_trunk_maintenance_schedule()

        else:
            available_commands = ["status", "detail", "test", "traffic", "maintenance"]
            return f"trunk: Unknown option '{args[0]}'\nAvailable commands: {', '.join(available_commands)}"

    def _update_trunk_states(self) -> None:
        """Update trunk group states based on time and network conditions."""
        import random

        # Simulate realistic state changes over time
        for tg_name, tg_data in self.trunk_groups.items():
            if tg_data["status"] == "ACTIVE":
                # Small random variations in utilization
                change = random.randint(-3, 5)
                tg_data["utilization"] = max(0, min(100, tg_data["utilization"] + change))

                # Quality can degrade slowly over time
                if random.random() < 0.05:  # 5% chance of quality change
                    quality_change = random.uniform(-0.002, 0.001)
                    tg_data["quality"] = max(0.990, min(0.999, tg_data["quality"] + quality_change))

    def _get_peak_period(self) -> str:
        """Get peak traffic period based on current time."""
        hour = self.clock.now().hour
        if 8 <= hour <= 10:
            return "Morning Business (08:00-10:00)"
        elif 14 <= hour <= 16:
            return "Afternoon Peak (14:00-16:00)"
        elif 19 <= hour <= 21:
            return "Evening Social (19:00-21:00)"
        else:
            return "Off-Peak Period"

    def _show_trunk_traffic_monitor(self, tg_name: str, tg_data: dict) -> str:
        """Show real-time traffic monitoring for a trunk group."""
        import random

        if tg_data["status"] == "MAINT":
            return f"Traffic monitoring unavailable - {tg_name} in maintenance mode"

        current_time = self.clock.now().strftime("%H:%M:%S")
        active_channels = int(tg_data["capacity"] * tg_data["utilization"] / 100)

        # Generate realistic traffic pattern
        traffic_samples = []
        for i in range(12):  # Last 12 5-minute intervals
            time_offset = (11 - i) * 5
            sample_time = (self.clock.now() - timedelta(minutes=time_offset)).strftime("%H:%M")
            utilization = max(0, min(100, tg_data["utilization"] + random.randint(-10, 10)))
            traffic_samples.append((sample_time, utilization))

        monitor_output = f"""Real-Time Traffic Monitor: {tg_name}
Monitor Time: {current_time}
Update Interval: 5 minutes

Current Status:
  Active Channels:    {active_channels}/{tg_data["capacity"]}
  Utilization:        {tg_data["utilization"]}%
  Call Rate:          {random.randint(45, 180)} calls/hour
  Revenue Rate:       ${random.randint(250, 850)}/hour

Traffic History (Last Hour):
Time    Util%   Channels   Revenue/5min
----    -----   --------   ------------"""

        for sample_time, utilization in traffic_samples:
            channels = int(tg_data["capacity"] * utilization / 100)
            revenue = random.randint(20, 80)
            monitor_output += f"\n{sample_time}   {utilization:>3}%    {channels:>2}/{tg_data['capacity']:<2}       ${revenue}"

        # Add real-time alerts
        alerts = []
        if tg_data["utilization"] > 90:
            alerts.append("⚠ CRITICAL: Utilization above 90% - overflow risk")
        elif tg_data["utilization"] > 80:
            alerts.append("⚠ WARNING: High utilization - monitor closely")

        if tg_data["quality"] < 0.995:
            alerts.append("⚠ QUALITY: Performance below threshold")

        if alerts:
            monitor_output += "\n\nActive Alerts:"
            for alert in alerts:
                monitor_output += f"\n  {alert}"
        else:
            monitor_output += "\n\n✓ No active alerts - normal operation"

        monitor_output += f"\n\nPress 'trunk detail {tg_name}' for comprehensive analysis"

        return monitor_output

    def _show_trunk_maintenance_schedule(self) -> str:
        """Show trunk group maintenance schedule."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M")

        schedule_output = f"""Bell System Trunk Group Maintenance Schedule
Generated: {current_time}

Scheduled Maintenance (Next 30 Days):
Date           Time        Trunk Group    Type              Duration
----           ----        -----------    ----              --------"""

        # Generate realistic maintenance schedule
        for i in range(5):
            maint_date = self.clock.now() + timedelta(days=random.randint(1, 30))
            maint_time = f"{random.randint(1, 4):02d}:{random.choice(['00', '30'])}"
            tg_name = random.choice(list(self.trunk_groups.keys()))
            maint_type = random.choice(["Preventive", "Calibration", "Upgrade", "Testing"])
            duration = f"{random.randint(2, 6)} hours"

            schedule_output += f"\n{maint_date.strftime('%b %d')}        {maint_time}       {tg_name}      {maint_type:<12}      {duration}"

        # Show current maintenance
        maint_trunks = [tg for tg, data in self.trunk_groups.items() if data["status"] == "MAINT"]
        if maint_trunks:
            schedule_output += "\n\nCurrently in Maintenance:"
            for tg_name in maint_trunks:
                schedule_output += f"\n  {tg_name}: Scheduled maintenance in progress"
                schedule_output += f"\n           Expected completion: {(self.clock.now() + timedelta(hours=random.randint(1, 4))).strftime('%H:%M')}"

        schedule_output += """

Maintenance Procedures:
  • All maintenance during low-traffic periods (01:00-05:00)
  • Automatic rerouting activated during maintenance
  • 24-hour advance notification to Network Operations
  • Emergency override procedures available

Contact: Central Maintenance Office ext 4200"""

        return schedule_output

    # Bell System Core Commands Implementation

    def cmd_switch(self, args: List[str]) -> str:
        """Enhanced switching center management with realistic operational dynamics."""
        import random

        # Update switching system states
        self._update_switching_states()

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            # Calculate dynamic metrics
            total_calls = sum(system["calls_hour"] for system in self.switching_systems.values())
            active_systems = len([s for s in self.switching_systems.values() if s["status"] == "ACTIVE"])
            total_systems = len(self.switching_systems)
            avg_completion = random.uniform(0.975, 0.995)

            status_output = f"""Bell System Switching Center Status
{current_time}

Electronic Switching Systems:"""

            for switch_id, system in self.switching_systems.items():
                load_indicator = f"{system['load']}%" if system["status"] == "ACTIVE" else "OFF"
                uptime_days = system["uptime"] // 24
                status_detail = f"- {system['calls_hour']:,} calls/hour"
                if system["status"] == "TESTING":
                    status_detail = "- Cutover operations in progress"
                elif uptime_days < 7:
                    status_detail = f"- {uptime_days} days uptime"

                status_output += f"\n  {switch_id:<15} {system['status']:<8} {load_indicator:<5} {status_detail}"

            # Add crossbar systems
            status_output += "\n\nCrossbar Systems:"
            for xb_id, xb_system in self.crossbar_systems.items():
                load_indicator = f"{xb_system['load']}%" if xb_system["status"] == "ACTIVE" else "OFF"
                maint_note = " - PM due" if xb_system["maintenance_due"] else " - Normal operation"
                status_output += f"\n  {xb_id:<15} {xb_system['status']:<8} {load_indicator:<5}{maint_note}"

            # System-wide performance metrics
            status_output += f"""

System Performance:
  Active Systems:           {active_systems}/{total_systems} electronic + {len([x for x in self.crossbar_systems.values() if x['status'] == 'ACTIVE'])}/{len(self.crossbar_systems)} crossbar
  Total Call Attempts:      {total_calls:,}/hour
  Call Completion Rate:     {avg_completion:.1%}
  Average Setup Time:       {random.uniform(1.8, 2.4):.1f} seconds
  Network Processor Load:   {sum(s['load'] for s in self.switching_systems.values() if s['status'] == 'ACTIVE') // active_systems}% average

Recent Events:"""

            # Add recent switching events
            events = []
            if any(s["status"] == "TESTING" for s in self.switching_systems.values()):
                events.append("⚡ 5ESS cutover operations scheduled")
            if any(x["maintenance_due"] for x in self.crossbar_systems.values()):
                events.append("🔧 Crossbar maintenance scheduled")
            if not events:
                events.append("✓ All systems operating normally")

            for event in events[:3]:
                status_output += f"\n  {event}"

            status_output += """

Commands:
  switch diagnostics <id>   Run comprehensive diagnostics
  switch performance <id>   Real-time performance monitoring
  switch maintenance <id>   Maintenance schedule and status
  switch cutover <id>       Cutover operations (5ESS only)"""

            return status_output

        elif args[0] == "diagnostics" and len(args) > 1:
            switch_id = args[1].upper()

            # Check if switch exists
            if switch_id not in self.switching_systems and switch_id not in self.crossbar_systems:
                return f"switch: ERROR - Switch {switch_id} not found\nAvailable systems: {', '.join(list(self.switching_systems.keys()) + list(self.crossbar_systems.keys()))}"

            # Determine system type and get data
            if switch_id in self.switching_systems:
                system = self.switching_systems[switch_id]
                is_electronic = True
            else:
                system = self.crossbar_systems[switch_id]
                is_electronic = False

            if system["status"] not in ["ACTIVE", "TESTING"]:
                return f"switch: Cannot run diagnostics on {switch_id} - system status: {system['status']}"

            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            # Simulate realistic diagnostic sequence
            diag_output = f"""Switching System Diagnostics: {switch_id}
Test Sequence Initiated: {current_time}
System Type: {'Electronic Stored Program Control' if is_electronic else 'Crossbar Electromechanical'}

Running Bell System Standard Diagnostic Suite:
"""

            # Different tests for electronic vs crossbar
            if is_electronic:
                tests = [
                    ("Central Processing Unit", 0.98),
                    ("Program Memory", 0.96),
                    ("Call Memory", 0.97),
                    ("I/O Controllers", 0.95),
                    ("Network Interface", 0.94),
                    ("Trunk Interface", 0.93),
                    ("Line Interface", 0.92),
                    ("Signal Processing", 0.96),
                    ("Call Processing Programs", 0.90),
                    ("Administrative Programs", 0.94),
                    ("Maintenance Programs", 0.95),
                    ("Database Integrity", 0.89),
                    ("Real-Time Clock", 0.98),
                    ("Interrupt System", 0.95)
                ]
            else:
                tests = [
                    ("Marker Selection", 0.92),
                    ("Crossbar Switch Matrix", 0.88),
                    ("Register Circuits", 0.90),
                    ("Sender Circuits", 0.87),
                    ("Connector Circuits", 0.85),
                    ("Common Control", 0.91),
                    ("Trunk Circuits", 0.89),
                    ("Line Circuits", 0.86),
                    ("Ringing Circuits", 0.93),
                    ("Power Systems", 0.95)
                ]

            # Run tests with realistic pass/fail based on system condition
            test_results = []
            base_reliability = 0.95 if system["status"] == "ACTIVE" else 0.85

            for test_name, base_pass_rate in tests:
                # Adjust pass rate based on system load and uptime
                if is_electronic:
                    load_factor = max(0.8, 1.0 - (system["load"] - 70) * 0.002) if system["load"] > 70 else 1.0
                    uptime_factor = max(0.9, 1.0 - (system["uptime"] - 8760) * 0.00005) if system["uptime"] > 8760 else 1.0
                else:
                    load_factor = max(0.7, 1.0 - (system["load"] - 60) * 0.003) if system["load"] > 60 else 1.0
                    uptime_factor = 0.85 if system["maintenance_due"] else 1.0

                adjusted_pass_rate = base_pass_rate * base_reliability * load_factor * uptime_factor
                passed = random.random() < adjusted_pass_rate

                # Generate realistic test values
                if passed:
                    if "memory" in test_name.lower():
                        value = f" ({random.randint(95, 100)}% utilized)"
                    elif "processing" in test_name.lower() or "cpu" in test_name.lower():
                        value = f" ({random.uniform(0.8, 2.5):.1f}ms response)"
                    elif "interface" in test_name.lower():
                        value = f" ({random.randint(98, 100)}% availability)"
                    else:
                        value = ""
                    status = f"PASS{value}"
                else:
                    if "memory" in test_name.lower():
                        value = " (parity error detected)"
                    elif "circuit" in test_name.lower():
                        value = " (intermittent failure)"
                    elif "interface" in test_name.lower():
                        value = " (signal degradation)"
                    else:
                        value = " (parameter out of range)"
                    status = f"FAIL{value}"

                progress_bar = "█" * 20
                diag_output += f"\n{test_name:<25} [{progress_bar}] {status}"
                test_results.append(passed)

            # Summary
            passed_count = sum(test_results)
            total_count = len(test_results)
            overall_pass = passed_count >= total_count * 0.9  # 90% pass rate required

            test_end = self.clock.now().strftime("%H:%M:%S")
            duration = random.randint(120, 300)

            diag_output += f"""

Diagnostic Sequence Completed: {test_end}
Total Duration: {duration} seconds

Results Summary:
  Tests Executed: {total_count}
  Tests Passed:   {passed_count}
  Tests Failed:   {total_count - passed_count}
  Success Rate:   {passed_count/total_count:.1%}
  Overall Status: {'OPERATIONAL' if overall_pass else 'DEGRADED'}
"""

            if overall_pass:
                diag_output += f"  Recommendation: {switch_id} certified for continued operation"
                if is_electronic and system["load"] < 85:
                    diag_output += "\n  Performance: Excellent - ready for increased traffic load"
            else:
                diag_output += f"  Recommendation: Schedule maintenance for {switch_id}"
                diag_output += "\n  Action Required: Investigate failed diagnostic phases"
                if not is_electronic and not system["maintenance_due"]:
                    # Mark crossbar for maintenance
                    system["maintenance_due"] = True

            diag_output += f"""

Diagnostic Log: /att/switching/diag/{switch_id.lower()}_{self.clock.now().strftime('%m%d_%H%M')}.log
Next Diagnostic: {(self.clock.now() + timedelta(days=7)).strftime('%B %d, %Y')}

Bell System Practice: BSP-100-300-001 (Electronic Switching Diagnostics)"""

            return diag_output

        elif args[0] == "performance" and len(args) > 1:
            switch_id = args[1].upper()

            if switch_id not in self.switching_systems and switch_id not in self.crossbar_systems:
                return f"switch: ERROR - Switch {switch_id} not found"

            return self._show_switch_performance_monitor(switch_id)

        elif args[0] == "maintenance" and len(args) > 1:
            switch_id = args[1].upper()

            if switch_id not in self.switching_systems and switch_id not in self.crossbar_systems:
                return f"switch: ERROR - Switch {switch_id} not found"

            return self._show_switch_maintenance_status(switch_id)

        elif args[0] == "cutover" and len(args) > 1:
            switch_id = args[1].upper()

            if switch_id not in self.switching_systems:
                return "switch: ERROR - Cutover operations only available for electronic switching systems"

            system = self.switching_systems[switch_id]
            if "5ESS" not in system["type"]:
                return "switch: ERROR - Cutover operations only supported on 5ESS systems"

            return self._perform_switch_cutover(switch_id, system)

        else:
            available_commands = ["diagnostics", "performance", "maintenance", "cutover"]
            return f"switch: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"

    def _update_switching_states(self) -> None:
        """Update switching system states based on operational patterns."""

        for switch_id, system in self.switching_systems.items():
            if system["status"] == "ACTIVE":
                # Vary call processing load
                load_change = random.randint(-2, 4)
                system["load"] = max(30, min(95, system["load"] + load_change))

                # Update call volume against the machine's engineered
                # ceiling, so a rural switch can never report metropolitan
                # traffic and a toll machine is rated on its trunks.
                ceiling = SWITCHING_SYSTEMS[system["type"]].busy_hour_capacity()
                system["calls_hour"] = int(
                    ceiling * (system["load"] / 100) * random.uniform(0.9, 1.1)
                )

                # Increment uptime
                system["uptime"] += random.uniform(0.8, 1.2)

    def _show_switch_performance_monitor(self, switch_id: str) -> str:
        """Show real-time performance monitoring for a switching system."""
        import random

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        if switch_id in self.switching_systems:
            system = self.switching_systems[switch_id]
            is_electronic = True
        else:
            system = self.crossbar_systems[switch_id]
            is_electronic = False

        if system["status"] not in ["ACTIVE", "TESTING"]:
            return f"Performance monitoring unavailable - {switch_id} status: {system['status']}"

        monitor_output = f"""Real-Time Performance Monitor: {switch_id}
Monitor Time: {current_time}
Update Interval: 30 seconds

System Status: {system['status']}"""

        if is_electronic:
            monitor_output += f"""
Current Load: {system['load']}%
Call Processing Rate: {system['calls_hour']:,} calls/hour
Memory Utilization: {random.randint(65, 85)}%

Real-Time Metrics (Last 10 minutes):
Time     CPU%  Mem%  Calls/min  Setup(ms)  Completion%
------   ----  ----  ---------  ---------  -----------"""

            # Generate 10 minutes of performance data
            for i in range(10):
                time_ago = 9 - i
                sample_time = (self.clock.now() - timedelta(minutes=time_ago)).strftime("%H:%M")
                cpu_load = max(40, min(95, system["load"] + random.randint(-5, 5)))
                mem_util = random.randint(60, 90)
                calls_min = system["calls_hour"] // 60 + random.randint(-50, 50)
                setup_time = random.randint(800, 2400)
                completion = random.uniform(0.975, 0.995)

                monitor_output += f"\n{sample_time}    {cpu_load:>3}%  {mem_util:>3}%  {calls_min:>9}  {setup_time:>9}  {completion:>10.1%}"

        else:  # Crossbar system
            monitor_output += f"""
Current Load: {system['load']}%
Marker Busy Time: {random.randint(15, 35)}%
Register Utilization: {random.randint(40, 70)}%

Electromechanical Status:
Crossbar Switches: {random.randint(890, 920)}/920 operational
Markers: {random.randint(18, 20)}/20 in service
Senders: {random.randint(45, 50)}/50 available
Connectors: {random.randint(180, 200)}/200 active"""

        # Add alerts based on performance
        alerts = []
        if is_electronic:
            if system["load"] > 90:
                alerts.append("⚠ CRITICAL: CPU load above 90%")
            elif system["load"] > 80:
                alerts.append("⚠ WARNING: High CPU utilization")
        else:
            if system["load"] > 85:
                alerts.append("⚠ WARNING: High traffic load on electromechanical system")
            if system["maintenance_due"]:
                alerts.append("🔧 NOTICE: Preventive maintenance overdue")

        if alerts:
            monitor_output += "\n\nActive Alerts:"
            for alert in alerts:
                monitor_output += f"\n  {alert}"
        else:
            monitor_output += "\n\n✓ All performance metrics within normal range"

        return monitor_output

    def _show_switch_maintenance_status(self, switch_id: str) -> str:
        """Show maintenance status and schedule for a switching system."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        if switch_id in self.switching_systems:
            system = self.switching_systems[switch_id]
            is_electronic = True
        else:
            system = self.crossbar_systems[switch_id]
            is_electronic = False

        maint_output = f"""Maintenance Status: {switch_id}
Report Generated: {current_time}
System Type: {'Electronic Stored Program Control' if is_electronic else 'Crossbar Electromechanical'}

Current Status: {system['status']}"""

        if is_electronic:
            last_maint = self.clock.now() - timedelta(days=random.randint(30, 180))
            next_maint = self.clock.now() + timedelta(days=random.randint(7, 90))
            uptime_hours = int(system["uptime"])

            maint_output += f"""
Uptime: {uptime_hours // 24} days, {uptime_hours % 24} hours
Last Maintenance: {last_maint.strftime('%B %d, %Y')}
Next Scheduled: {next_maint.strftime('%B %d, %Y %H:%M')}

Maintenance History:
  Program Memory Test: {(self.clock.now() - timedelta(days=7)).strftime('%b %d')} - PASSED
  I/O Controller Check: {(self.clock.now() - timedelta(days=14)).strftime('%b %d')} - PASSED
  Database Backup: {(self.clock.now() - timedelta(days=21)).strftime('%b %d')} - COMPLETED
  Environmental Check: {(self.clock.now() - timedelta(days=28)).strftime('%b %d')} - PASSED

Recommended Actions:"""

            if uptime_hours > 8760:  # More than 1 year
                maint_output += "\n  • Schedule comprehensive maintenance cycle"
            elif system["load"] > 85:
                maint_output += "\n  • Monitor closely due to high utilization"
            else:
                maint_output += "\n  • Continue routine monitoring"

        else:  # Crossbar
            maint_output += f"""
Maintenance Due: {'YES - OVERDUE' if system['maintenance_due'] else 'Current'}
Last Preventive Maintenance: {(self.clock.now() - timedelta(days=random.randint(60, 200))).strftime('%B %d, %Y')}

Mechanical Component Status:
  Crossbar Switches: {'Lubrication due' if system['maintenance_due'] else 'Good condition'}
  Relay Contacts: {'Cleaning required' if system['maintenance_due'] else 'Recently cleaned'}
  Motor Drives: {'Inspection due' if system['maintenance_due'] else 'Operating normally'}
  Wire Spring Relays: {'Testing required' if system['maintenance_due'] else 'Tested recently'}

Scheduled Maintenance Tasks:"""

            if system["maintenance_due"]:
                maint_output += """
  • URGENT: Contact cleaning and adjustment
  • Crossbar switch lubrication
  • Relay timing verification
  • Motor brush inspection
  • Wire spring relay testing"""
            else:
                maint_output += """
  • Routine contact inspection (monthly)
  • Lubrication schedule (quarterly)
  • Timing adjustment check (semi-annual)"""

        maint_output += """

Contact: Central Office Maintenance - ext 4300
Work Order System: Use 'service' command for maintenance requests"""

        return maint_output

    def _perform_switch_cutover(self, switch_id: str, system: dict) -> str:
        """Perform 5ESS cutover operations with realistic procedures."""
        import random

        if system["status"] != "TESTING":
            return f"switch: ERROR - {switch_id} must be in TESTING status for cutover operations"

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        cutover_output = f"""5ESS Cutover Operations: {switch_id}
Cutover Initiated: {current_time}

BELL SYSTEM 5ESS CUTOVER PROCEDURE BSP-100-500-001
⚠ WARNING: This operation will affect live customer traffic

Pre-Cutover Checklist:
✓ All diagnostic tests completed successfully
✓ Customer notification procedures completed
✓ Backup switching arrangements confirmed
✓ Technical staff positioned at critical locations
✓ Emergency rollback procedures verified

Cutover Sequence:"""

        # Simulate realistic cutover steps
        cutover_steps = [
            ("Traffic monitoring baseline established", 0.99),
            ("Administrative data verification", 0.95),
            ("Customer database synchronization", 0.92),
            ("Trunk group configuration transfer", 0.88),
            ("Line equipment initialization", 0.90),
            ("Billing system interface activation", 0.85),
            ("Emergency service verification", 0.98),
            ("Traffic load balancing activation", 0.87),
            ("Final system integration test", 0.83),
            ("Customer service verification", 0.80)
        ]

        all_successful = True
        for step_num, (step_name, success_rate) in enumerate(cutover_steps, 1):
            success = random.random() < success_rate
            status = "COMPLETE" if success else "FAILED"

            if not success:
                all_successful = False

            cutover_output += f"\nStep {step_num:>2}: {step_name:<35} [{status}]"

            if not success:
                cutover_output += f"\n         ERROR: Step {step_num} requires manual intervention"
                break

        completion_time = self.clock.now().strftime("%H:%M:%S EST")

        if all_successful:
            # Successful cutover
            system["status"] = "ACTIVE"
            system["load"] = random.randint(45, 65)  # Start with moderate load
            system["calls_hour"] = random.randint(15000, 25000)

            cutover_output += f"""

Cutover Completed Successfully: {completion_time}
Duration: {random.randint(45, 90)} minutes

POST-CUTOVER STATUS:
  System Status: ACTIVE
  Initial Load: {system['load']}%
  Call Processing: {system['calls_hour']:,} calls/hour
  Customer Impact: NONE - seamless transition achieved

IMMEDIATE ACTIONS:
  ✓ Customer service monitoring activated
  ✓ Performance baseline collection started
  ✓ 24-hour close monitoring period initiated
  ✓ All backup systems returned to standby

Next Review: {(self.clock.now() + timedelta(hours=24)).strftime('%B %d, %Y %H:%M')}
Project Completion: SUCCESSFUL"""

        else:
            # Failed cutover
            cutover_output += f"""

Cutover FAILED: {completion_time}
Status: ROLLBACK INITIATED

EMERGENCY PROCEDURES ACTIVATED:
  • Customer traffic restored to original switching system
  • Technical teams investigating failure points
  • Customer service impact minimized
  • Full investigation procedures initiated

Estimated Resolution: {random.randint(2, 8)} hours
Emergency Contact: Bell System NOC ext 911"""

        return cutover_output

    def cmd_3a(self, args: List[str]) -> str:
        """3A Central Control switching system operations"""
        if not args:
            return """3A Central Control Switching System
Common Control Electronic Switching

Available Commands:
  3a status            - System status and configuration
  3a diagnostics       - Run system diagnostics
  3a traffic           - Traffic load analysis
  3a maintenance       - Maintenance procedures
  3a translations      - Translation table management

Current 3A Systems:
  Systems Operational: 47 of 52 planned
  Call Processing:     Normal operation
  Memory Utilization:  73% of capacity

Project References: SD-1C900-01 (3A Central Control Circuit)"""

        if args[0] == "status":
            return """3A Central Control System Status
November 14, 1983 07:45:30

System Configuration:
  Central Control Units:       4 active, 1 standby
  Program Stores:              8MB ferrite core memory
  Call Stores:                 2MB working memory
  Scanner Units:               16 operational
  Network Control:             Crossbar network attached

Processing Status:
  Call Attempts:               45,892/hour (current)
  Successful Completions:      44,731 (97.5% success rate)
  Busy Hour Traffic:           892 CCS (within capacity)
  Processor Occupancy:         67% (Normal range: 40-80%)

Hardware Status:
  Central Control A:           ACTIVE - Normal operation
  Central Control B:           STANDBY - Ready
  Central Control C:           ACTIVE - Normal operation
  Central Control D:           MAINTENANCE - Scheduled PM

Translation Tables:
  Office Code Translations:    Current - Rev 47.3
  Routing Translations:        Current - Rev 12.8
  Screening Tables:            Current - Rev 6.2

Recent Activity:
  Last Translation Update:     1983-11-12 03:00
  Last Hardware Fault:         None (47 days)
  Performance Optimization:    Completed 1983-11-10"""

        elif args[0] == "diagnostics":
            return """3A Central Control Diagnostic Suite
Test Sequence Initiated: November 14, 1983 07:45:45

Memory Tests:
  Program Store Test:          [████████████████████] PASS
  Call Store Test:             [████████████████████] PASS
  Translation Table Test:      [████████████████████] PASS

Control Unit Tests:
  Central Control A:           [████████████████████] PASS
  Central Control B:           [████████████████████] PASS
  Central Control C:           [████████████████████] PASS
  Central Control D:           [██████████░░░░░░░░░░] MAINTENANCE

Network Interface Tests:
  Scanner Unit Test:           [████████████████████] PASS (16/16)
  Network Control Test:        [████████████████████] PASS
  Trunk Interface Test:        [████████████████████] PASS

Software Tests:
  Call Processing Programs:    [████████████████████] PASS
  Administrative Programs:     [████████████████████] PASS
  Maintenance Programs:        [████████████████████] PASS

Test Results Summary:
  Total Tests Run:             47 tests
  Tests Passed:                47 tests
  Tests Failed:                0 tests
  System Health:               EXCELLENT

Recommended Actions:
  Complete scheduled maintenance on Control Unit D
  Update trunk translation tables (due 11/20/83)
  Performance monitoring - all parameters normal"""

        return f"3a: unknown option '{args[0]}'"

    def cmd_testboard(self, args: List[str]) -> str:
        """
        Work the local test board: measure loops, reach test lines, read
        supervision.

        The board is where the three testing systems in this simulation meet.
        Loop measurement goes through mechanised loop testing, transmission
        goes through the test line series, and supervision is what single
        frequency signalling shows about a trunk.
        """
        if not args:
            pending = self.desk.pending()
            untested = [report for report in pending if not report.tested]
            return f"""Test Board - {self.home_office['clli']}
{self.clock.timestamp()}
{'=' * 66}

LOOP TESTING
  mlt <report>              Measure a subscriber loop
  testboard loop <report>   The same measurement, from the board
  report faults             What each condition measures like

TRANSMISSION TESTING
  testline                  The test line and responder series
  testline 105 <circuit>    Two-way loss, noise and gain slope
  testboard supervision <circuit>
                            Single frequency supervision state

BOARD STATUS
  Reports on the board      {len(pending)}
  Not yet measured          {len(untested)}
  Service index             {self.career.service_index():.1f} ({self.career.index_band()})

{tone_header()}. Loss objectives are stated at that frequency,
so every loss reading here is taken there."""

        action = args[0].lower()

        if action in ('loop', 'test') and len(args) > 1:
            return self.cmd_mlt([args[1]])

        if action == 'supervision':
            if len(args) < 2:
                return ("testboard: name a circuit.\n"
                        "Usage: testboard supervision <trunk group>")
            return self._show_supervision(args[1].upper())

        if action == 'results':
            return self._show_board_results()

        if action == 'status':
            return self.cmd_testboard([])

        return (f"testboard: unknown option '{args[0]}'\n"
                "Options: loop, supervision, results, status")

    def _show_supervision(self, circuit: str) -> str:
        """
        Show what single frequency signalling says about a trunk.

        The 2600 Hz tone is on an idle trunk and off a seized one. That makes
        the tone a supervisory signal a craftsperson reads: tone present while
        a connection is up is an irregularity, and it is what routine testing
        is looking for.
        """
        group = self.trunk_groups.get(circuit)
        if group is None:
            return (f"testboard: no trunk group {circuit}.\n"
                    f"Groups: {', '.join(sorted(self.trunk_groups))}")

        if group['status'] != 'ACTIVE':
            state = 'IDLE'
        elif group['quality'] < 0.994:
            state = 'ANOMALOUS'
        elif group['utilization'] > 70:
            state = 'CONNECTED'
        else:
            state = 'SEIZED'
        tone, note = SUPERVISION_STATES[state]

        lines = [
            f"Single Frequency Supervision - {circuit}",
            f"{group['route']}   {self.clock.timestamp()}",
            '=' * 66,
            f"  SF frequency        {SF_FREQUENCY_HZ} Hz",
            f"  Idle tone level     {SF_IDLE_LEVEL_DBM:+.1f} dBm",
            f"  Trunk state         {state}",
            f"  Tone                {tone}",
            '',
            f"  {note}",
            '',
            'ALL STATES',
            '-' * 66,
        ]
        for name, (tone_state, description) in SUPERVISION_STATES.items():
            marker = '>' if name == state else ' '
            lines.append(f"{marker} {name:<14} {tone_state:<28} {description}")
        lines.extend([
            '-' * 66,
            '',
            "Routine transmission testing on these groups is run by CAROT, "
            "which prints",
            "its exceptions to the maintenance teletype whether anybody is "
            "reading or not.",
        ])
        return '\n'.join(lines)

    def _show_board_results(self) -> str:
        """Show every measurement taken on the board this session."""
        measured = [
            report for report in self.desk.pending() + self.desk.closed()
            if report.test_notes
        ]
        if not measured:
            return ("No measurements taken this session.\n"
                    "Measure a loop with 'mlt <report>'.")
        lines = ["Measurements taken this session", '=' * 74]
        for report in measured:
            lines.append(f"{report.number}  {report.record.telephone_number}  "
                         f"cable {report.record.cable_pair()}")
            for note in report.test_notes:
                lines.append(f"    {note}")
        return '\n'.join(lines)

    def cmd_emergency(self, args: List[str]) -> str:
        """Enhanced emergency dispatch and escalation system"""
        if not args:
            return """Bell System Emergency Response System
Critical Incident Management and Escalation

Available Commands:
  emergency dispatch   - Initiate emergency response
  emergency status     - Current emergency conditions
  emergency escalate   - Escalate to higher authority
  emergency recovery   - Disaster recovery procedures

Current Emergency Status: GREEN (Normal Operations)
Active Incidents: 0
Response Teams: 4 available
Emergency Contacts: Updated November 1983"""

        if args[0] == "dispatch":
            return """Emergency Response Dispatch Initiated
Dispatch Time: November 14, 1983 07:46:30

Emergency Classification: [To be determined]
Response Level: STANDARD

Available Response Teams:
  Team Alpha:   Available - Network Operations
  Team Beta:    Available - Switching Systems
  Team Gamma:   Available - Transmission
  Team Delta:   Available - Field Operations

Escalation Contacts:
  Level 1: Regional Engineering Manager
  Level 2: Area Operations Director
  Level 3: Bell System Emergency Coordination

EMERGENCY PROCEDURES ACTIVATED
All response teams have been notified
Emergency coordination center staffed

Please specify incident type for appropriate response"""

        return f"emergency: unknown option '{args[0]}'"

    def cmd_ticket(self, args: List[str]) -> str:
        """Trouble ticket management system"""
        if not args:
            return """Bell System Trouble Ticket Management
Customer Service and Network Operations

Available Commands:
  ticket create        - Create new trouble ticket
  ticket status <ID>   - Display ticket status
  ticket update <ID>   - Update ticket information
  ticket escalate <ID> - Escalate ticket priority
  ticket close <ID>    - Close completed ticket

Current Ticket Summary:
  Open Tickets:        23 active
  Pending Review:      8 tickets
  Closed Today:        67 tickets
  Average Resolution:  4.2 hours

Priority Distribution:
  CRITICAL: 2    HIGH: 7    MEDIUM: 14    LOW: 8"""

        if args[0] == "status" and len(args) > 1:
            ticket_id = args[1].upper()
            return f"""Trouble Ticket Status: {ticket_id}
Last Updated: November 14, 1983 07:30:15

Ticket Information:
  Priority:           HIGH
  Customer Class:     BUSINESS-CRITICAL
  Reported Problem:   No dial tone - 555-0123
  Location:           123 Main St, New York, NY

Assignment:
  Assigned To:        Field Team 7
  Dispatch Time:      07:15
  ETA:                08:30

Progress Notes:
  07:15 - Ticket created, team dispatched
  07:30 - Team en route to location
  07:45 - Cable pair fault suspected

Escalation:
  Response Time SLA:  60 minutes
  Time Remaining:     45 minutes
  Next Escalation:    08:15 (Level 2)

Status: IN PROGRESS"""

        elif args[0] == "create":
            new_ticket = f"SW-{random.randint(2800, 2999)}"
            return f"""New Trouble Ticket Created: {new_ticket}
Creation Time: November 14, 1983 07:46:45

Ticket Type: [To be specified]
Priority: [To be assigned]
Customer Information: [To be entered]

Please provide:
1. Customer phone number or service address
2. Problem description
3. Customer class (RESIDENTIAL/BUSINESS/GOVERNMENT)
4. Urgency level

Use 'ticket update {new_ticket}' to add information"""

        return f"ticket: unknown option '{args[0]}'"

    def cmd_tnds(self, args: List[str]) -> str:
        """Enhanced Total Network Data System with realistic operational dynamics."""

        # Update TNDS state based on current time and network conditions
        self._update_tnds_state()

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")
            cycle = self._get_current_collection_cycle()

            return f"""Total Network Data System (TNDS) - Version 3.2A
Bell System Network Traffic Data Collection and Analysis
{current_time}

Current Operations Status:
  Collection Cycle:        {cycle['name']} ({cycle['time_range']})
  Data Points Collected:   {self.tnds_data['records_today']:,} (today)
  Processing Status:       {self.tnds_data['processing_status']}
  Storage Utilization:     {self.tnds_data['storage_used']}% of {self.tnds_data['storage_capacity']}GB

System Performance:
  Collection Success Rate: {self.tnds_data['collection_success']:.1%}
  Processing Efficiency:   {self.tnds_data['processing_efficiency']:.1%}
  Data Quality Index:      {self.tnds_data['data_quality']:.1%}
  Forecast Accuracy:       {self.tnds_data['forecast_accuracy']:.1%}

Available Commands:
  tnds status             - Detailed system operational status
  tnds collect            - Data collection operations and control
  tnds analysis           - Traffic analysis reports and statistics
  tnds forecast           - Traffic growth forecasting models
  tnds hierarchy          - Network hierarchy analysis
  tnds routing            - Dynamic routing analysis
  tnds reports            - Generate standardized reports
  tnds export             - Data export for engineering studies

Current Priority: {self._get_tnds_priority_task()}
Next Scheduled Operation: {self._get_next_tnds_operation()}

Project References: NP-8306 (TNDS Phase III Implementation)
Work Orders: WO-83054 (Data quality improvement initiatives)"""

        elif args[0] == "status":
            return self._show_tnds_detailed_status()

        elif args[0] == "collect":
            if len(args) > 1:
                return self._handle_tnds_collection_command(args[1:])
            else:
                return self._show_tnds_collection_status()

        elif args[0] == "analysis":
            if len(args) > 1:
                return self._generate_tnds_analysis_report(args[1])
            else:
                return self._generate_tnds_analysis_report("standard")

        elif args[0] == "forecast":
            if len(args) > 1:
                return self._generate_tnds_forecast(args[1])
            else:
                return self._generate_tnds_forecast("monthly")

        elif args[0] == "hierarchy":
            return self._show_network_hierarchy_analysis()

        elif args[0] == "routing":
            return self._show_dynamic_routing_analysis()

        elif args[0] == "reports":
            if len(args) > 1:
                return self._generate_tnds_report(args[1])
            else:
                return self._show_available_tnds_reports()

        elif args[0] == "export":
            if len(args) > 1:
                return self._handle_tnds_export(args[1:])
            else:
                return self._show_tnds_export_options()

        else:
            available_commands = ["status", "collect", "analysis", "forecast", "hierarchy", "routing", "reports", "export"]
            return f"tnds: Unknown option '{args[0]}'\nAvailable commands: {', '.join(available_commands)}"

    def _update_tnds_state(self) -> None:
        """Update TNDS operational state based on time and network conditions."""
        import random

        if not hasattr(self, 'tnds_data'):
            # Initialize TNDS operational data
            hour = self.clock.now().hour
            base_records = 2800000  # Base daily record count

            self.tnds_data: TndsData = {
                'records_today': int(base_records * (hour / 24) * random.uniform(0.95, 1.05)),
                'processing_status': random.choice(['Normal operation', 'High volume processing', 'Backlog processing']),
                'storage_used': random.randint(65, 85),
                'storage_capacity': random.choice([50, 75, 100]),  # GB capacity
                'collection_success': random.uniform(0.995, 0.999),
                'processing_efficiency': random.uniform(0.92, 0.98),
                'data_quality': random.uniform(0.996, 0.999),
                'forecast_accuracy': random.uniform(0.94, 0.97),
                'collection_points': random.randint(1240, 1260),
                'active_streams': random.randint(45, 50),
                'last_update': self.clock.now()
            }
        else:
            # Update existing data with small variations
            time_since_update = (self.clock.now() - self.tnds_data['last_update']).total_seconds() / 60
            if time_since_update > 5:  # Update every 5 minutes
                self.tnds_data['records_today'] += random.randint(1000, 5000)
                self.tnds_data['storage_used'] = min(95, self.tnds_data['storage_used'] + random.randint(-1, 2))
                self.tnds_data['last_update'] = self.clock.now()

    def _get_current_collection_cycle(self) -> dict:
        """Get current TNDS collection cycle information."""
        hour = self.clock.now().hour

        if 0 <= hour < 6:
            return {"name": "Cycle 1", "time_range": "00:00-06:00", "description": "Overnight processing"}
        elif 6 <= hour < 12:
            return {"name": "Cycle 2", "time_range": "06:00-12:00", "description": "Morning business traffic"}
        elif 12 <= hour < 18:
            return {"name": "Cycle 3", "time_range": "12:00-18:00", "description": "Peak traffic period"}
        else:
            return {"name": "Cycle 4", "time_range": "18:00-24:00", "description": "Evening traffic analysis"}

    def _get_tnds_priority_task(self) -> str:
        """Get current TNDS priority task based on time and conditions."""
        import random

        hour = self.clock.now().hour

        priority_tasks = {
            "morning": ["Peak traffic forecast validation", "Overnight data processing completion", "System health verification"],
            "business": ["Real-time traffic monitoring", "Capacity utilization analysis", "Performance optimization"],
            "peak": ["Traffic load balancing analysis", "Overflow pattern monitoring", "Revenue optimization tracking"],
            "evening": ["Daily report generation", "Archive preparation", "Forecast model updates"]
        }

        if 6 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "peak"
        elif 18 <= hour < 22:
            period = "evening"
        else:
            period = "business"

        return random.choice(priority_tasks[period])

    def _get_next_tnds_operation(self) -> str:
        """Get next scheduled TNDS operation."""

        next_ops = [
            f"Archive cycle: {(self.clock.now() + timedelta(hours=random.randint(2, 8))).strftime('%H:%M')}",
            f"Forecast update: {(self.clock.now() + timedelta(hours=random.randint(1, 4))).strftime('%H:%M')}",
            f"Report generation: {(self.clock.now() + timedelta(hours=random.randint(4, 12))).strftime('%H:%M')}",
            f"Data quality check: {(self.clock.now() + timedelta(hours=random.randint(1, 6))).strftime('%H:%M')}"
        ]

        return random.choice(next_ops)

    def _show_tnds_detailed_status(self) -> str:
        """Show detailed TNDS system status."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")
        cycle = self._get_current_collection_cycle()

        status_output = f"""TNDS System Status - Detailed Operations Report
Generated: {current_time}

Data Collection Status:
  Collection Points Online:    {self.tnds_data['collection_points']} of 1,255 total ({self.tnds_data['collection_points']/1255:.1%})
  Data Streams Active:         {self.tnds_data['active_streams']} trunk groups monitored
  Collection Interval:         5-minute samples (standard)
  Current Cycle:              {cycle['name']} - {cycle['description']}
  Collection Success Rate:     {self.tnds_data['collection_success']:.2%}

Processing Infrastructure:
  Data Processor A:            {'ACTIVE' if random.random() > 0.1 else 'MAINTENANCE'} - Primary processing unit
  Data Processor B:            {'STANDBY' if random.random() > 0.2 else 'ACTIVE'} - Backup/overflow processing
  Storage System:              {self.tnds_data['storage_used']}% utilized ({self.tnds_data['storage_capacity']}GB capacity)
  Analysis Engine:             {self.tnds_data['processing_status']}
  Database Server:             {'Online' if random.random() > 0.05 else 'Performance degraded'}

Current Data Flow (Last Hour):
  Call Detail Records:         {random.randint(45000, 85000):,} records
  Traffic Measurements:        {random.randint(8000, 15000):,} samples
  Network Performance Data:    {random.randint(3000, 8000):,} measurements
  Billing Records:             {random.randint(18000, 35000):,} transactions
  Equipment Status Reports:    {random.randint(500, 1200):,} status updates

Quality Metrics:
  Data Completeness:           {self.tnds_data['data_quality']:.2%}
  Validation Error Rate:       {(1 - self.tnds_data['data_quality']):.3%}
  Missing Timestamps:          {random.uniform(0.001, 0.01):.3%}
  Format Compliance:           {random.uniform(0.998, 0.999):.2%}
  Cross-Reference Accuracy:    {random.uniform(0.994, 0.998):.2%}

Performance Indicators:
  Processing Efficiency:       {self.tnds_data['processing_efficiency']:.1%}
  Average Response Time:       {random.uniform(0.8, 2.1):.1f} seconds
  Peak Hour Capacity:          {random.randint(85, 95)}% of maximum
  Forecast Accuracy:           {self.tnds_data['forecast_accuracy']:.1%} (30-day average)

Network Analysis Results:
  Peak Traffic Hour:           {random.randint(14, 16)}:{random.randint(0, 59):02d} - {random.randint(16, 18)}:{random.randint(0, 59):02d} EST
  Current Network Load:        {sum(tg['utilization'] for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE') // len([tg for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE'])}% of capacity
  Blocking Probability:        {random.uniform(0.001, 0.008):.3f} (Target: <0.01)
  Revenue per Hour:            ${random.randint(45000, 85000):,}

Scheduled Operations:
  Next Archive Cycle:          {(self.clock.now() + timedelta(hours=random.randint(4, 8))).strftime('%A %H:%M')}
  Forecast Model Update:       Daily at 18:00 EST
  Weekly Report Generation:    Monday 08:00 EST
  Database Maintenance:        Sunday 02:00-04:00 EST

Active Alerts:"""

        # Generate realistic alerts
        alerts = []
        if self.tnds_data['storage_used'] > 85:
            alerts.append("⚠ WARNING: Storage utilization above 85%")
        if self.tnds_data['collection_success'] < 0.998:
            alerts.append("⚠ NOTICE: Collection success rate below target")
        if random.random() < 0.2:
            alerts.append("ℹ INFO: High volume processing due to peak traffic")

        if alerts:
            for alert in alerts:
                status_output += f"\n  {alert}"
        else:
            status_output += "\n  ✓ All systems operating within normal parameters"

        status_output += """

Contact Information:
  TNDS Operations Center:      ext 4800
  Database Administration:     ext 4825
  Network Analysis Team:       ext 4850"""

        return status_output

    def _show_tnds_collection_status(self) -> str:
        """Show TNDS data collection operations status."""

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        collection_output = f"""TNDS Data Collection Operations
Status Report: {current_time}

Collection Infrastructure:
  Remote Collection Points:    {self.tnds_data['collection_points']} locations
  Data Communication Links:    T1 dedicated circuits
  Collection Frequency:        5-minute intervals (288 samples/day)
  Backup Collection System:    {'Active' if random.random() > 0.9 else 'Standby'}

Current Collection Status:
  Points Responding:           {self.tnds_data['collection_points'] - random.randint(0, 8)} of {self.tnds_data['collection_points']}
  Data Streams Active:         {self.tnds_data['active_streams']} trunk groups
  Collection Success Rate:     {self.tnds_data['collection_success']:.2%}
  Average Response Time:       {random.uniform(0.5, 1.8):.1f} seconds

Collection Volume (Last 24 Hours):
  Call Detail Records:         {random.randint(850000, 1200000):,}
  Traffic Measurements:        {random.randint(180000, 250000):,}
  Performance Metrics:         {random.randint(65000, 95000):,}
  Equipment Status:            {random.randint(12000, 18000):,}
  Billing Transactions:        {random.randint(420000, 580000):,}

Collection Points by Region:
  Northeast Corridor:          {random.randint(280, 320)} points (NYC, BOS, PHL, WAS)
  Southeast Region:            {random.randint(180, 220)} points (ATL, MIA, TAM, CHA)
  Central Region:              {random.randint(220, 260)} points (CHI, DET, STL, CLE)
  Western Region:              {random.randint(160, 200)} points (LAX, SFO, SEA, DEN)
  Southwest Region:            {random.randint(140, 180)} points (DAL, HOU, PHX, SAN)

Data Quality Assessment:
  Format Validation:           {random.uniform(0.998, 0.999):.3%} pass rate
  Timestamp Accuracy:          {random.uniform(0.999, 1.000):.3%} compliance
  Cross-Reference Check:       {random.uniform(0.995, 0.998):.3%} validation
  Completeness Index:          {self.tnds_data['data_quality']:.2%}

Collection Schedule:
  Standard Collection:         Continuous 24/7 operation
  Peak Period Enhancement:     14:00-16:00 EST (1-minute intervals)
  Maintenance Window:          Sunday 02:00-04:00 EST
  Archive Transfer:            Daily 01:00 EST to Bell Labs

Commands:
  tnds collect start           Initiate collection cycle
  tnds collect stop            Halt collection (emergency only)
  tnds collect test            Test collection point connectivity
  tnds collect status <region> Regional collection status"""

        return collection_output

    def _generate_tnds_analysis_report(self, report_type: str) -> str:
        """Generate TNDS traffic analysis report with realistic data patterns."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        if report_type == "standard":
            period = "November 7-14, 1983"
            days = 7
        elif report_type == "monthly":
            period = "November 1983"
            days = 30
        elif report_type == "weekly":
            period = f"Week of {(self.clock.now() - timedelta(days=7)).strftime('%B %d, %Y')}"
            days = 7
        else:
            period = "Custom Period"
            days = 7

        # Generate realistic traffic metrics
        base_calls = 850000 * days
        completion_rate = random.uniform(0.975, 0.995)
        total_attempts = int(base_calls * random.uniform(0.95, 1.05))
        successful_calls = int(total_attempts * completion_rate)

        analysis_output = f"""TNDS Traffic Analysis Report
Generated: {current_time}
Analysis Period: {period}

NETWORK PERFORMANCE SUMMARY
{'=' * 50}
Total Call Attempts:          {total_attempts:,}
Successful Completions:       {successful_calls:,} ({completion_rate:.1%})
Average Call Setup Time:      {random.uniform(1.8, 2.4):.1f} seconds
Network Efficiency:           {random.uniform(0.94, 0.97):.1%}
Revenue Generated:            ${random.randint(450000 * days, 650000 * days):,}

TRAFFIC PATTERNS ANALYSIS
{'=' * 50}"""

        # Generate daily peak traffic data
        peak_hours = []
        for day in range(min(days, 7)):  # Show up to 7 days of peaks
            day_name = (self.clock.now() - timedelta(days=day)).strftime('%A')
            peak_time = f"{random.randint(14, 16)}:{random.randint(0, 59):02d}"
            peak_ccs = random.randint(850, 950)
            peak_hours.append((day_name, peak_time, peak_ccs))

        for day_name, peak_time, peak_ccs in peak_hours:
            analysis_output += f"\n{day_name:<12} Peak: {peak_time} EST ({peak_ccs} CCS)"

        analysis_output += f"""

Busy Season Factor:           {random.uniform(1.10, 1.20):.2f} (Holiday adjustment)
Growth Rate vs Previous:      {random.uniform(2.8, 4.2):+.1f}% call volume change
Weekend Traffic Factor:       {random.uniform(0.65, 0.75):.2f} of weekday volume

TRUNK GROUP UTILIZATION
{'=' * 50}
Average Network Utilization:  {sum(tg['utilization'] for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE') // len([tg for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE'])}%"""

        # Show top utilized trunk groups
        sorted_trunks = sorted([(name, tg['utilization'], tg['route']) for name, tg in self.trunk_groups.items() if tg['status'] == 'ACTIVE'],
                              key=lambda x: x[1], reverse=True)

        for i, (tg_name, utilization, route) in enumerate(sorted_trunks[:5]):
            utilization_status = "HIGH" if utilization > 80 else "NORMAL" if utilization > 40 else "LOW"
            analysis_output += f"\n{i+1}. {tg_name:<12} {utilization:>3}% ({utilization_status:<6}) {route}"

        analysis_output += f"""

Overflow Events:              {random.randint(8, 25)} occurrences (all recovered <30 sec)
Peak Trunk Utilization:       {max(tg['utilization'] for tg in self.trunk_groups.values())}%
Load Balancing Efficiency:    {random.uniform(0.91, 0.96):.1%}

REVENUE AND ECONOMIC ANALYSIS
{'=' * 50}
Revenue per Call:             ${random.uniform(0.45, 0.75):.2f} average
Peak Hour Revenue Rate:       ${random.randint(25000, 45000):,}/hour
Interstate Long Distance:     {random.uniform(0.35, 0.45):.1%} of total revenue
International Traffic:        {random.uniform(0.08, 0.15):.1%} of total revenue
Operator Assisted:            {random.uniform(0.12, 0.18):.1%} of total revenue

FORECASTING RESULTS
{'=' * 50}
Next Month Peak Forecast:     {random.randint(920, 980)} CCS ({random.uniform(5, 8):+.1f}% vs current)
Capacity Requirements:        {random.randint(2, 5)} additional trunk groups recommended
Investment Requirement:       ${random.uniform(1.0, 2.5):.1f}M for network expansion
Growth Projection (6 months): {random.uniform(12, 18):+.1f}% call volume increase

RECOMMENDATIONS
{'=' * 50}"""

        # Generate realistic recommendations
        recommendations = []
        high_util_trunks = [name for name, tg in self.trunk_groups.items() if tg['utilization'] > 80 and tg['status'] == 'ACTIVE']

        if high_util_trunks:
            recommendations.append(f"1. Monitor {high_util_trunks[0]} for immediate capacity upgrade")
        else:
            recommendations.append("1. All trunk groups operating within capacity")

        recommendations.extend([
            "2. Implement Dynamic Non-Hierarchical Routing (DNHR) on high-traffic routes",
            "3. Schedule capacity planning review for Q1 1984",
            "4. Continue TNDS data quality improvement initiatives",
            f"5. Evaluate load balancing effectiveness on {random.choice(['Route 1', 'Route 3', 'Eastern Corridor'])}"
        ])

        for rec in recommendations:
            analysis_output += f"\n{rec}"

        analysis_output += f"""

Report Distribution:
  Network Planning Engineering: Copy 1
  Traffic Engineering: Copy 2
  Revenue Analysis: Copy 3
  Bell Laboratories: Copy 4 (for research)

Next Analysis Report: {(self.clock.now() + timedelta(days=7)).strftime('%B %d, %Y')}"""

        return analysis_output

    def _handle_tnds_collection_command(self, args: List[str]) -> str:
        """Handle TNDS data collection subcommands (start, stop, verify, poll)."""
        action = args[0].lower()
        timestamp = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        if action == "start":
            self.tnds_data['processing_status'] = 'Normal operation'
            return f"""TNDS Data Collection - Start Request
{'=' * 50}
Requested: {timestamp}

EADAS collection scheduler ACKNOWLEDGED
Collection points activated:  {self.tnds_data['collection_points']} of 1,255
Active data streams:          {self.tnds_data['active_streams']} trunk groups
Polling interval:             300 seconds (5 minute registers)

Status: COLLECTION ACTIVE
Authorization: WO-83054"""

        if action == "stop":
            self.tnds_data['processing_status'] = 'Collection suspended'
            return f"""TNDS Data Collection - Stop Request
{'=' * 50}
Requested: {timestamp}

WARNING: Halting collection creates gaps in the traffic record.
Peak-hour data cannot be reconstructed once the interval closes.

Collection points quiesced:   {self.tnds_data['collection_points']}
Records buffered for flush:   {random.randint(400, 2200):,}

Status: COLLECTION SUSPENDED
Resume with: tnds collect start"""

        if action == "verify":
            error_rate = 1 - self.tnds_data['data_quality']
            return f"""TNDS Collection Verification
{'=' * 50}
Verification Run: {timestamp}

REGISTER INTEGRITY
{'=' * 35}
Collection Points Polled:     {self.tnds_data['collection_points']}
Points Responding:            {self.tnds_data['collection_points'] - random.randint(0, 4)}
Success Rate:                 {self.tnds_data['collection_success']:.3%}
Validation Error Rate:        {error_rate:.3%}

DATA QUALITY
{'=' * 35}
Completeness Index:           {self.tnds_data['data_quality']:.3%}
Records Accepted Today:       {self.tnds_data['records_today']:,}
Records Rejected:             {int(self.tnds_data['records_today'] * error_rate):,}

Verification Result: {'PASS' if self.tnds_data['data_quality'] > 0.995 else 'REVIEW REQUIRED'}"""

        if action == "poll":
            target = args[1].upper() if len(args) > 1 else "ALL"
            polled = [t for t in self.trunk_groups if target in ("ALL", t)] or list(self.trunk_groups)
            output = f"""TNDS On-Demand Poll
{'=' * 50}
Poll Initiated: {timestamp}
Target: {target}

TRUNK GROUP REGISTERS
{'=' * 35}"""
            for tg_name in polled:
                tg = self.trunk_groups[tg_name]
                ccs = int(tg['capacity'] * tg['utilization'] * 0.36)
                output += f"""
{tg_name}:
  Route:              {tg['route']}
  Usage:              {ccs} CCS
  Utilization:        {tg['utilization']}%
  Register Status:    {'READ OK' if tg['status'] == 'ACTIVE' else 'OUT OF SERVICE'}"""
            output += f"\n\nPoll complete. {len(polled)} register set(s) read."
            return output

        return (f"tnds collect: Unknown action '{args[0]}'\n"
                "Available actions: start, stop, verify, poll [trunk-group]")

    def _generate_tnds_forecast(self, period: str) -> str:
        """Generate a TNDS traffic growth forecast for the requested period."""
        horizons = {
            "monthly": ("Monthly", 1, 30),
            "quarterly": ("Quarterly", 3, 90),
            "annual": ("Annual", 12, 365),
        }
        label, months, days = horizons.get(period.lower(), ("Monthly", 1, 30))
        growth = random.uniform(0.9, 1.8) * months
        current_ccs = sum(
            int(tg['capacity'] * tg['utilization'] * 0.36)
            for tg in self.trunk_groups.values()
        )
        projected_ccs = int(current_ccs * (1 + growth / 100))
        target = (self.clock.now() + timedelta(days=days)).strftime('%B %Y')

        output = f"""TNDS Traffic Forecast - {label} Model
Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}
Forecast Horizon: {target}
{'=' * 55}

MODEL PARAMETERS
{'=' * 40}
Forecast Method:              Exponential smoothing with seasonal index
Historical Base:              36 months of EADAS register data
Model Accuracy (backtest):    {self.tnds_data['forecast_accuracy']:.1%}
Confidence Interval:          {random.uniform(90, 95):.0f}%

AGGREGATE PROJECTION
{'=' * 40}
Current Measured Load:        {current_ccs:,} CCS
Projected Load ({label}):     {projected_ccs:,} CCS
Growth Rate:                  {growth:+.1f}%
Busy Hour Shift:              {random.choice(['None', '+30 min later', '-15 min earlier'])}

PER-ROUTE FORECAST
{'=' * 40}"""

        for tg_name, tg in self.trunk_groups.items():
            if tg['status'] != 'ACTIVE':
                continue
            route_growth = growth * random.uniform(0.6, 1.5)
            projected_util = min(100, tg['utilization'] * (1 + route_growth / 100))
            flag = 'BLOCKING RISK' if projected_util > 85 else 'WITHIN CAPACITY'
            output += f"""
{tg_name} ({tg['route']}):
  Current Utilization:  {tg['utilization']}%
  Projected:            {projected_util:.0f}%
  Growth:               {route_growth:+.1f}%
  Assessment:           {flag}"""

        at_risk = [
            n for n, t in self.trunk_groups.items()
            if t['status'] == 'ACTIVE' and t['utilization'] * (1 + growth / 100) > 85
        ]
        output += f"""

CAPACITY RECOMMENDATIONS
{'=' * 40}"""
        if at_risk:
            for i, name in enumerate(at_risk, 1):
                output += f"\n{i}. Augment {name} before {target} - projected blocking above P.01 grade of service"
            output += f"\n{len(at_risk) + 1}. Submit trunk order via TIRKS for affected routes"
        else:
            output += "\n1. No augmentation required within forecast horizon"
            output += "\n2. Continue routine quarterly capacity review"

        output += f"""

Distribution: Network Planning, Traffic Engineering
Project Reference: NP-8306 (TNDS Phase III)
Next Forecast Run: {(self.clock.now() + timedelta(days=days)).strftime('%B %d, %Y')}"""
        return output

    def _show_network_hierarchy_analysis(self) -> str:
        """Show Bell System switching hierarchy analysis (Class 1 through Class 5)."""
        hierarchy = [
            ("Class 1", "Regional Center", 10, 0, random.uniform(0.72, 0.84)),
            ("Class 2", "Sectional Center", 52, 0, random.uniform(0.68, 0.80)),
            ("Class 3", "Primary Center", 148, 20, random.uniform(0.64, 0.78)),
            ("Class 4", "Toll Center", 508, 425, random.uniform(0.58, 0.74)),
            ("Class 5", "End Office", 9803, 9000, random.uniform(0.52, 0.70)),
        ]

        output = f"""TNDS Network Hierarchy Analysis
Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}
{'=' * 55}

SWITCHING HIERARCHY (1982 office counts)
{'=' * 62}
Class    Office Type            Bell   Independent    Avg Util
{'-' * 62}"""
        for cls, name, bell, independent, util in hierarchy:
            ind = f"{independent:,}" if independent else "-"
            output += (f"\n{cls:<8} {name:<20} {bell:>6,}  {ind:>11}"
                       f"    {util:>6.1%}")

        output += f"""

FINAL AND HIGH-USAGE GROUPS
{'=' * 62}
Final Trunk Groups:           {random.randint(2400, 2900):,} (hierarchical backbone)
High-Usage Groups:            {random.randint(5200, 6400):,} (direct routes)
Overflow Discipline:          Hierarchical alternate routing
Grade of Service Objective:   P.01 final groups / P.10 high-usage

A call is completed at the lowest level of the hierarchy that can carry it,
using the fewest trunks in tandem. An office joined to a higher class office
by a final group is said to home on it, though not every office homes on the
next class up. When every trunk in a final group is busy the call is blocked
and the caller receives reorder.

Average trunks per toll connection:   slightly over 3, including toll
                                      connecting trunks
Maximum trunks in one connection:     9

TANDEM ROUTING ANALYSIS
{'=' * 45}"""

        for tg_name, tg in self.trunk_groups.items():
            if tg['status'] != 'ACTIVE':
                continue
            route_kind = 'High-usage direct' if tg['utilization'] > 65 else 'Final group'
            output += f"""
{tg_name} ({tg['route']}):
  Group Type:           {route_kind}
  Overflow Path:        {random.choice(['Via Class 3 tandem', 'Via Class 2 sectional', 'Direct final'])}
  Tandem Switches:      {random.randint(1, 3)} in path"""

        output += f"""

HIERARCHY OBSERVATIONS
{'=' * 45}
Offices Homing Correctly:     {random.uniform(0.985, 0.998):.1%}
Misrouted Homing Records:     {random.randint(3, 18)} (referred to Network Planning)
Alternate Route Depth:        {random.randint(2, 4)} levels average

Reference: Notes on the Network, Section 4 (Switching Hierarchy)
Distribution: Network Planning, Traffic Engineering"""
        return output

    def _show_dynamic_routing_analysis(self) -> str:
        """Show dynamic routing performance analysis for the trunk network."""
        active = {n: t for n, t in self.trunk_groups.items() if t['status'] == 'ACTIVE'}
        overflow_total = sum(
            int(t['capacity'] * max(0, t['utilization'] - 70) * 0.12) for t in active.values()
        )

        output = f"""TNDS Dynamic Routing Analysis
Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}
{'=' * 55}

ROUTING PERFORMANCE SUMMARY
{'=' * 45}
Routes Under Analysis:        {len(active)}
Total Overflow Attempts:      {overflow_total:,} (last measurement hour)
First-Route Completion:       {random.uniform(0.88, 0.96):.1%}
Alternate Route Completion:   {random.uniform(0.96, 0.995):.1%}
Network Blocking:             {random.uniform(0.002, 0.012):.3%}

PER-ROUTE ROUTING BEHAVIOR
{'=' * 45}"""

        for tg_name, tg in active.items():
            overflow = int(tg['capacity'] * max(0, tg['utilization'] - 70) * 0.12)
            output += f"""
{tg_name} ({tg['route']}):
  Offered Load:         {int(tg['capacity'] * tg['utilization'] * 0.36)} CCS
  Overflow to Alternate:{overflow:>6,} attempts
  Transmission Quality: {tg['quality']:.3%}
  Routing Decision:     {'Overflow active' if overflow else 'Direct route sufficient'}"""

        output += f"""

TIME-OF-DAY ROUTING
{'=' * 45}
Morning Business Peak:        10:00-11:00 EST ({random.randint(88, 97)}% of capacity)
Afternoon Business Peak:      14:00-15:00 EST ({random.randint(85, 95)}% of capacity)
Evening Residential Peak:     19:00-20:00 EST ({random.randint(70, 85)}% of capacity)
Time-Zone Load Shifting:      {random.uniform(12, 22):.0f}% capacity recovered east-to-west

ROUTING RECOMMENDATIONS
{'=' * 45}
1. Continue load-shifting studies against measured busy hour
2. Review alternate route depth on routes exceeding 85% utilization
3. Coordinate routing pattern changes with Network Planning (NP-8306)

Distribution: Network Operations, Traffic Engineering"""
        return output

    def _show_available_tnds_reports(self) -> str:
        """Show the catalog of standard TNDS reports available for generation."""
        return f"""TNDS Standard Report Catalog
{'=' * 55}

AVAILABLE REPORTS
{'=' * 45}
  tnds reports traffic        Traffic Usage Summary (TUS-1)
  tnds reports blocking       Blocking and Overflow Report (BOR-3)
  tnds reports quality        Data Quality Assurance Report (DQA-2)
  tnds reports capacity       Capacity Exhaust Projection (CEP-4)
  tnds reports monthly        Monthly Network Summary (MNS-1)

REPORT CHARACTERISTICS
{'=' * 45}
Source Data:                  EADAS collection registers
Retention Period:             36 months on-line, 7 years archived
Standard Distribution:        Network Planning, Traffic Engineering,
                              Revenue Accounting, Bell Laboratories
Generation Time:              2-6 minutes depending on period

SCHEDULING
{'=' * 45}
Daily Reports:                Generated 02:00 EST
Weekly Reports:               Generated Monday 03:00 EST
Monthly Reports:              Generated first business day 04:00 EST
Last Generation Run:          {(self.clock.now() - timedelta(hours=random.randint(2, 20))).strftime('%B %d, %Y %H:%M EST')}

Usage: tnds reports <report-name>"""

    def _generate_tnds_report(self, report_name: str) -> str:
        """Generate a named standard TNDS report."""
        name = report_name.lower()
        stamp = self.clock.now().strftime('%B %d, %Y %H:%M EST')
        active = {n: t for n, t in self.trunk_groups.items() if t['status'] == 'ACTIVE'}

        if name == "traffic":
            total_ccs = sum(int(t['capacity'] * t['utilization'] * 0.36) for t in active.values())
            output = f"""Traffic Usage Summary (TUS-1)
Generated: {stamp}
{'=' * 55}

NETWORK TOTALS
{'=' * 45}
Measured Trunk Groups:        {len(active)}
Total Offered Load:           {total_ccs:,} CCS
Average Utilization:          {sum(t['utilization'] for t in active.values()) / max(1, len(active)):.1f}%
Records Processed:            {self.tnds_data['records_today']:,}

PER-GROUP USAGE
{'=' * 45}"""
            for tg_name, tg in active.items():
                output += (f"\n{tg_name:<12} {tg['route']:<10} "
                           f"{int(tg['capacity'] * tg['utilization'] * 0.36):>6,} CCS  "
                           f"{tg['utilization']:>3}%")
            return output + "\n\nDistribution: Traffic Engineering, Network Planning"

        if name == "blocking":
            output = f"""Blocking and Overflow Report (BOR-3)
Generated: {stamp}
{'=' * 55}

GRADE OF SERVICE OBJECTIVE: P.01 (final groups)
{'=' * 45}"""
            for tg_name, tg in active.items():
                blocking = max(0.0001, (tg['utilization'] - 60) / 4000)
                status = 'OBJECTIVE MET' if blocking <= 0.01 else 'OBJECTIVE EXCEEDED'
                output += f"""
{tg_name} ({tg['route']}):
  Utilization:          {tg['utilization']}%
  Measured Blocking:    {blocking:.3%}
  Assessment:           {status}"""
            return output + "\n\nDistribution: Network Operations, Traffic Engineering"

        if name == "quality":
            error_rate = 1 - self.tnds_data['data_quality']
            return f"""Data Quality Assurance Report (DQA-2)
Generated: {stamp}
{'=' * 55}

COLLECTION INTEGRITY
{'=' * 45}
Collection Success Rate:      {self.tnds_data['collection_success']:.3%}
Data Completeness:            {self.tnds_data['data_quality']:.3%}
Validation Error Rate:        {error_rate:.3%}
Processing Efficiency:        {self.tnds_data['processing_efficiency']:.1%}

EXCEPTION SUMMARY
{'=' * 45}
Records Rejected:             {int(self.tnds_data['records_today'] * error_rate):,}
Missing Register Reads:       {random.randint(0, 12)}
Out-of-Range Values:          {random.randint(2, 30)}
Duplicate Records Purged:     {random.randint(0, 8)}

Assessment: {'WITHIN STANDARD' if error_rate < 0.005 else 'REVIEW REQUIRED'}
Distribution: Data Administration, Bell Laboratories"""

        if name == "capacity":
            output = f"""Capacity Exhaust Projection (CEP-4)
Generated: {stamp}
{'=' * 55}

PROJECTED EXHAUST BY ROUTE
{'=' * 45}"""
            for tg_name, tg in active.items():
                months = max(1, int((90 - tg['utilization']) / random.uniform(0.8, 2.2)))
                exhaust = (self.clock.now() + timedelta(days=months * 30)).strftime('%B %Y')
                output += f"""
{tg_name} ({tg['route']}):
  Current Utilization:  {tg['utilization']}%
  Months to Exhaust:    {months}
  Projected Exhaust:    {exhaust}
  Action:               {'Trunk order required' if months <= 6 else 'Monitor'}"""
            return output + "\n\nDistribution: Network Planning, Capital Planning"

        if name == "monthly":
            return f"""Monthly Network Summary (MNS-1)
Generated: {stamp}
Reporting Period: {self.clock.now().strftime('%B %Y')}
{'=' * 55}

VOLUME SUMMARY
{'=' * 45}
Total Records Collected:      {self.tnds_data['records_today'] * 30:,}
Collection Points:            {self.tnds_data['collection_points']} of 1,255
Active Data Streams:          {self.tnds_data['active_streams']}
Storage Utilization:          {self.tnds_data['storage_used']}% of {self.tnds_data['storage_capacity']}GB

SERVICE SUMMARY
{'=' * 45}
Average Network Utilization:  {sum(t['utilization'] for t in active.values()) / max(1, len(active)):.1f}%
Trunk Groups In Service:      {len(active)} of {len(self.trunk_groups)}
Groups Under Maintenance:     {len(self.trunk_groups) - len(active)}
Forecast Model Accuracy:      {self.tnds_data['forecast_accuracy']:.1%}

Distribution: Network Planning, Traffic Engineering, Revenue Accounting"""

        return (f"tnds reports: Unknown report '{report_name}'\n"
                "Use 'tnds reports' to list the available reports.")

    def _show_tnds_export_options(self) -> str:
        """Show available TNDS data export formats and destinations."""
        return f"""TNDS Data Export Options
{'=' * 55}

EXPORT FORMATS
{'=' * 45}
  tnds export tape            9-track tape, 1600 BPI, EBCDIC
  tnds export cards           80-column card image deck
  tnds export rje             Remote Job Entry to Bell Labs
  tnds export print           Line printer listing (132 column)

DESTINATIONS
{'=' * 45}
Network Planning:             Murray Hill, NJ
Traffic Engineering:          Holmdel, NJ
Bell Laboratories:            Whippany, NJ (research studies)
Revenue Accounting:           Regional accounting centers

DATA SETS AVAILABLE
{'=' * 45}
Trunk Group Usage:            {len(self.trunk_groups)} groups, 36 months history
Collection Registers:         {self.tnds_data['collection_points']} points
Records Available Today:      {self.tnds_data['records_today']:,}

Note: Exports require authorization under WO-83054.
Usage: tnds export <format> [destination]"""

    def _handle_tnds_export(self, args: List[str]) -> str:
        """Handle a TNDS data export request."""
        fmt = args[0].lower()
        destination = " ".join(args[1:]) if len(args) > 1 else "Network Planning"
        formats = {
            "tape": ("9-track tape, 1600 BPI, EBCDIC", "TAPE-" + str(random.randint(1000, 9999))),
            "cards": ("80-column card image deck", "DECK-" + str(random.randint(100, 999))),
            "rje": ("Remote Job Entry stream", "RJE-" + str(random.randint(1000, 9999))),
            "print": ("132-column line printer listing", "LP-" + str(random.randint(100, 999))),
        }

        if fmt not in formats:
            return (f"tnds export: Unknown format '{args[0]}'\n"
                    "Available formats: tape, cards, rje, print")

        description, volume_id = formats[fmt]
        records = self.tnds_data['records_today']
        return f"""TNDS Data Export - Request Accepted
{'=' * 55}
Submitted: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}

EXPORT PARAMETERS
{'=' * 45}
Format:                       {description}
Volume Identifier:            {volume_id}
Destination:                  {destination}
Records Selected:             {records:,}
Estimated Volume:             {records * 80 / 1_000_000:.1f} MB

PROCESSING
{'=' * 45}
Queue Position:               {random.randint(1, 5)}
Estimated Completion:         {(self.clock.now() + timedelta(minutes=random.randint(15, 90))).strftime('%H:%M EST')}
Operator Notification:        Console message on completion

Authorization: WO-83054
Status: QUEUED FOR PROCESSING"""

    def cmd_bsp(self, args: List[str]) -> str:
        """Bell System Practices - Standard Operating Procedures"""
        if not args:
            return """Bell System Practices (BSP)
Standard Operating Procedures and Technical References

Available Commands:
  bsp search <topic>   - Search BSP procedures
  bsp section <num>    - Display specific BSP section
  bsp recent          - Recently updated procedures
  bsp index           - BSP section index

Current BSP Library:
  Total Procedures:    14,892 sections
  Recent Updates:      47 sections (this month)
  Categories:          156 technical areas

Most Referenced:
  BSP 100-000         Bell System Fundamentals
  BSP 200-000         Switching Systems
  BSP 300-000         Transmission Systems
  BSP 400-000         Network Operations"""

        if args[0] == "search" and len(args) > 1:
            topic = " ".join(args[1:]).lower()
            return f"""BSP Search Results: "{topic}"

Matching Procedures:
  BSP 200-455-100     3A Central Control Maintenance
  BSP 200-455-200     3A System Administration
  BSP 200-455-300     3A Trouble Analysis
  BSP 200-455-400     3A Performance Monitoring

  BSP 300-125-001     TH-3 Microwave Alignment
  BSP 300-125-100     Radio Path Analysis
  BSP 300-125-200     Fade Margin Calculations

  BSP 400-200-001     TNDS Data Collection
  BSP 400-200-100     Traffic Analysis Procedures
  BSP 400-200-200     Network Performance Reports

Use 'bsp section <number>' for detailed procedures"""

        elif args[0] == "section" and len(args) > 1:
            section = args[1]
            return f"""Bell System Practice {section}
Revision Date: November 1983

PROCEDURE: 3A Central Control System Maintenance
CATEGORY: Electronic Switching Systems
DIVISION: Network Operations

SCOPE:
This practice covers routine maintenance procedures for the 3A Central
Control switching system including diagnostic testing, performance
monitoring, and preventive maintenance schedules.

PROCEDURE STEPS:

1. DAILY CHECKS (0800 hours)
   a. Review alarm logs for overnight activity
   b. Check processor occupancy levels
   c. Verify all central control units operational
   d. Review traffic load statistics

2. WEEKLY MAINTENANCE (Sunday 0200-0600)
   a. Run comprehensive diagnostic suite
   b. Exercise standby control units
   c. Update traffic translation tables
   d. Archive performance data

3. MONTHLY PROCEDURES
   a. Ferrite core memory tests
   b. Scanner unit calibration
   c. Network control verification
   d. Documentation updates

SAFETY CONSIDERATIONS:
- Follow lockout/tagout procedures
- Verify redundant systems before maintenance
- Coordinate with traffic engineering

REFERENCE DOCUMENTS:
SD-1C900-01: 3A Central Control Circuit Description
BSP 200-000: Electronic Switching Fundamentals"""

        return f"bsp: unknown option '{args[0]}'"

    # Additional essential commands
    def cmd_traffic(self, args: List[str]) -> str:
        """Enhanced network traffic analysis with real-time monitoring capabilities."""
        import random

        # Update traffic state for realistic behavior
        self._update_traffic_state()

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            # Calculate dynamic metrics from network state
            total_load = sum(tg['utilization'] for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE') // len([tg for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE'])

            traffic_output = f"""Bell System Network Traffic Analysis
Real-Time Monitoring and Statistics
{current_time}

CURRENT NETWORK STATUS
{'=' * 40}
Total Traffic Load:       {total_load}% of network capacity
Peak Period Today:        {self._get_peak_period()}
Call Completion Rate:     {self.network_metrics['call_completion']:.1%}
Average Hold Time:        {self.traffic_data['avg_duration']:.1f} minutes
Setup Time Average:       {self.network_metrics['setup_time']:.1f} seconds

REAL-TIME CALL VOLUME
{'=' * 40}
Active Calls:             {self.traffic_data['current_calls']:,}
Calls Completed Today:    {self.traffic_data['calls_today']:,}
Revenue Generated:        ${self.traffic_data['revenue_today']:,}
International Traffic:    {self.traffic_data['international_pct']:.1%} of total
Toll Traffic:             {self.traffic_data['toll_pct']:.1%} of total

INTER-OFFICE ROUTE STATUS
{'=' * 40}"""

            # Show major trunk group utilization
            major_routes = [
                ('NYC-WAS', next((tg['utilization'] for name, tg in self.trunk_groups.items() if 'NYC' in name and tg['route'] == 'NYC-WAS'), random.randint(75, 90))),
                ('NYC-BOS', next((tg['utilization'] for name, tg in self.trunk_groups.items() if 'BOS' in name and tg['route'] == 'NYC-BOS'), random.randint(60, 80))),
                ('WAS-ATL', next((tg['utilization'] for name, tg in self.trunk_groups.items() if 'WAS' in name and tg['route'] == 'WAS-ATL'), random.randint(40, 70))),
                ('CHI-NYC', next((tg['utilization'] for name, tg in self.trunk_groups.items() if 'CHI' in name and tg['route'] == 'CHI-NYC'), random.randint(35, 65)))
            ]

            for route, utilization in major_routes:
                status = "HIGH" if utilization > 80 else "NORMAL" if utilization > 40 else "LOW"
                calls_hour = int((utilization / 100) * random.randint(15000, 45000))
                traffic_output += f"\n{route:<15} {utilization:>3}% utilization  {status:<8} ({calls_hour:,} calls/hour)"

            # Regional traffic distribution
            traffic_output += f"""

REGIONAL TRAFFIC DISTRIBUTION
{'=' * 40}"""

            for region, data in self.regional_traffic.items():
                pct = (data['calls'] / self.traffic_data['current_calls']) * 100
                traffic_output += f"\n{region.title():<12} {data['calls']:>8,} calls ({pct:>4.1f}%)  Revenue: ${data['revenue']:,}"

            # Traffic quality metrics
            traffic_output += f"""

QUALITY METRICS
{'=' * 40}
Blocking Rate:            {self.network_metrics['blocking_rate']:.3f} (Target: <0.01)
Post-Dial Delay:          {self.network_metrics['setup_time']:.1f} seconds average
Network Efficiency:       {self.traffic_data['completion_rate']:.1%}
Customer Satisfaction:    {random.uniform(4.1, 4.7):.1f}/5.0 rating

Commands:
  traffic detail <region>   Regional traffic analysis
  traffic forecast          Traffic projection and planning
  traffic routes            Route-specific performance
  traffic peak              Peak period analysis
  traffic quality           Quality metrics and trending"""

            return traffic_output

        elif args[0] == "detail" and len(args) > 1:
            region = args[1].lower()
            return self._show_regional_traffic_detail(region)

        elif args[0] == "forecast":
            return self._generate_traffic_forecast()

        elif args[0] == "routes":
            return self._show_route_performance()

        elif args[0] == "peak":
            return self._show_peak_analysis()

        elif args[0] == "quality":
            return self._show_traffic_quality_metrics()

        else:
            available_commands = ["detail", "forecast", "routes", "peak", "quality"]
            return f"traffic: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"

    def _update_traffic_state(self) -> None:
        """Update traffic state with realistic time-based variations."""

        hour = self.clock.now().hour

        # Adjust traffic patterns based on time of day
        if 8 <= hour <= 10:  # Morning business peak
            multiplier = random.uniform(1.1, 1.3)
        elif 14 <= hour <= 16:  # Afternoon peak
            multiplier = random.uniform(1.2, 1.4)
        elif 19 <= hour <= 21:  # Evening social peak
            multiplier = random.uniform(0.9, 1.1)
        elif 22 <= hour or hour <= 6:  # Overnight
            multiplier = random.uniform(0.3, 0.5)
        else:  # Regular business hours
            multiplier = random.uniform(0.8, 1.0)

        # Update regional traffic with realistic variations
        for region, data in self.regional_traffic.items():
            variation = random.uniform(0.95, 1.05) * multiplier
            data['calls'] = int(data['calls'] * variation)
            data['revenue'] = int(data['revenue'] * variation * random.uniform(0.98, 1.02))

    def _show_regional_traffic_detail(self, region: str) -> str:
        """Show detailed traffic analysis for a specific region."""
        import random

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        if region not in self.regional_traffic:
            available_regions = list(self.regional_traffic.keys())
            return f"traffic: Unknown region '{region}'\nAvailable regions: {', '.join(available_regions)}"

        region_data = self.regional_traffic[region]

        detail_output = f"""Regional Traffic Detail - {region.title()}
Analysis Time: {current_time}

CURRENT ACTIVITY
{'=' * 30}
Active Calls:             {region_data['calls']:,}
Revenue This Hour:        ${region_data['revenue']:,}
Peak Hour Calls:          {int(region_data['calls'] * random.uniform(1.2, 1.5)):,} (estimated)
Market Share:             {(region_data['calls'] / sum(d['calls'] for d in self.regional_traffic.values())) * 100:.1f}% of total network

TRAFFIC PATTERNS
{'=' * 30}"""

        # Generate realistic traffic breakdown by type
        business_pct = random.uniform(0.60, 0.75) if region == 'northeast' else random.uniform(0.45, 0.65)
        residential_pct = 1.0 - business_pct - random.uniform(0.08, 0.15)  # Subtract toll/international

        detail_output += f"""
Business Hours (08:00-17:00):  {business_pct:.1%} of daily volume
Residential (17:00-22:00):     {residential_pct:.1%} of daily volume
Overnight (22:00-08:00):       {(1 - business_pct - residential_pct):.1%} of daily volume

MAJOR DESTINATIONS FROM {region.upper()}
{'=' * 30}"""

        # Define realistic destination patterns by region
        if region == 'northeast':
            destinations = [
                ('Washington DC', random.randint(8000, 15000), random.uniform(1.2, 1.8)),
                ('Boston', random.randint(6000, 12000), random.uniform(0.8, 1.4)),
                ('Philadelphia', random.randint(4000, 8000), random.uniform(0.6, 1.0)),
                ('Chicago', random.randint(3000, 6000), random.uniform(1.5, 2.2))
            ]
        elif region == 'southeast':
            destinations = [
                ('Miami', random.randint(5000, 9000), random.uniform(0.9, 1.5)),
                ('New York', random.randint(4000, 8000), random.uniform(1.8, 2.5)),
                ('Tampa', random.randint(3000, 6000), random.uniform(0.7, 1.2)),
                ('Charlotte', random.randint(2000, 4000), random.uniform(0.8, 1.3))
            ]
        elif region == 'central':
            destinations = [
                ('Detroit', random.randint(6000, 10000), random.uniform(0.8, 1.4)),
                ('New York', random.randint(5000, 9000), random.uniform(2.0, 2.8)),
                ('St. Louis', random.randint(4000, 7000), random.uniform(0.6, 1.1)),
                ('Cleveland', random.randint(3000, 5000), random.uniform(0.7, 1.2))
            ]
        else:  # west
            destinations = [
                ('San Francisco', random.randint(4000, 7000), random.uniform(0.5, 0.9)),
                ('New York', random.randint(3000, 6000), random.uniform(2.8, 3.5)),
                ('Seattle', random.randint(2000, 4000), random.uniform(0.8, 1.4)),
                ('Denver', random.randint(2000, 3500), random.uniform(1.2, 1.8))
            ]

        for i, (dest, calls, avg_rate) in enumerate(destinations, 1):
            revenue = int(calls * avg_rate)
            detail_output += f"\n{i}. {dest:<15} {calls:>6,} calls  ${revenue:>5,} revenue  (${avg_rate:.2f} avg)"

        detail_output += f"""

QUALITY INDICATORS
{'=' * 30}
Service Level:            {random.uniform(0.975, 0.995):.1%}
Call Completion Rate:     {random.uniform(0.970, 0.990):.1%}
Customer Satisfaction:    {random.uniform(4.0, 4.6):.1f}/5.0 rating
Technical Quality:        {'Excellent' if random.random() > 0.3 else 'Good'}

NETWORK UTILIZATION
{'=' * 30}
Trunk Utilization:        {random.randint(65, 85)}% average
Peak Period Load:         {random.randint(85, 95)}%
Overflow Events:          {random.randint(0, 3)} (last 24 hours)
Backup Route Usage:       {random.randint(2, 8)}% of traffic

Use 'trunk detail <TG-xxx>' for specific trunk group analysis"""

        return detail_output

    def _generate_traffic_forecast(self) -> str:
        """Generate traffic forecasting analysis."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        forecast_output = f"""Traffic Forecasting Analysis
Generated: {current_time}

IMMEDIATE FORECAST (Next 4 Hours)
{'=' * 45}"""

        current_hour = self.clock.now().hour
        base_calls = sum(data['calls'] for data in self.regional_traffic.values())

        for i in range(4):
            forecast_hour = (current_hour + i + 1) % 24

            # Apply realistic hourly patterns
            if 8 <= forecast_hour <= 10:
                multiplier = random.uniform(1.15, 1.35)
                period_desc = "Morning Peak"
            elif 14 <= forecast_hour <= 16:
                multiplier = random.uniform(1.25, 1.45)
                period_desc = "Afternoon Peak"
            elif 19 <= forecast_hour <= 21:
                multiplier = random.uniform(0.95, 1.15)
                period_desc = "Evening Social"
            elif 22 <= forecast_hour or forecast_hour <= 6:
                multiplier = random.uniform(0.35, 0.55)
                period_desc = "Overnight"
            else:
                multiplier = random.uniform(0.85, 1.05)
                period_desc = "Regular Business"

            forecast_calls = int(base_calls * multiplier)
            capacity_pct = min(100, int(multiplier * 70))

            forecast_output += f"\n{forecast_hour:02d}:00-{(forecast_hour+1)%24:02d}:00  {forecast_calls:>7,} calls  {capacity_pct:>3}% capacity  {period_desc}"

        forecast_output += f"""

WEEKLY TRENDS ANALYSIS
{'=' * 45}
Monday-Thursday:          Heavy business traffic pattern
Friday:                   Moderate business, increasing personal calls
Saturday:                 Light traffic, family-oriented calls
Sunday:                   Moderate traffic with evening peak

SPECIAL CONSIDERATIONS
{'=' * 45}"""

        # Generate realistic special events
        special_events = []
        if self.clock.now().month == 12:
            special_events.append("Holiday season: +15-20% expected volume")
        if self.clock.now().weekday() == 4:  # Friday
            special_events.append("Weekend effect: +10% Friday evening traffic")
        if random.random() < 0.3:
            special_events.append("Weather system may affect rural areas")
        if random.random() < 0.2:
            special_events.append("Major sporting event: +25% regional traffic expected")

        if special_events:
            for event in special_events:
                forecast_output += f"\n• {event}"
        else:
            forecast_output += "\n• No special events expected"

        forecast_output += f"""

CAPACITY RECOMMENDATIONS
{'=' * 45}
High-Traffic Routes:      Enable overflow routing during peaks
Operator Staffing:        Pre-position additional operators for peak periods
Trunk Monitoring:         Monitor utilization closely on major routes
Load Balancing:           Activate dynamic routing algorithms

GROWTH PROJECTIONS
{'=' * 45}
Next Month:               {random.uniform(3, 7):+.1f}% call volume increase
Quarter Forecast:         {random.uniform(8, 15):+.1f}% growth expected
Annual Growth Rate:       {random.uniform(12, 18):+.1f}% projected

Revenue Impact:           ${random.randint(25000, 45000):,} additional daily revenue
Infrastructure Needs:     {random.randint(2, 4)} new trunk groups by Q2 1984"""

        return forecast_output

    def _show_route_performance(self) -> str:
        """Show route-specific performance analysis."""
        import random

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        route_output = f"""Route Performance Analysis
Updated: {current_time}

MAJOR ROUTE PERFORMANCE
{'=' * 35}"""

        # Define major Bell System routes with realistic performance
        major_routes = [
            ('NYC-WAS', 'Northeast Corridor', random.randint(15000, 25000), random.uniform(0.975, 0.995)),
            ('NYC-BOS', 'New England Route', random.randint(12000, 18000), random.uniform(0.980, 0.998)),
            ('CHI-NYC', 'Central-East Route', random.randint(18000, 28000), random.uniform(0.970, 0.990)),
            ('LAX-SFO', 'California Corridor', random.randint(8000, 15000), random.uniform(0.985, 0.995)),
            ('WAS-ATL', 'Southeast Route', random.randint(10000, 16000), random.uniform(0.975, 0.992)),
            ('CHI-LAX', 'Transcontinental', random.randint(14000, 22000), random.uniform(0.965, 0.985))
        ]

        for route, description, calls_hour, completion in major_routes:
            setup_time = random.uniform(1.5, 2.8)
            revenue_rate = random.randint(25, 45)
            status = "EXCELLENT" if completion > 0.99 else "GOOD" if completion > 0.98 else "FAIR"

            route_output += f"""
{route} ({description})
  Calls/Hour:     {calls_hour:,}
  Completion:     {completion:.1%}
  Setup Time:     {setup_time:.1f} seconds
  Revenue/Hour:   ${calls_hour * revenue_rate // 1000:,}
  Status:         {status}"""

        route_output += f"""

ROUTE QUALITY METRICS
{'=' * 35}
Signal Quality:           {random.uniform(0.92, 0.98):.1%} acceptable or better
Echo Control:             {random.uniform(0.88, 0.96):.1%} within standards
Noise Level:              {random.uniform(0.90, 0.97):.1%} below threshold
Transmission Delay:       {random.uniform(0.85, 0.95):.1%} within limits

ALTERNATE ROUTING STATUS
{'=' * 35}"""

        # Show overflow and alternate routing
        alt_routes = [
            ('NYC-WAS via Philadelphia', random.randint(0, 15)),
            ('CHI-NYC via Cleveland', random.randint(0, 25)),
            ('LAX-SFO via Sacramento', random.randint(0, 8))
        ]

        for alt_route, usage_pct in alt_routes:
            status = "ACTIVE" if usage_pct > 5 else "STANDBY"
            route_output += f"\n{alt_route:<25} {usage_pct:>3}% usage  {status}"

        route_output += f"""

TRAFFIC ENGINEERING NOTES
{'=' * 35}
• Dynamic routing algorithms active on all major routes
• Load balancing optimization in progress
• Capacity planning review scheduled for next quarter
• New routing patterns being tested on select routes

Use 'trunk detail <TG-xxx>' for specific trunk group analysis"""

        return route_output

    def _show_peak_analysis(self) -> str:
        """Show peak period traffic analysis."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        peak_output = f"""Peak Period Traffic Analysis
Generated: {current_time}

TODAY'S PEAK ANALYSIS
{'=' * 30}"""

        # Generate realistic peak periods
        morning_peak = {
            'time': f"{random.randint(8, 10)}:{random.randint(15, 45):02d}",
            'calls': random.randint(45000, 65000),
            'duration': random.randint(45, 90),
            'completion': random.uniform(0.970, 0.990)
        }

        afternoon_peak = {
            'time': f"{random.randint(14, 16)}:{random.randint(0, 45):02d}",
            'calls': random.randint(55000, 75000),
            'duration': random.randint(60, 120),
            'completion': random.uniform(0.965, 0.985)
        }

        peak_output += f"""
Morning Peak:
  Time:           {morning_peak['time']} EST
  Call Volume:    {morning_peak['calls']:,} calls/hour
  Duration:       {morning_peak['duration']} minutes
  Completion:     {morning_peak['completion']:.1%}

Afternoon Peak:
  Time:           {afternoon_peak['time']} EST
  Call Volume:    {afternoon_peak['calls']:,} calls/hour
  Duration:       {afternoon_peak['duration']} minutes
  Completion:     {afternoon_peak['completion']:.1%}

PEAK HOUR CAPACITY ANALYSIS
{'=' * 30}
Network Capacity:         {random.randint(75000, 85000):,} calls/hour maximum
Current Peak Load:        {max(morning_peak['calls'], afternoon_peak['calls']):,} calls/hour
Capacity Utilization:     {(max(morning_peak['calls'], afternoon_peak['calls']) / 80000) * 100:.1f}%
Safety Margin:            {((80000 - max(morning_peak['calls'], afternoon_peak['calls'])) / 80000) * 100:.1f}%

HISTORICAL PEAK TRENDS
{'=' * 30}"""

        # Generate weekly peak trend data
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days:
            peak_calls = random.randint(40000, 70000)
            peak_time = f"{random.randint(14, 16)}:{random.randint(0, 59):02d}"
            trend = random.choice(['+', '+', '-']) + f"{random.uniform(0.5, 5.0):.1f}%"

            peak_output += f"\n{day:<10} {peak_calls:>6,} calls at {peak_time}  ({trend} vs last week)"

        peak_output += f"""

PEAK PERIOD CHALLENGES
{'=' * 30}
Trunk Utilization:        {random.randint(85, 95)}% on major routes during peaks
Operator Wait Times:      {random.uniform(8, 15):.1f} seconds average
System Response:          {random.uniform(2.1, 3.2):.1f} seconds call setup
Overflow Events:          {random.randint(3, 12)} occurrences today

CAPACITY MANAGEMENT
{'=' * 30}
• Dynamic routing activated during peak periods
• Additional operators scheduled for busy hours
• Overflow trunks available on all major routes
• Real-time load monitoring and adjustment active

RECOMMENDATIONS
{'=' * 30}
• Monitor trunk utilization closely during peaks
• Consider capacity expansion for routes exceeding 90%
• Optimize routing algorithms for better load distribution
• Schedule maintenance during off-peak hours only"""

        return peak_output

    def _show_traffic_quality_metrics(self) -> str:
        """Show traffic quality metrics and trending."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        quality_output = f"""Traffic Quality Metrics and Trending
Report Generated: {current_time}

CURRENT QUALITY INDICATORS
{'=' * 40}
Call Completion Rate:     {self.traffic_data['completion_rate']:.2%}
Post-Dial Delay:          {self.network_metrics['setup_time']:.1f} seconds average
Network Blocking:         {self.network_metrics['blocking_rate']:.3f} probability
Signal Quality Index:     {random.uniform(0.92, 0.98):.1%}
Customer Satisfaction:    {random.uniform(4.1, 4.7):.1f}/5.0 rating

QUALITY TREND ANALYSIS (30 Days)
{'=' * 40}"""

        # Generate 30-day quality trends
        metrics = [
            ('Completion Rate', 0.980, '%'),
            ('Setup Time', 2.1, 'sec'),
            ('Blocking Rate', 0.005, ''),
            ('Signal Quality', 0.95, '%'),
            ('Satisfaction', 4.3, '/5.0')
        ]

        for metric_name, baseline, unit in metrics:
            trend_direction = random.choice(['↑', '↑', '↓', '→'])  # Bias toward improvement
            if trend_direction == '↑':
                change = f"+{random.uniform(0.1, 2.5):.1f}"
            elif trend_direction == '↓':
                change = f"-{random.uniform(0.1, 1.5):.1f}"
            else:
                change = "0.0"

            current_value = baseline * random.uniform(0.98, 1.02)
            if unit == '%':
                quality_output += f"\n{metric_name:<18} {current_value:.1%} ({trend_direction} {change}{unit})"
            elif unit == 'sec':
                quality_output += f"\n{metric_name:<18} {current_value:.1f}{unit} ({trend_direction} {change}{unit})"
            elif unit == '/5.0':
                quality_output += f"\n{metric_name:<18} {current_value:.1f}{unit} ({trend_direction} {change})"
            else:
                quality_output += f"\n{metric_name:<18} {current_value:.3f} ({trend_direction} {change})"

        quality_output += f"""

QUALITY BY ROUTE TYPE
{'=' * 40}
Local Calls:              {random.uniform(0.985, 0.995):.1%} completion
Long Distance:            {random.uniform(0.975, 0.990):.1%} completion
International:            {random.uniform(0.960, 0.980):.1%} completion
Operator Assisted:        {random.uniform(0.970, 0.985):.1%} completion

TECHNICAL QUALITY METRICS
{'=' * 40}
Transmission Quality:     {random.uniform(0.88, 0.96):.1%} excellent/good
Echo Control:             {random.uniform(0.85, 0.94):.1%} within standards
Noise Level:              {random.uniform(0.90, 0.97):.1%} below threshold
Cross-Talk:               {random.uniform(0.95, 0.99):.1%} within limits
Frequency Response:       {random.uniform(0.92, 0.98):.1%} acceptable

CUSTOMER EXPERIENCE
{'=' * 40}
Average Hold Time:        {self.traffic_data['avg_duration']:.1f} minutes
Dial Tone Delay:          {random.uniform(0.2, 0.8):.1f} seconds
Wrong Number Rate:        {random.uniform(0.008, 0.025):.3f}
Dropped Call Rate:        {random.uniform(0.002, 0.012):.3f}
Service Difficulty:       {random.uniform(0.005, 0.020):.3f}

QUALITY IMPROVEMENT INITIATIVES
{'=' * 40}
• Digital switching deployment increasing completion rates
• Echo canceller installation on long-haul routes
• Improved operator training reducing handle times
• Network optimization reducing post-dial delay
• Customer feedback system implementation

TARGET PERFORMANCE STANDARDS
{'=' * 40}
Completion Rate Target:   98.5% or better
Setup Time Target:        Under 2.0 seconds
Blocking Target:          Less than 0.01 probability
Quality Index Target:     95% excellent/good ratings
Satisfaction Target:      4.5/5.0 or better

Next Quality Review: {(self.clock.now() + timedelta(days=7)).strftime('%B %d, %Y')}"""

        return quality_output

    def cmd_billing(self, args: List[str]) -> str:
        """Customer billing and toll charge calculation"""
        return """Bell System Billing Operations
Customer billing and toll charge management

Current Operations:
  Daily Processing:     147,892 call records
  Billing Accuracy:     99.97%
  Collection Rate:      98.2%

Rate Structures:
  Interstate Day:       $0.45 first minute
  Interstate Evening:   $0.32 first minute
  International:        Varies by destination

Use 'billing rates' for current tariff information"""

    def cmd_uucp(self, args: List[str]) -> str:
        """UUCP network mail and file transfer"""
        return """UNIX-to-UNIX Copy Protocol (UUCP)
Network mail and file transfer operations

Current Status:
  Queue Status:         47 files pending transfer
  Active Connections:   3 of 8 possible
  Transfer Rate:        Normal operation

Network Links:
  bell-labs:           ACTIVE
  research:            ACTIVE
  btl:                 STANDBY

Use 'uucp status' for detailed queue information"""

    def cmd_tsps(self, args: List[str]) -> str:
        """Enhanced Traffic Service Position System with realistic operator management."""

        # Update TSPS state for realistic operational behavior
        self._update_tsps_state()

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            return f"""Traffic Service Position System (TSPS)
Operator Services and Assisted Calling
{current_time}

CURRENT OPERATIONS STATUS
{'=' * 35}
Active Positions:         {self.tsps_data['active_positions']} of {self.tsps_data['total_positions']} staffed
Position Occupancy:       {self.tsps_data['occupancy']:.1f}% ({self._get_tsps_period()})
Queue Length:             {self.tsps_data['queue_length']} calls waiting
Average Work Time:        {self.tsps_data['avg_work_time']:.1f} seconds per call
Answer Time:              {self.tsps_data['answer_time']:.1f} seconds average

OPERATOR FUNCTIONS THIS TOUR
{'=' * 45}
Coin, initial period and overtime:  {self.tsps_data['coin']:>6,} calls
Calling card:                       {self.tsps_data['calling_card']:>6,} calls
Collect:                            {self.tsps_data['collect_calls']:>6,} calls
Bill to third number:               {self.tsps_data['third_number']:>6,} calls
Person to person:                   {self.tsps_data['person_to_person']:>6,} calls
Operator assistance (0-):           {self.tsps_data['assistance']:>6,} calls
Operator number identification:     {self.tsps_data['oni']:>6,} calls
Hotel and motel guest:              {self.tsps_data['hotel_motel']:>6,} calls
International assistance:           {self.tsps_data['international']:>6,} calls
Busy line verification:             {self.tsps_data['verification']:>6,} calls

Directory assistance is not a position function here. It is served by a
separate operator force on 411 and NPA-555-1212, concentrated on an
automatic call distributor.

SERVICE MEASUREMENTS
{'=' * 45}
Speed of answer:          {self.tsps_data['answer_time']:.1f} seconds (objective 2 to 6)
Average work time:        {self.tsps_data['avg_work_time']:.1f} seconds per request
Positions manned:         {self.tsps_data['active_positions']} of {self.tsps_data['total_positions']}
Force requirement:        {self.tsps_data['force_requirement']} positions (Erlang C, next quarter hour)
Force adjustment:         {self.tsps_data['force_adjustment']}
System availability:      {self.tsps_data['system_availability']:.1%}

Commands:
  tsps position <id>      Individual position status
  tsps operators          Operator staffing and performance
  tsps training           Training programs and certification
  tsps queue              Call queue management
  tsps reports            Performance and productivity reports"""

        elif args[0] == "position" and len(args) > 1:
            position_id = args[1]
            return self._show_tsps_position_detail(position_id)

        elif args[0] == "operators":
            return self._show_tsps_operator_status()

        elif args[0] == "training":
            return self._show_tsps_training_programs()

        elif args[0] == "queue":
            return self._show_tsps_queue_management()

        elif args[0] == "reports":
            if len(args) > 1:
                return self._generate_tsps_report(args[1])
            else:
                return self._show_available_tsps_reports()

        else:
            available_commands = ["position", "operators", "training", "queue", "reports"]
            return f"tsps: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"

    def _update_tsps_state(self) -> None:
        """Update TSPS operational state with realistic patterns."""
        import random

        if not hasattr(self, 'tsps_data'):
            # Initialize TSPS operational data
            hour = self.clock.now().hour

            # Adjust staffing and load based on time of day
            if 8 <= hour <= 17:  # Business hours
                base_positions = random.randint(45, 52)
                base_occupancy = random.uniform(75, 90)
            elif 17 <= hour <= 22:  # Evening
                base_positions = random.randint(25, 35)
                base_occupancy = random.uniform(60, 80)
            else:  # Overnight
                base_positions = random.randint(8, 15)
                base_occupancy = random.uniform(40, 65)

            self.tsps_data: TspsData = {
                'total_positions': 52,
                'active_positions': base_positions,
                'occupancy': base_occupancy,
                'queue_length': random.randint(0, 25),
                'avg_work_time': random.uniform(20, 45),
                'answer_time': random.uniform(2.5, 8.0),
                'coin': random.randint(900, 2200),
                'calling_card': random.randint(400, 1100),
                'collect_calls': random.randint(350, 900),
                'third_number': random.randint(120, 400),
                'person_to_person': random.randint(90, 320),
                'assistance': random.randint(200, 700),
                'oni': random.randint(150, 500),
                'hotel_motel': random.randint(40, 180),
                'international': random.randint(20, 110),
                'verification': random.randint(10, 70),
                'force_requirement': base_positions + random.randint(-2, 3),
                'force_adjustment': random.choice([
                    'Within objective',
                    'Calling out additional operators',
                    'Releasing operators to clerical work',
                    'Rescheduling lunches and reliefs',
                ]),
                'service_quality': random.uniform(0.95, 0.99),
                'productivity_rating': random.choice(['Excellent', 'Above Average', 'Average']),
                'system_availability': random.uniform(0.995, 0.999),
                'last_update': self.clock.now()
            }
        else:
            # Update existing data with small variations
            time_since_update = (self.clock.now() - self.tsps_data['last_update']).total_seconds() / 60
            if time_since_update > 2:  # Update every 2 minutes
                self.tsps_data['queue_length'] = max(0, self.tsps_data['queue_length'] + random.randint(-3, 5))
                self.tsps_data['answer_time'] = max(1.0, self.tsps_data['answer_time'] + random.uniform(-0.5, 0.8))
                self.tsps_data['last_update'] = self.clock.now()

    def _get_tsps_period(self) -> str:
        """Get current TSPS period description."""
        hour = self.clock.now().hour
        if 8 <= hour <= 17:
            return "busy hour"
        elif 17 <= hour <= 22:
            return "evening shift"
        else:
            return "night shift"

    def _show_tsps_position_detail(self, position_id: str) -> str:
        """Show detailed status for a specific TSPS position."""
        import random

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Generate realistic operator data
        operators = [
            {"name": "Susan Johnson", "id": "4472", "experience": "3.5 years", "level": "Advanced"},
            {"name": "Mary Williams", "id": "4481", "experience": "2.8 years", "level": "Intermediate"},
            {"name": "Barbara Davis", "id": "4495", "experience": "5.2 years", "level": "Senior"},
            {"name": "Patricia Miller", "id": "4503", "experience": "1.9 years", "level": "Basic"},
            {"name": "Linda Wilson", "id": "4517", "experience": "4.1 years", "level": "Advanced"}
        ]

        operator = random.choice(operators)
        shift_hours = self._get_shift_hours()

        position_output = f"""TSPS Position Status - {position_id}
Query Time: {current_time}

OPERATOR INFORMATION
{'=' * 30}
Operator ID:              {operator['id']}
Name:                     {operator['name']}
Shift:                    {shift_hours}
Experience Level:         {operator['experience']}
Certification:            {operator['level']} Level Certified
Union Local:              Communications Workers Local 1101

CURRENT ACTIVITY
{'=' * 30}
Status:                   {'ACTIVE' if random.random() > 0.1 else 'ON BREAK'}"""

        if random.random() > 0.1:  # Active status
            call_types = ['Person-to-Person NYC to BOS', 'Collect call to Chicago', 'Directory assistance request',
                         'Conference call setup', 'International call to London', 'Billing inquiry']
            current_call = random.choice(call_types)
            position_output += f"""
Call in Progress:         {current_call}
Call Duration:            {random.randint(15, 180)} seconds
Queue Position:           Handling priority call
Customer Location:        {random.choice(['Manhattan, NY', 'Boston, MA', 'Philadelphia, PA', 'Washington, DC'])}

PERFORMANCE TODAY
{'=' * 30}
Calls Handled:            {random.randint(85, 145)}
Average Handle Time:      {random.uniform(25, 40):.1f} seconds
Customer Rating:          {random.uniform(4.5, 5.0):.1f}/5.0
Resolution Rate:          {random.uniform(0.92, 0.98):.1%}
Escalations:              {random.randint(0, 3)}
Break Time Used:          {random.randint(12, 18)} minutes

EQUIPMENT STATUS
{'=' * 30}
Headset:                  OPERATIONAL
Position Terminal:        ONLINE
Conference Bridge:        AVAILABLE
Recording System:         ACTIVE
Billing Interface:        CONNECTED
Directory Database:       ACCESSIBLE

SUPERVISOR NOTES
{'=' * 30}"""

            notes = [
                "Excellent performance maintaining service standards",
                "Assisting with new operator training today",
                "Recommended for advanced certification program",
                "Consistently exceeds productivity targets",
                "Strong customer service skills demonstrated"
            ]
            position_output += f"• {random.choice(notes)}"

        else:  # On break
            position_output += f"""
Break Type:               {random.choice(['Scheduled 15-minute', 'Lunch break', 'Relief break'])}
Return Time:              {(self.clock.now() + timedelta(minutes=random.randint(5, 30))).strftime('%H:%M')}
Coverage:                 Position covered by relief operator"""

        return position_output

    def _show_tsps_operator_status(self) -> str:
        """Show comprehensive operator staffing and performance status."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        operators_output = f"""TSPS Operator Staffing and Performance
Report Generated: {current_time}

STAFFING STATUS
{'=' * 25}
Total Positions:          {self.tsps_data['total_positions']}
Currently Staffed:        {self.tsps_data['active_positions']}
On Duty:                  {self.tsps_data['active_positions'] - random.randint(0, 3)}
On Break:                 {random.randint(0, 3)}
Relief Operators:         {random.randint(2, 5)}
Supervisors:              {random.randint(3, 5)}

SHIFT DISTRIBUTION
{'=' * 25}"""

        # Generate realistic shift data
        shifts = [
            ("Day Shift (08:00-16:00)", random.randint(18, 25)),
            ("Evening Shift (16:00-24:00)", random.randint(12, 18)),
            ("Night Shift (24:00-08:00)", random.randint(6, 12))
        ]

        for shift_name, operators in shifts:
            operators_output += f"\n{shift_name:<25} {operators} operators"

        operators_output += f"""

CERTIFICATION LEVELS
{'=' * 25}
Basic Level:              {random.randint(8, 15)} operators
Intermediate Level:       {random.randint(15, 22)} operators
Advanced Level:           {random.randint(12, 18)} operators
Senior Level:             {random.randint(6, 10)} operators
Supervisor Track:         {random.randint(3, 6)} operators

PERFORMANCE METRICS
{'=' * 25}
Average Experience:       {random.uniform(2.8, 4.2):.1f} years
Productivity Rating:      {random.uniform(0.92, 0.98):.1%} of standard
Quality Score:            {random.uniform(4.3, 4.8):.1f}/5.0 average
Attendance Rate:          {random.uniform(0.94, 0.98):.1%}
Turnover Rate:            {random.uniform(0.08, 0.15):.1%} annually

TOP PERFORMERS (This Month)
{'=' * 25}"""

        top_performers = [
            ("Barbara Davis", "4495", random.uniform(4.8, 5.0), random.randint(125, 145)),
            ("Susan Johnson", "4472", random.uniform(4.7, 4.9), random.randint(120, 140)),
            ("Linda Wilson", "4517", random.uniform(4.6, 4.8), random.randint(115, 135))
        ]

        for name, op_id, rating, calls in top_performers:
            operators_output += f"\n{name:<18} ({op_id})  {rating:.1f}/5.0  {calls} avg calls/day"

        operators_output += f"""

TRAINING AND DEVELOPMENT
{'=' * 25}
New Hires in Training:    {random.randint(2, 6)}
Certification Testing:    {random.randint(4, 8)} operators scheduled
Skills Development:       {random.randint(8, 15)} enrolled in programs
Cross-Training:           {random.randint(5, 12)} operators

SCHEDULING NOTES
{'=' * 25}
Peak Coverage:            14:00-16:00 EST (all positions staffed)
Minimum Staffing:         02:00-06:00 EST ({random.randint(6, 10)} positions)
Holiday Schedule:         Modified staffing for upcoming holidays
Overtime Authorized:      Up to {random.randint(8, 15)} hours per week"""

        return operators_output

    def _show_tsps_training_programs(self) -> str:
        """Show TSPS training programs and certification status."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        training_output = f"""TSPS Training Program Status
Report Generated: {current_time}

ACTIVE TRAINING SESSIONS
{'=' * 35}"""

        training_sessions = [
            ("New Operator Orientation", random.randint(3, 6), "Week 1-2", "Basic"),
            ("Advanced Call Handling", random.randint(4, 8), "Ongoing", "Advanced"),
            ("International Procedures", random.randint(6, 12), "2 weeks", "Intermediate"),
            ("Emergency Protocol Review", random.randint(8, 15), "1 week", "All Levels"),
            ("Customer Service Excellence", random.randint(5, 10), "3 weeks", "Intermediate"),
            ("Technology Update Session", random.randint(10, 18), "1 day", "All Levels")
        ]

        for session, participants, duration, level in training_sessions:
            training_output += f"\n{session:<25} {participants:>2} trainees  {duration:<8} {level}"

        training_output += f"""

CERTIFICATION PROGRAM
{'=' * 35}
Certification Levels:     4 levels (Basic through Senior)
Current Testing Cycle:    {random.choice(['Week 2', 'Week 3', 'Week 4'])} of monthly cycle
Pass Rate:                {random.uniform(0.85, 0.95):.1%} overall
Next Exam Date:           {(self.clock.now() + timedelta(days=random.randint(7, 21))).strftime('%B %d, %Y')}

CERTIFICATION STATUS
{'=' * 35}
Eligible for Testing:     {random.randint(8, 15)} operators
Pending Results:          {random.randint(2, 6)} operators
Recent Certifications:    {random.randint(3, 8)} operators (last 30 days)
Certification Renewals:   {random.randint(5, 12)} operators (next 90 days)

TRAINING EFFECTIVENESS
{'=' * 35}
Post-Training Performance: {random.uniform(15, 25):+.0f}% improvement average
Customer Satisfaction:     {random.uniform(0.3, 0.6):+.1f} point increase
Error Reduction:          {random.uniform(20, 35):.0f}% decrease
Handle Time Improvement:   {random.uniform(8, 18):.0f}% faster
Confidence Rating:         {random.uniform(20, 35):+.0f}% increase

SPECIALIZED TRAINING
{'=' * 35}
Emergency Services:       All operators certified
International Calls:     {random.randint(25, 35)} operators certified
Conference Setup:         {random.randint(20, 30)} operators certified
Billing Systems:          {random.randint(15, 25)} operators certified
Directory Assistance:     All operators certified

UPCOMING TRAINING
{'=' * 35}"""

        upcoming_training = [
            ("New Technology Integration", f"{(self.clock.now() + timedelta(days=random.randint(7, 14))).strftime('%B %d')}"),
            ("Customer Relations Workshop", f"{(self.clock.now() + timedelta(days=random.randint(14, 28))).strftime('%B %d')}"),
            ("Quality Assurance Methods", f"{(self.clock.now() + timedelta(days=random.randint(21, 35))).strftime('%B %d')}"),
            ("Regulatory Compliance Update", f"{(self.clock.now() + timedelta(days=random.randint(28, 42))).strftime('%B %d')}")
        ]

        for training, date in upcoming_training:
            training_output += f"\n{training:<30} {date}"

        training_output += f"""

TRAINING RESOURCES
{'=' * 35}
Training Manuals:         Current (Version 3.2)
Practice Simulators:      {random.randint(8, 12)} systems available
Instructor Staff:         {random.randint(4, 7)} certified trainers
Training Facilities:      2 dedicated training centers

Contact: Training Coordinator ext 4225"""

        return training_output

    def _show_tsps_queue_management(self) -> str:
        """Show TSPS call queue management and statistics."""

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        queue_output = f"""TSPS Call Queue Management
Real-Time Status: {current_time}

CURRENT QUEUE STATUS
{'=' * 30}
Calls in Queue:           {self.tsps_data['queue_length']}
Average Wait Time:        {self.tsps_data['answer_time']:.1f} seconds
Longest Wait:             {max(int(self.tsps_data['answer_time'] * 2), random.randint(45, 180))} seconds
Queue Growth Rate:        {random.choice(['+', '-'])}{random.randint(1, 8)} calls/minute

QUEUE BY SERVICE TYPE
{'=' * 30}"""

        queue_breakdown = [
            ("Person-to-Person", int(self.tsps_data['queue_length'] * 0.25), "HIGH"),
            ("Collect Calls", int(self.tsps_data['queue_length'] * 0.35), "NORMAL"),
            ("Directory Assistance", int(self.tsps_data['queue_length'] * 0.30), "NORMAL"),
            ("Conference Setup", int(self.tsps_data['queue_length'] * 0.05), "LOW"),
            ("International", int(self.tsps_data['queue_length'] * 0.05), "LOW")
        ]

        for service, calls, priority in queue_breakdown:
            queue_output += f"\n{service:<20} {calls:>2} calls  {priority} priority"

        queue_output += f"""

QUEUE PERFORMANCE (Last Hour)
{'=' * 30}
Calls Answered:           {random.randint(280, 450)}
Average Handle Time:      {self.tsps_data['avg_work_time']:.1f} seconds
Service Level:            {random.uniform(0.92, 0.98):.1%} (answered <20 sec)
Abandonment Rate:         {random.uniform(0.02, 0.08):.1%}
Peak Queue Length:        {random.randint(15, 35)} calls

TRAFFIC PATTERNS
{'=' * 30}"""

        # Generate hourly queue patterns
        for hour_offset in range(-3, 1):
            pattern_hour = (self.clock.now().hour + hour_offset) % 24
            if 8 <= pattern_hour <= 17:
                queue_size = random.randint(15, 35)
                pattern = "Business Peak"
            elif 17 <= pattern_hour <= 22:
                queue_size = random.randint(8, 20)
                pattern = "Evening Traffic"
            else:
                queue_size = random.randint(2, 8)
                pattern = "Overnight"

            time_str = f"{pattern_hour:02d}:00"
            queue_output += f"\n{time_str}  {queue_size:>2} calls avg  {pattern}"

        queue_output += f"""

OPERATOR AVAILABILITY
{'=' * 30}
Available Operators:      {self.tsps_data['active_positions'] - random.randint(1, 3)}
Busy Operators:           {random.randint(1, 3)}
On Break:                 {random.randint(0, 2)}
In Training:              {random.randint(0, 1)}

QUEUE MANAGEMENT ALERTS
{'=' * 30}"""

        alerts = []
        if self.tsps_data['queue_length'] > 20:
            alerts.append("⚠ WARNING: Queue length exceeds normal range")
        if self.tsps_data['answer_time'] > 15:
            alerts.append("⚠ NOTICE: Answer time above target")
        if random.random() < 0.3:
            alerts.append("ℹ INFO: Peak traffic period - additional operators requested")

        if alerts:
            for alert in alerts:
                queue_output += f"\n{alert}"
        else:
            queue_output += "\n✓ All queue metrics within normal range"

        queue_output += f"""

RECOMMENDED ACTIONS
{'=' * 30}
• Monitor queue length closely during peak hours
• Request overflow assistance if queue exceeds 25 calls
• Implement call-back service for extended wait times
• Track abandonment rate and adjust staffing accordingly"""

        return queue_output

    def _get_shift_hours(self) -> str:
        """Get current shift description."""
        hour = self.clock.now().hour
        if 8 <= hour < 16:
            return "Day Shift (08:00-16:00)"
        elif 16 <= hour < 24:
            return "Evening Shift (16:00-24:00)"
        else:
            return "Night Shift (24:00-08:00)"

    def _show_available_tsps_reports(self) -> str:
        """Show available TSPS reporting options."""
        return """Available TSPS Reports:

  tsps reports daily        Daily performance summary
  tsps reports weekly       Weekly productivity analysis
  tsps reports monthly      Monthly operational report
  tsps reports operators    Individual operator performance
  tsps reports quality      Service quality metrics
  tsps reports training     Training effectiveness report

Use 'tsps reports <type>' to generate specific report"""

    def _generate_tsps_report(self, report_type: str) -> str:
        """Generate specific TSPS performance report."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        if report_type == "daily":
            return f"""TSPS Daily Performance Report
Generated: {current_time}

DAILY SUMMARY
{'=' * 20}
Calls Handled:            {random.randint(2800, 4200):,}
Average Handle Time:      {random.uniform(25, 40):.1f} seconds
Service Level:            {random.uniform(0.92, 0.98):.1%}
Customer Satisfaction:    {random.uniform(4.2, 4.8):.1f}/5.0
Operator Utilization:     {random.uniform(0.75, 0.90):.1%}

Peak traffic occurred at {random.randint(14, 16)}:{random.randint(0, 59):02d} with {random.randint(45, 65)} calls in queue."""

        elif report_type == "weekly":
            return f"""TSPS Weekly Productivity Analysis
Generated: {current_time}

WEEKLY PERFORMANCE TRENDS
{'=' * 30}
Total Calls:              {random.randint(18000, 28000):,}
Average Daily Volume:     {random.randint(2800, 4200):,}
Productivity Increase:    {random.uniform(2, 8):+.1f}% vs last week
Quality Improvement:      {random.uniform(0.1, 0.5):+.1f} points
Training Impact:          {random.uniform(5, 15):.0f}% improvement"""

        else:
            return f"tsps: Report type '{report_type}' not implemented\nUse 'tsps reports' for available options"

    # Implement remaining critical commands with similar patterns
    def cmd_toll(self, args: List[str]) -> str:
        """Toll switching and billing operations"""
        return self._subsystem_unavailable("toll", "Toll switching operations")

    def cmd_trace(self, args: List[str]) -> str:
        """Call tracing and routing analysis"""
        return self._subsystem_unavailable("trace", "Call trace operations")

    def cmd_dialtone(self, args: Optional[List[str]] = None) -> str:
        """Call-progress tone reference and dial tone speed testing."""
        args = args or []

        if not args:
            output = f"""Bell System Call Progress Tones
Precise Tone Plan
{'=' * 78}

TONE                     FREQUENCIES          CADENCE                       LEVEL
{'-' * 78}"""
            for tone in PROGRESS_TONES.values():
                pair = '+'.join(str(hz) for hz in tone.frequencies)
                if tone.cadence is None:
                    timing = 'continuous'
                else:
                    on, off = tone.cadence
                    timing = f'{on:g}s on / {off:g}s off'
                    if tone.interruptions_per_minute:
                        timing += f' {tone.interruptions_per_minute} IPM'
                output += (f"\n{tone.name[:24]:<25}{pair:<21}{timing:<30}"
                           f"{tone.level_dbm:>4g} dBm")

            output += f"""

DIAL TONE SPEED
{'=' * 45}
Objective:                Dial tone within 3 seconds on 98% of attempts
Measured this hour:       {random.uniform(0.15, 1.4):.2f} seconds average
Attempts exceeding 3s:    {random.uniform(0.1, 1.8):.1f}%
Dial tone delay alarms:   {random.randint(0, 2)}

Commands:
  dialtone test <office>    Dial tone speed test on an office
  dialtone tone <name>      Detail for one call progress tone
  dialtone mf <digits>      Show the MF train for a called number

Reference: Precise Tone Plan; BSP 660-100-000"""
            return output

        action = args[0].lower()

        if action == 'tone' and len(args) > 1:
            key = args[1].lower()
            tone = PROGRESS_TONES.get(key)
            if tone is None:
                return (f"dialtone: no tone named '{args[1]}'\n"
                        f"Available: {', '.join(PROGRESS_TONES)}")
            timing = ('continuous' if tone.cadence is None
                      else f'{tone.cadence[0]:g}s on / {tone.cadence[1]:g}s off')
            return f"""{tone.name}
{'=' * 52}
Frequencies:      {' + '.join(f'{hz} Hz' for hz in tone.frequencies)}
Timing:           {timing}
Interruptions:    {tone.interruptions_per_minute or 'not applicable'} per minute
Level:            {tone.level_dbm:g} dBm

{tone.meaning}"""

        if action == 'mf' and len(args) > 1:
            digits = ''.join(c for c in args[1] if c.isdigit())
            if not digits:
                return "dialtone mf: supply the digits to outpulse"
            train = mf_sequence(digits)
            output = f"""Multifrequency Outpulsing
{'=' * 52}
Called number:    {digits}
Signal train:     {' '.join(sig.symbol for sig in train)}
Train duration:   {mf_train_duration_ms(train)} ms

SIGNAL           LOW       HIGH      FUNCTION
{'-' * 52}"""
            for sig in train:
                output += (f"\n{sig.symbol:<16} {sig.low:>4} Hz  {sig.high:>4} Hz  "
                           f"{sig.purpose}")
            return output + f"""

MF frequencies:        {', '.join(f'{hz} Hz' for hz in MF_FREQUENCIES)}
Trunk supervision:     SF {SF_FREQUENCY_HZ} Hz at {SF_IDLE_LEVEL_DBM:g} dBm when idle;
                       removal of tone marks seizure, return marks release."""

        if action == 'test':
            office = args[1].upper() if len(args) > 1 else 'LOCAL'
            samples = [random.uniform(0.12, 2.6) for _ in range(10)]
            over = [s for s in samples if s > 3.0]
            dial = PROGRESS_TONES['dial']
            return f"""Dial Tone Speed Test
{'=' * 52}
Office:           {office}
Test run:         {self.clock.timestamp()}
Samples:          {len(samples)} originating attempts

Average delay:    {sum(samples) / len(samples):.2f} seconds
Longest delay:    {max(samples):.2f} seconds
Exceeding 3s:     {len(over)} of {len(samples)}

Objective:        3 seconds on 98 percent of attempts
Result:           {'MEETS OBJECTIVE' if not over else 'REVIEW REQUIRED'}

Dial tone is {' + '.join(f'{hz} Hz' for hz in dial.frequencies)} at {dial.level_dbm:g} dBm."""

        return (f"dialtone: Unknown option '{args[0]}'\n"
                "Available commands: test, tone, mf")

    def cmd_routing(self, args: Optional[List[str]] = None) -> str:
        """Hierarchical alternate routing analysis and call tracing."""
        args = args or []
        network = self.toll_network

        if not args or args[0] == 'status':
            output = f"""Hierarchical Alternate Routing
{self.clock.timestamp()}
{'=' * 62}

ROUTING RULE
{'=' * 62}
Complete each connection at the lowest level of the hierarchy that can
carry it, using the fewest trunks in tandem. A call is offered first to a
high-usage group; only when every trunk there is busy does it overflow to
a final group up its homing chain.

Final groups are the last route available. When every trunk in one is
busy the call is blocked and the caller receives reorder.

GRADE OF SERVICE
{'=' * 62}
Final trunk groups:       P.01 - one call in 100 finds all trunks busy
High-usage groups:        P.10 - engineered to overflow, which is the
                          purpose of provisioning one
Maximum trunks in tandem: {MAX_TRUNKS_IN_CONNECTION}
Typical toll connection:  3 trunks - up a toll connecting trunk, across
                          one intertoll group, and back down

OFFICES IN THE ROUTING TABLE
{'=' * 62}
CODE          CLASS  OFFICE                          HOMES ON
{'-' * 62}"""
            for office in sorted(network.offices.values(),
                                 key=lambda o: (o.switch_class, o.code)):
                output += (f"\n{office.code:<13} {office.switch_class:<6} "
                           f"{office.name[:30]:<31} {office.homes_on or '-'}")
            return output + """

Commands:
  routing trace <from> <to>   Offer a call and follow it through
  routing chain <office>      Show an office's homing chain
  routing status              This display"""

        if args[0] == 'chain' and len(args) > 1:
            code = args[1].upper()
            if code not in network.offices:
                return f"routing: no office {code} in the routing table"
            output = f"""Homing Chain: {code}
{'=' * 55}

An office joined to a higher class office by a final group is said to
home on it, though not every office homes on the next class up.

"""
            for depth, entry in enumerate(network.homing_chain(code)):
                office = network.offices[entry]
                output += (f"{'  ' * depth}{'+- ' if depth else ''}"
                           f"{office.code} ({office.class_name()}) {office.name}\n")
            return output.rstrip()

        if args[0] == 'trace' and len(args) > 2:
            origin, destination = args[1].upper(), args[2].upper()
            result = network.route(origin, destination)
            output = f"""Route Trace
{self.clock.timestamp()}
{'=' * 62}
Originating office:   {origin}
Terminating office:   {destination}

ROUTE ADVANCE
{'=' * 62}"""
            for step, attempt in enumerate(result.attempts, 1):
                output += f"\n{step}. {attempt}"

            output += f"""

RESULT
{'=' * 62}
Outcome:              {'COMPLETED' if result.completed else 'BLOCKED - REORDER'}
Trunks in tandem:     {result.trunk_count()} of {MAX_TRUNKS_IN_CONNECTION} maximum
{result.reason}"""

            if result.legs:
                output += f"""

CONNECTION
{'=' * 62}
FROM          TO            GROUP TYPE             OCCUPANCY
{'-' * 62}"""
                for leg in result.legs:
                    output += (f"\n{leg.from_office:<13} {leg.to_office:<13} "
                               f"{leg.group_type:<22} {leg.utilization:>3}%"
                               f"{'  ALL TRUNKS BUSY' if leg.blocked else ''}")
            return output

        return (f"routing: Unknown option '{args[0]}'\n"
                "Available commands: status, trace <from> <to>, chain <office>")

    def cmd_capacity(self, args: List[str]) -> str:
        """Network capacity planning and utilization"""
        return self._subsystem_unavailable("capacity", "Capacity planning")

    def cmd_service(self, args: List[str]) -> str:
        """Service order management and provisioning"""
        if not args:
            return f"""Bell System Service Orders - {self.clock.now().strftime("%H:%M:%S EST")}
============================================================

Current Service Queue Status:
  Pending Repairs:           12 tickets
  New Installations:         23 orders
  Service Changes:           8 orders
  Emergency Priority:        3 tickets

Active Repair Tickets:
  EV-8042: Pentagon priority circuit - URGENT
  EV-8039: Hospital emergency line - HIGH
  EV-8041: Police station backup - HIGH

Priority Queue (Government/Emergency):
  Position 1: EV-8042 - Pentagon line outage
  Position 2: EV-8039 - St. Mary's Hospital
  Position 3: EV-8041 - 14th Precinct backup

Commands:
  service repair <ticket>    Process repair ticket
  service install <order>    Installation coordination
  service status <id>        Check order status
  service queue              View full queue"""

        elif len(args) >= 2 and args[0] == "repair":
            ticket = args[1]
            if ticket == "EV-8042":
                return f"""URGENT REPAIR TICKET: EV-8042
Pentagon Priority Circuit Outage
============================================================
Ticket Created: {self.clock.now().strftime("%Y-%m-%d %H:%M:%S EST")}
Priority Level: GOVERNMENT EMERGENCY
Customer: Department of Defense - Pentagon
Circuit ID: T1-PENTAGON-MAIN-01

OUTAGE DETAILS:
  Circuit Type: Dedicated T1 Digital Circuit
  Affected Services: Primary Pentagon communications
  Outage Start: 13:15 EST
  Impact: CRITICAL - Government operations affected

DISPATCH STATUS:
  Field Technician: Team Alpha-7 (Security Cleared)
  ETA Pentagon: 14:30 EST
  Equipment Status: Emergency repair kit loaded
  Access Clearance: DOD Security approved

TECHNICAL ANALYSIS:
  Fault Location: Pentagon Building entrance facility
  Circuit Path: Pentagon -> Arlington CO -> DC-4 Toll
  Test Results: Loss of carrier signal at building demarc
  Probable Cause: Facility cable damage or equipment failure

REPAIR PROGRESS:
  ✓ Emergency dispatch authorized
  ✓ DOD security clearance confirmed
  ✓ Field team en route with emergency equipment
  → Arrival and fault isolation: 14:30 EST
  → Repair completion target: 16:00 EST

ESCALATION CONTACTS:
  Pentagon Comm Center: (703) 545-6700 Priority Line
  Bell System NOC: Emergency Desk ext 911
  DOD Liaison Office: Contact when service restored

Next Update: 15:00 EST or upon status change"""
            else:
                return f"""REPAIR TICKET: {ticket}
============================================================
Ticket Status: {ticket}
Created: {self.clock.now().strftime("%Y-%m-%d %H:%M:%S EST")}

Standard Repair Process:
1. Trouble ticket analysis
2. Field technician dispatch
3. Fault isolation and testing
4. Repair completion
5. Service verification
6. Customer notification

Use 'service repair EV-8042' for Pentagon priority ticket
Use 'service status {ticket}' for detailed ticket information"""

        elif len(args) >= 2 and args[0] == "status":
            order_id = args[1]
            return f"""SERVICE ORDER STATUS: {order_id}
============================================================
Order Number: {order_id}
Status Check: {self.clock.now().strftime("%H:%M:%S EST")}

Order Information:
  Customer Type: Business Service
  Service Address: [Address on file]
  Order Priority: Standard
  Due Date: Within 5 business days

Current Status:
  → Order received and validated
  → Engineering review completed
  → Installation scheduled
  → Equipment allocation confirmed

Progress Tracking:
  Order Processing: COMPLETE
  Equipment Status: AVAILABLE
  Installation Team: ASSIGNED
  Completion Target: On schedule

Contact your service representative for detailed updates."""

        elif args[0] == "queue":
            return f"""COMPLETE SERVICE QUEUE - {self.clock.now().strftime("%H:%M:%S EST")}
============================================================

EMERGENCY REPAIRS (Government/Critical):
  EV-8042: Pentagon circuit outage - ACTIVE REPAIR
  EV-8039: Hospital emergency line - Dispatched
  EV-8041: Police backup circuit - Pending

HIGH PRIORITY REPAIRS:
  TK-4789: Bank data circuit - Testing
  TK-4791: Airport communication - Scheduled 15:30
  TK-4793: Fire department backup - Parts ordered

STANDARD REPAIRS:
  TK-4785: Business line static - Scheduled tomorrow
  TK-4787: Residential no dial tone - Team assigned
  TK-4788: PBX trunk problem - Customer callback

NEW INSTALLATIONS:
  SO-8847: 50-line business system - Cable survey
  SO-8849: Residential service - Standard install
  SO-8851: Centrex upgrade - Equipment ordered

SERVICE CHANGES:
  SC-2134: Office relocation - Coordination phase
  SC-2136: Line additions - Installation ready"""

        else:
            return """Bell System Service Management
============================================================
Available Commands:

  service repair <ticket>    Handle repair tickets
  service status <order>     Check order status
  service queue              View complete queue
  service install <order>    Installation coordination

Current Active Issues:
  EV-8042: Pentagon priority circuit - NEEDS IMMEDIATE ATTENTION

For immediate Pentagon repair: service repair EV-8042"""

    def cmd_operator(self, args: List[str]) -> str:
        """Enhanced operator services with realistic assisted calling operations."""

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            return f"""Bell System Operator Services
Assisted Calling and Special Services
{current_time}

CURRENT OPERATIONS STATUS
{'=' * 35}
Active Operators:         {random.randint(25, 45)} (Day Shift)
Call Queue Length:        {random.randint(3, 18)} calls waiting
Average Answer Time:      {random.uniform(3.2, 8.5):.1f} seconds
Service Level:            {random.uniform(0.92, 0.98):.1%} (within 20 seconds)

SERVICE TYPES AVAILABLE
{'=' * 35}
Person-to-Person:         Available
Collect Calls:            Available
Conference Calls:         Available (up to 8 parties)
International:            Available (120+ countries)
Directory Assistance:     Available 24/7
Credit Card Calls:        Available
Time and Weather:         Available

PERFORMANCE METRICS
{'=' * 35}
Calls Completed Today:    {random.randint(2800, 4500):,}
Average Handle Time:      {random.uniform(35, 55):.1f} seconds
Customer Satisfaction:    {random.uniform(4.3, 4.8):.1f}/5.0 rating
First Call Resolution:    {random.uniform(0.88, 0.95):.1%}

Commands:
  operator assist          Request operator assistance
  operator conference      Set up conference call
  operator international   International calling rates
  operator status          Detailed service status"""

        elif args[0] == "assist":
            return self._handle_operator_assistance()

        elif args[0] == "conference":
            return self._setup_conference_call()

        elif args[0] == "international":
            return self._show_international_rates()

        elif args[0] == "status":
            return self._show_operator_detailed_status()

        else:
            available_commands = ["assist", "conference", "international", "status"]
            return f"operator: Unknown option '{args[0]}'\nAvailable commands: {', '.join(available_commands)}"

    def _handle_operator_assistance(self) -> str:
        """Handle operator assistance request."""
        import random

        assistance_types = [
            "Person-to-person call to Chicago",
            "Collect call setup",
            "Conference call arrangement",
            "International call to London",
            "Credit card verification",
            "Directory assistance request"
        ]

        current_request = random.choice(assistance_types)
        wait_time = random.uniform(2.5, 12.0)

        return f"""Operator Assistance Request
{'=' * 30}

Connecting you with the next available operator...

Estimated Wait Time:      {wait_time:.1f} seconds
Queue Position:           {random.randint(1, 8)}
Service Type:             {current_request}

Please hold while we connect your call.
An operator will be with you shortly to assist with your request.

For immediate assistance, dial 0 for the operator, or report to
the Switching Control Center on the emergency order wire."""

    def _setup_conference_call(self) -> str:
        """Set up conference call with realistic procedures."""

        return f"""Bell System Conference Call Setup
{'=' * 40}

Conference Bridge Available: Bridge-{random.randint(1, 12)}
Maximum Participants:        8 parties
Setup Time:                  {random.uniform(2.5, 5.0):.1f} minutes estimated

CONFERENCE PROCEDURES
{'=' * 30}
1. Operator will place calls to each participant
2. Each party will be placed on hold during setup
3. All parties connected simultaneously when ready
4. Conference moderator designated (calling party)
5. Recording available if requested (additional charges apply)

CURRENT RATES
{'=' * 30}
Setup Fee:                   $3.50
Per-Minute Rate:            $0.85 per participant
Overtime Surcharge:         25% after 6:00 PM
Recording Fee:              $8.00 per hour

Estimated Total Cost:       ${random.uniform(15.50, 45.75):.2f} for 30-minute call

To proceed, please provide participant phone numbers when operator connects."""

    def _show_international_rates(self) -> str:
        """Show international calling rates and procedures."""
        import random

        return f"""Bell System International Calling
Rates and Service Information
{'=' * 40}

POPULAR DESTINATIONS (Per Minute)
{'=' * 40}
United Kingdom:              ${random.uniform(1.85, 2.25):.2f}
France:                      ${random.uniform(2.10, 2.45):.2f}
West Germany:                ${random.uniform(1.95, 2.35):.2f}
Japan:                       ${random.uniform(3.25, 3.85):.2f}
Australia:                   ${random.uniform(2.85, 3.25):.2f}
Mexico:                      ${random.uniform(1.25, 1.65):.2f}
Canada:                      ${random.uniform(0.85, 1.15):.2f}

SERVICE OPTIONS
{'=' * 40}
Direct Dial International:   Available to 35+ countries
Operator Assisted:           Available worldwide (120+ countries)
Station-to-Station:          Standard rate
Person-to-Person:           Additional $3.75 charge
Collect Calls:              Accepted by most countries

PEAK/OFF-PEAK RATES
{'=' * 40}
Peak Hours (8 AM - 6 PM):   Standard rates (above)
Off-Peak (6 PM - 8 AM):     25% discount
Weekend (Sat-Sun):          35% discount
Holiday Rates:              Peak rates apply

DIALING PROCEDURES
{'=' * 40}
Direct Dial:                011 + Country Code + Number
Operator Assisted:          0 + Country Code + Number
Emergency International:    Dial 0 for immediate assistance

For current rates to specific countries, dial 0 for operator assistance."""

    def _show_operator_detailed_status(self) -> str:
        """Show detailed operator service status."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        return f"""Detailed Operator Services Status
Report Generated: {current_time}

STAFFING AND CAPACITY
{'=' * 30}
Total Operator Positions:    52
Currently Staffed:          {random.randint(28, 45)}
Available for Calls:        {random.randint(25, 42)}
On Break:                   {random.randint(1, 4)}
In Training:                {random.randint(0, 2)}

CALL VOLUME STATISTICS
{'=' * 30}
Calls Today:                {random.randint(3200, 5800):,}
Average per Hour:           {random.randint(180, 320)}
Peak Hour Volume:           {random.randint(420, 680)} calls
Current Queue Length:       {random.randint(2, 25)} calls

SERVICE QUALITY METRICS
{'=' * 30}
Answer Time Average:        {random.uniform(3.8, 9.2):.1f} seconds
Service Level Target:       85% answered within 20 seconds
Current Service Level:      {random.uniform(0.82, 0.96):.1%}
Customer Satisfaction:      {random.uniform(4.1, 4.7):.1f}/5.0 rating
Call Completion Rate:       {random.uniform(0.94, 0.98):.1%}

SPECIALIZED SERVICES
{'=' * 30}
Conference Calls Setup:     {random.randint(45, 125)} today
International Assistance:   {random.randint(180, 340)} calls
Directory Assistance:       {random.randint(1200, 2100)} requests
Emergency Services:         {random.randint(8, 25)} calls
Credit Verification:        {random.randint(95, 180)} transactions

Next Shift Change: {(self.clock.now() + timedelta(hours=random.randint(2, 6))).strftime('%H:%M EST')}"""

    def cmd_directory(self, args: List[str]) -> str:
        """Enhanced directory assistance with realistic number lookup operations."""
        import random

        if not args:
            return f"""Bell System Directory Assistance
Information Services and Number Lookup
{'=' * 45}

CURRENT SERVICE STATUS
{'=' * 30}
Service:                     Available 24/7
Average Response Time:       {random.uniform(4.5, 8.2):.1f} seconds
Information Accuracy:        {random.uniform(0.96, 0.99):.1%}
Operator Availability:       {random.randint(18, 32)} operators on duty

REQUEST VOLUME TODAY
{'=' * 30}
Directory Requests:          {random.randint(2400, 4200):,}
Business Listings:           {random.randint(1200, 2100):,}
Residential Listings:        {random.randint(1100, 1900):,}
Government Numbers:          {random.randint(95, 180):,}

AVAILABLE SERVICES
{'=' * 30}
Local Directory:             Free within calling area
Long Distance Directory:     $0.50 per request
Business Information:        Free (includes addresses)
Government Listings:         Free
New Listings:               Updated daily
Unlisted Numbers:           Not available

COVERAGE AREAS
{'=' * 30}
Local Exchange:              Complete coverage
Metropolitan Area:           All exchanges covered
Interstate:                  48 states + DC
International:               Major cities only (limited)

To request directory assistance: Dial 411 (local) or 1-Area Code-555-1212 (long distance)"""

        elif args[0] == "lookup" and len(args) > 1:
            return self._perform_directory_lookup(" ".join(args[1:]))

        elif args[0] == "business":
            return self._show_business_directory()

        elif args[0] == "government":
            return self._show_government_directory()

        else:
            available_commands = ["lookup", "business", "government"]
            return f"directory: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"

    def _perform_directory_lookup(self, search_term: str) -> str:
        """Perform a realistic directory lookup simulation."""

        # Generate realistic directory entries
        sample_listings = [
            ("JOHNSON, ROBERT", "212-555-4729", "147 W 42ND ST"),
            ("SMITH, MARY E", "212-555-8361", "89 PARK AVE"),
            ("ACME CORPORATION", "212-555-9000", "250 BROADWAY"),
            ("BROWN, JAMES", "617-555-2847", "BOSTON, MA"),
            ("CITY HALL", "212-555-1000", "MUNICIPAL BLDG"),
            ("WILLIAMS, SUSAN", "212-555-5623", "BROOKLYN, NY")
        ]

        found_listing = random.choice(sample_listings)
        search_time = random.uniform(3.5, 8.5)

        return f"""Directory Assistance Lookup Result
{'=' * 40}

Search Term: "{search_term}"
Search Time: {search_time:.1f} seconds

LISTING FOUND
{'=' * 20}
Name:        {found_listing[0]}
Number:      {found_listing[1]}
Address:     {found_listing[2]}

Status:      CURRENT LISTING
Last Update: {(self.clock.now() - timedelta(days=random.randint(1, 90))).strftime('%B %Y')}

Charges: {'Free (local)' if random.random() > 0.3 else '$0.50 (long distance)'}

Would you like this number connected automatically?
Additional charge: $0.25 for direct connection."""

    def _show_business_directory(self) -> str:
        """Show business directory services."""
        import random

        return f"""Business Directory Services
{'=' * 35}

BUSINESS CATEGORIES
{'=' * 25}
Banking and Finance:         {random.randint(180, 320)} listings
Medical Services:            {random.randint(240, 450)} listings
Legal Services:              {random.randint(95, 180)} listings
Restaurants:                 {random.randint(450, 780)} listings
Retail and Shopping:         {random.randint(680, 1200)} listings
Transportation:              {random.randint(120, 220)} listings
Government Services:         {random.randint(85, 150)} listings

FEATURED BUSINESS LISTINGS
{'=' * 35}
ABC TAXI SERVICE            212-555-TAXI (8294)
CITY HOSPITAL               212-555-9911
FIRST NATIONAL BANK         212-555-2100
GRAND CENTRAL STATION       212-555-4455
MACY'S DEPARTMENT STORE     212-555-6700

YELLOW PAGES INFORMATION
{'=' * 35}
Total Business Listings:    {random.randint(8500, 12000):,}
Updated:                    Monthly
Advertising Available:      Contact 212-555-SELL
Directory Distribution:     Free to all customers

For specific business lookups, dial 411 or use 'directory lookup <business name>'"""

    def _show_government_directory(self) -> str:
        """Show government directory listings."""
        return f"""Government Directory Listings
{'=' * 40}

EMERGENCY SERVICES
{'=' * 25}
Police Emergency:            911
Fire Department:             911
Ambulance/EMS:              911
Poison Control:             212-555-1212

FEDERAL GOVERNMENT
{'=' * 25}
Federal Information:         202-555-1212
Internal Revenue Service:    800-555-1040
Social Security Admin:       800-555-1213
Veterans Administration:     212-555-4400

STATE AND LOCAL
{'=' * 25}
City Hall:                  212-555-1000
Department of Motor Vehicles: 212-555-2020
Public Works:               212-555-3000
Building Department:        212-555-3500
Board of Elections:         212-555-8683

COURTS AND LEGAL
{'=' * 25}
Municipal Court:            212-555-7000
County Clerk:               212-555-7500
Legal Aid Society:          212-555-9200

All government directory assistance is provided free of charge."""

    def cmd_crossbar(self, args: List[str]) -> str:
        """Enhanced crossbar switching system with realistic electromechanical operations."""
        import random

        if not args:
            crossbar_output = f"""Bell System Crossbar Switching Systems
Electromechanical Central Office Equipment
{'=' * 50}

CROSSBAR SYSTEMS STATUS
{'=' * 30}"""

            # Show crossbar systems from our initialized state
            for xb_id, xb_data in self.crossbar_systems.items():
                status_detail = "Normal operation"
                if xb_data["maintenance_due"]:
                    status_detail = "Preventive maintenance due"
                elif xb_data["status"] == "MAINT":
                    status_detail = "Under maintenance"

                crossbar_output += f"""
{xb_id}:
  Status:           {xb_data['status']}
  Load:             {xb_data['load']}%
  Condition:        {status_detail}"""

            crossbar_output += f"""

SYSTEM CHARACTERISTICS
{'=' * 30}
Switch Type:                 Electromechanical Crossbar
Switching Speed:             {random.uniform(0.8, 1.5):.1f} seconds average
Capacity:                    {random.randint(8000, 12000)} lines per system
Reliability:                 {random.uniform(0.985, 0.995):.2%} uptime

MECHANICAL COMPONENTS
{'=' * 30}
Crossbar Switches:           {random.randint(450, 680)} units
Markers:                     {random.randint(18, 24)} active
Senders:                     {random.randint(45, 60)} available
Connectors:                  {random.randint(180, 240)} operational
Registers:                   {random.randint(95, 140)} in service

Commands:
  crossbar status <system>    Detailed system status
  crossbar test <system>      Run mechanical tests
  crossbar maintenance        Maintenance schedule
  crossbar performance        Performance analysis"""

            return crossbar_output

        elif args[0] == "status" and len(args) > 1:
            system_id = args[1].upper()
            return self._show_crossbar_system_status(system_id)

        elif args[0] == "test" and len(args) > 1:
            system_id = args[1].upper()
            return self._run_crossbar_mechanical_test(system_id)

        elif args[0] == "maintenance":
            return self._show_crossbar_maintenance()

        elif args[0] == "performance":
            return self._show_crossbar_performance()

        else:
            available_commands = ["status", "test", "maintenance", "performance"]
            return f"crossbar: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"

    def _show_crossbar_system_status(self, system_id: str) -> str:
        """Show detailed crossbar system status."""

        if system_id not in self.crossbar_systems:
            return f"crossbar: System {system_id} not found\nAvailable systems: {', '.join(self.crossbar_systems.keys())}"

        system = self.crossbar_systems[system_id]
        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        return f"""Crossbar System Status: {system_id}
Status Report: {current_time}

SYSTEM OVERVIEW
{'=' * 25}
System Status:               {system['status']}
Traffic Load:                {system['load']}%
Maintenance Due:             {'YES' if system['maintenance_due'] else 'NO'}
Last Inspection:             {(self.clock.now() - timedelta(days=random.randint(30, 180))).strftime('%B %d, %Y')}

MECHANICAL COMPONENTS
{'=' * 25}
Crossbar Switches:           {random.randint(85, 100)}% operational
Contact Condition:           {'GOOD' if not system['maintenance_due'] else 'REQUIRES ATTENTION'}
Spring Tension:              Within specifications
Relay Response Time:         {random.uniform(15, 35):.1f} milliseconds

TRAFFIC STATISTICS
{'=' * 25}
Calls Processed Today:       {random.randint(15000, 35000):,}
Peak Hour Load:              {random.randint(85, 98)}%
Average Setup Time:          {random.uniform(0.8, 2.2):.1f} seconds
Blocking Rate:               {random.uniform(0.001, 0.015):.3f}

PERFORMANCE METRICS
{'=' * 25}
Call Completion Rate:        {random.uniform(0.92, 0.97):.1%}
Equipment Reliability:       {random.uniform(0.985, 0.995):.2%}
Maintenance Interval:        {'OVERDUE' if system['maintenance_due'] else 'CURRENT'}

{'RECOMMENDATION: Schedule immediate maintenance' if system['maintenance_due'] else 'STATUS: Normal operation'}"""

    def _run_crossbar_mechanical_test(self, system_id: str) -> str:
        """Run mechanical tests on crossbar system."""
        import random

        if system_id not in self.crossbar_systems:
            return f"crossbar: System {system_id} not found"

        system = self.crossbar_systems[system_id]

        return f"""Crossbar Mechanical Test Sequence: {system_id}
Test Initiated: {self.clock.now().strftime('%H:%M:%S EST')}

MECHANICAL TEST SUITE
{'=' * 30}
Contact Resistance Test:     {'PASS' if random.random() > 0.1 else 'FAIL'} ({random.uniform(0.5, 2.8):.1f} ohms)
Spring Tension Check:        {'PASS' if random.random() > 0.15 else 'MARGINAL'} ({random.uniform(28, 35):.1f} grams)
Relay Operation Test:        {'PASS' if random.random() > 0.08 else 'FAIL'} ({random.uniform(18, 45):.1f} ms response)
Switch Matrix Scan:          {'PASS' if random.random() > 0.12 else 'FAIL'} ({random.randint(890, 920)}/920 contacts OK)
Motor Drive Check:           {'PASS' if random.random() > 0.05 else 'FAIL'} (RPM within spec)
Timing Verification:         {'PASS' if random.random() > 0.20 else 'MARGINAL'} (±{random.uniform(2, 8):.1f}% deviation)

LUBRICATION STATUS
{'=' * 30}
Contact Points:              {'ADEQUATE' if not system['maintenance_due'] else 'LOW'}
Pivot Bearings:              {'GOOD' if not system['maintenance_due'] else 'DRY'}
Drive Mechanisms:            {'LUBRICATED' if not system['maintenance_due'] else 'REQUIRES SERVICE'}

Test Duration: {random.randint(45, 180)} seconds
Overall Result: {'PASS - System operational' if not system['maintenance_due'] else 'MARGINAL - Maintenance recommended'}

Use 'crossbar maintenance' for service scheduling."""

    def _show_crossbar_maintenance(self) -> str:
        """Show crossbar maintenance requirements and schedule."""

        maintenance_output = f"""Crossbar System Maintenance Schedule
{'=' * 45}

MAINTENANCE REQUIREMENTS
{'=' * 35}
Contact Cleaning:            Every 6 months
Lubrication:                 Every 3 months
Timing Adjustment:           Annually
Complete Inspection:         Every 18 months

CURRENT MAINTENANCE STATUS
{'=' * 35}"""

        for xb_id, xb_data in self.crossbar_systems.items():
            next_maint = "OVERDUE" if xb_data["maintenance_due"] else f"{random.randint(15, 90)} days"
            maintenance_output += f"""
{xb_id}:
  Last Service:        {(self.clock.now() - timedelta(days=random.randint(60, 200))).strftime('%B %d, %Y')}
  Next Due:            {next_maint}
  Priority:            {'HIGH' if xb_data['maintenance_due'] else 'NORMAL'}"""

        maintenance_output += f"""

MAINTENANCE PROCEDURES
{'=' * 35}
• Contact cleaning with approved solvents
• Spring tension adjustment and calibration
• Relay timing verification and adjustment
• Motor brush inspection and replacement
• Lubrication of all mechanical components
• Complete operational testing

Estimated Service Time: 4-6 hours per system
Maintenance Window: 02:00-06:00 EST (low traffic period)

Contact: Electromechanical Maintenance Team ext 4380"""

        return maintenance_output

    def _show_crossbar_performance(self) -> str:
        """Show crossbar performance analysis."""
        performance_output = f"""Crossbar System Performance Analysis
Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}

PERFORMANCE COMPARISON
{'=' * 35}"""

        for xb_id, xb_data in self.crossbar_systems.items():
            efficiency = random.uniform(0.88, 0.95)
            setup_time = random.uniform(0.9, 2.5)
            performance_output += f"""
{xb_id}:
  Efficiency:          {efficiency:.1%}
  Avg Setup Time:      {setup_time:.1f} seconds
  Reliability:         {random.uniform(0.985, 0.996):.2%}
  Maintenance Score:   {'EXCELLENT' if not xb_data['maintenance_due'] else 'FAIR'}"""

        performance_output += f"""

HISTORICAL TRENDS
{'=' * 35}
Reliability Trend:           {random.choice(['↑ Improving', '→ Stable', '↓ Declining'])}
Maintenance Costs:           ${random.randint(15000, 35000):,} (last quarter)
Service Quality:             {random.uniform(0.92, 0.97):.1%} customer satisfaction

TECHNOLOGY COMPARISON
{'=' * 35}
Crossbar vs Electronic:      Electronic 40% faster setup
Maintenance Requirements:    Crossbar requires 3x more service
Reliability:                 Electronic 15% more reliable
Cost of Operation:           Crossbar 25% higher operating cost

MODERNIZATION PLANNING
{'=' * 35}
Replacement Schedule:        5ESS deployment in progress
Migration Timeline:          24-36 months for complete conversion
Training Requirements:       Technician retraining program active"""

        return performance_output

    def cmd_netplan(self, args: List[str]) -> str:
        """Enhanced network planning with realistic route optimization and capacity analysis."""

        if not args:
            return f"""Bell System Network Planning and Engineering
Route Optimization and Capacity Management
{'=' * 50}

CURRENT PLANNING ACTIVITIES
{'=' * 35}
Active Projects:             {random.randint(8, 15)}
Capacity Studies:            {random.randint(3, 8)} in progress
Route Optimization:          {random.randint(2, 6)} analyses
Equipment Planning:          {random.randint(4, 12)} evaluations

NETWORK GROWTH PROJECTIONS
{'=' * 35}
Annual Traffic Growth:       {random.uniform(12, 18):.1f}%
New Circuit Requirements:    {random.randint(45, 85)} T1 equivalents
Equipment Expansion:         ${random.uniform(2.5, 8.5):.1f}M investment needed
Service Area Growth:         {random.randint(3, 8)} new exchanges

CURRENT STUDIES
{'=' * 35}
NYC-WAS Corridor:           Capacity upgrade analysis
Chicago Hub:                Route diversity study
West Coast Links:           Fiber optic feasibility
Rural Coverage:             Economic analysis

Commands:
  netplan capacity           Network capacity analysis
  netplan routes             Route planning and optimization
  netplan growth             Traffic growth projections
  netplan investment         Capital investment planning"""

        elif args[0] == "capacity":
            return self._show_network_capacity_analysis()

        elif args[0] == "routes":
            return self._show_route_planning()

        elif args[0] == "growth":
            return self._show_traffic_growth_projections()

        elif args[0] == "investment":
            return self._show_investment_planning()

        else:
            available_commands = ["capacity", "routes", "growth", "investment"]
            return f"netplan: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"

    def _show_network_capacity_analysis(self) -> str:
        """Show comprehensive network capacity analysis."""
        import random

        return f"""Network Capacity Analysis
Report Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}

CURRENT NETWORK UTILIZATION
{'=' * 40}
Overall Network Load:        {random.randint(65, 85)}% of capacity
Peak Hour Utilization:      {random.randint(85, 95)}%
Reserve Capacity:           {random.randint(15, 35)}% margin
Critical Routes:            {random.randint(3, 8)} approaching limits

HIGH-UTILIZATION ROUTES
{'=' * 40}
NYC-Washington Corridor:     {random.randint(85, 95)}% utilization
Chicago-New York:           {random.randint(80, 90)}% utilization
Los Angeles-San Francisco:  {random.randint(70, 85)}% utilization
Boston-New York:            {random.randint(75, 88)}% utilization

CAPACITY CONSTRAINTS
{'=' * 40}
Equipment Limitations:       {random.randint(2, 6)} locations
Facility Constraints:        {random.randint(1, 4)} rights-of-way
Economic Thresholds:         {random.randint(3, 7)} marginal routes

EXPANSION RECOMMENDATIONS
{'=' * 40}
Immediate (6 months):        {random.randint(15, 25)} new circuits
Short-term (12 months):      {random.randint(35, 55)} circuit additions
Long-term (24 months):       {random.randint(65, 95)} circuit expansion

Investment Required:         ${random.uniform(15.5, 35.8):.1f}M total
Revenue Impact:              ${random.uniform(8.2, 18.5):.1f}M annually
ROI Projection:             {random.uniform(18, 35):.0f}% over 5 years"""

    def _show_route_planning(self) -> str:
        """Show route planning and optimization analysis."""

        return f"""Route Planning and Optimization
Analysis Date: {self.clock.now().strftime('%B %d, %Y')}

ROUTE OPTIMIZATION STUDIES
{'=' * 40}
Primary Route Analysis:      {random.randint(12, 24)} routes evaluated
Alternate Path Planning:     {random.randint(6, 15)} backup routes
Diversity Requirements:      {random.randint(85, 95)}% geographic separation
Load Balancing Efficiency:  {random.uniform(0.88, 0.95):.1%}

MAJOR ROUTE CORRIDORS
{'=' * 40}
Northeast Corridor:
  Primary Path:              I-95 Fiber Route
  Utilization:              {random.randint(75, 90)}%
  Backup Available:         Microwave diversity
  Expansion Plan:           Additional fiber planned 1984

Transcontinental Routes:
  Northern Route:           CHI-DEN-SFO via I-80
  Southern Route:           CHI-DAL-LAX via I-40
  Utilization Balance:      {random.randint(65, 85)}% / {random.randint(55, 75)}%

ROUTE ECONOMICS
{'=' * 40}
Cost per Circuit Mile:       ${random.randint(285, 450)}
Installation Time:           {random.randint(8, 18)} months average
Permit Acquisition:          {random.randint(3, 12)} months
Environmental Review:        {random.randint(6, 24)} months

TECHNOLOGY PLANNING
{'=' * 40}
Fiber Optic Deployment:     35% of new routes
Digital Microwave:          45% of new routes
Satellite Backup:           20% for remote areas
Copper Retirement:          Systematic replacement program

Next Planning Review: {(self.clock.now() + timedelta(days=90)).strftime('%B %d, %Y')}"""

    def _show_traffic_growth_projections(self) -> str:
        """Show traffic growth projections and forecasting."""
        import random

        return f"""Traffic Growth Projections and Forecasting
Forecast Period: 1984-1988
{'=' * 50}

HISTORICAL GROWTH ANALYSIS
{'=' * 40}
1980-1983 Growth Rate:       {random.uniform(8.5, 15.2):.1f}% annually
Voice Traffic:              {random.uniform(6.2, 12.8):.1f}% annual growth
Data Traffic:               {random.uniform(25.5, 45.8):.1f}% annual growth
International:              {random.uniform(18.2, 28.5):.1f}% annual growth

5-YEAR PROJECTIONS (1984-1988)
{'=' * 40}
Total Call Volume Growth:    {random.uniform(65, 125):.0f}% increase
Peak Hour Calls:            From {random.randint(850, 950)}K to {random.randint(1400, 1800)}K
Data Communication:          {random.uniform(180, 320):.0f}% growth expected
Video Services:             Emerging market - 5% by 1988

TECHNOLOGY IMPACT
{'=' * 40}
Digital Switching:          85% deployment by 1988
Fiber Optic Transmission:  70% of long-haul by 1988
ISDN Services:             15% market penetration
Mobile Communications:      2% of total traffic

CAPACITY REQUIREMENTS
{'=' * 40}
New Switching Capacity:     {random.uniform(2.2, 3.8):.1f}M additional ports
Transmission Expansion:     {random.uniform(45, 75):.0f}% more circuits
Operator Positions:         {random.uniform(-15, -25):.0f}% reduction (automation)
Data Processing:            {random.uniform(250, 450):.0f}% increase

INVESTMENT PROJECTIONS
{'=' * 40}
Total Investment (5-year):  ${random.uniform(12.5, 28.8):.1f}B
Network Expansion:          ${random.uniform(7.2, 15.5):.1f}B
Technology Upgrade:         ${random.uniform(3.8, 8.5):.1f}B
Facilities:                 ${random.uniform(1.5, 4.8):.1f}B

Revenue Projections:        ${random.uniform(45.5, 78.2):.1f}B (1988)
Market Share Target:        {random.uniform(78, 88):.0f}% of US telecommunications"""

    def _show_investment_planning(self) -> str:
        """Show capital investment planning analysis."""

        return f"""Capital Investment Planning Analysis
Planning Horizon: 1984-1988
{'=' * 50}

INVESTMENT CATEGORIES
{'=' * 40}
Network Infrastructure:     ${random.uniform(8.5, 15.2):.1f}B ({random.uniform(45, 65):.0f}%)
Technology Modernization:   ${random.uniform(3.2, 7.8):.1f}B ({random.uniform(18, 28):.0f}%)
Facilities and Buildings:   ${random.uniform(1.8, 4.5):.1f}B ({random.uniform(10, 18):.0f}%)
Research and Development:   ${random.uniform(1.2, 2.8):.1f}B ({random.uniform(8, 15):.0f}%)

PRIORITY PROJECTS
{'=' * 40}
Electronic Switching:       ${random.uniform(4.5, 8.2):.1f}B
  - 5ESS Deployment
  - Legacy System Replacement
  - Digital Feature Enhancement

Fiber Optic Network:        ${random.uniform(2.8, 5.5):.1f}B
  - Long-haul Routes
  - Metropolitan Networks
  - Customer Access

TNDS Expansion:            ${random.uniform(0.8, 1.8):.1f}B
  - Processing Capacity
  - Database Systems
  - Analysis Tools

FINANCIAL PROJECTIONS
{'=' * 40}
Total Capital Required:     ${random.uniform(15.8, 32.5):.1f}B
Financing Sources:
  Internal Cash Flow:       {random.uniform(55, 75):.0f}%
  Long-term Debt:          {random.uniform(20, 35):.0f}%
  Equipment Leasing:       {random.uniform(5, 15):.0f}%

Expected ROI:              {random.uniform(15, 25):.1f}% over 7 years
Payback Period:            {random.uniform(4.2, 6.8):.1f} years average
Risk Assessment:           MODERATE (technology transition)

ECONOMIC IMPACT
{'=' * 40}
Job Creation:              {random.randint(15000, 35000):,} new positions
Economic Stimulus:         ${random.uniform(25.8, 48.5):.1f}B regional impact
Productivity Gain:         {random.uniform(25, 45):.0f}% operational efficiency
Service Quality:           {random.uniform(15, 28):.0f}% improvement target

Regulatory Approval:       Required for major projects
Environmental Impact:      Assessments in progress
Public Service Benefits:   Universal service expansion"""

    def cmd_trouble(self, args: List[str]) -> str:
        """Enhanced trouble ticket management with authentic Bell System operations."""

        if not args:
            return self._show_trouble_ticket_dashboard()

        elif args[0] == "list":
            priority_filter = args[1] if len(args) > 1 else None
            return self._list_trouble_tickets(priority_filter)

        elif args[0] == "detail" and len(args) > 1:
            ticket_id = args[1].upper()
            return self._show_trouble_ticket_detail(ticket_id)

        elif args[0] == "assign" and len(args) > 2:
            ticket_id = args[1].upper()
            team = " ".join(args[2:])
            return self._assign_trouble_ticket(ticket_id, team)

        elif args[0] == "update" and len(args) > 2:
            ticket_id = args[1].upper()
            status = args[2].upper()
            return self._update_trouble_ticket(ticket_id, status)

        elif args[0] == "escalate" and len(args) > 1:
            ticket_id = args[1].upper()
            return self._escalate_trouble_ticket(ticket_id)

        elif args[0] == "resolve" and len(args) > 1:
            ticket_id = args[1].upper()
            return self._resolve_trouble_ticket(ticket_id)

        elif args[0] == "create":
            return self._create_manual_ticket(args[1:] if len(args) > 1 else [])

        elif args[0] == "geographic":
            return self._show_geographic_trouble_overview()

        elif args[0] == "priority":
            return self._show_priority_analysis()

        else:
            available_commands = ["list", "detail", "assign", "update", "escalate", "resolve", "create", "geographic", "priority"]
            return f"trouble: Unknown option '{args[0]}'\nAvailable commands: {', '.join(available_commands)}"

    def _show_trouble_ticket_dashboard(self) -> str:
        """Show comprehensive trouble ticket dashboard with real-time status."""
        current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

        # Calculate ticket statistics
        critical_tickets = [t for t in self.active_tickets if t['priority'] == 'CRITICAL']
        major_tickets = [t for t in self.active_tickets if t['priority'] == 'MAJOR']
        minor_tickets = [t for t in self.active_tickets if t['priority'] == 'MINOR']

        # Calculate customer impact
        total_customers_affected = sum(t['customer_impact'] for t in self.active_tickets)
        revenue_impact = sum(t['business_impact']['revenue_loss_hour'] for t in self.active_tickets)

        dashboard = f"""Bell System Trouble Ticket Management System
Real-Time Operations Dashboard
{current_time}

ACTIVE TROUBLE TICKETS
{'=' * 40}
Critical Priority:        {len(critical_tickets)} tickets
Major Priority:           {len(major_tickets)} tickets
Minor Priority:           {len(minor_tickets)} tickets
Total Active:             {len(self.active_tickets)} tickets

CUSTOMER IMPACT ANALYSIS
{'=' * 40}
Customers Affected:       {total_customers_affected:,}
Revenue Impact (hourly):  ${revenue_impact:,}
Service Quality Impact:   {'SEVERE' if len(critical_tickets) > 2 else 'MODERATE' if len(major_tickets) > 5 else 'MINIMAL'}

RECENT CRITICAL ISSUES
{'=' * 40}"""

        # Show most recent critical tickets
        recent_critical = sorted(critical_tickets, key=lambda x: x['created_time'], reverse=True)[:3]

        if recent_critical:
            for ticket in recent_critical:
                age = self.clock.now() - ticket['created_time']
                age_str = f"{int(age.total_seconds() // 3600)}h{int((age.total_seconds() % 3600) // 60)}m"
                dashboard += f"\n{ticket['id']:<8} {age_str:<6} {ticket['affected_office']['city']:<12} {ticket['title'][:45]}"
        else:
            dashboard += "\n✓ No critical issues currently active"

        # Geographic distribution
        geographic_impact = {}
        for ticket in self.active_tickets:
            state = ticket['affected_office']['state']
            if state not in geographic_impact:
                geographic_impact[state] = 0
            geographic_impact[state] += 1

        dashboard += f"""

GEOGRAPHIC DISTRIBUTION
{'=' * 40}"""

        for state, count in sorted(geographic_impact.items(), key=lambda x: x[1], reverse=True)[:8]:
            dashboard += f"\n{state:<4} {count:>2} active tickets"

        dashboard += f"""

OPERATIONAL METRICS
{'=' * 40}
Average Resolution Time:  {sum(t['estimated_duration'] for t in self.completed_tickets[-20:]) // max(len(self.completed_tickets[-20:]), 1) if self.completed_tickets else 180} minutes
Escalation Rate:          {len([t for t in self.active_tickets if t['escalation_level'] > 1]) / max(len(self.active_tickets), 1) * 100:.1f}%
On-Time Resolution:       {85 + random.randint(-5, 10):.1f}%

Commands:
  trouble list [priority]     List tickets by priority
  trouble detail <id>         Show detailed ticket information
  trouble assign <id> <team>  Assign ticket to team
  trouble escalate <id>       Escalate ticket priority
  trouble geographic          Geographic trouble overview
  trouble priority            Priority analysis and trends"""

        return dashboard

    def _list_trouble_tickets(self, priority_filter: Optional[str] = None) -> str:
        """List trouble tickets with optional priority filtering."""
        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Filter tickets if priority specified
        if priority_filter:
            priority_filter = priority_filter.upper()
            filtered_tickets = [t for t in self.active_tickets if t['priority'] == priority_filter]
            title = f"Trouble Tickets - {priority_filter} Priority"
        else:
            filtered_tickets = self.active_tickets
            title = "All Active Trouble Tickets"

        listing = f"""{title}
Query Time: {current_time}

{'ID':<10} {'PRIORITY':<8} {'AGE':<6} {'LOCATION':<15} {'CUSTOMERS':<9} {'STATUS':<12} {'DESCRIPTION':<30}
{'=' * 100}"""

        # Sort by priority (Critical first) then by age
        priority_order = {'CRITICAL': 0, 'MAJOR': 1, 'MINOR': 2}
        sorted_tickets = sorted(filtered_tickets,
                              key=lambda x: (priority_order[x['priority']], x['created_time']))

        for ticket in sorted_tickets:
            age = self.clock.now() - ticket['created_time']
            age_str = f"{int(age.total_seconds() // 3600)}h{int((age.total_seconds() % 3600) // 60)}m"

            location = f"{ticket['affected_office']['city']}, {ticket['affected_office']['state']}"
            customers = f"{ticket['customer_impact']:,}"
            description = ticket['title'][:28] + ".." if len(ticket['title']) > 30 else ticket['title']

            listing += f"\n{ticket['id']:<10} {ticket['priority']:<8} {age_str:<6} {location:<15} {customers:<9} {ticket['status']:<12} {description}"

        if not filtered_tickets:
            listing += f"\n{'No tickets found matching criteria' if priority_filter else 'No active tickets'}"

        listing += f"\n\nTotal: {len(filtered_tickets)} tickets"
        return listing

    def _show_trouble_ticket_detail(self, ticket_id: str) -> str:
        """Show comprehensive details for a specific trouble ticket."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found\nUse 'trouble list' to see active tickets"

        age = self.clock.now() - ticket['created_time']
        age_str = f"{int(age.total_seconds() // 3600)}h {int((age.total_seconds() % 3600) // 60)}m"

        detail = f"""Trouble Ticket Detail: {ticket['id']}
{'=' * 50}

TICKET IDENTIFICATION
{'=' * 30}
Ticket ID:                {ticket['id']}
Category:                 {ticket['category']}
Priority:                 {ticket['priority']}
Status:                   {ticket['status']}
Escalation Level:         {ticket['escalation_level']}
Created:                  {ticket['created_time'].strftime('%B %d, %Y %H:%M EST')}
Age:                      {age_str}

PROBLEM DESCRIPTION
{'=' * 30}
Title:                    {ticket['title']}

Description:
{ticket['description']}

AFFECTED INFRASTRUCTURE
{'=' * 30}
Central Office:           {ticket['affected_office']['city']}, {ticket['affected_office']['state']}
Area Code:                {ticket['affected_office']['npa']}
Exchange:                 {ticket['affected_office']['nxx']}
Switch Type:              {ticket['affected_office']['switch_type']}
Office Capacity:          {ticket['affected_office']['capacity']:,} lines
Current Utilization:      {ticket['affected_office']['utilization']}%

IMPACT ASSESSMENT
{'=' * 30}
Customers Affected:       {ticket['customer_impact']:,}
Geographic Scope:         {ticket['geographic_scope']}
Revenue Impact (hourly):  ${ticket['business_impact']['revenue_loss_hour']:,}
Service Level Impact:     {ticket['business_impact']['service_level_impact']}
Regulatory Exposure:      {'YES' if ticket['business_impact']['regulatory_exposure'] else 'NO'}

TECHNICAL DETAILS
{'=' * 30}
{ticket['technical_details']}

Equipment Involved:       {', '.join(ticket['equipment_involved'])}

ASSIGNMENT AND RESPONSE
{'=' * 30}
Assigned Team:            {ticket['assigned_team']}
Estimated Duration:       {ticket['estimated_duration']} minutes
Response Time Target:     {15 if ticket['priority'] == 'CRITICAL' else 30 if ticket['priority'] == 'MAJOR' else 60} minutes

REQUIRED ACTIONS
{'=' * 30}"""

        for i, action in enumerate(ticket['required_actions'], 1):
            detail += f"\n{i}. {action}"

        if ticket['resolution_steps']:
            detail += f"""

RESOLUTION PROGRESS
{'=' * 30}"""
            for i, step in enumerate(ticket['resolution_steps'], 1):
                detail += f"\n{i}. {step}"

        detail += f"""

ESCALATION CONTACTS
{'=' * 30}
Level 1:                  Field Maintenance Team ext 4350
Level 2:                  Engineering Support ext 4370
Level 3:                  Network Operations Center ext 4911
Emergency:                Bell System Emergency Line ext 911

Commands:
  trouble assign {ticket_id} <team>     Assign to team
  trouble update {ticket_id} <status>   Update status
  trouble escalate {ticket_id}          Escalate priority
  trouble resolve {ticket_id}           Mark as resolved"""

        return detail

    def _assign_trouble_ticket(self, ticket_id: str, team: str) -> str:
        """Assign trouble ticket to a specific team."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found"

        old_team = ticket['assigned_team']
        ticket['assigned_team'] = team
        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Add resolution step
        ticket['resolution_steps'].append(f"[{current_time}] Reassigned from '{old_team}' to '{team}' by {self.username}")

        return f"""Ticket Assignment Updated
{'=' * 30}
Ticket ID:        {ticket_id}
Previous Team:    {old_team}
New Team:         {team}
Updated By:       {self.username}
Time:             {current_time}

Assignment notification sent to {team}.
Ticket status updated in Bell System Trouble Management Database."""

    def _update_trouble_ticket(self, ticket_id: str, status: str) -> str:
        """Update trouble ticket status."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found"

        valid_statuses = ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'PENDING', 'TESTING', 'RESOLVED', 'CLOSED']
        if status not in valid_statuses:
            return f"trouble: Invalid status '{status}'\nValid statuses: {', '.join(valid_statuses)}"

        old_status = ticket['status']
        ticket['status'] = status
        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Add resolution step
        ticket['resolution_steps'].append(f"[{current_time}] Status changed from '{old_status}' to '{status}' by {self.username}")

        return f"""Ticket Status Updated
{'=' * 25}
Ticket ID:        {ticket_id}
Previous Status:  {old_status}
New Status:       {status}
Updated By:       {self.username}
Time:             {current_time}

Status change recorded in Bell System Operations Log."""

    def _escalate_trouble_ticket(self, ticket_id: str) -> str:
        """Escalate trouble ticket to higher priority or management level."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found"

        # Increase escalation level
        old_level = ticket['escalation_level']
        ticket['escalation_level'] = min(old_level + 1, 4)  # Max escalation level 4

        # Escalate priority if appropriate
        priority_escalation = {
            'MINOR': 'MAJOR',
            'MAJOR': 'CRITICAL',
            'CRITICAL': 'CRITICAL'  # Already at highest
        }

        old_priority = ticket['priority']
        if old_level == 1 and ticket['priority'] != 'CRITICAL':
            ticket['priority'] = priority_escalation[ticket['priority']]

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Add resolution step
        escalation_note = f"[{current_time}] Escalated to level {ticket['escalation_level']} by {self.username}"
        if ticket['priority'] != old_priority:
            escalation_note += f" - Priority raised from {old_priority} to {ticket['priority']}"

        ticket['resolution_steps'].append(escalation_note)

        # Determine escalation contacts
        escalation_contacts = {
            2: "Engineering Support ext 4370",
            3: "Network Operations Manager ext 4950",
            4: "Director of Operations ext 4980"
        }

        return f"""Ticket Escalation Completed
{'=' * 35}
Ticket ID:            {ticket_id}
Previous Level:       {old_level}
New Escalation Level: {ticket['escalation_level']}
Priority:             {old_priority} → {ticket['priority']}
Escalated By:         {self.username}
Time:                 {current_time}

Escalation Contact:   {escalation_contacts.get(ticket['escalation_level'], 'Executive Team')}

Automatic notifications sent to management chain.
Escalation logged in Bell System Operations Database."""

    def _resolve_trouble_ticket(self, ticket_id: str) -> str:
        """Mark trouble ticket as resolved and move to completed tickets."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found"

        # Calculate resolution time
        resolution_time = self.clock.now()
        total_time = resolution_time - ticket['created_time']
        resolution_minutes = int(total_time.total_seconds() / 60)

        # Update ticket
        ticket['status'] = 'RESOLVED'
        ticket['resolution_time'] = resolution_time
        ticket['actual_duration'] = resolution_minutes

        current_time = resolution_time.strftime("%H:%M:%S EST")
        ticket['resolution_steps'].append(f"[{current_time}] Ticket resolved by {self.username}")

        # Move to completed tickets
        self.active_tickets.remove(ticket)
        self.completed_tickets.append(ticket)

        # Calculate metrics
        target_time = 15 if ticket['priority'] == 'CRITICAL' else 30 if ticket['priority'] == 'MAJOR' else 60
        on_time = resolution_minutes <= target_time

        return f"""Trouble Ticket Resolved
{'=' * 30}
Ticket ID:            {ticket_id}
Resolution Time:      {current_time}
Total Duration:       {resolution_minutes} minutes
Target Time:          {target_time} minutes
Performance:          {'ON TIME' if on_time else 'EXCEEDED TARGET'}

Customer Impact:      {ticket['customer_impact']:,} customers restored
Revenue Recovered:    ${ticket['business_impact']['revenue_loss_hour'] * (resolution_minutes / 60):,.0f}

Resolution Details:
{ticket['technical_details']}

Ticket closed and archived in Bell System Trouble Management Database.
Service restoration confirmed for affected customers."""

    def _create_manual_ticket(self, args: List[str]) -> str:
        """Create a trouble ticket manually from craft-entered parameters."""
        valid_categories = list(self.ticket_categories.keys())
        valid_priorities = ['CRITICAL', 'MAJOR', 'MINOR']

        if not args:
            return f"""Trouble Ticket - Manual Entry
{'=' * 50}

Usage: trouble create <category> <priority> <description>

Valid categories:  {', '.join(valid_categories)}
Valid priorities:  {', '.join(valid_priorities)}

Example:
  trouble create {valid_categories[0]} MAJOR Water in cable at Elm St manhole"""

        category = args[0].upper()
        if category not in self.ticket_categories:
            return (f"trouble create: Unknown category '{args[0]}'\n"
                    f"Valid categories: {', '.join(valid_categories)}")

        priority = args[1].upper() if len(args) > 1 else 'MINOR'
        if priority not in valid_priorities:
            return (f"trouble create: Unknown priority '{args[1]}'\n"
                    f"Valid priorities: {', '.join(valid_priorities)}")

        description = " ".join(args[2:]) if len(args) > 2 else "Craft-reported trouble, details pending"

        category_data = self.ticket_categories[category]
        self.ticket_counter += random.randint(1, 5)
        ticket_id = f"TK-{self.ticket_counter}"

        # The same shape the generated tickets carry. This used to be a bare
        # office code, which every display that reached into the office
        # record then crashed on.
        affected_office = self._select_affected_infrastructure()
        customer_impact = random.randint(*category_data['customer_impact'][priority])
        estimated_duration = random.randint(*category_data['typical_duration'][priority])

        ticket = {
            'id': ticket_id,
            'category': category,
            'priority': priority,
            'title': description[:60],
            'description': description,
            'affected_office': affected_office,
            'customer_impact': customer_impact,
            'estimated_duration': estimated_duration,
            'status': 'OPEN',
            'assigned_team': 'UNASSIGNED',
            'created_time': self.clock.now(),
            'escalation_level': 1,
            'technical_details': 'Manually entered by craft; awaiting test board verification',
            'required_actions': ['Dispatch test board', 'Verify trouble condition', 'Assign repair force'],
            'equipment_involved': [],
            'geographic_scope': 'LOCAL',
            'business_impact': self._calculate_business_impact(priority, customer_impact),
            'resolution_steps': []
        }
        self.active_tickets.append(ticket)

        return f"""Trouble Ticket Created
{'=' * 50}
Ticket ID:                {ticket_id}
Created:                  {ticket['created_time'].strftime('%B %d, %Y %H:%M EST')}
Entered By:               {self.username}

TICKET DETAILS
{'=' * 40}
Category:                 {category}
Priority:                 {priority}
Description:              {description}
Affected Office:          {self._office_label(affected_office)}
Customers Affected:       {customer_impact:,}
Estimated Duration:       {estimated_duration} minutes
Status:                   OPEN (unassigned)

NEXT STEPS
{'=' * 40}
  trouble detail {ticket_id}          Review full ticket record
  trouble assign {ticket_id} <team>   Assign to a repair team
  trouble escalate {ticket_id}        Escalate priority

Total Active Tickets: {len(self.active_tickets)}"""

    def _show_geographic_trouble_overview(self) -> str:
        """Show geographic distribution and analysis of trouble tickets."""
        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        # Analyze geographic distribution
        state_analysis = {}
        metro_analysis = {}

        for ticket in self.active_tickets:
            state = ticket['affected_office']['state']
            city = ticket['affected_office']['city']

            # State-level analysis
            if state not in state_analysis:
                state_analysis[state] = {
                    'total': 0, 'critical': 0, 'major': 0, 'minor': 0,
                    'customers': 0, 'revenue_impact': 0
                }

            state_analysis[state]['total'] += 1
            state_analysis[state][ticket['priority'].lower()] += 1
            state_analysis[state]['customers'] += ticket['customer_impact']
            state_analysis[state]['revenue_impact'] += ticket['business_impact']['revenue_loss_hour']

            # Metro area analysis
            if city not in metro_analysis:
                metro_analysis[city] = {'count': 0, 'customers': 0}
            metro_analysis[city]['count'] += 1
            metro_analysis[city]['customers'] += ticket['customer_impact']

        overview = f"""Geographic Trouble Analysis
Report Generated: {current_time}

STATE-LEVEL IMPACT ANALYSIS
{'=' * 40}
{'STATE':<6} {'TOTAL':<5} {'CRIT':<4} {'MAJ':<4} {'MIN':<4} {'CUSTOMERS':<10} {'REV/HR':<8}"""

        for state, data in sorted(state_analysis.items(), key=lambda x: x[1]['total'], reverse=True):
            overview += f"\n{state:<6} {data['total']:<5} {data['critical']:<4} {data['major']:<4} {data['minor']:<4} {data['customers']:<10,} ${data['revenue_impact']:<7,.0f}"

        overview += f"""

METROPOLITAN AREA IMPACT
{'=' * 40}
{'CITY':<15} {'TICKETS':<7} {'CUSTOMERS':<10} {'SEVERITY':<8}"""

        for city, data in sorted(metro_analysis.items(), key=lambda x: x[1]['customers'], reverse=True)[:12]:
            severity = 'HIGH' if data['customers'] > 5000 else 'MEDIUM' if data['customers'] > 1000 else 'LOW'
            overview += f"\n{city:<15} {data['count']:<7} {data['customers']:<10,} {severity:<8}"

        # Network topology impact
        overview += f"""

NETWORK TOPOLOGY ANALYSIS
{'=' * 40}
Interstate Routes:        {len([t for t in self.active_tickets if t['geographic_scope'] == 'INTERSTATE'])} tickets
Regional Networks:        {len([t for t in self.active_tickets if t['geographic_scope'] == 'REGIONAL'])} tickets
Local Exchanges:          {len([t for t in self.active_tickets if t['geographic_scope'] == 'LOCAL'])} tickets

INFRASTRUCTURE TYPE IMPACT
{'=' * 40}"""

        # Analyze by switch type
        switch_impact = {}
        for ticket in self.active_tickets:
            switch_type = ticket['affected_office']['switch_type']
            if switch_type not in switch_impact:
                switch_impact[switch_type] = 0
            switch_impact[switch_type] += 1

        for switch_type, count in sorted(switch_impact.items(), key=lambda x: x[1], reverse=True):
            overview += f"\n{switch_type:<12} {count} tickets affecting this equipment type"

        # Risk assessment
        high_risk_areas = [state for state, data in state_analysis.items() if data['critical'] > 0 or data['customers'] > 10000]

        overview += f"""

RISK ASSESSMENT
{'=' * 40}
High Risk Areas:          {len(high_risk_areas)} states/territories
Critical Situations:      {len([t for t in self.active_tickets if t['priority'] == 'CRITICAL'])} active
Network Vulnerability:    {'ELEVATED' if len(high_risk_areas) > 3 else 'NORMAL'}

Recommended Actions:
• Monitor high-impact areas closely
• Prepare additional resources for critical regions
• Review network redundancy in affected areas
• Coordinate with regional operations centers"""

        return overview

    def _show_priority_analysis(self) -> str:
        """Show priority analysis and trends for trouble tickets."""
        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        # Analyze current priorities
        priority_stats = {'CRITICAL': 0, 'MAJOR': 0, 'MINOR': 0}
        for ticket in self.active_tickets:
            priority_stats[ticket['priority']] += 1

        total_tickets = len(self.active_tickets)

        analysis = f"""Trouble Ticket Priority Analysis
Report Generated: {current_time}

CURRENT PRIORITY DISTRIBUTION
{'=' * 40}
Critical Priority:        {priority_stats['CRITICAL']} tickets ({priority_stats['CRITICAL']/max(total_tickets,1)*100:.1f}%)
Major Priority:           {priority_stats['MAJOR']} tickets ({priority_stats['MAJOR']/max(total_tickets,1)*100:.1f}%)
Minor Priority:           {priority_stats['MINOR']} tickets ({priority_stats['MINOR']/max(total_tickets,1)*100:.1f}%)

PRIORITY THRESHOLDS
{'=' * 40}
Critical Threshold:       Service affecting >1000 customers
Major Threshold:          Service affecting >100 customers
Minor Threshold:          Service affecting <100 customers

ESCALATION ANALYSIS
{'=' * 40}"""

        escalated_tickets = [t for t in self.active_tickets if t['escalation_level'] > 1]
        analysis += f"\nEscalated Tickets:        {len(escalated_tickets)} tickets"
        analysis += f"\nEscalation Rate:          {len(escalated_tickets)/max(total_tickets,1)*100:.1f}%"

        # Show escalated tickets
        if escalated_tickets:
            analysis += "\n\nEscalated Ticket Details:"
            for ticket in escalated_tickets:
                age = self.clock.now() - ticket['created_time']
                age_str = f"{int(age.total_seconds() // 3600)}h{int((age.total_seconds() % 3600) // 60)}m"
                analysis += f"\n{ticket['id']:<10} Level {ticket['escalation_level']} {ticket['priority']:<8} {age_str:<6} {ticket['affected_office']['city']}"

        # Performance metrics
        if self.completed_tickets:
            recent_completed = self.completed_tickets[-20:]  # Last 20 completed tickets
            avg_resolution = sum(t.get('actual_duration', 180) for t in recent_completed) / len(recent_completed)

            analysis += f"""

RESOLUTION PERFORMANCE
{'=' * 40}
Average Resolution Time:  {avg_resolution:.0f} minutes
Target Performance:
  Critical (15 min):      {len([t for t in recent_completed if t['priority'] == 'CRITICAL' and t.get('actual_duration', 999) <= 15])}/{len([t for t in recent_completed if t['priority'] == 'CRITICAL'])if recent_completed else 1} on time
  Major (30 min):         {len([t for t in recent_completed if t['priority'] == 'MAJOR' and t.get('actual_duration', 999) <= 30])}/{len([t for t in recent_completed if t['priority'] == 'MAJOR']) if recent_completed else 1} on time
  Minor (60 min):         {len([t for t in recent_completed if t['priority'] == 'MINOR' and t.get('actual_duration', 999) <= 60])}/{len([t for t in recent_completed if t['priority'] == 'MINOR']) if recent_completed else 1} on time"""

        # Trending analysis
        analysis += f"""

TRENDING ANALYSIS
{'=' * 40}
Current Workload:         {'HIGH' if total_tickets > 15 else 'NORMAL' if total_tickets > 8 else 'LOW'}
Critical Trend:           {'INCREASING' if priority_stats['CRITICAL'] > 2 else 'STABLE'}
Network Health:           {'DEGRADED' if priority_stats['CRITICAL'] > 0 else 'GOOD'}

RECOMMENDATIONS
{'=' * 40}"""

        if priority_stats['CRITICAL'] > 2:
            analysis += "\n• IMMEDIATE: Activate emergency response procedures"
            analysis += "\n• Deploy additional technical resources"
            analysis += "\n• Implement network protection measures"
        elif priority_stats['MAJOR'] > 8:
            analysis += "\n• Increase maintenance staffing levels"
            analysis += "\n• Review preventive maintenance schedules"
            analysis += "\n• Monitor for pattern development"
        else:
            analysis += "\n• Continue normal operations monitoring"
            analysis += "\n• Maintain current staffing levels"
            analysis += "\n• Focus on preventive maintenance"

        return analysis

    def cmd_dbquery(self, args: List[str]) -> str:
        """Database query and management tools"""
        return self._subsystem_unavailable("dbquery", "Database operations")

    def cmd_custdb(self, args: List[str]) -> str:
        """Customer database operations"""
        return self._subsystem_unavailable("custdb", "Customer database")

    def cmd_provision(self, args: List[str]) -> str:
        """Service provisioning and installation"""
        return self._subsystem_unavailable("provision", "Service provisioning")

    def cmd_collect(self, args: List[str]) -> str:
        """Toll collection and billing verification"""
        return self._subsystem_unavailable("collect", "Collect call operations")

    def cmd_handoff(self, args: List[str]) -> str:
        """Bell System shift handoff briefing and turnover record."""
        previous = self.shift_handoff["previous_shift"]
        pending_reports = self.desk.pending()
        overdue_reports = [r for r in pending_reports if r.overdue()]
        untested_reports = [r for r in pending_reports if not r.tested]
        open_now = [t for t in self.active_tickets if t['status'] != 'RESOLVED']
        critical = [t for t in open_now if t['priority'] == 'CRITICAL']
        unacknowledged = [a for a in self.active_alarms if not a['acknowledged']]

        output = f"""Bell System Shift Handoff Record
{self.clock.now().strftime('%B %d, %Y %H:%M EST')}
{'=' * 50}

INCOMING FROM PREVIOUS SHIFT
{'=' * 40}
Operator:                 {previous['operator']}
Shift Ended:              {previous['end_time']}
Summary:                  {previous['summary']}
System Status:            {previous['system_status']}

Key Issues Carried Forward:"""
        for issue in previous['key_issues']:
            output += f"\n  - {issue}"

        output += f"""

Tickets Transferred:      {', '.join(previous['open_tickets'])}

Special Instructions:
  {previous['special_instructions']}

CURRENT SHIFT POSITION
{'=' * 40}
Operator On Duty:         {self.username}
Role:                     {self.role_name or 'Unassigned'}
Shift Number:             {self.career.shift}
Time Worked:              {self.shift_time()} of \
{SHIFT_LENGTH_MINUTES // 60}:00
Commands This Session:    {len(self.command_history)}

Open Trouble Tickets:     {len(open_now)}
  Critical:               {len(critical)}
Unacknowledged Alarms:    {len(unacknowledged)}
Overall Health:           {self.system_health['overall_status']}

REPAIR SERVICE BUREAU
{'=' * 40}
Reports Pending:          {len(pending_reports)}
  Past Commitment:        {len(overdue_reports)}
  Not Yet Measured:       {len(untested_reports)}
Closed This Session:      {len(self.desk.closed())}
Service Index:            {self.career.service_index():.1f} \
({self.career.index_band()})
Qualifications Held:      {len(self.career.qualifications)} of \
{len(QUALIFICATIONS)}
"""

        if pending_reports:
            output += ("\nREPORTS CARRIED TO THE NEXT SHIFT\n" + "=" * 40)
            for report in pending_reports[:6]:
                output += (
                    f"\n{report.number}: {report.record.telephone_number}"
                    f"\n  Customer states:    {report.symptom}"
                    f"\n  Commitment:         "
                    f"{report.commitment.strftime('%H:%M %a %b %d')}"
                    f" ({report.age_label()}"
                    f" {'past' if report.overdue() else 'remaining'})"
                    f"\n  Measured:           "
                    f"{'yes' if report.tested else 'NO'}")

        if critical:
            output += "\nCRITICAL TICKETS REQUIRING HANDOFF\n" + "=" * 40
            for ticket in critical:
                output += f"""
{ticket['id']}: {ticket['title']}
  Office:             {self._office_label(ticket['affected_office'])}
  Assigned:           {ticket['assigned_team']}
  Customers Affected: {ticket['customer_impact']:,}"""

        output += f"""

TURNOVER CHECKLIST
{'=' * 40}
  [ ] Review all open trouble tickets with relieving operator
  [ ] Transfer unacknowledged alarms
  [ ] Confirm maintenance windows in progress
  [ ] Record special instructions in the shift log
  [ ] Verify emergency contact roster is current
  [ ] Hand the board over with every commitment stated

Reference: BSP 010-100-000 (Shift Turnover Procedures)

Type 'handoff relieve' to sign off. The service index is banked against
this shift and the next one starts on a fresh board."""

        if args and args[0].lower() in ('relieve', 'signoff', 'end'):
            return self._end_shift()
        return output

    def _end_shift(self) -> str:
        """
        Sign off: bank the index, advance the shift, and start a new board.

        Reports left pending are carried forward, because they were. Anything
        past commitment is still past commitment in the morning.
        """
        banked = self.career.service_index()
        worked = self.shift_time()
        carried = self.desk.pending()
        self.career.end_shift()
        self.current_shift = self.career.shift

        # A new shift starts with its own clock and its own schedule.
        self.shift_minutes = 0
        self._charged_total = sum(report.desk_minutes
                                  for report in self.reports_all())
        self._fired_events = set()
        self.generate_shift_events()

        difficulty = self._difficulty()
        opened = self.desk.open_shift(
            self.clock.now(), difficulty.commitment_slack_minutes)

        lines = [
            f"Relieved. Shift {self.career.shift - 1} closed after "
            f"{worked} worked.",
            '=' * 66,
            f"  Service index banked      {banked:.1f}  "
            f"{self.career.index_band()}",
            f"  Reports closed to date    {self.career.reports_closed}",
            f"  Carried forward           {len(carried)}",
            f"  New on the board          {len(opened)}",
            f"  Shift events              {len(self.shift_events)} scheduled",
            '',
            f"Shift {self.career.shift} begins. "
            f"{len(self.desk.pending())} pending.",
        ]
        if self.career.index_history:
            lines.append('  Index history             '
                         + ', '.join(f"{entry:.1f}"
                                     for entry in
                                     self.career.index_history[-8:]))
        granted = self._grant_qualifications()
        if granted:
            lines.append('')
            lines.extend(granted)
        return '\n'.join(lines)

    def cmd_tariff(self, args: List[str]) -> str:
        """Bell System tariff and rate structure information."""
        rates = self.rate_structures

        if args:
            category = args[0].lower()
            if category not in rates:
                return (f"tariff: Unknown category '{args[0]}'\n"
                        f"Available categories: {', '.join(rates)}")

            output = f"""Bell System Tariff Schedule - {category.title()}
Effective: {self.clock.now().strftime('%B %Y')}
{'=' * 50}

RATE SCHEDULE (per call, station-to-station)
{'=' * 45}
Period/Destination        First Minute    Each Additional
{'-' * 45}"""
            for period, amounts in rates[category].items():
                output += (f"\n{period.title():<24}      ${amounts['first_minute']:>5.2f}"
                           f"          ${amounts['additional']:>5.2f}")
            output += """

Rates shown are for direct-dialed station-to-station calls.
Operator-assisted calls carry an additional service charge.

Reference: FCC Tariff No. 263 (Interstate)"""
            return output

        output = f"""Bell System Tariff and Rate Structures
Effective: {self.clock.now().strftime('%B %Y')}
{'=' * 50}

RATE CATEGORIES
{'=' * 45}"""
        for category, periods in rates.items():
            output += f"\n\n{category.upper()}"
            for period, amounts in periods.items():
                output += (f"\n  {period.title():<14} "
                           f"${amounts['first_minute']:.2f} first minute, "
                           f"${amounts['additional']:.2f} additional")

        output += """

RATE PERIODS
=============================================
Day:              8:00 AM - 5:00 PM weekdays
Evening:          5:00 PM - 11:00 PM daily
Night/Weekend:    11:00 PM - 8:00 AM, all day Saturday,
                  Sunday until 5:00 PM

Usage: tariff <category>   Detailed schedule for one category

Reference: FCC Tariff No. 263 (Interstate)
           State commission tariffs (Intrastate)"""
        return output

    def cmd_events(self, args: List[str]) -> str:
        """Bell System operational events and shift activity"""
        if not args:
            output = [f"Bell System Operational Events - Shift {self.current_shift}"]
            output.append("=" * 55)
            output.append("")

            for i, event in enumerate(self.shift_events, 1):
                priority_marker = "*** " if event["priority"] == "CRITICAL" else "** " if event["priority"] == "HIGH" else "* " if event["priority"] == "MEDIUM" else ""
                output.append(f"{i:2d}. {event['time']} [{event['type']}] {priority_marker}{event['status']}")
                output.append(f"    {event['title']}")
                output.append(f"    Event ID: {event['id']}")
                output.append("")

            output.append("Commands:")
            output.append("  events detail <event_id>     - View detailed event information")
            output.append("  events work <event_id>       - Work on specific event")
            output.append("  events priority <level>      - Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)")
            output.append("  events status <status>       - Filter by status")
            output.append("")
            return "\n".join(output)

        elif args[0] == "detail" and len(args) > 1:
            event_id = args[1].upper()
            event = next((e for e in self.shift_events if e["id"] == event_id), None)

            if not event:
                return f"Event {event_id} not found. Use 'events' to see available events."

            output = [f"BELL SYSTEM EVENT DETAILS: {event['id']}"]
            output.append("=" * 50)
            output.append("")
            output.append(f"Time:        {event['time']}")
            output.append(f"Type:        {event['type']}")
            output.append(f"Priority:    {event['priority']}")
            output.append(f"Status:      {event['status']}")
            output.append(f"Title:       {event['title']}")
            output.append("")
            output.append("Description:")
            output.append(f"  {event['description']}")
            output.append("")
            output.append("Details:")
            output.append(f"  {event['details']}")
            output.append("")
            output.append("Recommended Actions:")
            for i, action in enumerate(event['actions'], 1):
                output.append(f"  {i}. {action}")
            output.append("")
            output.append(f"Use 'events work {event_id}' to begin working this event")
            output.append("")
            return "\n".join(output)

        elif args[0] == "work" and len(args) > 1:
            event_id = args[1].upper()
            event = next((e for e in self.shift_events if e["id"] == event_id), None)

            if not event:
                return f"Event {event_id} not found. Use 'events' to see available events."

            # Update event status to indicate work started
            event["status"] = "IN_PROGRESS"

            output = [f"WORKING EVENT: {event['id']} - {event['title']}"]
            output.append("=" * 60)
            output.append("")
            output.append(f"Event Type: {event['type']}")
            output.append(f"Priority: {event['priority']}")
            output.append("")
            output.append("WORK LOG INITIATED:")
            output.append(f"  {self.clock.now().strftime('%H:%M')} - Work started by {self.username}")
            output.append(f"  {self.clock.now().strftime('%H:%M')} - Reviewing event details and recommended actions")
            output.append("")
            output.append("NEXT STEPS:")
            for i, action in enumerate(event['actions'], 1):
                output.append(f"  {i}. {action}")
            output.append("")

            # Role-specific guidance
            role_guidance = {
                "radio": "Use 'radio' commands to investigate microwave path issues",
                "switch": "Use 'switch' and '3a' commands for switching system problems",
                "noc": "Coordinate with other teams and monitor network impact",
                "field": "Dispatch field technicians and coordinate on-site activities",
                "sysop": "Check system logs and coordinate with development teams"
            }

            if self.role in role_guidance:
                output.append("Role-Specific Guidance:")
                output.append(f"  {role_guidance[self.role]}")
                output.append("")

            output.append("Use relevant Bell System commands to investigate and resolve this event.")
            output.append("Document progress with 'ticket create' if escalation needed.")
            output.append("")
            return "\n".join(output)

        elif args[0] == "priority" and len(args) > 1:
            priority = args[1].upper()
            filtered_events = [e for e in self.shift_events if e["priority"] == priority]

            if not filtered_events:
                return f"No events found with priority '{priority}'"

            output = [f"Events with Priority: {priority}"]
            output.append("=" * 40)
            output.append("")
            for event in filtered_events:
                output.append(f"{event['time']} [{event['type']}] {event['status']}")
                output.append(f"  {event['title']}")
                output.append(f"  Event ID: {event['id']}")
                output.append("")

            return "\n".join(output)

        elif args[0] == "status" and len(args) > 1:
            status = args[1].upper()
            filtered_events = [e for e in self.shift_events if e["status"] == status]

            if not filtered_events:
                return f"No events found with status '{status}'"

            output = [f"Events with Status: {status}"]
            output.append("=" * 40)
            output.append("")
            for event in filtered_events:
                output.append(f"{event['time']} [{event['type']}] {event['priority']}")
                output.append(f"  {event['title']}")
                output.append(f"  Event ID: {event['id']}")
                output.append("")

            return "\n".join(output)

        else:
            return f"events: unknown option '{args[0]}'\nUse 'events' for available commands"

    def cmd_training(self, args: List[str]) -> str:
        """Bell System training programs and procedures"""
        return self._subsystem_unavailable("training", "Training programs")

    # Enhanced commands
    def cmd_5ess(self, args: List[str]) -> str:
        """5ESS Electronic Switching System operations"""
        return self._subsystem_unavailable("5ess", "5ESS operations")

    def cmd_western(self, args: List[str]) -> str:
        """Western Electric equipment specifications"""
        return self._subsystem_unavailable("western", "Western Electric equipment")

    def cmd_coer(self, args: List[str]) -> str:
        """Central Office Equipment Reports"""
        return self._subsystem_unavailable("coer", "COER reporting")

    def cmd_lmos(self, args: List[str]) -> str:
        """Loop Maintenance Operations System"""
        return self._subsystem_unavailable("lmos", "LMOS operations")

    def cmd_sarts(self, args: List[str]) -> str:
        """Special service remote testing"""
        return self._subsystem_unavailable("sarts", "SARTS testing")

    def cmd_radio(self, args: List[str]) -> str:
        """TH-3 microwave radio system monitoring and maintenance"""
        if not args:
            return """TH-3 Microwave Radio System Management
Bell System Long-Haul Radio Network

Available Commands:
  radio status         - System status and performance overview
  radio path <route>   - Analyze specific radio path performance
  radio fade           - Fade margin analysis and monitoring
  radio diversity      - Diversity switching status and control
  radio alignment      - Antenna alignment procedures
  radio maintenance    - Maintenance schedules and procedures
  radio propagation    - Propagation analysis and predictions
  radio interference   - Interference detection and mitigation
  radio power          - Transmitter power monitoring
  radio frequency      - Frequency coordination and management
  radio weather        - Weather impact assessment
  radio backup         - Backup path and diversity routing

Current Network Status:
  Radio Paths Active:           347 of 351 (98.9%)
  Total Route Miles:            47,293 miles
  System Availability:          99.97%
  Average Fade Margin:          32.4 dB

Current Radio Paths:
  NYC-WAS-001:         NORMAL    RSL: -42 dBm    Fade Margin: 31 dB
  NYC-BOS-002:         FADE      RSL: -67 dBm    Diversity Active
  WAS-ATL-003:         NORMAL    RSL: -38 dBm    Fade Margin: 35 dB
  CHI-DET-004:         MAINT     Scheduled alignment 14:30

Project References: TP-8311 (Microwave Radio Diversity Implementation)
Work Orders: WO-83051 (TH-3 microwave system alignment)"""

        elif args[0] == "status":
            return """TH-3 Microwave Radio System Status
November 14, 1983 07:45:30

Network Overview:
  Total Radio Sites:            1,247 sites
  Active Radio Paths:           347 paths
  Total Circuit Capacity:       184,320 voice circuits
  Current Utilization:          73.8%

Performance Metrics (24-hour period):
  System Availability:          99.97%
  Path Outages:                 2 (< 30 seconds each)
  Diversity Switches:           47 activations
  Maintenance Actions:          8 completed

Path Performance Summary:
  NYC-WAS Corridor:            99.99% availability
  CHI-STL Route:               99.98% availability
  LAX-SFO Path:                99.95% availability
  BOS-NYC Link:                99.99% availability

Current Weather Impact:
  High Pressure System:        Excellent propagation
  Rain Activity:               Minimal (< 2mm/hr)
  Atmospheric Ducting:         None detected
  Fade Predictions:            Normal conditions

Equipment Status:
  Transmitter Power:           Normal (all sites)
  Receiver Sensitivity:       Within specifications
  Antenna Pointing:           Optimal alignment
  Diversity Equipment:        OPERATIONAL

Alerts:
  SITE-147: Backup power test scheduled 14:00
  PATH-23: Fade margin below threshold (monitoring)
  ROUTE-89: Scheduled maintenance 11/15/83"""

        elif args[0] == "path" and len(args) > 1:
            route = args[1].upper()
            return f"""TH-3 Radio Path Analysis: {route}
Analysis Time: November 14, 1983 07:45:45

Path Configuration:
  Route Distance:              89.3 miles
  Number of Hops:              4 hops
  Frequency Band:              6 GHz
  Channel Capacity:            1,800 voice circuits

Current Performance:
  Received Signal Level:       -42.3 dBm
  Fade Margin:                 31.7 dB (Excellent)
  Bit Error Rate:              < 10^-9
  Path Availability:           99.98% (30-day average)

Hop-by-Hop Analysis:
  Hop 1 (Terminal-Relay1):     31.2 miles, -38.4 dBm, 34.1 dB margin
  Hop 2 (Relay1-Relay2):      28.7 miles, -41.2 dBm, 29.8 dB margin
  Hop 3 (Relay2-Relay3):      15.8 miles, -35.6 dBm, 36.7 dB margin
  Hop 4 (Relay3-Terminal):    13.6 miles, -33.9 dBm, 38.2 dB margin

Weather Sensitivity:
  Rain Fade Threshold:         15 mm/hr
  Atmospheric Fade Risk:       Low
  Multipath Probability:       0.02%

Diversity Protection:
  Space Diversity:             ACTIVE (all hops)
  Frequency Diversity:         STANDBY
  Route Diversity:             Available via ROUTE-47

Maintenance History:
  Last Alignment:              1983-10-15
  Next Scheduled:              1983-12-15
  Performance Trend:           STABLE"""

        elif args[0] == "fade":
            return """TH-3 Radio Fade Analysis
Real-time Fade Monitoring System

Current Fade Events:
  PATH NYC-WAS-001:           Normal operation (31.2 dB margin)
  PATH NYC-BOS-002:           FADE EVENT - Space diversity active
    Current RSL:              -67.4 dBm
    Fade Depth:               25.1 dB
    Duration:                 47 seconds
    Diversity Switch:         Automatic at 09:23:15

  PATH WAS-ATL-003:           Normal operation (35.1 dB margin)
  PATH CHI-DET-004:           Maintenance mode

Fade Statistics (24-hour period):
  Total Fade Events:           23 events
  Average Duration:            12.3 seconds
  Maximum Fade Depth:          28.7 dB
  Diversity Activations:       18 successful

Weather Correlation:
  Current Conditions:         Clear, high pressure
  Rain Rate:                  0.0 mm/hr
  Atmospheric Conditions:     Stable
  K-Factor:                   1.33 (normal)

Fade Predictions:
  Next 6 hours:               Stable conditions expected
  Weather Front:              Approaching from west (18:00 EST)
  Rain Fade Risk:             Low to moderate after 20:00

Use 'radio weather' for detailed meteorological analysis"""

        elif args[0] == "diversity":
            return """TH-3 Diversity System Status
Space and Frequency Diversity Operations

System Overview:
  Total Diversity Sites:       156 sites equipped
  Space Diversity:             ACTIVE on all critical paths
  Frequency Diversity:         Available on 23 paths
  Route Diversity:             12 alternate routes available

Current Diversity Activity:
  Active Switches:             3 paths currently on diversity

  NYC-BOS-002 (Space Diversity):
    Main Path RSL:             -67.4 dBm (fade condition)
    Diversity Path RSL:        -43.2 dBm (normal)
    Switch Status:             DIVERSITY ACTIVE
    Switch Time:               09:23:15

  LAX-SFO-007 (Frequency Diversity):
    Primary Frequency:         6,175 MHz - Normal
    Backup Frequency:          6,475 MHz - Standby
    Protection Status:         PROTECTED

  CHI-STL-012 (Route Diversity):
    Primary Route:             Direct path - Normal
    Alternate Route:           Via MIL relay - Available

Diversity Performance:
  Switch Success Rate:         99.97%
  Average Switch Time:         < 50 milliseconds
  Failed Switches (30-day):    2 events

Protection Thresholds:
  Space Diversity:             -58 dBm
  Frequency Diversity:         -62 dBm
  Automatic Switch:            ENABLED
  Manual Override:             Available

Use 'radio path <route>' for specific diversity analysis"""

        elif args[0] == "alignment":
            return """TH-3 Antenna Alignment Procedures
Microwave Antenna Pointing and Optimization

Scheduled Alignments Today:
  SITE-CHI-004:               14:30 - Quarterly maintenance
  SITE-DET-007:               16:00 - Performance optimization

Alignment Status:
  Last 30 Days:               47 sites aligned
  Performance Improvement:    Average 2.3 dB gain
  Alignment Accuracy:         ±0.1 degree achieved

Alignment Procedure Checklist:
  1. Weather Assessment:       Clear conditions required
  2. Traffic Coordination:     Low-traffic period preferred
  3. Equipment Preparation:    Alignment tools calibrated
  4. Safety Procedures:        Tower safety protocol active
  5. Backup Planning:          Diversity/alternate route ready

Current Site Conditions:
  SITE-CHI-004:
    Current Pointing:          247.3° azimuth, 1.2° elevation
    Signal Strength:           -44.7 dBm
    Optimization Target:       -42.0 dBm (2.7 dB improvement)
    Weather:                   Clear, wind 8 mph
    Safety Status:             CLEARED for maintenance

Alignment Tools Required:
  - Precision inclinometer
  - Signal level meter
  - Tower safety equipment
  - Backup communication link

Coordination Required:
  - NOC notification (traffic rerouting)
  - Field maintenance team dispatch
  - Safety coordinator approval

Use 'radio maintenance' for detailed procedures"""

        elif args[0] == "maintenance":
            return """TH-3 Radio System Maintenance
Preventive and Corrective Maintenance Operations

Today's Maintenance Schedule:
  09:00 - SITE-NYC-001:      Monthly transmitter calibration
  14:30 - SITE-CHI-004:      Antenna alignment (TP-8311)
  16:00 - SITE-DET-007:      Waveguide inspection
  22:00 - SITE-BOS-003:      Backup power system test

Maintenance Categories:
  PREVENTIVE (Scheduled):
    Quarterly:                Antenna alignment, waveguide checks
    Monthly:                  Transmitter calibration, power supplies
    Weekly:                   Site inspections, alarm tests
    Daily:                    Performance monitoring, log review

  CORRECTIVE (As Required):
    Equipment Failures:       Component replacement, repair
    Performance Degradation:  Optimization, troubleshooting
    Weather Damage:           Storm repair, realignment

Current Maintenance Tickets:
  WO-83051: TH-3 microwave system alignment
    Sites: 12 locations
    Priority: MEDIUM
    Completion: 85%

  WO-83052: Waveguide pressurization system
    Sites: 8 locations
    Priority: HIGH
    Completion: 60%

Equipment Status:
  Transmitters:               98.7% operational
  Receivers:                  99.2% operational
  Antennas:                   97.8% optimal alignment
  Waveguides:                 99.1% pressurized
  Power Systems:              99.4% operational

Spare Parts Inventory:
  Transmitter Modules:        23 units available
  Receiver Components:        67 units available
  Waveguide Sections:         12 units available
  Antenna Hardware:           Available per requirements

Use 'radio power' for transmitter details
Use 'radio weather' for environmental impact assessment"""

        elif args[0] == "weather":
            return """TH-3 Radio Weather Impact Assessment
Meteorological Analysis for Microwave Propagation

Current Weather Conditions:
  Temperature:                 47°F (8°C)
  Humidity:                    62%
  Barometric Pressure:         30.15 inches Hg (rising)
  Wind Speed:                  8 mph, gusting to 12 mph
  Visibility:                  10+ miles

Propagation Conditions:
  Atmospheric Stability:       STABLE
  K-Factor:                    1.33 (normal propagation)
  Refractive Index:            315 N-units (standard)
  Multipath Activity:          MINIMAL

Weather Impact on Paths:
  NYC-WAS-001:                NO IMPACT - Clear path
  NYC-BOS-002:                MINIMAL - Light haze
  WAS-ATL-003:                NO IMPACT - Excellent conditions
  CHI-DET-004:                NO IMPACT - Clear and cool

6-Hour Forecast:
  14:00-16:00:                Continued stable conditions
  16:00-18:00:                Possible light cloud development
  18:00-20:00:                Weather front approaching from west

Fade Risk Assessment:
  Rain Fade Risk:             LOW (0-10% probability)
  Atmospheric Fade Risk:      LOW (stable conditions)
  Multipath Risk:             MINIMAL (good K-factor)

Historical Weather Impact:
  Rain Fade Events (30-day):  12 events
  Average Duration:           8.3 minutes
  Maximum Fade Depth:         31.2 dB
  Recovery Rate:              99.8%

Critical Weather Thresholds:
  Rain Rate for Fade:         > 8 mm/hr
  K-Factor Limit:             < 0.8 or > 1.8
  Temperature Gradient:       > 4°C per 100m

Weather Monitoring:
  Automatic Stations:         47 locations
  Manual Observations:        12 locations
  Radar Integration:          NOAA WSR-74 network
  Forecast Updates:           Every 3 hours

Use 'radio fade' for current fade event analysis"""

        elif args[0] == "power":
            return """TH-3 Transmitter Power Monitoring
RF Power Output and Performance Analysis

System Power Status:
  Total Transmitters:         347 units
  Operational:                342 units (98.6%)
  Reduced Power:              3 units (maintenance)
  Out of Service:             2 units (repair)

Power Output Monitoring:
  NYC-WAS-001:               +37.2 dBm (nominal +37.0 dBm)
  NYC-BOS-002:               +36.8 dBm (nominal +37.0 dBm)
  WAS-ATL-003:               +37.1 dBm (nominal +37.0 dBm)
  CHI-DET-004:               MAINTENANCE MODE

Power System Performance:
  Average Output Power:       36.95 dBm
  Power Stability:            ±0.2 dB (excellent)
  Amplifier Efficiency:       47.3%
  Heat Dissipation:           Normal (all sites)

Power Supply Systems:
  Primary AC Power:           NORMAL (all sites)
  Battery Backup:             TESTED (monthly cycle)
  Engine Generators:          AVAILABLE (12 sites)
  Uninterruptible Power:      OPERATIONAL

Recent Power Events:
  SITE-BOS-003:              Power reduction to 75% (cooling issue)
    Status:                   Repair scheduled 22:00
    Impact:                   Minimal (diversity available)

  SITE-LAX-009:              Transmitter replacement
    Status:                   New unit installed 11/12/83
    Performance:              Exceeds specifications

Power Quality Monitoring:
  Voltage Regulation:         ±2% (within spec)
  Frequency Stability:        ±0.1 Hz (excellent)
  Harmonic Distortion:        < 1% (all transmitters)

Alarm Thresholds:
  Low Power Warning:          < 90% of nominal
  Critical Power Alarm:       < 80% of nominal
  Automatic Shutdown:         < 70% of nominal

Power Optimization:
  Automatic Level Control:    ACTIVE (all transmitters)
  Temperature Compensation:   ENABLED
  Aging Compensation:         ACTIVE

Use 'radio maintenance' for power system maintenance
Use 'radio alignment' for antenna optimization"""

        else:
            return f"Unknown radio command: {args[0]}\nUse 'radio' for available options"

    def cmd_microwave(self, args: List[str]) -> str:
        """Microwave system analysis"""
        return self._subsystem_unavailable("microwave", "Microwave analysis")

    def cmd_satellite(self, args: List[str]) -> str:
        """Satellite communication links"""
        return self._subsystem_unavailable("satellite", "Satellite operations")

    def cmd_alarm(self, args: List[str]) -> str:
        """Central office alarm monitoring and acknowledgement."""
        health = self.system_health

        if args and args[0] == "ack" and len(args) > 1:
            alarm_id = args[1].upper()
            for alarm in self.active_alarms:
                if alarm["id"] == alarm_id:
                    if alarm["acknowledged"]:
                        return f"alarm: {alarm_id} was already acknowledged."
                    alarm["acknowledged"] = True
                    return f"""Alarm Acknowledged
{'=' * 45}
Alarm:            {alarm_id}
Type:             {alarm['type']}
Severity:         {alarm['severity']}
System:           {alarm['system']}
Acknowledged By:  {self.username}
Time:             {self.clock.now().strftime('%B %d, %Y %H:%M EST')}

The alarm remains active until the condition clears."""
            return f"alarm: No active alarm with identifier '{alarm_id}'"

        if args and args[0] not in ("status", "list"):
            return ("alarm: Unknown option '%s'\n"
                    "Available commands: status, list, ack <alarm-id>" % args[0])

        output = f"""Bell System Central Office Alarm Monitor
{self.clock.now().strftime('%B %d, %Y %H:%M EST')}
{'=' * 50}

SYSTEM HEALTH
{'=' * 40}
Overall Status:           {health['overall_status']}
Critical Alarms:          {health['critical_alarms']}
Major Alarms:             {health['major_alarms']}
Minor Alarms:             {health['minor_alarms']}
Continuous Uptime:        {health['uptime_days']} days
Last Service Outage:      {health['last_outage'].strftime('%B %d, %Y')}

ACTIVE ALARMS
{'=' * 40}"""

        if not self.active_alarms:
            output += "\nNo active alarms. All monitored systems normal."
        else:
            for alarm in sorted(
                self.active_alarms,
                key=lambda a: {'CRITICAL': 0, 'MAJOR': 1, 'MINOR': 2}[a['severity']]
            ):
                age = int((self.clock.now() - alarm['timestamp']).total_seconds() / 60)
                output += f"""
{alarm['id']} [{alarm['severity']}]
  Type:               {alarm['type']}
  System:             {alarm['system']}
  Condition:          {alarm['description']}
  Raised:             {alarm['timestamp'].strftime('%H:%M EST')} ({age} minutes ago)
  Acknowledged:       {'YES' if alarm['acknowledged'] else 'NO - REQUIRES ATTENTION'}"""

        unacknowledged = [a for a in self.active_alarms if not a['acknowledged']]
        output += f"""

SUMMARY
{'=' * 40}
Total Active:             {len(self.active_alarms)}
Awaiting Acknowledgement: {len(unacknowledged)}

Commands:
  alarm status              Show this display
  alarm ack <alarm-id>      Acknowledge an alarm

Reference: BSP 660-100-000 (Alarm Surveillance)"""
        return output

    def cmd_pwb(self, args: List[str]) -> str:
        """Programmer's Workbench operations"""
        return self._subsystem_unavailable("pwb", "PWB operations")

    def cmd_rje(self, args: List[str]) -> str:
        """Remote Job Entry system"""
        return self._subsystem_unavailable("rje", "RJE operations")

    # Document preparation commands
    def cmd_nroff(self, args: List[str]) -> str:
        """Document formatting with nroff"""
        return self._subsystem_unavailable("nroff", "nroff text processing")

    def cmd_troff(self, args: List[str]) -> str:
        """Typesetting with troff"""
        return self._subsystem_unavailable("troff", "troff typesetting")

    def cmd_tbl(self, args: List[str]) -> str:
        """Table formatting preprocessor"""
        return self._subsystem_unavailable("tbl", "Table formatting")

    def cmd_eqn(self, args: List[str]) -> str:
        """Mathematical equation formatting"""
        return self._subsystem_unavailable("eqn", "Equation formatting")

    def cmd_pic(self, args: List[str]) -> str:
        """Picture drawing language"""
        return self._subsystem_unavailable("pic", "Picture drawing")

    def cmd_refer(self, args: List[str]) -> str:
        """Bibliography and reference management"""
        return self._subsystem_unavailable("refer", "Reference management")

    def cmd_netdata(self, args: List[str]) -> str:
        """Network data collection tools"""
        return self._subsystem_unavailable("netdata", "Network data tools")

    def cmd_analysis(self, args: List[str]) -> str:
        """Advanced network analysis and modeling"""
        return self._subsystem_unavailable("analysis", "Network analysis")

    def cmd_t1carrier(self, args: List[str]) -> str:
        """T1 Digital Carrier System Operations"""
        if not args:
            return """T1 Digital Carrier System Management
Bell System Digital Transmission Hierarchy

Available Commands:
  t1carrier status         - System overview and DS-1 circuits
  t1carrier test <ds1>     - Digital circuit testing procedures
  t1carrier multiplex     - Digital multiplexing hierarchy
  t1carrier regenerator   - Regenerator status and maintenance
  t1carrier sync          - Timing and synchronization
  t1carrier performance   - Performance monitoring and analysis
  t1carrier alarm         - Alarm status and error analysis
  t1carrier provision     - Circuit provisioning procedures

Current Digital Hierarchy Status:
  DS-1 Circuits (1.544 Mbps):     2,347 active
  DS-2 Circuits (6.312 Mbps):     156 active
  DS-3 Circuits (44.736 Mbps):    23 active

Performance Summary:
  Bit Error Rate:              < 10^-9 (all circuits)
  Slip Rate:                   < 1 per day
  Availability:                99.95% (monthly average)

Reference: Western Electric T1 Carrier System Technical Manual"""

        elif args[0] == "status":
            return """T1 Digital Carrier System Status
November 14, 1983 07:45:30

DS-1 Circuit Status (1.544 Mbps):
  DS1-NYC-WAS-001:            ACTIVE    BER: < 10^-9    No alarms
  DS1-NYC-BOS-002:            ACTIVE    BER: 2.3x10^-8  Minor alarm (B8ZS)
  DS1-WAS-ATL-003:            ACTIVE    BER: < 10^-9    No alarms
  DS1-CHI-DET-004:            TESTING   Loop-back test in progress
  DS1-LAX-SFO-005:            ACTIVE    BER: < 10^-9    No alarms

Digital Signal Hierarchy:
  DS-0 (64 kbps):             Voice channel fundamental rate
  DS-1 (1.544 Mbps):          24 DS-0 channels + framing
  DS-2 (6.312 Mbps):          4 DS-1 signals multiplexed
  DS-3 (44.736 Mbps):         7 DS-2 signals multiplexed

M12 Multiplexer Status:
  M12-NYC-001:                OPERATIONAL (4 DS-1 → 1 DS-2)
  M12-BOS-002:                OPERATIONAL (4 DS-1 → 1 DS-2)
  M12-WAS-003:                MAINTENANCE (Scheduled 14:30)

M23 Multiplexer Status:
  M23-NYC-001:                OPERATIONAL (7 DS-2 → 1 DS-3)
  M23-CHI-001:                OPERATIONAL (7 DS-2 → 1 DS-3)

Regenerator Status:
  Line Regenerators:          1,247 units operational
  Terminal Equipment:         156 units operational
  Timing Sources:             All synchronized to LORAN-C

Performance Monitoring:
  Error Seconds (ES):         < 0.01% (excellent)
  Severely Errored Seconds:   0 events (24-hour period)
  Unavailable Seconds:        < 10 seconds total"""

        elif args[0] == "test" and len(args) > 1:
            circuit = args[1].upper()
            return f"""T1 Digital Circuit Test: {circuit}
Test Sequence Initiated: November 14, 1983 07:46:00

Circuit Configuration:
  Circuit Type:               DS-1 (1.544 Mbps)
  Line Code:                  B8ZS (Bipolar 8-Zero Substitution)
  Framing Format:             Extended Superframe (ESF)
  Interface:                  DSX-1 cross-connect

Test Procedures:
  1. Loop-back Test:          [████████████████████] COMPLETE
     Near-end loop:           PASS - No errors detected
     Far-end loop:            PASS - Pattern integrity verified

  2. Bit Error Rate Test:     [████████████████████] COMPLETE
     Test Pattern:            2^15-1 PRBS (Pseudo Random)
     Duration:                15 minutes
     BER Result:              < 10^-9 (Excellent)

  3. Jitter Measurement:      [████████████████████] COMPLETE
     Peak-to-peak jitter:     0.05 UI (within spec < 0.28 UI)
     RMS jitter:              0.02 UI (excellent)

  4. Signal Level Test:       [████████████████████] COMPLETE
     Transmit level:          +12.0 dBm (nominal +13 dBm)
     Receive level:           -8.5 dBm (nominal -7.5 dBm)

  5. Alarm Generation Test:   [██████████████░░░░░] IN PROGRESS
     AIS insertion:           Testing alarm propagation
     Yellow alarm:            Verifying upstream notification

Test Results Summary:
  Overall Performance:        EXCELLENT
  Circuit Quality:            Meets all specifications
  Recommended Action:         Return to service

Next Test Scheduled:         November 21, 1983 02:00"""

        elif args[0] == "multiplex":
            return """Digital Multiplexing Hierarchy
Bell System Digital Signal Standards

Digital Signal Levels:
  DS-0:    64 kbps     (Voice channel - 8-bit PCM, 8 kHz sampling)
  DS-1:    1.544 Mbps  (24 DS-0 + 8 kbps framing)
  DS-2:    6.312 Mbps  (4 DS-1 + stuffing bits)
  DS-3:    44.736 Mbps (7 DS-2 + overhead)
  DS-4:    274.176 Mbps (6 DS-3 + overhead) [Future implementation]

M12 Multiplexer Operations:
  Function:                   Combine 4 DS-1 signals into 1 DS-2
  Bit Stuffing:               Asynchronous multiplexing
  Stuff Ratio:                Average 1.2% overhead

  Active M12 Units:
    M12-NYC-001:              Input: 4 DS-1, Output: DS-2 #47
    M12-BOS-002:              Input: 4 DS-1, Output: DS-2 #48
    M12-WAS-003:              Input: 4 DS-1, Output: DS-2 #49

M23 Multiplexer Operations:
  Function:                   Combine 7 DS-2 signals into 1 DS-3
  Bit Stuffing:               Positive/negative stuffing
  Stuff Ratio:                Average 2.1% overhead

  Active M23 Units:
    M23-NYC-001:              Input: 7 DS-2, Output: DS-3 #12
    M23-CHI-001:              Input: 7 DS-2, Output: DS-3 #13

Multiplexing Performance:
  Stuff Jitter:               < 0.1 UI (all multiplexers)
  Pattern Jitter:             < 0.05 UI (excellent)
  Frequency Accuracy:         ±32 ppm (within ±50 ppm spec)

Synchronization:
  Master Clock:               LORAN-C referenced
  Clock Accuracy:             ±1 x 10^-11 (cesium standard)
  Distribution:               Stratum 1 → Stratum 2 → Stratum 3

Use 't1carrier sync' for detailed timing information"""

        elif args[0] == "regenerator":
            return """T1 Digital Regenerator System
Line and Terminal Equipment Status

Regenerator Functions:
  Signal Detection:           Extract timing and data
  Retiming:                   Eliminate accumulated jitter
  Reshaping:                  Restore pulse amplitude
  Regeneration:               Output clean digital signal

Line Regenerator Status:
  REG-NYC-WAS-001-R47:       OPERATIONAL - Signal: -18.2 dBm
  REG-NYC-WAS-001-R48:       OPERATIONAL - Signal: -19.1 dBm
  REG-NYC-BOS-002-R23:       OPERATIONAL - Signal: -17.8 dBm
  REG-WAS-ATL-003-R56:       MAINTENANCE - Scheduled PM

Performance Parameters:
  Input Sensitivity:          -36 dBm (minimum detectable)
  Output Level:               +13 dBm (nominal DS-1 level)
  Jitter Accumulation:        < 0.01 UI per regenerator
  Bit Error Rate:             < 10^-12 (regenerator contribution)

Terminal Equipment:
  Channel Service Unit (CSU): 156 units operational
  Data Service Unit (DSU):    89 units operational
  Office Channel Unit (OCU):  234 units operational

Regenerator Spacing:
  T1 Cable (22 AWG):          6,000 feet maximum
  T1 Cable (19 AWG):          9,000 feet maximum
  Environmental Limits:       -40°F to +140°F operating

Maintenance Status:
  Last PM Cycle:              47 regenerators completed
  Performance Degradation:    0 units flagged
  Spare Units Available:      23 units (central stock)

Power Systems:
  -130V DC Distribution:      NORMAL (all regenerators)
  Current Consumption:        Average 47 mA per unit
  Alarm Monitoring:           Remote monitoring active

Testing Procedures:
  Monthly:                    Signal level verification
  Quarterly:                  BER performance testing
  Annually:                   Environmental stress testing"""

        elif args[0] == "sync":
            return """T1 Network Synchronization
Digital Timing Hierarchy and Distribution

Network Timing Standards:
  Stratum 1:                  ±1 x 10^-11 accuracy (cesium)
  Stratum 2:                  ±1.6 x 10^-8 accuracy
  Stratum 3:                  ±4.6 x 10^-6 accuracy
  Stratum 4:                  ±32 x 10^-6 accuracy

Current Synchronization Status:
  Primary Reference:          LORAN-C Navigation System
  Secondary Reference:        Cesium beam standard (backup)
  Distribution Method:        Through digital hierarchy

Timing Distribution:
  Master Clock (Stratum 1):   AT&T Network Operations Center
    Location:                 Hillsboro, New Jersey
    Accuracy:                 ±1 x 10^-11
    Distribution:             Via DS-1 timing signals

  Regional Clocks (Stratum 2):
    NYC Regional Center:      Synchronized, tracking normal
    CHI Regional Center:      Synchronized, tracking normal
    LAX Regional Center:      Synchronized, tracking normal

  Local Office Clocks (Stratum 3):
    NYC Central Office:       Synchronized, ±2.1 x 10^-6 drift
    BOS Central Office:       Synchronized, ±1.8 x 10^-6 drift
    WAS Central Office:       Synchronized, ±3.2 x 10^-6 drift

Synchronization Methods:
  Through-Timing:             DS-1 signals carry timing
  External Timing:            Separate timing distribution
  Loop Timing:                Terminal derives from line

Performance Monitoring:
  Slip Events (24-hour):      0 controlled slips
  Timing Errors:              No events detected
  Clock Drift:                All within specifications

Slip Control:
  Controlled Slip Rate:       < 1 slip per 72 days (target)
  Slip Buffer Depth:          ±2 frame positions
  Slip Indication:            Yellow alarm generation

LORAN-C Reception:
  Signal Strength:            40 dB above noise floor
  Time Difference:            Tracking within 0.1 microsecond
  Chain Selection:            Northeast U.S. Chain (9960)

Backup Timing:
  Cesium Standard:            Available (automatic switchover)
  GPS Timing:                 Under evaluation [Future]
  Rubidium Standards:         Local office backup"""

        else:
            return f"t1carrier: unknown option '{args[0]}'\nUse 't1carrier' for available commands"

    def cmd_lcarrier(self, args: List[str]) -> str:
        """L-Carrier Coaxial Cable System Operations"""
        if not args:
            return """L-Carrier Coaxial Cable System Management
Bell System Analog Long-Haul Transmission

Available Commands:
  lcarrier status          - System overview and route status
  lcarrier test <route>    - Coaxial cable testing procedures
  lcarrier repeater        - Repeater status and maintenance
  lcarrier equalizer       - Equalization and frequency response
  lcarrier pilot           - Pilot tone monitoring and control
  lcarrier temperature     - Cable temperature monitoring
  lcarrier fault           - Fault location and analysis

Current L-Carrier Routes:
  L3 Systems (1860 circuits):     23 routes operational
  L4 Systems (3600 circuits):     47 routes operational
  L5 Systems (10800 circuits):    12 routes operational

Performance Summary:
  Noise Level:                43 dBrnC (excellent)
  Frequency Response:         ±0.5 dB (within spec)
  Cross-talk:                 < -65 dB (all systems)

Reference: Western Electric L-Carrier Technical Manual"""

        elif args[0] == "status":
            return """L-Carrier Coaxial Cable System Status
November 14, 1983 07:45:30

L3 Coaxial Systems (1860 voice circuits):
  L3-NYC-PHL-001:             OPERATIONAL - 1847 circuits active
    Pilot Level:              -20.0 dBm0 (nominal -20 dBm0)
    Noise Level:              42.8 dBrnC (excellent)
    Temperature:              68°F (normal range)

  L3-BOS-NYC-002:             OPERATIONAL - 1854 circuits active
    Pilot Level:              -19.8 dBm0 (nominal -20 dBm0)
    Noise Level:              43.2 dBrnC (good)
    Temperature:              71°F (normal range)

L4 Coaxial Systems (3600 voice circuits):
  L4-NYC-WAS-001:             OPERATIONAL - 3587 circuits active
    Pilot Level:              -20.1 dBm0 (nominal -20 dBm0)
    Noise Level:              41.5 dBrnC (excellent)
    Repeater Status:          47 repeaters operational

  L4-CHI-STL-002:             OPERATIONAL - 3594 circuits active
    Pilot Level:              -19.9 dBm0 (nominal -20 dBm0)
    Noise Level:              42.1 dBrnC (excellent)
    Repeater Status:          39 repeaters operational

L5 Coaxial Systems (10800 voice circuits):
  L5-NYC-CHI-001:             OPERATIONAL - 10,756 circuits active
    Pilot Level:              -20.0 dBm0 (nominal -20 dBm0)
    Noise Level:              40.2 dBrnC (superior)
    Repeater Status:          156 repeaters operational
    Cable Length:             789.3 miles total

System Performance:
  Overall Availability:       99.98% (monthly average)
  Mean Time to Repair:        3.7 hours (system outages)
  Preventive Maintenance:     Schedule compliance 97%

Cable Plant Status:
  Cable Pressure:             All sections pressurized (8.5 psi)
  Moisture Detection:         No moisture alarms
  Sheath Current:             Normal (< 10 mA all cables)

Frequency Allocation:
""" + self._format_carrier_bands()

        elif args[0] == "repeater":
            return """L-Carrier Repeater Status and Operations
Analog Amplification and Equalization

Repeater Functions:
  Amplification:              Restore signal level
  Equalization:               Compensate cable loss
  Regulation:                 Maintain constant output
  Monitoring:                 Performance surveillance

L4 Repeater Status (NYC-WAS Route):
  REP-L4-001 (Mile 23.4):    OPERATIONAL
    Input Level:              -43.2 dBm (pilot tone)
    Output Level:             +7.8 dBm (pilot tone)
    Gain:                     51.0 dB (nominal 51 dB)
    Temperature:              73°F (normal)

  REP-L4-002 (Mile 46.8):    OPERATIONAL
    Input Level:              -42.8 dBm (pilot tone)
    Output Level:             +8.1 dBm (pilot tone)
    Gain:                     50.9 dB (nominal 51 dB)
    Temperature:              69°F (normal)

L5 Repeater Status (NYC-CHI Route):
  REP-L5-001 (Mile 12.1):    OPERATIONAL
    Input Level:              -41.5 dBm (pilot tone)
    Output Level:             +8.5 dBm (pilot tone)
    Gain:                     50.0 dB (nominal 50 dB)
    Temperature:              71°F (normal)
    AGC Range:                ±3 dB (automatic gain control)

Repeater Spacing:
  L3 Systems:                 4 miles (approximate)
  L4 Systems:                 2 miles (approximate)
  L5 Systems:                 1 mile (approximate)

Automatic Gain Control:
  Pilot Tone Frequency:
    L3: 552 kHz               Reference level -20 dBm0
    L4: 1116 kHz              Reference level -20 dBm0
    L5: 564 kHz               Reference level -20 dBm0

  AGC Response Time:          < 100 milliseconds
  Gain Tracking:              ±0.1 dB (temperature compensated)

Maintenance Procedures:
  Monthly Gain Checks:        Scheduled via pilot tone
  Quarterly Alignments:       Frequency response verification
  Annual Overhaul:            Component replacement cycle

Power Systems:
  Remote Powering:            -130V DC via cable center
  Current Consumption:        Average 2.3 A per repeater
  Power Feeding:              From terminal equipment

Environmental Monitoring:
  Temperature Range:          -40°F to +140°F operating
  Humidity:                   0-95% non-condensing
  Vibration:                  MIL-STD-810 compliance"""

        elif args[0] == "test" and len(args) > 1:
            route = args[1].upper()
            return f"""L-Carrier System Test: {route}
Test Sequence Initiated: November 14, 1983 07:46:15

System Configuration:
  Route Type:                 L4 Coaxial Cable System
  Circuit Capacity:           3600 voice channels
  Frequency Range:            564 kHz - 3084 kHz
  Cable Type:                 0.375" coax, foam dielectric

Test Procedures:
  1. Pilot Tone Check:        [████████████████████] COMPLETE
     564 kHz Pilot:           -19.8 dBm0 (nominal -20.0 dBm0)
     1116 kHz Pilot:          -20.2 dBm0 (nominal -20.0 dBm0)
     Result:                  PASS - Levels within ±0.5 dB

  2. Noise Measurement:       [████████████████████] COMPLETE
     C-Message Weighted:      42.1 dBrnC (excellent)
     3 kHz Flat:              47.3 dBrn (good)
     Impulse Noise:           2 counts/15 min (acceptable)

  3. Frequency Response:      [████████████████████] COMPLETE
     300 Hz - 3400 Hz:        ±0.3 dB variation
     Group Delay:             < 1.5 ms (excellent)
     Envelope Delay:          Within specifications

  4. Cross-talk Test:         [████████████████████] COMPLETE
     Near-end cross-talk:     -67.2 dB (excellent)
     Far-end cross-talk:      -71.5 dB (superior)
     Echo return loss:        -28.4 dB (good)

  5. Repeater Gain Test:      [██████████████░░░░░] IN PROGRESS
     Testing 39 repeaters:    Gain stability ±0.1 dB
     Temperature compensation: Active

Test Results Summary:
  Overall Performance:        EXCELLENT
  All Parameters:             Within specifications
  Recommended Action:         Continue normal service

Next Scheduled Test:         November 28, 1983 02:00"""

        elif args[0] == "pilot":
            return """L-Carrier Pilot Tone System
Automatic Level Control and System Monitoring

Pilot Tone Functions:
  Level Control:              Automatic gain regulation
  System Monitoring:          Performance surveillance
  Fault Detection:            Rapid alarm generation
  Temperature Compensation:   Thermal stability

L3 System Pilot Tones:
  552 kHz Pilot:
    Current Level:            -19.9 dBm0 (nominal -20.0 dBm0)
    Regulation Range:         ±3.0 dB
    Response Time:            < 2 seconds

L4 System Pilot Tones:
  564 kHz Pilot (Group 1):    -20.1 dBm0 (nominal -20.0 dBm0)
  1116 kHz Pilot (Group 2):   -19.8 dBm0 (nominal -20.0 dBm0)
  1620 kHz Pilot (Group 3):   -20.2 dBm0 (nominal -20.0 dBm0)

L5 System Pilot Tones:
  564 kHz Master Pilot:       -20.0 dBm0 (nominal -20.0 dBm0)
  8284 kHz Regulation Pilot:  -20.1 dBm0 (nominal -20.0 dBm0)

Automatic Level Regulation:
  Regulation Accuracy:        ±0.1 dB (short term)
  Temperature Stability:      ±0.3 dB (-40°F to +140°F)
  Frequency Stability:        ±1 Hz (crystal controlled)

Alarm Thresholds:
  Minor Alarm:                ±1.0 dB deviation
  Major Alarm:                ±2.0 dB deviation
  Critical Alarm:             ±3.0 dB deviation (system failure)

Current Alarm Status:
  All Systems:                NO ALARMS
  Regulation Status:          NORMAL
  Pilot Continuity:           VERIFIED

Pilot Tone Monitoring:
  Measurement Interval:       Every 6 seconds
  Data Recording:             15-minute averages
  Trend Analysis:             24-hour performance graphs
  Historical Data:            30-day retention"""

        elif args[0] == "fault":
            return """L-Carrier Fault Location System
Cable Fault Detection and Analysis

Fault Location Methods:
  Time Domain Reflectometry:  Cable impedance analysis
  Pilot Tone Interruption:    Service affecting faults
  Sheath Current Monitoring:  Moisture detection
  Temperature Monitoring:     Thermal anomalies

Recent Fault History:
  No active faults detected   (Last 30 days)

Fault Location Equipment:
  TDR Test Set:               Model WE-810A
    Range:                    0-50 miles
    Resolution:               ±25 feet
    Impedance:                75 ohms (coaxial standard)

  Bridge Measurements:
    Cable Resistance:         0.31 ohms/mile (center conductor)
    Cable Capacitance:        21.5 nF/mile (normal)
    Insulation Resistance:    >1000 megohms/mile

Preventive Monitoring:
  Cable Pressure:             8.5 psi (all sections)
  Moisture Indicators:        Dry gas flow normal
  Temperature Sensors:        47 locations monitored
  Sheath Current:             < 5 mA (all cables)

Historical Fault Analysis:
  Cable Cuts (6 months):      2 events (external damage)
  Moisture Intrusion:         0 events
  Equipment Failures:         3 repeater replacements
  Mean Time to Locate:        1.2 hours (cable faults)
  Mean Time to Repair:        4.7 hours (including splicing)

Fault Response Procedures:
  1. Alarm Reception:         Immediate NOC notification
  2. Remote Testing:          TDR and pilot tone analysis
  3. Dispatch Authorization:  Field crew deployment
  4. Fault Location:          Precise distance measurement
  5. Repair Coordination:     Service restoration priority

Emergency Procedures:
  Service Protection:         Automatic rerouting available
  Backup Facilities:          Microwave protection routes
  Repair Priority:            Based on circuit criticality
  Customer Notification:      Automated for major outages"""

        else:
            return f"lcarrier: unknown option '{args[0]}'\nUse 'lcarrier' for available commands"

    def cmd_multiplex(self, args: List[str]) -> str:
        """Digital Multiplexing Operations and Hierarchy Management"""
        if not args:
            return """Digital Multiplexing Operations
Bell System Digital Signal Hierarchy

Available Commands:
  multiplex status         - Overall multiplexing system status
  multiplex m12            - M12 multiplexer operations (DS-1 to DS-2)
  multiplex m23            - M23 multiplexer operations (DS-2 to DS-3)
  multiplex stuff          - Bit stuffing analysis and control
  multiplex alarm          - Multiplexer alarm status
  multiplex test <unit>    - Multiplexer testing procedures
  multiplex sync           - Synchronization and timing

Digital Signal Hierarchy:
  DS-0:    64 kbps         Voice channel (8-bit PCM)
  DS-1:    1.544 Mbps      24 DS-0 + framing (193 bits/frame)
  DS-2:    6.312 Mbps      4 DS-1 + bit stuffing
  DS-3:    44.736 Mbps     7 DS-2 + overhead

Current Multiplexer Status:
  M12 Units:               23 operational
  M23 Units:               8 operational
  Performance:             All within specifications"""

        elif args[0] == "m12":
            return """M12 Multiplexer Operations
DS-1 to DS-2 Digital Multiplexing

M12 Multiplexer Function:
  Input:                      4 independent DS-1 signals (1.544 Mbps each)
  Output:                     1 DS-2 signal (6.312 Mbps)
  Multiplexing:               Asynchronous (bit stuffing)
  Stuff Ratio:                Nominal 1.15% overhead

Active M12 Units:
  M12-NYC-001:
    Input DS-1 #1:            ACTIVE - 1.5440 Mbps, sync normal
    Input DS-1 #2:            ACTIVE - 1.5441 Mbps, sync normal
    Input DS-1 #3:            ACTIVE - 1.5439 Mbps, sync normal
    Input DS-1 #4:            ACTIVE - 1.5440 Mbps, sync normal
    Output DS-2:              ACTIVE - 6.3120 Mbps
    Stuff Rate:               1.12% (normal)

  M12-BOS-002:
    Input DS-1 #1:            ACTIVE - 1.5441 Mbps, sync normal
    Input DS-1 #2:            ACTIVE - 1.5440 Mbps, sync normal
    Input DS-1 #3:            ACTIVE - 1.5442 Mbps, sync normal
    Input DS-1 #4:            ACTIVE - 1.5439 Mbps, sync normal
    Output DS-2:              ACTIVE - 6.3121 Mbps
    Stuff Rate:               1.14% (normal)

Bit Stuffing Operation:
  Justification:              Positive stuffing only
  Stuff Decision:             Made every 4 input bits
  Stuff Indication:           C-bits indicate stuffing
  Buffer Depth:               ±2 bits (elastic store)

Performance Parameters:
  Jitter Accumulation:        < 0.05 UI (output)
  Frequency Accuracy:         ±20 ppm (all inputs accepted)
  Phase Hits:                 < 1 per hour (excellent)
  Bit Error Rate:             < 10^-9 (multiplexer contribution)

Frame Structure:
  Frame Length:               1176 bits (186.3 μs)
  Overhead Bits:              48 bits per frame (4.08%)
  Payload Capacity:           1128 bits per frame
  Framing Pattern:            F0F1F2F3 sequence

Alarm Conditions:
  Loss of Signal (LOS):       Input DS-1 signal failure
  Out of Frame (OOF):         Frame synchronization lost
  AIS Detection:              All-ones pattern received
  Equipment Failure:          Internal multiplexer fault"""

        elif args[0] == "m23":
            return """M23 Multiplexer Operations
DS-2 to DS-3 Digital Multiplexing

M23 Multiplexer Function:
  Input:                      7 independent DS-2 signals (6.312 Mbps each)
  Output:                     1 DS-3 signal (44.736 Mbps)
  Multiplexing:               Asynchronous (positive/negative stuffing)
  Stuff Ratio:                Nominal 2.05% overhead

Active M23 Units:
  M23-NYC-001:
    Input DS-2 #1:            ACTIVE - 6.3120 Mbps, sync normal
    Input DS-2 #2:            ACTIVE - 6.3121 Mbps, sync normal
    Input DS-2 #3:            ACTIVE - 6.3119 Mbps, sync normal
    Input DS-2 #4:            ACTIVE - 6.3122 Mbps, sync normal
    Input DS-2 #5:            ACTIVE - 6.3120 Mbps, sync normal
    Input DS-2 #6:            ACTIVE - 6.3118 Mbps, sync normal
    Input DS-2 #7:            ACTIVE - 6.3121 Mbps, sync normal
    Output DS-3:              ACTIVE - 44.7360 Mbps
    Stuff Rate:               2.03% (normal)

Bit Stuffing Operation:
  Justification:              Positive and negative stuffing
  Stuff Decision:             Made every 8 input bits
  Stuff Indication:           C-bits and S-bits
  Buffer Management:          ±4 bits elastic store

Advanced Features:
  Stuff Threshold:            Adaptive based on input frequency
  Jitter Reduction:           Phase-locked loop filtering
  Alarm Integration:          Upstream/downstream coordination
  Performance Monitoring:     Real-time BER estimation

Frame Structure:
  Frame Length:               4760 bits (106.4 μs)
  M-Frame Length:             (4 × 4760) = 19,040 bits
  Overhead Allocation:        Framing, stuffing, maintenance
  Payload Efficiency:         97.95% (nominal)

Performance Monitoring:
  Input Frequency Tracking:   ±50 ppm range
  Output Jitter:              < 0.1 UI peak-to-peak
  Stuff Jitter:               < 0.2 UI (filtered)
  Error Detection:            CRC-based monitoring"""

        else:
            return f"multiplex: unknown option '{args[0]}'\nUse 'multiplex' for available commands"

    def cmd_regenerator(self, args: List[str]) -> str:
        """Digital Signal Regenerator Management"""
        if not args:
            return """Digital Regenerator System Management
T1 Line and Terminal Equipment

Available Commands:
  regenerator status       - System overview and regenerator status
  regenerator test <id>    - Individual regenerator testing
  regenerator power        - Power system monitoring
  regenerator alarm        - Alarm status and fault analysis
  regenerator maintenance  - Preventive maintenance schedules
  regenerator performance  - Performance monitoring and trends

Current Regenerator Status:
  Line Regenerators:           1,247 units operational
  Terminal Equipment:          156 CSU/DSU units
  Performance:                 All within specifications
  Power Consumption:           Normal (58.7 kW total)"""

        elif args[0] == "status":
            return """Digital Regenerator System Status
November 14, 1983 07:45:30

Line Regenerator Status:
  REG-NYC-WAS-001-R47:
    Location:                 Mile 23.4 (manhhole MH-2347)
    Input Signal:             -18.2 dBm (nominal -22.5 dBm)
    Output Signal:            +13.0 dBm (nominal +13.0 dBm)
    Bit Error Rate:           < 10^-12
    Jitter:                   0.02 UI (excellent)
    Temperature:              68°F (normal)

  REG-NYC-WAS-001-R48:
    Location:                 Mile 46.8 (repeater hut RH-4680)
    Input Signal:             -19.1 dBm (nominal -22.5 dBm)
    Output Signal:            +12.8 dBm (nominal +13.0 dBm)
    Bit Error Rate:           < 10^-12
    Jitter:                   0.03 UI (excellent)
    Temperature:              71°F (normal)

Terminal Equipment Status:
  CSU-NYC-001 (Channel Service Unit):
    Circuit:                  DS1-NYC-WAS-001
    Input Level:              +13.2 dBm
    Output Level:             +13.0 dBm
    Loop-back:                Available (remote/local)

  DSU-NYC-002 (Data Service Unit):
    Circuit:                  DS1-NYC-BOS-002
    Data Rate:                56 kbps (subrate)
    Clock Source:             Network derived
    Interface:                V.35 to customer

Performance Summary:
  Signal Quality:             Excellent (all regenerators)
  Power Efficiency:           47 mA average consumption
  Environmental:              All within operating range
  Maintenance Status:         Current with PM schedule

Regenerator Spacing:
  Cable Type:                 T1 (22 AWG, PIC)
  Span Length:                6,000 feet (nominal)
  Signal Loss:                22.5 dB per span
  Safety Margin:              10.5 dB (adequate)"""

        else:
            return f"regenerator: unknown option '{args[0]}'\nUse 'regenerator' for available commands"

    def cmd_errors(self, args: Optional[List[str]] = None) -> str:
        """Display recent command errors and troubleshooting information."""
        if not self.recent_errors:
            return "No recent errors recorded.\n"

        result = "RECENT COMMAND ERRORS\n"
        result += "=" * 50 + "\n\n"

        recent_errors_list = list(self.recent_errors)[-10:]  # Convert to list and get last 10
        for i, error in enumerate(recent_errors_list, 1):
            timestamp = error['timestamp'].strftime("%H:%M:%S")
            result += f"{i}. [{timestamp}] Command: {error['command']}\n"
            result += f"   Error: {error['error']}\n"
            result += f"   Count: {error['count']} time(s)\n\n"

        # Add troubleshooting tips
        result += "TROUBLESHOOTING TIPS:\n"
        result += "- Type 'help' for available commands\n"
        result += "- Use 'man <command>' for detailed help\n"
        result += "- Check command spelling and syntax\n"
        result += "- Use command aliases (h=help, st=status, etc.)\n"

        return result

    def cmd_verbosity(self, args: List[str]) -> str:
        """Control logging verbosity level."""
        if not args:
            current_level = self.logger.level
            level_names = {10: 'DEBUG', 20: 'INFO', 30: 'WARNING', 40: 'ERROR'}
            current_name = level_names.get(current_level, 'UNKNOWN')
            return f"Current logging level: {current_name} ({current_level})\n" + \
                   "Usage: verbosity [debug|info|warning|error]\n"

        level = args[0].upper()
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }

        if level in level_map:
            self.logger.setLevel(level_map[level])
            self.logger.info(f"Logging level changed to {level}")
            return f"Logging verbosity set to: {level}\n"
        else:
            return f"Invalid level '{args[0]}'. Use: debug, info, warning, error\n"

    def cmd_history(self, args: Optional[List[str]] = None) -> str:
        """Display command history with optional filtering."""
        if not self.command_history:
            return "No command history available.\n"

        result = "COMMAND HISTORY\n"
        result += "=" * 40 + "\n\n"

        # Show last 20 commands by default
        history_slice = list(self.command_history)[-20:]

        for i, cmd in enumerate(history_slice, 1):
            result += f"{i:2d}. {cmd}\n"

        if len(self.command_history) > 20:
            result += f"\n... showing last 20 of {len(self.command_history)} commands\n"

        # Add usage statistics
        if hasattr(self, 'command_counts'):
            result += "\nMOST USED COMMANDS:\n"
            sorted_commands = sorted(self.command_counts.items(),
                                   key=lambda x: x[1], reverse=True)
            for cmd, count in sorted_commands[:5]:
                result += f"  {cmd}: {count} times\n"

        return result

    def cmd_status(self, args: Optional[List[str]] = None) -> str:
        """Display Bell System operational status overview."""
        return """BELL SYSTEM STATUS OVERVIEW
=============================

System Time:           """ + self.clock.timestamp() + """
Session ID:            """ + str(self.session_id) + """
Current Role:          """ + (str(self.role) if self.role else "Not selected") + """
Active Shift:          """ + str(self.current_shift) + """

Network Status:        OPERATIONAL
Switching Centers:     12 active, 0 maintenance
Trunk Groups:          47 active, 3 busy
Emergency Services:    NORMAL

Recent Activity:
- """ + str(len(self.command_history)) + """ commands executed this session
- """ + str(len(self.recent_errors)) + """ errors in last hour
- """ + str(len(self.shift_events)) + """ shift events logged

Type 'help' for available commands.
"""

    def cmd_test(self, args: Optional[List[str]] = None) -> str:
        """Bell System equipment testing interface."""
        if not args:
            return """BELL SYSTEM TEST INTERFACE
============================

Available Test Categories:
- trunk      Test trunk group connectivity
- switch     Test switching equipment
- line       Test subscriber line equipment
- radio      Test microwave radio systems
- carrier    Test digital carrier systems

Usage: test <category> [options]
Example: test trunk TG-001
"""

        test_type = args[0].lower()

        if test_type == "trunk":
            return """TRUNK GROUP TEST RESULTS
======================
Test Target: """ + (args[1] if len(args) > 1 else "All Groups") + """
Test Time: """ + self.clock.log_stamp() + """

Continuity:    PASS
Signaling:     PASS
Traffic Load:  67% (Normal)
Error Rate:    <0.001% (Excellent)

All trunk circuits operational.
"""
        elif test_type == "switch":
            return """SWITCHING EQUIPMENT TEST
=====================
Equipment: Crossbar No. 5
Status: OPERATIONAL
Test Completed: """ + self.clock.log_stamp() + """

Register Tests:     PASS
Marker Tests:       PASS
Connector Tests:    PASS
Selector Tests:     PASS

All switching functions normal.
"""
        else:
            return f"test: unknown test type '{test_type}'\nUse 'test' for available options"

    def cmd_antenna(self, args: Optional[List[str]] = None) -> str:
        """Bell System antenna and microwave equipment management."""
        if not args:
            return """ANTENNA SYSTEM STATUS
===================

Microwave Antennas:
- Antenna A1: Horn antenna, 6 GHz, aligned
- Antenna A2: Parabolic dish, 4 GHz, operational
- Antenna A3: Horn antenna, 11 GHz, maintenance mode

Tower Equipment:
- Tower height: 250 feet
- Wind load: 45 mph (normal)
- Ice loading: None detected

Usage: antenna [status|test|align|maintenance]
"""

        option = args[0].lower()

        if option == "status":
            return """ANTENNA DETAILED STATUS
=====================
Test Time: """ + self.clock.log_stamp() + """

Main Microwave Path (A1):
  Frequency:         6.125 GHz
  Power Output:      +10 dBm
  VSWR:             1.2:1 (Excellent)
  Alignment:        0.1° deviation (Normal)

Backup Path (A2):
  Frequency:         4.835 GHz
  Power Output:      +8 dBm
  VSWR:             1.4:1 (Good)
  Alignment:        On target

All antenna systems operational.
"""
        elif option == "test":
            return """ANTENNA TEST SEQUENCE
===================
Initiated: """ + self.clock.log_stamp() + """

Testing A1 (Main Path):
  Transmitter Test:    PASS
  Receiver Test:       PASS
  Path Loss:          132.5 dB (Normal)
  Signal Quality:      -45 dBm (Strong)

Testing A2 (Backup):
  Transmitter Test:    PASS
  Receiver Test:       PASS
  Path Loss:          128.2 dB (Normal)
  Signal Quality:      -42 dBm (Strong)

All antenna tests completed successfully.
"""
        elif option == "align":
            return """ANTENNA ALIGNMENT PROCEDURE
=========================
Target: """ + (args[1] if len(args) > 1 else "A1") + """
Started: """ + self.clock.log_stamp() + """

Phase 1: Coarse Alignment
  Azimuth sweep:      COMPLETED
  Peak signal found:  -38 dBm at 127.5°

Phase 2: Fine Alignment
  Elevation adjust:   COMPLETED
  Final position:     127.4° Az, 2.1° El
  Signal strength:    -36 dBm (Optimal)

Antenna alignment completed successfully.
"""
        else:
            return f"antenna: unknown option '{option}'\nUse 'antenna' for available commands"

    # ------------------------------------------------------------------
    # Repair service bureau: the trouble report loop
    # ------------------------------------------------------------------

    def _initialize_repair_bureau(self) -> None:
        """
        Stand up the report board, the other craft, and the home wire centre.

        The wire centre is chosen from the geographic data already loaded so
        the reports the desk generates carry a numbering plan area and a
        COMMON LANGUAGE code that belong together.
        """
        home = None
        for office in self.central_offices.values():
            if office['npa'] in ('201', '212', '203'):
                home = office
                break
        if home is None and self.central_offices:
            home = next(iter(self.central_offices.values()))

        if home is None:
            npa, nxx, city, state, switch_type = '201', '555', 'Newark', 'NJ', '1ESS'
        else:
            npa = home['npa']
            nxx = home['nxx']
            city = home['city']
            state = home['state']
            switch_type = home['switch_type']

        self.home_office = {
            'npa': npa, 'nxx': nxx, 'city': city,
            'state': STATE_CODES.get(state, state),
            'switch_type': switch_type,
            'clli': self._office_clli(city, state, switch_type) or 'NWRKNJ02',
        }

        self.desk = ReportDesk(npa, nxx, self.home_office['clli'])
        self.switchroom = Switchroom()
        self._queued_messages: deque = deque()
        self._assigned_tickets: set = set()

        # Minutes of the working shift consumed. The simulated clock runs in
        # real time, so a shift's events would never come due inside a
        # session if they waited on it. They come due on the work instead:
        # every command costs a minute at the terminal, and everything
        # charged against a report is charged against the shift too.
        self.shift_minutes = 0
        self._charged_total = 0
        self._fired_events: set = set()

        slack = self.career.difficulty.commitment_slack_minutes
        self.desk.open_shift(self.clock.now(), slack)

    # -- helpers ---------------------------------------------------------

    def _difficulty(self):
        """Return the active difficulty profile."""
        return self.career.difficulty

    def _stamp(self) -> str:
        """Return a timestamp in the form the messaging channels carried."""
        return self.clock.log_stamp()

    def _queue_message(self, message, after: int) -> None:
        """Hold a message back so it lands a few commands from now."""
        self._queued_messages.append([after, message])

    def _drain_queue(self) -> List[str]:
        """Return any held messages that are now due."""
        due: List[str] = []
        remaining: deque = deque()
        while self._queued_messages:
            countdown, message = self._queued_messages.popleft()
            countdown -= 1
            if countdown <= 0:
                due.append(render_message(message, self._stamp()))
            else:
                remaining.append([countdown, message])
        self._queued_messages = remaining
        return due

    def _interrupt(self) -> str:
        """
        Advance the shift and return whatever the building has to say.

        Called after every command. The shift clock, new work arriving and
        tickets being assigned are simulation state and happen regardless;
        the ambience setting governs only whether anybody tells you about
        them. Interruption rate is the difficulty's: a shift on the forgiving
        setting is quiet, a shift on the other one is not.
        """
        quiet = not self.settings.is_on('game.ambience')
        difficulty = self._difficulty()
        pieces = self._advance_shift()
        if not quiet:
            pieces = self._drain_queue() + pieces

        # The switching control centre puts a ticket on you now and then.
        # These are the tickets the trouble system already carries; being
        # handed one by name is the difference between a list and an
        # assignment.
        if random.random() < difficulty.interruption_rate * 0.3:
            unassigned = [
                ticket for ticket in self.active_tickets
                if ticket['status'] != 'RESOLVED'
                and ticket['id'] not in self._assigned_tickets
            ]
            if unassigned:
                ticket = random.choice(unassigned)
                self._assigned_tickets.add(ticket['id'])
                ticket['assigned_team'] = f"{self.username} (this position)"
                pieces.append(render_message(self.switchroom.ticket_assignment(
                    self.clock.now(), ticket['id'], ticket['title'],
                    ticket['priority'],
                    self._office_label(ticket['affected_office']),
                ), self._stamp()))

        # New work arrives. The rate falls off as the board fills, which is
        # what a finite repair force actually produces: a board that hovers
        # around a working depth rather than emptying or running away.
        depth = len(self.desk.pending())
        arrival = max(0.0, 0.45 - 0.045 * depth)
        if not self.desk.full() and random.random() < arrival:
            report = self.desk.receive(
                self.clock.now(), difficulty.commitment_slack_minutes)
            same_day = report.commitment.date() == report.received.date()
            committed = report.commitment.strftime(
                '%H:%M' if same_day else '%H:%M %a')
            pieces.append(render_message(self.switchroom.assignment(
                self.clock.now(), report.number,
                report.record.telephone_number, report.symptom, committed,
            ), self._stamp()))

        # Somebody says something, at the difficulty's rate.
        if random.random() < difficulty.interruption_rate:
            message = self._craft_interruption(difficulty)
            if message is not None:
                pieces.append(render_message(message, self._stamp()))

        return '' if quiet else '\n'.join(pieces)

    def _craft_interruption(self, difficulty):
        """
        Return whatever one of the other craft would say right now.

        A report past its commitment gets chased first, because that is what
        would actually happen. Otherwise it is advice on the forgiving
        setting and ordinary building noise on either.
        """
        now = self.clock.now()
        pending = self.desk.pending()
        overdue = [report for report in pending if report.overdue()]
        untested = [report for report in pending if not report.tested]
        roll = random.random()

        if overdue and roll < 0.45:
            target = random.choice(overdue)
            return self.switchroom.chase(
                now, target.number, target.record.telephone_number)
        if untested and roll < 0.60 and not difficulty.require_test_before_close:
            return self.switchroom.hint(now)
        if untested and roll < 0.50:
            return self.switchroom.hint(now)
        return self.switchroom.chatter(now)

    def _advance_shift(self) -> List[str]:
        """
        Charge the shift for the work just done and fire anything now due.

        Returns:
            Rendered notices for events that came due, whether or not the
            caller will display them
        """
        charged = sum(report.desk_minutes
                      for report in self.reports_all())
        self.shift_minutes += 1 + max(0, charged - self._charged_total)
        self._charged_total = charged
        return self._fire_due_events()

    def reports_all(self):
        """Return every report the desk has seen this session."""
        return list(self.desk.reports.values())

    def shift_time(self) -> str:
        """Return how far into the shift the work has got, as hours:minutes."""
        return f"{self.shift_minutes // 60}:{self.shift_minutes % 60:02d}"

    def _fire_due_events(self) -> List[str]:
        """
        Bring shift events due as the working shift reaches their time.

        Events carry a wall-clock time because that is how a shift schedule
        was written. They are measured here against the work done rather than
        against the real-time clock, which would leave every afternoon event
        unreachable in a session anybody would actually sit through.
        """
        reached = EPOCH_HOUR * 60 + self.shift_minutes
        notices: List[str] = []
        for event in self.shift_events:
            if event['id'] in self._fired_events:
                continue
            try:
                hour, minute = event['time'].split(':')
                due = int(hour) * 60 + int(minute)
            except (ValueError, KeyError):
                continue
            if due > reached:
                continue

            self._fired_events.add(event['id'])
            if event.get('status') == 'PENDING':
                event['status'] = 'ACTIVE'
            notices.append(render_message(self.switchroom.shift_event(
                self.clock.now(), event['id'], event['type'],
                event['title'], event['priority'], event['time'],
            ), self._stamp()))

        if (self.shift_minutes >= SHIFT_LENGTH_MINUTES
                and 'SHIFT-END' not in self._fired_events):
            self._fired_events.add('SHIFT-END')
            notices.append(self._shift_over_notice())
        return notices

    def _shift_over_notice(self) -> str:
        """Return the wire chief telling you your eight hours are up."""
        pending = len(self.desk.pending())
        overdue = sum(1 for report in self.desk.pending() if report.overdue())
        return render_message(Message(
            channel='write', sender='ehalloran', received=self.clock.now(),
            lines=[
                'That is eight hours.',
                f'{pending} still on your board, {overdue} past commitment.',
                "'handoff relieve' when you are ready to sign off.",
            ],
            kind='shift', subject='End of shift', about=None,
        ), self._stamp())

    def _qualification_block(self, command: str) -> Optional[str]:
        """
        Return the wire chief's refusal when a command is not signed off.

        Qualification governed what a craftsperson was allowed to work on, so
        an unqualified command is refused by a person rather than reported as
        a missing binary.
        """
        needed = self.career.qualification_for_command(command)
        if needed is None or self.career.is_qualified(needed):
            return None
        qualification = QUALIFICATIONS_BY_KEY[needed]
        remaining = max(
            0,
            qualification.requires_reports
            * self._difficulty().reports_per_qualification
            - self.career.reports_correct,
        )
        return (
            f"{command}: you are not signed off on {qualification.name}.\n\n"
            f"{qualification.description}\n\n"
            f"Correct closures still needed: {remaining}\n"
            f"Type 'qual' for your craft record."
        )

    def _grant_qualifications(self) -> List[str]:
        """Award anything newly earned and return the notices."""
        notices: List[str] = []
        for qualification in self.career.grant_available():
            message = self.switchroom.qualification_notice(
                self.clock.now(), qualification.name, qualification.unlocks)
            notices.append(render_message(message, self._stamp()))
        return notices

    # -- report command --------------------------------------------------

    def cmd_report(self, args: Optional[List[str]] = None) -> str:
        """Work the repair service bureau's board of customer trouble reports."""
        args = args or []
        if not args:
            return self._show_report_board()

        action = args[0].lower()
        rest = args[1:]

        if action in ('board', 'list'):
            return self._show_report_board()
        if action == 'closed':
            return self._show_closed_reports()
        if action == 'faults':
            return self._show_fault_reference()
        if action == 'forces':
            return ('Repair forces a report may be dispatched to:\n  '
                    + '\n  '.join(DISPATCH_FORCES))
        if action in ('show', 'detail'):
            if not rest:
                return "report: usage: report show <number>"
            return self._show_report_detail(rest[0])
        if action == 'dispatch':
            if len(rest) < 2:
                return ("report: usage: report dispatch <number> <force>\n"
                        "Forces: " + ', '.join(DISPATCH_FORCES))
            return self._dispatch_report(rest[0], ' '.join(rest[1:]))
        if action == 'close':
            if not rest:
                return ("report: usage: report close <number> <5|8> [fault]\n"
                        "  5  trouble found - name the fault\n"
                        "  8  no trouble found")
            return self._close_report(rest[0], rest[1:])
        if action == 'callback':
            if not rest:
                return "report: usage: report callback <number>"
            return self._report_callback(rest[0])

        return (f"report: unknown option '{args[0]}'\n"
                "Options: board, show, dispatch, close, callback, closed, "
                "faults, forces")

    def _show_report_board(self) -> str:
        """Render the pending list, nearest commitment first."""
        pending = self.desk.pending()
        office = self.home_office
        header = (
            f"Repair Service Bureau - Pending Trouble Reports\n"
            f"{office['city']}, {office['state']}  {office['clli']}"
            f"{' ' * 6}{self.clock.timestamp()}\n"
            + '=' * 74
        )
        if not pending:
            return (header + "\n\nBoard is clear. Nothing pending.\n\n"
                    "New reports arrive during the shift. Type 'qual' for "
                    "your craft record.")

        lines = [
            header,
            f"{'#':>2}  {'REPORT':<10} {'TELEPHONE':<14} {'CLS':<5} "
            f"{'CUSTOMER STATES':<26} {'DUE':>6}  ST",
            '-' * 74,
        ]
        for position, report in enumerate(pending, 1):
            marker = '!' if report.overdue() else ' '
            repeat = 'R' if report.repeat_of else ' '
            lines.append(
                f"{position:>2}{marker} {report.number:<10} "
                f"{report.record.telephone_number:<14} "
                f"{report.record.class_of_service:<5} "
                f"{report.symptom[:26]:<26} "
                f"{report.age_label():>6}  {report.status}{repeat}"
            )
        lines.append('-' * 74)

        overdue = sum(1 for report in pending if report.overdue())
        repeats = sum(1 for report in pending if report.repeat_of)
        lines.append(
            f"{len(pending)} pending, {overdue} past commitment, "
            f"{repeats} repeat. Service index {self.career.service_index():.1f} "
            f"({self.career.index_band()})."
        )
        lines.append('')
        lines.append("report show <n> | mlt <n> | report dispatch <n> <force> "
                     "| report close <n> <5|8> [fault]")
        return '\n'.join(lines)

    def _show_report_detail(self, token: str) -> str:
        """Render one report in full: the line record and everything done to it."""
        report = self.desk.find(token)
        if report is None:
            return f"report: no report matching '{token}'"

        record = report.record
        class_name = CLASSES_OF_SERVICE.get(record.class_of_service, 'Unknown')
        lines = [
            f"{report.number}"
            f"{' ' * max(1, 40 - len(report.number))}"
            f"Received {report.received.strftime('%H:%M %a %b %d')}",
            '=' * 74,
            'LINE RECORD',
            f"  Telephone number    {record.telephone_number}",
            f"  Name                {record.name}",
            f"  Address             {record.address}",
            f"  Class of service    {record.class_of_service}  ({class_name})",
            f"  Cable and pair      {record.cable_pair()}",
            f"  Frame appearance    H {record.horizontal} / V {record.vertical}",
            f"  Line equipment      {record.line_equipment}",
            f"  Office              {record.clli}",
            '',
            'REPORT',
            f"  Customer states     {report.symptom}",
            f"  Commitment          "
            f"{report.commitment.strftime('%H:%M %a %b %d')}"
            f"   ({report.age_label()} "
            f"{'past' if report.overdue() else 'remaining'})",
            f"  Status              {report.status}",
            f"  Time charged        {report.minutes_spent // 60}:"
            f"{report.minutes_spent % 60:02d}",
        ]
        if report.repeat_of:
            lines.append(f"  Repeat of           {report.repeat_of}")
        if report.dispatched_to:
            lines.append(f"  Dispatched to       {report.dispatched_to}")

        lines.extend(['', 'MEASUREMENTS'])
        if report.test_notes:
            for note in report.test_notes:
                lines.append(f"  {note}")
        else:
            lines.append("  None. The line has not been tested.")
            lines.append(f"  Measure it:  mlt {report.number}")

        lines.extend([
            '',
            'CLOSE OUT',
            f"  report close {report.number} 5 <fault>   trouble found",
            f"  report close {report.number} 8           no trouble found",
        ])
        if self._difficulty().require_test_before_close:
            lines.append("  This shift will not accept a close on a line that "
                         "has not been measured.")
        return '\n'.join(lines)

    def _show_closed_reports(self) -> str:
        """Render what has been closed this session and how it was judged."""
        closed = self.desk.closed()
        if not closed:
            return "No reports closed this session."
        lines = [
            "Reports closed this session",
            '=' * 74,
            f"{'REPORT':<10} {'TELEPHONE':<14} {'DISP':<5} {'FOUND':<10} "
            f"{'TRUTH':<10} RESULT",
            '-' * 74,
        ]
        for report in closed:
            verdict = 'correct' if report.correct else 'WRONG'
            if report.missed_commitment:
                verdict += ', missed commitment'
            lines.append(
                f"{report.number:<10} {report.record.telephone_number:<14} "
                f"{'code ' + str(report.disposition):<5} "
                f"{(report.found or '-'):<10} "
                f"{report.record.fault:<10} {verdict}"
            )
        lines.append('-' * 74)
        lines.append(
            f"Closed {self.career.reports_closed}, correct "
            f"{self.career.reports_correct}, repeats {self.career.repeat_reports}. "
            f"Service index {self.career.service_index():.1f} "
            f"({self.career.index_band()})."
        )
        return '\n'.join(lines)

    def _show_fault_reference(self) -> str:
        """Render the fault vocabulary a close out is written against."""
        lines = [
            "Trouble conditions and where they live",
            '=' * 74,
            f"{'CODE':<10} {'NAME':<26} {'WHERE':<9} DISPATCH",
            '-' * 74,
        ]
        for fault in FAULTS.values():
            lines.append(
                f"{fault.code:<10} {fault.name:<26} {fault.where:<9} "
                f"{fault.dispatch}"
            )
        lines.extend([
            '-' * 74,
            '',
            'What each one measures like:',
            '',
        ])
        for fault in FAULTS.values():
            lines.append(f"  {fault.code:<10} {fault.mlt_signature}")
        lines.extend([
            '',
            "Close a report with 'report close <n> 5 <code>' when you have "
            "found and",
            "cleared one of these, or with code 8 when nothing was there.",
        ])
        return '\n'.join(lines)

    def _dispatch_report(self, token: str, force: str) -> str:
        """Send a repair force out and report what they found."""
        report = self.desk.find(token)
        if report is None:
            return f"report: no report matching '{token}'"
        if report.status == 'CLOSED':
            return f"{report.number} is already closed."

        canonical = valid_force(force)
        if canonical is None:
            return (f"report: '{force}' is not a repair force.\n"
                    f"Forces: {', '.join(DISPATCH_FORCES)}")

        finding = self.desk.dispatch(report, canonical)
        if report.field_finding:
            fault = FAULTS[report.field_finding]
            called_in = (
                'nothing wrong at the station, line tests good'
                if fault.code == 'NONE'
                else f'{fault.name.lower()} cleared, back in service')
        else:
            called_in = (f'nothing at our end. Somebody else has this one, '
                         f'not {canonical.lower()}')
        message = self.switchroom.field_call(
            self.clock.now(), report.number, called_in, force=canonical)
        self._queue_message(message, after=random.randint(1, 3))

        return (f"{report.number} dispatched to {canonical}.\n"
                f"{finding}\n"
                f"Time charged {report.minutes_spent // 60}:"
                f"{report.minutes_spent % 60:02d} of the commitment "
                f"({report.age_label()} "
                f"{'past' if report.overdue() else 'remaining'}).")

    def _close_report(self, token: str, rest: List[str]) -> str:
        """Close a report against a disposition code and judge the call."""
        report = self.desk.find(token)
        if report is None:
            return f"report: no report matching '{token}'"
        if report.status == 'CLOSED':
            return f"{report.number} is already closed."
        if not rest:
            return ("report: name a disposition code.\n"
                    "  5  trouble found - name the fault\n"
                    "  8  no trouble found")

        try:
            disposition = int(rest[0])
        except ValueError:
            return f"report: '{rest[0]}' is not a disposition code. Use 5 or 8."
        if disposition not in DISPOSITIONS:
            return (f"report: code {disposition} is not a disposition this "
                    f"bureau uses. Use 5 or 8.")

        difficulty = self._difficulty()
        if difficulty.require_test_before_close and not report.tested:
            return (f"{report.number} has not been measured.\n\n"
                    "Verify, locate, repair, verify. This shift will not "
                    "accept a close on a line\n"
                    f"nobody tested. Run 'mlt {report.number}' first.")

        found = None
        if disposition == 5:
            if not rest[1:]:
                return ("report: code 5 is trouble found. Name what you "
                        "found.\n"
                        f"  report close {report.number} 5 <code>\n"
                        f"Codes: {', '.join(FAULTS)}")
            found = rest[1].upper()
            if found not in FAULTS:
                return (f"report: '{found}' is not a trouble condition.\n"
                        f"Codes: {', '.join(FAULTS)}\n"
                        "Type 'report faults' for what each one means.")

        correct = self.desk.close(
            report, disposition, found, self.clock.now(),
            difficulty.count_missed_commitments)
        self.career.record_closure(correct, report.missed_commitment)

        lines = [
            f"{report.number} closed, code {disposition} - "
            f"{disposition_name(disposition)}.",
        ]
        if correct:
            lines.append("The close out matches what was on the line.")
        else:
            truth = FAULTS[report.record.fault]
            if report.record.fault == 'NONE':
                lines.append("Nothing was actually wrong with that line.")
            elif disposition == 8:
                lines.append(f"There was a {truth.name.lower()} on that pair.")
            else:
                lines.append(f"That pair had a {truth.name.lower()}, not "
                             f"{FAULTS[found].name.lower() if found else 'that'}.")

        if report.missed_commitment:
            lines.append("Commitment was missed. It counts.")

        if self.desk.should_repeat(report, difficulty.repeat_report_chance):
            repeat = self.desk.repeat(
                report, self.clock.now(), difficulty.commitment_slack_minutes)
            self.career.record_repeat()
            notice = self.switchroom.repeat_notice(
                self.clock.now(), repeat.number,
                f"code {disposition}", report.record.telephone_number)
            self._queue_message(notice, after=random.randint(2, 5))

        lines.append('')
        lines.append(
            f"Closed {self.career.reports_closed}, correct "
            f"{self.career.reports_correct}. Service index "
            f"{self.career.service_index():.1f} ({self.career.index_band()})."
        )

        granted = self._grant_qualifications()
        if granted:
            lines.append('')
            lines.extend(granted)
        return '\n'.join(lines)

    def _report_callback(self, token: str) -> str:
        """Call the customer back and get more out of them than the card has."""
        report = self.desk.find(token)
        if report is None:
            return f"report: no report matching '{token}'"
        if report.status == 'CLOSED':
            return f"{report.number} is already closed."

        report.spend(COST_CALLBACK)
        fault = FAULTS[report.record.fault]
        detail = {
            'OPEN': "It went dead all at once. There was work in the street "
                    "last week.",
            'SHORT': "Nothing at all when I pick it up, and my daughter says "
                     "she gets a busy signal every time.",
            'GROUND': "There is a hum, worse when it rains, and sometimes it "
                      "rings once by itself.",
            'CROSS': "I can hear two other people talking. They can hear me "
                     "as well.",
            'WET': "It has been getting worse all week, since the storm. The "
                   "neighbours have it too.",
            'FCG': "I get nothing when I dial. The dial tone is there and "
                   "then it just sits.",
            'FEMF': "There is a loud buzz, and I felt something off the set "
                    "once. The power line runs right past.",
            'ROH': "No, I have not had any trouble calling out. People say "
                   "they cannot reach me.",
            'CO_EQUIP': "It never rings. I have tried a different telephone "
                        "and it does the same thing.",
            'NONE': "It happened twice on Tuesday and it has been fine since. "
                    "Perhaps it fixed itself.",
        }.get(report.record.fault, fault.description)

        return (f"Call back on {report.record.telephone_number} "
                f"({report.record.name}).\n\n"
                f"  \"{detail}\"\n\n"
                f"{COST_CALLBACK} minutes charged. "
                f"{report.age_label()} "
                f"{'past' if report.overdue() else 'remaining'}.")

    # -- mechanised loop testing -----------------------------------------

    def cmd_mlt(self, args: Optional[List[str]] = None) -> str:
        """Measure a subscriber loop and report the readings."""
        args = args or []
        if not args:
            pending = self.desk.pending()
            if not pending:
                return ("mlt: name a report or a telephone number.\n"
                        "Usage: mlt <report number | telephone number>")
            return ("mlt: name a report or a telephone number.\n"
                    "Usage: mlt <report number | telephone number>\n\n"
                    "Pending: "
                    + ', '.join(report.number for report in pending))

        report = self.desk.find(args[0])
        if report is None:
            return (f"mlt: no line record for '{args[0]}'.\n"
                    "Mechanised loop testing works from the loop assignment "
                    "record; a\nnumber with no record on this board cannot be "
                    "reached from here.")
        if report.status == 'CLOSED':
            return f"{report.number} is closed. Nothing to test."

        record = report.record
        name_fault = not self._difficulty().require_test_before_close
        measurement = measure_loop(
            record.telephone_number, record.fault, name_fault=name_fault)

        length_kft = round(measurement.distance_miles * 5.28, 1)
        loop_ohms = measurement.loop_resistance_ohms
        loop_reading = (f"{loop_ohms:>12,} ohms" if loop_ohms is not None
                        else f"{'open':>12}")
        lines = [
            f"MECHANISED LOOP TEST - {record.telephone_number}",
            f"{record.clli}  cable {record.cable_pair()}  "
            f"{self.clock.timestamp()}",
            '=' * 74,
            'INSULATION RESISTANCE (loop open, office battery removed)',
            f"  Tip to ring         {measurement.tip_ring_ohms:>12,} ohms",
            f"  Tip to ground       {measurement.tip_ground_ohms:>12,} ohms",
            f"  Ring to ground      {measurement.ring_ground_ohms:>12,} ohms",
            '',
            'FOREIGN POTENTIAL (office battery removed)',
            f"  DC                  {measurement.dc_volts:>12.1f} volts",
            f"  AC                  {measurement.ac_volts:>12.1f} volts",
            '',
            'LOOP',
            f"  Capacitance         {measurement.capacitance_uf:>12.3f} uF",
            f"  Implied distance    "
            f"{distance_to_open(measurement.capacitance_uf):>12.2f} miles "
            f"({length_kft} kft)",
            f"  Loop resistance     {loop_reading}",
            f"  Loop current        {measurement.loop_current_ma:>12.1f} mA",
            f"  Station termination "
            f"{'present' if measurement.station_termination else 'ABSENT':>12}",
            '',
            f"  {design_note(loop_ohms, length_kft)}",
        ]
        if record.class_of_service == 'COIN':
            lines.append(f"  Coin station: needs {COIN_STATION_CURRENT_MA} mA "
                         f"to operate.")
        lines.extend(['', 'TEST RESULT', f"  {measurement.verdict}"])
        if measurement.suspected:
            suspected = FAULTS[measurement.suspected]
            lines.append(f"  System reads this as: {suspected.name} "
                         f"({suspected.code})")
            lines.append(f"  Dispatch to: {suspected.dispatch}")
        else:
            lines.append("  The system will not name a condition on this "
                         "setting.")
            lines.append("  Match the reading against 'report faults'.")

        loop_note = f"{loop_ohms:,} ohms" if loop_ohms is not None else 'open'
        note = (f"{self.clock.time()} MLT: insulation T-R "
                f"{measurement.tip_ring_ohms:,}, "
                f"T-G {measurement.tip_ground_ohms:,}, "
                f"R-G {measurement.ring_ground_ohms:,}; "
                f"C {measurement.capacitance_uf} uF; loop {loop_note}")
        self.desk.record_test(report, note)

        lines.append('')
        lines.append(f"Charged to {report.number}. "
                     f"{report.age_label()} "
                     f"{'past' if report.overdue() else 'remaining'}.")
        return '\n'.join(lines)

    # -- test lines ------------------------------------------------------

    def cmd_testline(self, args: Optional[List[str]] = None) -> str:
        """Reach a test line or responder on a circuit and read the result."""
        args = args or []
        if not args:
            lines = [
                "Test lines and responders",
                '=' * 74,
                tone_header() + '.',
                '',
                f"{'CODE':<6} {'ACCESS':<8} {'NAME':<34} MEASURES",
                '-' * 74,
            ]
            for code in TEST_LINE_ORDER:
                test_line = TEST_LINES[code]
                lines.append(
                    f"{test_line.code:<6} {test_line.access:<8} "
                    f"{test_line.name:<34} {', '.join(test_line.measures)}"
                )
            lines.extend([
                '-' * 74,
                '',
                "Usage: testline <code> <circuit>",
                "       testline 105 TG-001-NYC",
                '',
                "Access codes are the simulation's own: real ones were local "
                "to each office.",
            ])
            return '\n'.join(lines)

        code = args[0].upper()
        if code not in TEST_LINES:
            return (f"testline: no {args[0]} test line.\n"
                    f"Codes: {', '.join(TEST_LINE_ORDER)}")
        if len(args) < 2:
            test_line = TEST_LINES[code]
            return (f"{test_line.name}\n"
                    f"{'=' * 50}\n"
                    f"Access:    {test_line.access}\n"
                    f"Direction: {test_line.direction}\n"
                    f"Measures:  {', '.join(test_line.measures)}\n\n"
                    f"{test_line.description}\n\n"
                    f"Usage: testline {code.lower()} <circuit>")

        circuit = args[1].upper()
        group = self.trunk_groups.get(circuit)
        degraded = bool(group and (group['status'] != 'ACTIVE'
                                   or group['quality'] < 0.994))
        result = access_test_line(code, circuit, degraded=degraded)
        if result is None:
            return f"testline: no {code} test line."

        lines = [
            f"{result.test_line} - {circuit}",
            f"{tone_header()}   {self.clock.timestamp()}",
            '=' * 74,
        ]
        if result.loss_db is not None:
            label = ('Return loss' if code == 'BAL' else 'Loss at 1004 Hz')
            lines.append(f"  {label:<24}{result.loss_db:>8.1f} dB")
        if result.noise_dbrnc is not None:
            lines.append(f"  {'Noise':<24}{result.noise_dbrnc:>8.1f} dBrnC")
        if result.noise_with_tone_dbrnc is not None:
            lines.append(f"  {'Noise with tone':<24}"
                         f"{result.noise_with_tone_dbrnc:>8.1f} dBrnC")
        if result.slope_db is not None:
            lines.append(f"  {'Gain slope':<24}{result.slope_db:>8.1f} dB")
        lines.append('')
        lines.append(f"  {'PASS' if result.passed else 'FAIL'}")
        for note in result.notes:
            lines.append(f"  {note}")
        return '\n'.join(lines)

    # -- craft record ----------------------------------------------------

    def cmd_qual(self, args: Optional[List[str]] = None) -> str:
        """Show the craft record: difficulty, qualifications and service index."""
        args = args or []
        if args and args[0].lower() == 'index':
            return self._show_service_index()

        career = self.career
        difficulty = career.difficulty
        lines = [
            f"Craft Record - {self.username}",
            '=' * 74,
            f"  Difficulty          {difficulty.name}",
            f"  {' ' * 18}  {difficulty.summary}",
            f"  Shift               {career.shift}",
            f"  Reports closed      {career.reports_closed} "
            f"({career.reports_correct} correct, {career.reports_wrong} wrong)",
            f"  Repeat reports      {career.repeat_reports}",
            f"  Missed commitments  {career.missed_commitments}"
            + ('' if difficulty.count_missed_commitments else '  (not counted)'),
            f"  Customer reports    {career.service_index():.1f} of 100  "
            f"{career.index_band()}",
            f"  Worth to the office {career.office_contribution():.1f} of "
            f"{NSPMP_WEIGHTS['customer_reports']} index points",
            '',
            'QUALIFICATIONS',
            '-' * 74,
        ]
        for qualification in QUALIFICATIONS:
            held = career.is_qualified(qualification.key)
            mark = 'x' if held else ' '
            lines.append(f"  [{mark}] {qualification.name}")
            lines.append(f"      {qualification.description}")
            lines.append(f"      Opens: {', '.join(qualification.unlocks)}")
            if not held:
                needed = (qualification.requires_reports
                          * difficulty.reports_per_qualification
                          - career.reports_correct)
                lines.append(f"      Needs {max(0, needed)} more correct "
                             f"closures.")
            lines.append('')

        nxt = career.next_qualification()
        if nxt is None:
            lines.append("Fully qualified. Every system on this terminal is "
                         "open to you.")
        else:
            lines.append(f"Next: {nxt.name} in "
                         f"{career.reports_until_next()} correct closures.")
        lines.extend([
            '',
            "Change difficulty with 'set game.difficulty fun' or "
            "'set game.difficulty craft'.",
            "'qual index' explains how the index is scored.",
        ])
        return '\n'.join(lines)

    def _show_service_index(self) -> str:
        """Explain the index against the published measurement weights."""
        career = self.career
        difficulty = career.difficulty
        lines = [
            "Service index",
            '=' * 74,
            "The network switching performance measurement plan scored an",
            "office across ten weighted components summing to 100. Customer",
            "reports carried ten of them.",
            '',
            f"{'COMPONENT':<28} {'CATEGORY':<20} WEIGHT",
            '-' * 74,
        ]
        for key, weight in NSPMP_WEIGHTS.items():
            label = key.replace('_', ' ').title()
            marker = ' <' if key == 'customer_reports' else ''
            lines.append(
                f"{label:<28} {NSPMP_CATEGORIES[key]:<20} {weight:>3}{marker}")
        lines.extend([
            '-' * 74,
            f"{'Total':<49} {sum(NSPMP_WEIGHTS.values()):>3}",
            '',
            "You are scored on the marked component, out of 100, because that",
            "is the one you work. Total failure on it would cost the office",
            "only ten of its hundred points, which would tell you nothing.",
            '',
            'HOW THE HUNDRED IS LOST',
            '-' * 74,
            f"  Wrong disposition   {WRONG_DISPOSITION_WEIGHT:>3}",
            f"  Repeat report       {REPEAT_REPORT_WEIGHT:>3}",
            f"  Missed commitment   {MISSED_COMMITMENT_WEIGHT:>3}"
            + ('' if difficulty.count_missed_commitments
               else '  (not counted on this setting)'),
            f"  Difficulty factor   {difficulty.index_penalty:>3.1f} "
            f"({difficulty.name})",
            '',
            "  Each is lost in proportion to the share of your closed reports",
            "  it applies to, then scaled by the difficulty factor. Close every",
            "  report wrongly and the whole 55 goes.",
            '',
            "  A wrong close weighs heaviest because it is the one that leaves",
            "  a customer out of service believing somebody has dealt with",
            "  them. The apportionment is the simulation's own; the ten points",
            "  the component is worth to the office are the published figure.",
            '',
            'YOUR STANDING',
            '-' * 74,
            f"  Reports closed      {career.reports_closed}",
            f"  Closed correctly    {career.reports_correct}",
            f"  Closed wrongly      {career.reports_wrong}",
            f"  Came back as repeat {career.repeat_reports}",
            f"  Missed commitments  {career.missed_commitments}",
            f"  Customer reports    {career.service_index():.1f} of 100  "
            f"({career.index_band()})",
            f"  Worth to the office {career.office_contribution():.1f} of "
            f"{NSPMP_WEIGHTS['customer_reports']} points",
        ])
        if career.index_history:
            lines.append('')
            lines.append('  Previous shifts     '
                         + ', '.join(f"{entry:.1f}"
                                     for entry in career.index_history[-10:]))
        lines.extend([
            '',
            "A report closed as no trouble found on a line that really was",
            "faulty counts twice against you: once as a wrong disposition, and",
            "again when the customer calls back.",
        ])
        return '\n'.join(lines)

    # -- messaging channels ----------------------------------------------

    def cmd_write(self, args: Optional[List[str]] = None) -> str:
        """Send a line to another craftsperson's terminal, as write(1) did."""
        args = args or []
        if not args:
            lines = [
                "write: usage: write <user> [message]",
                '',
                f"{'LOGIN':<12} {'TTY':<5} {'NAME':<16} WHERE",
                '-' * 66,
            ]
            for person in CRAFT.values():
                lines.append(f"{person.login:<12} tty{person.tty:<2} "
                             f"{person.name:<16} {person.location}")
            lines.append('-' * 66)
            lines.append("Type 'who' for who is on the system.")
            return '\n'.join(lines)

        login = args[0].lower()
        person = CRAFT.get(login)
        if person is None:
            return f"write: {args[0]} is not logged on."
        if login == 'carot':
            return ("write: CAROT is a test system, not a terminal. It prints "
                    "to you; you\ndo not write back to it.")

        if len(args) == 1:
            return (f"write: say something.\n"
                    f"Usage: write {login} <message>\n\n"
                    f"{person.name}, {person.title}, {person.location}.\n"
                    f"{person.manner}")

        reply = self._craft_reply(login)
        return (f"Message sent to {login} tty{person.tty}.\n"
                f"EOT\n\n"
                f"Message from {login} tty{person.tty} [{self._stamp()}]...\n"
                f"{reply}\nEOT")

    def _craft_reply(self, login: str) -> str:
        """Return what a craftsperson says back when written to."""
        pending = self.desk.pending()
        oldest = pending[0] if pending else None
        replies = {
            'rjohnson': [
                "Busy on the frame. If it is a pair, take it to the board.",
                "I have seen that one. Measure it before you believe it.",
            ],
            'mreyes': [
                f"You have {len(pending)} on your board. I have more coming.",
                "Tell me something I can put on the card and I will call them.",
            ],
            'dpetrak': [
                "SCC has you. Nothing outstanding from here.",
                "Keep the order wire clear, we are routining trunks tonight.",
            ],
            'lokafor': [
                "I am up a pole. Make it quick.",
                "Give me a cable and pair and I will go look at it.",
            ],
            'gvasquez': [
                "Board is yours. Send me a number and I will read it out.",
                "Capacitance is the distance. That is the whole trick.",
            ],
            'ehalloran': [
                f"Your index is {self.career.service_index():.1f}. "
                f"{self.career.index_band()}.",
                "Work what you are signed off on and nothing else.",
            ],
            'tnakamura': [
                "Everything is stated at 1004 Hz. Read it there.",
                "If a trunk is long on loss, do not put it back in service.",
            ],
        }
        pool = replies.get(login, ["Go ahead."])
        if oldest is not None and login == 'mreyes':
            pool.append(f"{oldest.number} is the one I would do first.")
        return random.choice(pool)

    def cmd_mail(self, args: Optional[List[str]] = None) -> str:
        """Read the mail the other craft have left, as mail(1) did."""
        args = args or []
        if args and args[0].lower() in ('-s', 'send'):
            return ("mail: this terminal takes mail; it does not originate "
                    "it.\nUse 'write <user>' to reach somebody now.")

        waiting = self.switchroom.take_mail()
        if not waiting:
            return "No mail."
        rendered = [f"Mail for {self.username}: {len(waiting)} message(s)", '']
        for message in waiting:
            rendered.append(render_message(
                message, message.received.strftime('%a %b %d %H:%M:%S %Y')))
            rendered.append('-' * 66)
        return '\n'.join(rendered)

    def cmd_orderwire(self, args: Optional[List[str]] = None) -> str:
        """Listen on, or speak into, the maintenance order wire."""
        args = args or []
        if not args:
            traffic = [
                message for message in self.switchroom.log
                if message.channel == 'orderwire'
            ][-6:]
            lines = [
                "Order wire - maintenance circuit",
                f"{self.home_office['clli']} to SCC_BEDMINSTER   "
                f"{self.clock.timestamp()}",
                '=' * 66,
            ]
            if not traffic:
                lines.append("Circuit quiet. Nothing on the wire.")
            else:
                for message in traffic:
                    lines.append(render_message(
                        message, message.received.strftime('%H:%M')))
            lines.extend([
                '',
                "Usage: orderwire report <what you are calling in>",
                "       orderwire scc            raise the control centre",
            ])
            return '\n'.join(lines)

        action = args[0].lower()
        if action == 'scc':
            pending = len(self.desk.pending())
            return (f"[ORDER WIRE SCC_BEDMINSTER {self._stamp()}]\n"
                    f"Petrak, SCC. Go ahead.\n\n"
                    f"You report {pending} pending and a service index of "
                    f"{self.career.service_index():.1f}.\n"
                    f"SCC acknowledges. Nothing outstanding from this end.")
        if action == 'report':
            if len(args) < 2:
                return "orderwire: say what you are reporting."
            said = ' '.join(args[1:])
            return (f"[ORDER WIRE {self.home_office['clli']} {self._stamp()}]\n"
                    f"{self.username}: {said}\n\n"
                    f"[ORDER WIRE SCC_BEDMINSTER {self._stamp()}]\n"
                    f"SCC copies. Logged against this office.")
        return ("orderwire: unknown option. Use 'orderwire', "
                "'orderwire scc' or\n'orderwire report <text>'.")

    # -- test calls ------------------------------------------------------

    def cmd_testcall(self, args: Optional[List[str]] = None) -> str:
        """Place a test call through the network and watch every stage of it."""
        args = args or []
        network = self.toll_network

        if not args or args[0].lower() in ('help', 'offices'):
            lines = [
                "Test Call",
                '=' * 74,
                '',
                "A test call is how a trunk is proved. The originating office",
                "seizes it, outpulses the address in multifrequency, the",
                "network advances the call through the hierarchy, and",
                "something at the far end answers so the connection can be",
                "measured. Every stage leaves a signal a craftsperson can",
                "read.",
                '',
                "Usage:",
                "  testcall <from> <to>              Place a call and follow it",
                "  testcall <from> <to> <test line>  Terminate on a test line",
                "                                    and measure the connection",
                '',
                "Test lines: " + ', '.join(TEST_LINE_ORDER),
                '',
                "OFFICES",
                '-' * 74,
            ]
            for office in sorted(network.offices.values(),
                                 key=lambda entry: (entry.switch_class,
                                                    entry.code)):
                lines.append(f"  {office.code:<13} {office.class_name():<22} "
                             f"{office.name}")
            return '\n'.join(lines)

        if len(args) < 2:
            return ("testcall: name an originating and a terminating office.\n"
                    "Usage: testcall <from> <to> [test line]")

        origin, destination = args[0].upper(), args[1].upper()
        for code in (origin, destination):
            if code not in network.offices:
                return (f"testcall: no office {code} in the routing table.\n"
                        f"Type 'testcall offices' for the list.")
        if origin == destination:
            return ("testcall: a test call needs two different offices. A "
                    "call to the office\nit started in never reaches a trunk.")

        test_line = None
        if len(args) > 2:
            code = args[2].upper()
            if code not in TEST_LINES:
                return (f"testcall: no {args[2]} test line.\n"
                        f"Test lines: {', '.join(TEST_LINE_ORDER)}")
            test_line = TEST_LINES[code]

        return self._place_test_call(origin, destination, test_line)

    def _place_test_call(self, origin: str, destination: str,
                         test_line: Optional[Any]) -> str:
        """
        Run a test call from seizure to release and narrate every stage.

        The stages are the real ones: seizure removes the single frequency
        supervisory tone toward the far end, the far end returns a start
        signal, the address goes out in multifrequency bracketed by KP and
        ST, the network advances the call through the hierarchy, and answer
        supervision comes back. Release restores the tone.
        """
        network = self.toll_network
        result = network.route(origin, destination)
        terminating = network.offices[destination]

        # The address outpulsed. A test line has its own access code; a plain
        # trunk test outpulses the terminating office's test number. Both are
        # the simulation's own: real test numbers were office records.
        address = (test_line.access if test_line is not None
                   else self.__class__._test_number_for(terminating.code))
        train = mf_sequence(address)
        train_ms = mf_train_duration_ms(train)
        start_type = self.__class__._start_signal_for(origin)

        lines = [
            f"Test Call  {origin} to {destination}",
            f"{self.clock.timestamp()}",
            '=' * 74,
            '',
            'SUPERVISION AND ADDRESS',
            '-' * 74,
            f"  Seizure              SF tone removed toward the far end "
            f"({SF_FREQUENCY_HZ} Hz)",
            f"  Idle tone level      {SF_IDLE_LEVEL_DBM:+.1f} dBm before "
            f"seizure",
            f"  Start signal         {start_type}",
            "  Address signalling   multifrequency; the talking path is "
            "muted while",
            "                       an office outpulses, which is why MF "
            "needs no",
            "                       protection against the human voice",
            f"  Address outpulsed    "
            f"{' '.join(signal.symbol for signal in train)}",
            f"  Train duration       {train_ms} ms",
            '',
            'ROUTE ADVANCE',
            '-' * 74,
        ]
        for step, attempt in enumerate(result.attempts, 1):
            lines.append(f"  {step}. {attempt}")

        lines.extend(['', 'RESULT', '-' * 74])
        if not result.completed:
            lines.extend([
                "  Outcome              BLOCKED",
                "  Caller receives      reorder",
                f"  Trunks in tandem     {result.trunk_count()} before the "
                f"block",
                '',
                "  Every trunk in a final group was busy. A final group is the",
                "  last route available, so there is nowhere for the call to",
                "  overflow to. Final groups are engineered to P.01 - one call",
                "  in a hundred finds all trunks busy - so this is the one in",
                "  a hundred, not a fault.",
            ])
            return '\n'.join(lines)

        lines.extend([
            "  Outcome              COMPLETED",
            f"  Trunks in tandem     {result.trunk_count()} of "
            f"{MAX_TRUNKS_IN_CONNECTION} permitted",
            "  Answer supervision   returned; SF tone off in both directions",
        ])

        if test_line is None:
            lines.extend([
                '',
                "  The connection is up and the talking path is through. To",
                "  measure it, terminate the call on a test line:",
                f"    testcall {origin} {destination} 105",
                '',
                "  Release              SF tone restored, trunk returned to "
                "idle",
            ])
            return '\n'.join(lines)

        degraded = result.trunk_count() >= 5
        measurement = access_test_line(
            test_line.code, f"{origin}-{destination}", degraded=degraded)

        lines.extend([
            '',
            f'MEASUREMENT - {test_line.name.upper()}',
            '-' * 74,
            f"  {tone_header()}",
        ])
        if measurement.loss_db is not None:
            label = ('Return loss' if test_line.code == 'BAL'
                     else 'Loss at 1004 Hz')
            lines.append(f"  {label:<24}{measurement.loss_db:>8.1f} dB")
        if measurement.noise_dbrnc is not None:
            lines.append(f"  {'Noise':<24}{measurement.noise_dbrnc:>8.1f} "
                         f"dBrnC")
        if measurement.noise_with_tone_dbrnc is not None:
            lines.append(f"  {'Noise with tone':<24}"
                         f"{measurement.noise_with_tone_dbrnc:>8.1f} dBrnC")
        if measurement.slope_db is not None:
            lines.append(f"  {'Gain slope':<24}{measurement.slope_db:>8.1f} dB")

        lines.append('')
        lines.append(f"  {'PASS' if measurement.passed else 'FAIL'}")
        for note in measurement.notes:
            lines.append(f"  {note}")
        if degraded:
            lines.append("  Five trunks in tandem. Loss and noise accumulate "
                         "on every one of them.")
        lines.extend([
            '',
            "  Release              SF tone restored, trunk returned to idle",
        ])
        if not measurement.passed:
            lines.extend([
                '',
                "  A circuit outside its working limits should not go back in",
                "  service. CAROT routines these groups and will find it again",
                "  tonight if you leave it.",
            ])
        return '\n'.join(lines)

    @staticmethod
    def _test_number_for(code: str) -> str:
        """
        Return the seven digit test number an office answers on.

        Real test numbers were carried in office records and varied office to
        office, so this one is the simulation's own, derived from the office
        code so a given office always answers on the same number.
        """
        seed = sum(ord(character) for character in code)
        nxx = 200 + seed % 700
        line = 1100 + seed % 90
        return f"{nxx}{line}"

    @staticmethod
    def _start_signal_for(origin: str) -> str:
        """
        Return the start signal the originating office would see.

        Which start arrangement a trunk group used was an office record, not
        a national rule. The choice here is deterministic on the office code
        so a group answers the same way every time it is tested.
        """
        arrangements = (
            'wink start - far end winks off-hook then on again, register ready',
            'delay dial - far end holds off-hook until its register is free',
            'immediate start - outpulse after a fixed interval, no handshake',
        )
        return arrangements[sum(ord(character) for character in origin)
                            % len(arrangements)]

    def cmd_quit(self, args: Optional[List[str]] = None) -> str:
        """Exit the Bell System terminal session."""
        # Save command history if readline is available
        if READLINE_AVAILABLE and getattr(self, 'history_file', None):
            try:
                readline.write_history_file(self.history_file)
            except OSError as exc:
                self.logger.warning(f"Could not save command history: {exc}")

        self.logger.info(f"Session {self.session_id} terminated by user")
        self.emit("\nBell System session terminated.")
        self.emit("Thank you for using Bell System UNIX V7 Operations Terminal.")
        sys.exit(0)

    def cmd_clear(self, args: Optional[List[str]] = None) -> str:
        """Clear the terminal screen."""
        clear_screen()
        return ""


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
