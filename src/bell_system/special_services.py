"""
Special services circuits, and the systems that reached them remotely.

Engineering and Operations in the Bell System draws the line this way:
ordinary services are residence, public telephone, mobile and basic
individual-line business service, and "all other services are considered
special services (often called specials)". Specials "require special
treatment with respect to transmission, signaling, switching, billing, or
customer use and are used mostly by business customers", and there were about
twenty-five major categories of them. The document names foreign exchange
service, Wide Area Telecommunications Service, private branch exchange and
centrex, and private-line and private network services.

Two systems get a circuit onto a test set without anybody driving anywhere.
The Switched Maintenance Access System, "through the use of relays, provides
concentrated metallic access to individual circuits to permit remote access
and testing by the Switched Access Remote Test System (SARTS)". In the
digital environment, digital access and cross-connect test access served as
an alternative to jack or SMAS arrangements.

Not verified, and marked rather than hidden: circuit identifiers here follow
a plausible shape rather than the COMMON LANGUAGE circuit identification
format, which no document available to this project sets out in full. The
per-category circuit counts and the trouble rates are the simulation's own.
"""

import random
from typing import Dict, List, NamedTuple, Optional, Tuple

from .data.positions import desk_only


class ServiceCategory(NamedTuple):
    """One major category of special service."""

    code: str
    name: str
    description: str
    # Whether the category is attested by name in the bundled documents.
    attested: bool
    # Two-wire or four-wire, which decides what can be measured on it.
    wires: int


CATEGORIES: Dict[str, ServiceCategory] = {
    'FX': ServiceCategory(
        'FX', 'Foreign exchange',
        'A line served by an office other than the one the customer sits in, '
        'so calls to that exchange are local to them.',
        attested=True, wires=2),
    'WATS': ServiceCategory(
        'WATS', 'Wide Area Telecommunications Service',
        'Bulk-rated long distance over a dedicated access line, outward or '
        'inward.',
        attested=True, wires=2),
    'PBX': ServiceCategory(
        'PBX', 'PBX trunk',
        'Trunk between a customer switchboard and the serving office.',
        attested=True, wires=2),
    'CTX': ServiceCategory(
        'CTX', 'Centrex',
        'Switching served from the central office rather than customer '
        'premises, with direct inward dialling.',
        attested=True, wires=2),
    'PL': ServiceCategory(
        'PL', 'Private line',
        'A dedicated circuit between fixed points, not switched.',
        attested=True, wires=4),
    'PN': ServiceCategory(
        'PN', 'Private network',
        'A customer network of private lines and switching.',
        attested=True, wires=4),
    'DATA': ServiceCategory(
        'DATA', 'Data circuit',
        'Conditioned circuit carrying data at a stated rate.',
        attested=False, wires=4),
    'PGM': ServiceCategory(
        'PGM', 'Program audio',
        'Wideband audio for broadcast distribution.',
        attested=False, wires=4),
    'OCC': ServiceCategory(
        'OCC', 'Other common carrier access',
        'Local distribution and network access provided to a competing '
        'carrier.',
        attested=True, wires=4),
}

# How the categories turn up in a wire centre's special services inventory.
_CATEGORY_WEIGHTS: Tuple[Tuple[str, int], ...] = (
    ('PBX', 26), ('FX', 18), ('WATS', 16), ('PL', 14),
    ('CTX', 10), ('DATA', 8), ('PN', 4), ('OCC', 3), ('PGM', 1),
)

# Access arrangements a circuit can be reached through.
ACCESS_ARRANGEMENTS: Dict[str, str] = {
    'SMAS': 'Switched Maintenance Access System. Relays give concentrated '
            'metallic access to individual circuits for remote testing.',
    'DACS': 'Digital access and cross-connect test access, an alternative to '
            'jack or SMAS arrangements in the digital environment.',
    'JACK': 'Manual jack access at the office. Somebody has to be there.',
}

STATUS_IN_SERVICE = 'IS'
STATUS_TROUBLE = 'TRBL'
STATUS_OUT = 'OOS'

# Where a failing special service can be bad, in the order a loop-back test
# walks them: the equipment at this office, the interoffice facility
# (Engineering and Operations notes that specials troubles "may be traced to
# interoffice facilities"), and the customer's end. The shift minutes a
# repair takes at each place are the simulation's own.
PLACES: Dict[str, Tuple[str, int]] = {
    'OFFICE': ('the equipment at this office', 10),
    'FACILITY': ('the interoffice facility', 20),
    'PREMISES': ("the customer's end", 15),
}

# Looping a circuit back at a point costs the shift this much when the
# access arrangement can do it by relay, and much more when somebody has to
# go and plug in at the jack. Also the simulation's own.
LOOP_REMOTE_MINUTES = 3
LOOP_VISIT_MINUTES = 15


class Circuit:
    """One special services circuit as the test system sees it."""

    def __init__(self, circuit_id: str, category: str, customer: str,
                 from_clli: str, to_clli: str, access: str,
                 status: str = STATUS_IN_SERVICE, impaired: bool = False):
        self.circuit_id = circuit_id
        self.category = category
        self.customer = customer
        self.from_clli = from_clli
        self.to_clli = to_clli
        self.access = access
        self.status = status
        # The electrical truth, revealed only by measuring it.
        self.impaired = impaired
        self.last_result: Optional[str] = None
        # Where the impairment sits, which only a loop-back test shows.
        self.fault_place: Optional[str] = None
        # Shift minutes held in trouble this tour.
        self.out_minutes = 0

    @property
    def service(self) -> ServiceCategory:
        """Return the category this circuit belongs to."""
        return CATEGORIES[self.category]

    @property
    def wires(self) -> int:
        """Return whether the circuit is two-wire or four-wire."""
        return self.service.wires

    def reachable(self) -> bool:
        """Return whether SARTS can get to this circuit without a visit."""
        return self.access in ('SMAS', 'DACS')


# Customer names for the inventory. Ordinary period business names; no real
# subscriber or firm is depicted.
_CUSTOMERS: Tuple[str, ...] = (
    'Amalgamated Casualty', 'Bergen County Trust', 'Calumet Steel',
    'Delaware Valley Press', 'Eastern Freight Lines', 'Fairlawn Savings',
    'Great Lakes Chemical', 'Hudson Terminal Warehouse', 'Idlewild Motors',
    'Jersey Central Dairy', 'Keystone Insurance', 'Lakeshore Broadcasting',
    'Meridian Data Services', 'Northfield Hospital', 'Orchard Park Schools',
    'Piedmont Textiles', 'Queensboro Wholesale', 'Riverside Foundry',
)


class SartsInventory:
    """
    The special services circuits a test position can reach.

    Generated once for a wire centre, then worked. Impairment is hidden until
    a circuit is measured, the same way a loop fault is.
    """

    def __init__(self, home_clli: str, rng: Optional[random.Random] = None,
                 count: int = 24):
        self.home_clli = home_clli
        self.rng = rng or random.Random()
        self.circuits: Dict[str, Circuit] = {}
        self._build(count)

    def _circuit_id(self, category: str, serial: int) -> str:
        """
        Return a circuit identifier.

        Shape only. The COMMON LANGUAGE circuit identification format is not
        set out in any document available to this project, so this is the
        simulation's own and is marked as such.
        """
        return f"{serial:04d}-{category}-{self.rng.randint(100, 999)}"

    def _build(self, count: int) -> None:
        """Generate the wire centre's special services inventory."""
        codes = [code for code, _ in _CATEGORY_WEIGHTS]
        weights = [weight for _, weight in _CATEGORY_WEIGHTS]
        for serial in range(1, count + 1):
            category = self.rng.choices(codes, weights=weights)[0]
            access = self.rng.choices(
                ('SMAS', 'DACS', 'JACK'), weights=(62, 24, 14))[0]
            impaired = self.rng.random() < 0.25
            status = STATUS_TROUBLE if impaired and self.rng.random() < 0.5 \
                else STATUS_IN_SERVICE
            circuit = Circuit(
                circuit_id=self._circuit_id(category, serial),
                category=category,
                customer=self.rng.choice(_CUSTOMERS),
                from_clli=self.home_clli,
                to_clli=f"{self.rng.choice(('NWRK', 'NYCM', 'PHLA', 'BSTN'))}"
                        f"{self.rng.choice(('NJ', 'NY', 'PA', 'MA'))}"
                        f"CG{self.rng.randint(0, 9)}",
                access=access,
                status=status,
                impaired=impaired,
            )
            if impaired:
                # Its own generator, keyed on the circuit, so that giving a
                # fault a place leaves every later draw of the inventory
                # exactly where it was.
                circuit.fault_place = random.Random(
                    f"place:{circuit.circuit_id}").choices(
                        list(PLACES), weights=(3, 4, 3))[0]
            self.circuits[circuit.circuit_id] = circuit

    # -- the outage clock ---------------------------------------------------

    _tour = 0
    _clocked_to = 0

    def accrue(self, tour: int, now: int) -> None:
        """
        Charge every circuit held in trouble for the shift minutes since the
        last look.

        Called before anything that changes a status, so the minutes a
        circuit was out are exact. A new tour starts the count again, as it
        starts the shift clock again.
        """
        if tour != self._tour or now < self._clocked_to:
            self._tour = tour
            self._clocked_to = 0
            for circuit in self.circuits.values():
                circuit.out_minutes = 0
        span = now - self._clocked_to
        for circuit in self.in_trouble():
            circuit.out_minutes += span
        self._clocked_to = now

    def minutes_out(self) -> int:
        """Circuit-minutes out of service this tour, repaired or not."""
        return sum(circuit.out_minutes for circuit in self.circuits.values())

    # -- access ----------------------------------------------------------

    def find(self, token: str) -> Optional[Circuit]:
        """Look a circuit up by identifier, or by position in the listing."""
        token = token.strip().upper()
        if token in self.circuits:
            return self.circuits[token]
        for circuit_id, circuit in self.circuits.items():
            if circuit_id.startswith(token) or token in circuit_id:
                return circuit
        if token.isdigit():
            listing = self.listing()
            position = int(token)
            if 1 <= position <= len(listing):
                return listing[position - 1]
        return None

    def listing(self) -> List[Circuit]:
        """Return the inventory, circuits in trouble first."""
        order = {STATUS_TROUBLE: 0, STATUS_OUT: 1, STATUS_IN_SERVICE: 2}
        return sorted(self.circuits.values(),
                      key=lambda c: (order.get(c.status, 3), c.circuit_id))

    def in_trouble(self) -> List[Circuit]:
        """Return circuits currently reported in trouble."""
        return [c for c in self.circuits.values() if c.status == STATUS_TROUBLE]

    def by_category(self) -> Dict[str, int]:
        """Return how many circuits sit in each category."""
        counts: Dict[str, int] = {}
        for circuit in self.circuits.values():
            counts[circuit.category] = counts.get(circuit.category, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: -item[1]))

    def by_access(self) -> Dict[str, int]:
        """Return how many circuits sit behind each access arrangement."""
        counts: Dict[str, int] = {}
        for circuit in self.circuits.values():
            counts[circuit.access] = counts.get(circuit.access, 0) + 1
        return counts

    def remotely_testable(self) -> int:
        """Return how many circuits SARTS can reach without a visit."""
        return sum(1 for circuit in self.circuits.values() if circuit.reachable())


class SartsConsole:
    """
    The Switched Access Remote Test System position.

    Reaches special services circuits through their access arrangement and
    measures them with the same test line series a trunk is proved on, since
    that is what the position had. Circuits behind a manual jack cannot be
    reached from here, which is the point of the distinction.
    """

    def __init__(self, terminal):
        self.terminal = terminal

    def command(self, args: Optional[List[str]] = None) -> str:
        """Dispatch a ``sarts`` subcommand."""
        args = args or []
        if not args:
            return self.status()

        action = args[0].lower()
        rest = args[1:]
        if action == 'status':
            return self.status()
        if action in ('list', 'inventory'):
            return self.inventory(rest[0] if rest else None)
        if action in ('circuit', 'detail', 'show'):
            if not rest:
                return "sarts: usage: sarts circuit <circuit id>"
            return self.circuit(rest[0])
        if action == 'test':
            if not rest:
                return "sarts: usage: sarts test <circuit id>"
            return self.test(rest[0])
        if action == 'trouble':
            return self.trouble_board()
        if action == 'repair':
            return self.repair(rest)
        if action == 'access':
            return self.access()
        if action in ('categories', 'services'):
            return self.categories()
        return (f"sarts: unknown option '{args[0]}'\n"
                "Options: status, list, circuit, test, trouble, repair, "
                "access, categories")

    # -- screens ---------------------------------------------------------

    @property
    def inventory_state(self) -> SartsInventory:
        """Return the terminal's special services inventory."""
        return self.terminal.special_services

    def clock(self) -> None:
        """Bring the outage clock up to the shift clock."""
        self.inventory_state.accrue(self.terminal.career.shift,
                                    self.terminal.shift_minutes)

    def status(self) -> str:
        """Render the test position's overall picture."""
        self.clock()
        inventory = self.inventory_state
        office = self.terminal.home_office
        trouble = inventory.in_trouble()
        return '\n'.join([
            "Switched Access Remote Test System",
            f"{office['city']}, {office['state']}  {office['clli']}   "
            f"{self.terminal.clock.timestamp()}",
            '=' * 74,
            '',
            'SPECIAL SERVICES INVENTORY',
            f"  Circuits on this position   {len(inventory.circuits):>6}",
            f"  Reported in trouble         {len(trouble):>6}",
            f"  Reachable without a visit   {inventory.remotely_testable():>6}",
            f"  Circuit-minutes out, tour   {inventory.minutes_out():>6}",
            '',
            'ACCESS ARRANGEMENTS',
            *[f"  {code:<6}{count:>4}   {ACCESS_ARRANGEMENTS[code].split('.')[0]}."
              for code, count in sorted(inventory.by_access().items())],
            '',
            "  Special services require special treatment as to transmission,",
            "  signalling, switching, billing or customer use, and are used",
            "  mostly by business customers. There were about twenty-five",
            "  major categories.",
            '',
            "  sarts list        The inventory",
            "  sarts trouble     Circuits reported in trouble",
            "  sarts test <id>   Reach a circuit and measure it",
            "  sarts repair <id> Loop a failing circuit back, then send "
            "a force",
            "  sarts categories  What counts as a special service",
        ])

    def inventory(self, status_filter: Optional[str] = None) -> str:
        """Render the circuit inventory, optionally filtered by status."""
        circuits = self.inventory_state.listing()
        if status_filter:
            wanted = status_filter.upper()
            circuits = [c for c in circuits if c.status == wanted]
            if not circuits:
                return f"No circuits with status {wanted}."

        lines = [
            "Special Services Circuits",
            '=' * 74,
            f"{'#':>3} {'CIRCUIT':<14}{'SERVICE':<26}{'ACCESS':<7}{'ST':<6}"
            f"{'W':<3}CUSTOMER",
            '-' * 74,
        ]
        for position, circuit in enumerate(circuits, 1):
            mark = '!' if circuit.status == STATUS_TROUBLE else ' '
            lines.append(
                f"{position:>3}{mark}{circuit.circuit_id:<14}"
                f"{circuit.service.name[:25]:<26}{circuit.access:<7}"
                f"{circuit.status:<6}{circuit.wires:<3}{circuit.customer[:22]}"
            )
        lines.append('-' * 74)
        lines.append(f"{len(circuits)} circuit(s). "
                     f"'sarts test <circuit>' to measure one.")
        return '\n'.join(lines)

    def circuit(self, token: str) -> str:
        """Render one circuit's record."""
        circuit = self.inventory_state.find(token)
        if circuit is None:
            return f"sarts: no circuit matching '{token}'"

        service = circuit.service
        attested = ('attested in the bundled documents' if service.attested
                    else "this simulation's own category")
        lines = [
            f"Circuit {circuit.circuit_id}",
            '=' * 74,
            f"  Service              {service.name} ({service.code})",
            f"  Customer             {circuit.customer}",
            f"  From                 {circuit.from_clli}",
            f"  To                   {circuit.to_clli}",
            f"  Facility             {circuit.wires}-wire",
            f"  Access               {circuit.access}",
            f"  Status               {circuit.status}",
            '',
            f"  {service.description}",
            f"  Category is {attested}.",
            '',
            f"  {ACCESS_ARRANGEMENTS[circuit.access]}",
        ]
        if circuit.last_result:
            lines.extend(['', 'LAST MEASUREMENT', f"  {circuit.last_result}"])
        if not circuit.reachable():
            lines.extend([
                '',
                "  This circuit is on manual jack access. SARTS cannot reach",
                "  it; somebody has to be at the office.",
            ])
        else:
            lines.append(f"\n  sarts test {circuit.circuit_id}")
        return '\n'.join(lines)

    def test(self, token: str) -> str:
        """Reach a circuit through its access arrangement and measure it."""
        from .data.testlines import TEST_LINES
        from .loop_testing import access_test_line, tone_header

        self.clock()
        circuit = self.inventory_state.find(token)
        if circuit is None:
            return f"sarts: no circuit matching '{token}'"
        if not circuit.reachable():
            return (f"{circuit.circuit_id} is on manual jack access.\n\n"
                    "SARTS reaches circuits through the Switched Maintenance "
                    "Access System,\nwhich uses relays to give concentrated "
                    "metallic access, or through digital\naccess and "
                    "cross-connect test access. Neither is fitted here, so "
                    "this one\nneeds somebody at the office.")

        # A four-wire circuit supports the full two-way responder; a two-wire
        # circuit gets the one-way loss and noise measurement.
        code = '105' if circuit.wires == 4 else '100'
        result = access_test_line(code, circuit.circuit_id,
                                  degraded=circuit.impaired)
        if result is None:  # pragma: no cover - both codes are in the table
            return (f"sarts: the {code}-type test line is not available on "
                    f"this position.")
        test_line = TEST_LINES[code]

        lines = [
            f"SARTS Test - {circuit.circuit_id}",
            f"{circuit.customer}   {circuit.service.name}",
            f"{self.terminal.clock.timestamp()}",
            '=' * 74,
            f"  Access               {circuit.access}",
            f"  Facility             {circuit.wires}-wire",
            f"  Test line            {test_line.name}",
            f"  {tone_header()}",
            '',
        ]
        if result.loss_db is not None:
            lines.append(f"  {'Loss at 1004 Hz':<24}{result.loss_db:>8.1f} dB")
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

        circuit.last_result = (
            f"{self.terminal.clock.time()} {code}-type: "
            f"{'pass' if result.passed else 'FAIL'}")
        if result.passed and circuit.status == STATUS_TROUBLE:
            circuit.status = STATUS_IN_SERVICE
            lines.append("")
            lines.append("  Circuit measures clean. Returned to service.")
        elif not result.passed:
            circuit.status = STATUS_TROUBLE
            lines.append("")
            lines.append("  Circuit held in trouble. A special service out of")
            lines.append("  limits should not go back to the customer.")
            lines.append(f"  sarts repair {circuit.circuit_id}")
        return '\n'.join(lines)

    # -- the circuits in trouble, and fixing them ---------------------------

    def trouble_board(self) -> str:
        """
        The circuits held in trouble, with how long each has been out.

        Every minute on this board is the customer's, and the shift clock
        is what counts it. The ACCESS column is the part worth reading: it
        decides what finding the trouble costs.
        """
        self.clock()
        circuits = [c for c in self.inventory_state.listing()
                    if c.status == STATUS_TROUBLE]
        if not circuits:
            return "No circuits held in trouble."
        lines = [
            "Special Services Circuits Held In Trouble",
            f"Shift time {self.terminal.shift_time()}",
            '=' * 74,
            f"{'#':>3} {'CIRCUIT':<14}{'ACCESS':<7}{'OUT':>6}  "
            f"{'LOOP':<10}CUSTOMER",
            '-' * 74,
        ]
        for position, circuit in enumerate(circuits, 1):
            cost = (LOOP_REMOTE_MINUTES if circuit.reachable()
                    else LOOP_VISIT_MINUTES)
            how = 'by relay' if circuit.reachable() else 'a visit'
            lines.append(
                f"{position:>3} {circuit.circuit_id:<14}{circuit.access:<7}"
                f"{circuit.out_minutes:>5}m  {cost:>2}m {how:<6} "
                f"{circuit.customer[:22]}")
        lines.append('-' * 74)
        out = self.inventory_state.minutes_out()
        lines.append(f"{len(circuits)} circuit(s), {out} circuit-minutes "
                     f"out this tour.")
        lines.append("'sarts repair <circuit>' loops one back.")
        return '\n'.join(lines)

    def repair(self, rest: List[str]) -> str:
        """
        Find where a failing circuit is bad, then send the force for it.

        ``sarts repair <id>`` loops the circuit back at each point the
        arrangement can reach and prints what each loop read: the first
        loop that fails brackets the trouble. ``sarts repair <id> <place>``
        sends the force for that place. The right one clears it; the wrong
        one finds nothing and the circuit stays out while the clock runs.

        The SSC desk's own verb. Special services are tested from one
        position, and the position's job is to say where to send people.
        """
        refusal = desk_only(self.terminal.position, 'sarts', 'sarts repair')
        if refusal:
            return refusal
        if not rest:
            return ("sarts: usage: sarts repair <circuit id> [office | "
                    "facility | premises]")
        self.clock()
        circuit = self.inventory_state.find(rest[0])
        if circuit is None:
            return f"sarts: no circuit matching '{rest[0]}'"
        if circuit.status != STATUS_TROUBLE:
            return (f"{circuit.circuit_id} is not held in trouble.\n"
                    f"A circuit comes to repair once it has failed a "
                    f"measurement: sarts test {circuit.circuit_id}")
        if len(rest) == 1:
            return self.loop_back(circuit)
        place = rest[1].upper()
        if place not in PLACES:
            return (f"sarts repair: '{rest[1]}' is not a place to send "
                    f"anyone.\nPlaces: office, facility, premises.")
        return self.send_force(circuit, place)

    def spend(self, minutes: int) -> None:
        """Let the shift clock run, and charge the circuits for it."""
        self.terminal._pass_time(minutes)
        self.clock()

    def loop_back(self, circuit: Circuit) -> str:
        """Loop a failing circuit back at each point and print the reads."""
        visit = not circuit.reachable()
        self.spend(LOOP_VISIT_MINUTES if visit else LOOP_REMOTE_MINUTES)
        failing_from = list(PLACES).index(circuit.fault_place or 'OFFICE')
        points = (
            ("this office, at the access point", 'OFFICE'),
            (f"the far end of the facility, {circuit.to_clli}", 'FACILITY'),
            ("the customer's end", 'PREMISES'),
        )
        lines = [
            f"SARTS Loop-back - {circuit.circuit_id}",
            f"{circuit.customer}   {circuit.service.name}",
            f"{self.terminal.clock.timestamp()}",
            '=' * 74,
        ]
        if visit:
            lines += [f"  {circuit.access}: somebody went to the jack and "
                      f"looped it by hand.", '']
        for index, (where, _) in enumerate(points):
            lines.append(f"  Loop at {where:<48}"
                         f"{'FAIL' if index >= failing_from else 'PASS'}")
        lines += [
            '',
            "  Each loop reads everything between it and this office. The",
            "  trouble is in the stretch after the last loop that passed.",
            f"  Out {circuit.out_minutes} minutes this tour.",
            f"  sarts repair {circuit.circuit_id} <office | facility | "
            f"premises>",
        ]
        return '\n'.join(lines)

    def send_force(self, circuit: Circuit, place: str) -> str:
        """Send the force for a place; it clears the circuit or finds nothing."""
        where, minutes = PLACES[place]
        self.spend(minutes)
        if place != circuit.fault_place:
            return '\n'.join([
                f"{circuit.circuit_id}: the force went to {where} and found "
                f"nothing.",
                f"That took {minutes} minutes of the shift. The circuit is "
                f"still out",
                f"({circuit.out_minutes} minutes this tour); the loops read "
                f"as they did.",
            ])
        circuit.impaired = False
        circuit.fault_place = None
        circuit.status = STATUS_IN_SERVICE
        circuit.last_result = (f"{self.terminal.clock.time()} cleared at "
                               f"{place.lower()}")
        return '\n'.join([
            f"{circuit.circuit_id}: the force cleared the trouble at "
            f"{where}.",
            f"It measures clean and is back in service for "
            f"{circuit.customer}.",
            f"Out {circuit.out_minutes} minutes this tour.",
        ])

    def access(self) -> str:
        """Explain the access arrangements a circuit can sit behind."""
        inventory = self.inventory_state
        counts = inventory.by_access()
        lines = ["Test Access Arrangements", '=' * 74, '']
        for code, description in ACCESS_ARRANGEMENTS.items():
            lines.append(f"  {code}  ({counts.get(code, 0)} circuits)")
            lines.append(f"      {description}")
            lines.append('')
        lines.append("  SMAS and DACS are reachable from this position. A "
                     "circuit on jack")
        lines.append("  access needs somebody at the office.")
        return '\n'.join(lines)

    def categories(self) -> str:
        """List the special service categories and what they are."""
        counts = self.inventory_state.by_category()
        lines = [
            "Special Service Categories",
            '=' * 74,
            "Ordinary service is residence, public telephone, mobile and "
            "basic",
            "individual-line business service. Everything else is a special "
            "service.",
            "There were about twenty-five major categories; these are the "
            "ones this",
            "position carries.",
            '',
            f"{'CODE':<7}{'SERVICE':<34}{'WIRES':>6}{'ON HAND':>9}  SOURCE",
            '-' * 74,
        ]
        for code, service in CATEGORIES.items():
            source = 'attested' if service.attested else "simulation's own"
            lines.append(
                f"{code:<7}{service.name:<34}{service.wires:>6}"
                f"{counts.get(code, 0):>9}  {source}")
        return '\n'.join(lines)
