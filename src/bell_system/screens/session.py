"""
The session state the screens read, declared once.

Splitting ``terminal.py`` into subsystem mixins made an existing coupling
visible: every screen reads session state - the clock, the settings, the
trunk groups, the report desk - that the terminal constructs. The coupling
was always there; it was simply invisible while everything lived in one
class.

This module makes it a contract. :class:`SessionState` declares every
attribute the screens are entitled to read, each mixin inherits from it, and
a type checker can then verify a screen against the state it actually uses
rather than trusting that the attribute exists somewhere in an eleven
thousand line file.

Adding an attribute here is a deliberate act: it widens what every screen may
touch. Prefer passing state to a subsystem that owns it - the way
:mod:`bell_system.lmos` and :mod:`bell_system.special_services` do - over
adding another shared field.
"""

import logging
from collections import deque
from typing import TYPE_CHECKING, Any, Dict, FrozenSet, List, Optional, Set

from ..clock import SimClock
from ..progression import Career, Difficulty
from ..reports import ReportDesk
from ..routing import TollNetwork
from ..settings import Settings
from ..types import (
    Alarm,
    CentralOffice,
    CrossbarSystem,
    SystemHealth,
    TndsData,
    TroubleTicket,
    TrunkGroup,
    TspsData,
)

if TYPE_CHECKING:  # pragma: no cover - avoids an import cycle at runtime
    from ..lmos import LmosConsole
    from ..npc import Switchroom
    from ..special_services import SartsConsole, SartsInventory


class SessionState:
    """
    What a screen may read from the terminal it is mixed into.

    Declarations only; :class:`~bell_system.terminal.BellSystemTerminal`
    constructs all of it.
    """

    # -- session ---------------------------------------------------------
    settings: Settings
    clock: SimClock
    logger: logging.Logger
    session_id: str
    session_start_time: float
    username: str
    hostname: str
    shell: str
    current_directory: str
    role: Optional[str]
    role_name: Optional[str]
    history_file: str

    # -- command dispatch and history ------------------------------------
    _command_handlers: Dict[str, Any]
    _performance_log: Dict[str, Any]
    command_history: deque
    command_counts: Dict[str, int]
    error_counts: Dict[str, int]
    recent_errors: deque
    failed_command_attempts: int
    log_verbosity: str
    man_pages: Dict[str, str]

    # -- the work --------------------------------------------------------
    career: Career
    desk: ReportDesk
    switchroom: 'Switchroom'
    lmos_console: 'LmosConsole'
    sarts_console: 'SartsConsole'
    special_services: 'SartsInventory'
    home_office: Dict[str, str]

    # -- the shift -------------------------------------------------------
    current_shift: int
    shift_minutes: int
    shift_events: List[Dict[str, Any]]
    shift_handoff: Dict[str, Any]
    _charged_total: int
    _fired_events: Set[str]
    _queued_messages: deque

    # -- plant -----------------------------------------------------------
    toll_network: TollNetwork
    trunk_groups: Dict[str, TrunkGroup]
    switching_systems: Dict[str, Any]
    crossbar_systems: Dict[str, CrossbarSystem]
    switching_centers: Dict[str, Any]
    microwave_sites: Dict[str, Any]
    central_offices: Dict[str, CentralOffice]
    frame_state: Dict[str, Any]
    network_metrics: Dict[str, Any]
    system_health: SystemHealth
    active_alarms: List[Alarm]

    # -- geography -------------------------------------------------------
    nanpa_data: Dict[str, Any]
    bell_system_exchanges: Dict[str, Any]
    geography_degraded: bool

    # -- measurement systems ---------------------------------------------
    tnds_data: TndsData
    tsps_data: TspsData
    traffic_data: Dict[str, Any]
    regional_traffic: Dict[str, Any]

    # -- tickets ---------------------------------------------------------
    active_tickets: List[TroubleTicket]
    completed_tickets: List[TroubleTicket]
    ticket_categories: Dict[str, Any]
    ticket_counter: int
    ticket_system: Dict[str, Any]
    _assigned_tickets: Set[str]

    # -- simulated host --------------------------------------------------
    filesystem: Dict[str, Any]
    processes: List[Dict[str, Any]]
    users: List[Dict[str, str]]
    project_numbers: Dict[str, Any]
    rate_structures: Dict[str, Any]

    # -- shared behaviour ------------------------------------------------
    #
    # Methods one screen calls that another screen or the terminal defines.
    # Declared here for the same reason the attributes are: a mixin should be
    # checkable against what it actually uses. The bodies live with their own
    # subsystem.

    # Cities large enough to have carried a metropolitan-class machine.
    METROPOLITAN_CITIES: FrozenSet[str]

    def emit(self, text: str = '', end: str = '\n') -> None:
        """Write simulation output under the active character-set setting."""
        raise NotImplementedError

    def _subsystem_unavailable(self, command: str, summary: str) -> str:
        """Report a command whose screens are not built in this release."""
        raise NotImplementedError

    def _office_clli(self, city: str, state: str, switch_type: str,
                     is_toll: bool = False, ordinal: int = 0) -> str:
        """Return the COMMON LANGUAGE location identifier for an office."""
        raise NotImplementedError

    @staticmethod
    def _office_label(office: Any) -> str:
        """Render an affected office for display."""
        raise NotImplementedError

    def _difficulty(self) -> Difficulty:
        """Return the active difficulty profile."""
        raise NotImplementedError

    def _stamp(self) -> str:
        """Return a timestamp in the form the messaging channels carried."""
        raise NotImplementedError

    def _queue_message(self, message: Any, after: int) -> None:
        """Hold a message back so it lands a few commands from now."""
        raise NotImplementedError

    def _grant_qualifications(self) -> List[str]:
        """Award anything newly earned and return the notices."""
        raise NotImplementedError

    def reports_all(self) -> List[Any]:
        """Return every report the desk has seen this session."""
        raise NotImplementedError

    def _get_shift_hours(self) -> str:
        """Return the hours the current shift covers."""
        raise NotImplementedError

    def _get_peak_period(self) -> str:
        """Return the traffic period the clock currently falls in."""
        raise NotImplementedError

    def _select_affected_infrastructure(self) -> dict:
        """Select a central office for a generated ticket to affect."""
        raise NotImplementedError

    def _calculate_business_impact(self, priority: str,
                                   customer_count: int) -> dict:
        """Return the business impact figures for a ticket."""
        raise NotImplementedError

    def _show_network_hierarchy_analysis(self) -> str:
        """Render the switching hierarchy analysis."""
        raise NotImplementedError

    def _show_dynamic_routing_analysis(self) -> str:
        """Render the alternate routing analysis."""
        raise NotImplementedError

    def _get_sysop_briefing(self) -> str:
        """Return the UNIX systems operator's shift briefing."""
        raise NotImplementedError

    def _get_switch_briefing(self) -> str:
        """Return the switching technician's shift briefing."""
        raise NotImplementedError

    def _get_field_briefing(self) -> str:
        """Return the field support liaison's shift briefing."""
        raise NotImplementedError

    def _get_noc_briefing(self) -> str:
        """Return the network operations analyst's shift briefing."""
        raise NotImplementedError

    def _get_tsps_briefing(self) -> str:
        """Return the operator services shift briefing."""
        raise NotImplementedError

    def _get_dba_briefing(self) -> str:
        """Return the database administrator's shift briefing."""
        raise NotImplementedError

    def _get_netplan_briefing(self) -> str:
        """Return the network planning engineer's shift briefing."""
        raise NotImplementedError

    def _get_custserv_briefing(self) -> str:
        """Return the customer service technician's shift briefing."""
        raise NotImplementedError

    def _get_radio_briefing(self) -> str:
        """Return the radio technician's shift briefing."""
        raise NotImplementedError

    def _get_tnds_briefing(self) -> str:
        """Return the TNDS analyst's shift briefing."""
        raise NotImplementedError

    def _get_sarts_briefing(self) -> str:
        """Return the SARTS technician's shift briefing."""
        raise NotImplementedError

    def _get_docprep_briefing(self) -> str:
        """Return the document preparation specialist's shift briefing."""
        raise NotImplementedError
