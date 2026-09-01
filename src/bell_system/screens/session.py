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
from typing import (
    TYPE_CHECKING, Any, Dict, FrozenSet, List, Optional, Set, Tuple,
)

from ..clock import SimClock
from ..filesystem import Node
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

    # Short names the dispatcher expands before looking a command up.
    COMMAND_ALIASES: Dict[str, str]

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

    # Where the working shift is written so it survives being closed, and
    # whether this session picked one up.
    shift_file: str
    resumed: bool

    # The career counters as they stood when this tour opened.
    _tour_baseline: Tuple[int, int, int, int]

    # What hint(1) was last asked about, and how many times. The level
    # resets when the situation changes.
    _hint_situation: str
    _hint_level: int
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
    filesystem: Dict[str, 'Node']
    # What the previous stage of a pipeline produced, for commands that read
    # standard input when given no file arguments.
    _pipe_input: str
    _in_pipeline: bool
    # The running ed session, and the programs cc has built.
    _editor: Any
    _compiled: Dict[str, str]
    processes: List[Dict[str, Any]]
    # Commands queued by at(1), the next job number, and how many uux
    # requests have been spooled this session.
    _at_jobs: List[Dict[str, Any]]
    _at_number: int
    _uux_jobs: int
    # Service orders raised this tour, and the number given out so far.
    _service_orders: List[Dict[str, Any]]
    _order_number: int
    # Batch jobs submitted to the revenue accounting office over the RJE
    # link, and the number given out so far.
    _rje_queue: List[Dict[str, Any]]
    _rje_jobs: int
    # The desk this session is sitting at. Neutral until a role is taken,
    # and neutral is what every session did before positions differed.
    position: Any
    # The office this console has connected to, and the group it watches.
    remote_office: Optional[Any]
    _watched: Optional[List[Any]]
    _office_alarms: Dict[str, List[Any]]
    _scc_assigned: Optional[str]
    _tour_nudges: Any
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

    def _read(self, path: str) -> Optional[str]:
        """Return a file's text, or None if it is not a readable file."""
        raise NotImplementedError

    def _gather(self, args: List[str], command: str) -> tuple:
        """Return (text, error) for a command reading files or stdin."""
        raise NotImplementedError

    def _node(self, path: str) -> Optional[Any]:
        """Return the filesystem entry at a path, or None."""
        raise NotImplementedError

    def editor_input(self, line: str) -> str:
        """Hand one line to the running editor."""
        raise NotImplementedError

    def run_compiled(self, path: str) -> Optional[str]:
        """Return a compiled program's output, or None."""
        raise NotImplementedError

    def write_file(self, path: str, text: str,
                   append: bool = False) -> Optional[str]:
        """Create or replace a file; returns an error string or None."""
        raise NotImplementedError

    def execute_command(self, command_line: str) -> str:
        """Run one command line, as if it had been typed."""
        raise NotImplementedError

    def run_profile(self) -> str:
        """Run the home directory's .profile, the way login does."""
        raise NotImplementedError

    def at_due(self) -> List[str]:
        """Run every at(1) job now due and return what they printed."""
        raise NotImplementedError

    def board_depth(self) -> int:
        """How many open reports this desk carries."""
        raise NotImplementedError

    def ticket_rate(self, base: float) -> float:
        """Scale how often the control centre hands you something."""
        raise NotImplementedError

    def prefer_tickets(self, tickets: List[Any]) -> List[Any]:
        """Narrow unassigned tickets to this desk's kind, if any are."""
        raise NotImplementedError

    def position_voices(self) -> Any:
        """Who talks to this desk on top of the whole building."""
        raise NotImplementedError

    def position_tally(self) -> List[Any]:
        """What this desk did this tour, as label and value."""
        raise NotImplementedError

    def position_measure(self) -> List[str]:
        """What this desk is judged on, and what it is not."""
        raise NotImplementedError

    def current_office(self) -> Any:
        """The office the machine-side screens should be reading."""
        raise NotImplementedError

    def office_is_remote(self) -> bool:
        """Whether the console is on somebody else's office."""
        raise NotImplementedError

    def remote_banner(self) -> str:
        """One line marking a screen that is showing another building."""
        raise NotImplementedError

    def watched_offices(self) -> List[Any]:
        """The offices this control centre has on its console."""
        raise NotImplementedError

    def company_note(self, state: str) -> List[str]:
        """Whose office this is, and where it goes in January."""
        raise NotImplementedError

    def office_alarms(self, office: Any) -> List[Any]:
        """The alarms standing in a given office."""
        raise NotImplementedError

    def office_health(self, office: Any) -> Any:
        """Counted from whatever is standing in that office."""
        raise NotImplementedError

    def scc_assignment(self) -> Optional[str]:
        """The control centre putting an office on you for the tour."""
        raise NotImplementedError

    def next_action(self) -> Any:
        """The single next thing worth doing on this board."""
        raise NotImplementedError

    def next_line(self) -> str:
        """The standing prompt, or nothing."""
        raise NotImplementedError

    def guidance_rows(self) -> List[str]:
        """The WHAT TO DO NOW block at the top of help(1)."""
        raise NotImplementedError

    def dead_end(self, message: str) -> str:
        """Put a way out on the end of a refusal."""
        raise NotImplementedError

    def shift_time(self) -> str:
        """How far into the shift the operator is, as h:mm."""
        raise NotImplementedError

    def generate_shift_events(self) -> None:
        """Build the schedule of events this tour will bring due."""
        raise NotImplementedError

    def cmd_shift(self, args: Optional[List[str]] = None) -> str:
        """Where you are in the tour."""
        raise NotImplementedError

    def _tour_worked(self) -> Tuple[int, int, int, int]:
        """Closed, correct, missed and repeats for this tour alone."""
        raise NotImplementedError

    def save_shift(self) -> None:
        """Write the shift down where the next session will find it."""
        raise NotImplementedError

    def cmd_hint(self, args: Optional[List[str]] = None) -> str:
        """Ask somebody. Ask again and you get more."""
        raise NotImplementedError

    def tour_summary(self, closed: int, correct: int, missed: int,
                     repeats: int) -> List[str]:
        """Three sentences on a tour, written from its tally."""
        raise NotImplementedError

    def sparkline(self, values: List[float], span: int = 5) -> str:
        """Draw the last few figures as a bar, so a trend reads."""
        raise NotImplementedError

    def first_tour(self, after_close: bool = False) -> bool:
        """Whether this is somebody's first ten minutes on the job."""
        raise NotImplementedError

    def first_tour_nudge(self, step: str) -> Optional[str]:
        """The wire chief walking a new craftsperson through one report."""
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
