"""
The twelve positions, and what is different about sitting at each of them.

Selecting a role used to change three things: your home directory, one
starting qualification, and a section of the help text. The board was the
same twelve ways over, the same people said the same things to you, and a
planning desk was judged on repair commitments it had no part in.

This is the table that changes that. One record per position, read at four
seams that already existed, and no new subsystem anywhere.

THE RULE THAT DECIDES EVERYTHING ELSE

Every position works the same board, with the same ten faults, the same
report / mlt / dispatch / close verbs and the same two disposition codes.
A desk is never handed work whose vocabulary it has not been taught, and
no desk is ever given LESS work than another - only a different mix of it.

That matters because the point of this simulation is sitting at a UNIX
terminal at work in 1983, not passing twelve telephony examinations. A
switching desk seeing three times the false-cross-and-ground does not have
to know what one is: mlt(1) still names it. What changes is the texture of
the tour, not the amount you have to learn before you can have one.

WHAT IS THE SIMULATION'S OWN

All of it, and it is worth being plain about that. The twelve position
names came with the original codebase and are not drawn from any Bell
System job classification this project has been able to check. The fault
weights, the board share and the ticket preferences are tuning, chosen so
that twelve desks feel different; they are not a claim about how work was
actually distributed in a wire centre. What IS grounded is named where it
appears: the NSPMP component each desk is or is not measured by, and the
admission where no measurement plan covering a desk could be found.
"""

from typing import Dict, NamedTuple, Optional, Tuple


class Position(NamedTuple):
    """One desk, and what is different about working it."""

    key: str
    name: str

    # Commands this desk reaches for, printed as its section of help(1).
    commands: Tuple[str, ...]

    # Multipliers on the draw for what kind of trouble a report is. A bias
    # and never a filter: no weight here is ever zero, so no desk is handed
    # work it cannot recognise, and a wet cable still lands on a switching
    # position now and then because that is what happens.
    fault_bias: Dict[str, float]

    # How much of this desk's work arrives as customer trouble on the board,
    # against how much arrives as tickets and traffic from the control
    # centre. One number, in [0.15, 0.85], because two would let a desk end
    # up quieter on both - and a quieter board has to mean a busier order
    # wire, not an emptier tour. 0.5 is today's behaviour exactly.
    board_share: float

    # Ticket categories this desk gets first refusal on. A preference, not
    # a filter: when nothing of its own is waiting it takes what there is.
    ticket_categories: Tuple[str, ...]

    # Who talks to this desk on top of the whole building. Logins in
    # npc.CRAFT.
    voices: Tuple[str, ...]

    # The network switching performance measurement plan component that
    # measures this desk, or None where no plan covering it was found. The
    # None is not laziness: NSPMP measures a switching machine, and most of
    # these desks are outside its scope. Saying so beats forcing a key.
    nspmp: Optional[str]

    # What the handoff record says this desk did tonight, as counter keys
    # resolved in screens/position.py. Not a score - a tally.
    tally: Tuple[str, ...]


# Today's behaviour, and what an unknown or unselected position gets. Every
# default here is chosen so that role=None is byte for byte what the
# simulation did before this table existed.
NEUTRAL = Position(
    key='', name='', commands=(), fault_bias={}, board_share=0.5,
    ticket_categories=(), voices=(), nspmp='customer_reports', tally=(),
)


POSITIONS: Dict[str, Position] = {

    'sysop': Position(
        key='sysop', name='UNIX Systems Operator',
        commands=('ps', 'df', 'who', 'uucp', 'uulog', 'at', 'date', 'ls'),
        # Nothing about a disc is a loop condition. The board is the board.
        fault_bias={},
        board_share=0.42,
        ticket_categories=('MAINTENANCE',),
        voices=('adm', 'tnakamura'),
        nspmp=None,
        tally=('at_jobs', 'uucp_queue', 'commands_run'),
    ),

    'switch': Position(
        key='switch', name='Switching Station Technician',
        commands=('trunk', 'switch', 'toll', 'crossbar', 'alarm', '5ess',
                  '3a'),
        # The two faults whose `where` is OFFICE rather than LOOP.
        fault_bias={'FCG': 3.0, 'CO_EQUIP': 2.5},
        board_share=0.5,
        ticket_categories=('EQUIPMENT_FAILURE', 'NETWORK_OUTAGE'),
        voices=('rjohnson', 'ehalloran'),
        nspmp='customer_reports',
        tally=('office_faults', 'alarms_open', 'wasted_trips'),
    ),

    'field': Position(
        key='field', name='Field Support Liaison',
        commands=('trace', 'dialtone', 'emergency', 'ticket', 'provision',
                  'sarts'),
        # Everything that puts somebody in a truck.
        fault_bias={'WET': 2.5, 'OPEN': 1.6, 'GROUND': 1.6, 'CROSS': 1.4},
        board_share=0.72,
        ticket_categories=('SERVICE_INTERRUPTION',),
        voices=('lokafor', 'wfinch', 'mreyes'),
        nspmp=None,
        tally=('dispatches', 'wasted_trips', 'sheaths_cleared'),
    ),

    'noc': Position(
        key='noc', name='National NOC Analyst',
        commands=('trunk', 'emergency', 'switch', 'ticket', 'traffic',
                  'tnds', 'satellite'),
        fault_bias={},
        board_share=0.28,
        ticket_categories=('NETWORK_OUTAGE', 'TRAFFIC_ANOMALY'),
        voices=('dpetrak', 'carot'),
        nspmp=None,
        tally=('groups_over', 'alarms_open', 'tickets_worked'),
    ),

    'tsps': Position(
        key='tsps', name='Traffic Service Position System Operator',
        commands=('tsps', 'operator', 'directory', 'collect', 'billing'),
        # A short and a receiver off hook look the same from a position,
        # which is this desk's one good puzzle and costs nothing to learn.
        fault_bias={'ROH': 3.0, 'NONE': 1.4, 'SHORT': 1.3},
        board_share=0.62,
        ticket_categories=('SERVICE_INTERRUPTION',),
        voices=('jhaverty', 'mreyes'),
        nspmp=None,
        tally=('no_trouble_found', 'off_hook_caught', 'commitments_met'),
    ),

    'dba': Position(
        key='dba', name='Database Administrator',
        # CO_EQUIP is the only fault carrying a frame defect, and
        # cosmos jumper already finds it for less than a measurement costs.
        commands=('dbquery', 'custdb', 'billing', 'service'),
        fault_bias={'CO_EQUIP': 3.0, 'FCG': 1.5},
        board_share=0.42,
        ticket_categories=('MAINTENANCE',),
        voices=('lokafor', 'ehalloran'),
        nspmp='customer_reports',
        tally=('found_in_records', 'orders_raised', 'office_faults'),
    ),

    'netplan': Position(
        key='netplan', name='Network Planning Engineer',
        commands=('netplan', 'traffic', 'routing', 'capacity', 'billing',
                  'tnds'),
        fault_bias={},
        board_share=0.25,
        ticket_categories=('TRAFFIC_ANOMALY', 'MAINTENANCE'),
        voices=('ehalloran', 'tnakamura'),
        nspmp=None,
        tally=('groups_over', 'tickets_worked', 'commands_run'),
    ),

    'custserv': Position(
        key='custserv', name='Customer Service Interface Technician',
        # The desk that talks to customers gets the no-trouble-founds.
        commands=('service', 'provision', 'billing', 'custdb', 'directory'),
        fault_bias={'NONE': 1.6, 'ROH': 1.4},
        board_share=0.78,
        ticket_categories=('SERVICE_INTERRUPTION',),
        voices=('mreyes', 'jhaverty'),
        nspmp='customer_reports',
        tally=('commitments_met', 'no_trouble_found', 'repeats'),
    ),

    'radio': Position(
        key='radio', name='Radio/Microwave Technician',
        commands=('radio', 'microwave', 'satellite', 'alarm'),
        fault_bias={},
        board_share=0.3,
        ticket_categories=('EQUIPMENT_FAILURE',),
        voices=('tnakamura', 'gvasquez'),
        nspmp=None,
        tally=('alarms_open', 'weather_now', 'tickets_worked'),
    ),

    'tnds': Position(
        key='tnds', name='Total Network Data System (TNDS) Analyst',
        commands=('tnds', 'traffic', 'capacity', 'trace'),
        fault_bias={},
        board_share=0.3,
        ticket_categories=('TRAFFIC_ANOMALY', 'MAINTENANCE'),
        voices=('carot', 'dpetrak'),
        nspmp=None,
        tally=('groups_over', 'commands_run', 'tickets_worked'),
    ),

    'sarts': Position(
        key='sarts', name='SARTS (Switched Access Remote Test) Technician',
        commands=('sarts', 'testline', 'testcall', 'provision', 'trunk'),
        fault_bias={'FEMF': 1.8, 'CROSS': 1.4},
        board_share=0.4,
        ticket_categories=('SERVICE_INTERRUPTION', 'EQUIPMENT_FAILURE'),
        voices=('gvasquez', 'tnakamura'),
        nspmp=None,
        tally=('circuits_in_trouble', 'tests_run', 'tickets_worked'),
    ),

    'docprep': Position(
        key='docprep', name='Document Preparation Specialist',
        commands=('nroff', 'troff', 'tbl', 'eqn', 'pic', 'refer', 'spell'),
        fault_bias={},
        board_share=0.35,
        ticket_categories=('MAINTENANCE',),
        voices=('dpetrak', 'adm'),
        nspmp=None,
        tally=('documents_set', 'commands_run', 'files_written'),
    ),
}


# The help(1) section for each desk, which used to live in terminal.py as
# ROLE_COMMANDS and is the half of this table that already existed.
POSITION_COMMANDS: Dict[str, list] = {
    key: list(position.commands) for key, position in POSITIONS.items()
}


def get(key: Optional[str]) -> Position:
    """
    Return a position by login name, or the neutral one.

    Everything the simulation did before this table existed is what the
    neutral position produces, so an unselected role, an unknown role and
    the whole test suite all take the same path they always did.
    """
    return POSITIONS.get(key or '', NEUTRAL)
