"""
The main distributing frame, COSMOS assignment and CLLI coding.
"""
from ..data.clli import build as build_clli
from ..data.clli import parse as parse_clli
import random
from datetime import timedelta
from typing import (
    Any,
    Dict,
    List,
    Optional,
)
from ..data.clli import (
    ATTESTED_CLLI,
    STATE_CODES,
    describe_entity,
    entity_for_switch,
)


from .session import SessionState


class FrameCommands(SessionState):
    """
    The main distributing frame, COSMOS assignment and CLLI coding.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

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
                if parsed is None:
                    output += "  will not parse as a CLLI code\n"
                else:
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
