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
    TYPE_CHECKING, Any, Dict, FrozenSet, List, Mapping, Optional, Set, Tuple,
)

from ..clock import SimClock
from ..filesystem import Node
from ..progression import Career, Difficulty, Kpis
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
    # Set when 'career new' files the career: nothing this session does from
    # then on is written to the career's files, or to the player's home.
    _career_filed: bool = False
    _home_locked: bool = False

    # The career counters as they stood when this tour opened.
    _tour_baseline: Tuple[int, int, int, int]

    # What hint(1) was last asked about, and how many times. The level
    # resets when the situation changes.
    _hint_situation: str
    _hint_level: int
    # What a practical's stage moved or said, for its strike and its re-brief.
    _practical_memory: Dict[str, Any]
    shift_minutes: int
    shift_events: List[Dict[str, Any]]
    shift_handoff: Dict[str, Any]
    _charged_total: int
    _tour_desk_start: int
    _board_reviewed: bool
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
    alarm_deck: List[Dict[str, Any]]

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
    _command_depth: int
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
    users: List[Dict[str, Any]]
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

    def _office_clear(self, args: List[str]) -> str:
        """Clear a false cross or ground from the switch side."""
        raise NotImplementedError

    def _difficulty(self) -> Difficulty:
        """Return the active difficulty profile."""
        raise NotImplementedError

    def _reading_stage(self, report: Any, count: bool = True) -> str:
        """Return how much to say about a report's fault, and count it."""
        raise NotImplementedError

    def _stamp(self) -> str:
        """Return a timestamp in the form the messaging channels carried."""
        raise NotImplementedError

    def start_tour_clock(self) -> None:
        """Put the clock on this tour's day and the hour of its watch."""
        raise NotImplementedError

    def _read(self, path: str) -> Optional[str]:
        """Return a file's text, or None if it is not a readable file."""
        raise NotImplementedError

    def _gather(self, args: List[str], command: str,
                note: bool = False) -> tuple:
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

    def _setup_logging(self) -> None:
        """Apply the logging settings."""
        raise NotImplementedError

    def write_file(self, path: str, text: str,
                   append: bool = False) -> Optional[str]:
        """Create or replace a file; returns an error string or None."""
        raise NotImplementedError

    def put_file(self, path: str, text: str,
                 append: bool = False) -> Optional[str]:
        """Write a file as the machine does, whoever owns it."""
        raise NotImplementedError

    def store_node(self, path: str, node: Node,
                   command: str = 'sh') -> Optional[str]:
        """Put a node in the tree, or return why it would not fit."""
        raise NotImplementedError

    def execute_command(self, command_line: str) -> str:
        """Run one command line, as if it had been typed."""
        raise NotImplementedError

    def run_profile(self) -> str:
        """Run the home directory's .profile, the way login does."""
        raise NotImplementedError

    def cmd_qual(self, args: Optional[List[str]] = None) -> str:
        """Show the craft record, which career(1) falls back to."""
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

    def is_in(self, login: str) -> bool:
        """Whether this person is in the building on the tour being worked."""
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

    def _pass_time(self, minutes: int) -> None:
        """Let shift minutes go by that nobody spent on a report."""
        raise NotImplementedError

    def _named_section(self, words: str
                       ) -> Tuple[str, Optional[Tuple[int, int]], str]:
        """Split a cable and binder group off the end of a dispatch."""
        raise NotImplementedError

    def _section_asked(self, force: str,
                       section: Optional[Tuple[int, int]]) -> str:
        """Refuse a Cable repair dispatch that does not say where to go."""
        raise NotImplementedError

    def cmd_cable(self, args: Optional[List[str]] = None) -> str:
        """The binder groups of a 600-pair cable."""
        raise NotImplementedError

    def _report_callback(self, token: str, topic: Optional[str] = None
                         ) -> str:
        """Ring a customer back, with a question or without."""
        raise NotImplementedError

    def _dispatch_job(self, token: str, force: str) -> str:
        """Send a crew to a job the plant opened for itself."""
        raise NotImplementedError

    def _fraud_block(self) -> str:
        """The toll holding-time exception, while there is one."""
        raise NotImplementedError

    def _fraud_events(self) -> List[Any]:
        """The note about it, once."""
        raise NotImplementedError

    def _plant_case(self) -> None:
        """Decide whether this tour's trouble has a shared cause."""
        raise NotImplementedError

    def _case_events(self) -> List[Any]:
        """Let whatever reports a cause has thrown come onto the board."""
        raise NotImplementedError

    def _case_cleared(self, report: Any) -> None:
        """Say once that the cause behind a report has been cleared."""
        raise NotImplementedError

    def _is_own_section(self, report: Any,
                        section: Optional[Tuple[int, int]]) -> bool:
        """Whether a dispatch's section is the one the report is in."""
        raise NotImplementedError

    def _advance_shift(self) -> List[str]:
        """Charge the shift for the work just done and fire what is due."""
        raise NotImplementedError

    def _end_shift(self) -> str:
        """Sign off: bank the index and start the next tour."""
        raise NotImplementedError

    def _time_is_up(self) -> str:
        """Eight hours are worked: relief takes the position."""
        raise NotImplementedError

    def _relief_due(self) -> str:
        """The handoff, if the tour has run its eight hours."""
        raise NotImplementedError

    def tour_minute(self) -> int:
        """The shift minute the desks count their windows against."""
        raise NotImplementedError

    def generate_shift_events(self) -> None:
        """Build the schedule of events this tour will bring due."""
        raise NotImplementedError

    def deliver_news(self) -> None:
        """File the articles the feed has brought in by this tour."""
        raise NotImplementedError

    def deliver_fragments(self) -> None:
        """Put the files that have arrived by this tour on the machine."""
        raise NotImplementedError

    def sync_groups(self) -> None:
        """Record the groups the held sign-offs give."""
        raise NotImplementedError

    def _note_read(self, path: str) -> None:
        """Record that a file has been put in front of the player."""
        raise NotImplementedError

    def take_find_notice(self) -> str:
        """Return the one-time note about finds, once, if it is due."""
        raise NotImplementedError

    def tour_script(self) -> Optional[Any]:
        """This tour's entry in data/tours.py, if the calendar fits."""
        raise NotImplementedError

    def tour_brief(self, counts: Optional[Mapping[str, int]] = None
                   ) -> List[str]:
        """The tour's theme, briefing and goals, as printed lines."""
        raise NotImplementedError

    def cmd_shift(self, args: Optional[List[str]] = None) -> str:
        """Where you are in the tour."""
        raise NotImplementedError

    def _tour_worked(self) -> Tuple[int, int, int, int]:
        """Closed, correct, missed and repeats for this tour alone."""
        raise NotImplementedError

    def desk_overdue(self) -> int:
        """What this desk holds past its window, beyond the board."""
        raise NotImplementedError

    def add_mailbox(self) -> None:
        """Put this position's mailbox under /usr/spool/mail."""
        raise NotImplementedError

    def _sync_report_files(self) -> None:
        """Keep one file per pending report under /usr/lmos."""
        raise NotImplementedError

    def save_shift(self) -> None:
        """Write the shift down where the next session will find it."""
        raise NotImplementedError

    def cmd_hint(self, args: Optional[List[str]] = None) -> str:
        """Ask somebody. Ask again and you get more."""
        raise NotImplementedError

    def tour_summary(self, closed: int, correct: int, missed: int,
                     repeats: int, unmeasured: int = 0) -> List[str]:
        """Three sentences on a tour, written from its tally."""
        raise NotImplementedError

    def sparkline(self, values: List[float], span: int = 5) -> str:
        """Draw the last few figures as a bar, so a trend reads."""
        raise NotImplementedError

    def kpi_rows(self, kpis: Kpis, heading: str) -> List[str]:
        """The five KPIs under a heading, with the PROVISIONAL label."""
        raise NotImplementedError

    def tour_index_row(self) -> str:
        """This tour's own index, beside the cumulative one."""
        raise NotImplementedError

    def board_meter(self) -> str:
        """How much of this tour's board has been cleared."""
        raise NotImplementedError

    def credit_rows(self) -> List[str]:
        """The tour's index, its meter and its KPIs."""
        raise NotImplementedError

    def commendation_lines(self, earned: List[str]) -> List[str]:
        """The commendations earned this tour, named."""
        raise NotImplementedError

    def commendation_roll(self) -> List[str]:
        """Every commendation, marked where it is held."""
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

    def _offer_qualifications(self) -> List[str]:
        """Say once that a sign-off is ready for its practical."""
        raise NotImplementedError

    def _practical_open(self) -> Optional[Tuple[Any, Any]]:
        """The practical on the board and the report it staged."""
        raise NotImplementedError

    def _practical_key(self) -> Optional[str]:
        """The sign-off whose practical is on the board, if one is."""
        raise NotImplementedError

    def _may_use(self, command: str, action: str = '') -> bool:
        """Whether a command is open to the operator, a practical included."""
        raise NotImplementedError

    def _practical_hints(self) -> List[Tuple[str, List[str]]]:
        """The nudges for the practical on the board, smallest first."""
        raise NotImplementedError

    def _abandon_practical(self) -> None:
        """End a practical that was never handed in."""
        raise NotImplementedError

    def _qual_practical(self, args: List[str]) -> str:
        """Take a practical, or hand one in."""
        raise NotImplementedError

    def reports_all(self) -> List[Any]:
        """Return every report the desk has seen this session."""
        raise NotImplementedError

    def _charged_minutes(self) -> int:
        """The desk minutes charged so far, reports and plant jobs."""
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
