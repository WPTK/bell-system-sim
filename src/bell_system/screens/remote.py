"""
Working an office you are not standing in.

The switching control centre qualification is supposed to mean remote
administration of offices from a console: one maintenance administrator
watching eleven buildings, which is what Petrak in the craft roster does
for a living. It has never meant anything mechanically. Everything in this
simulation happened in the one office you were sitting in.

connect(1) is that qualification cashed. It reaches another office by its
CLLI code, shows you what is in it, and lets the commands that read an
office read that one instead until you disconnect.

WHAT A REMOTE OFFICE IS AND IS NOT

It is not a second board. Trouble reports are customer loops and a loop
terminates in exactly one building - the one whose frame it lands on - so
reports stay where they are. What travels is everything above the loop:
the switching machine, its alarms, its trunk groups, and the records.

That division is not a simplification. It is why a switching control centre
could watch eleven offices and a repair service bureau could not.
"""

import random
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..data.clli import STATE_CODES, parse as parse_clli
from ..data.positions import desk_only
from ..data.trouble import DISPATCH_FORCES
from ..reports import COST_DISPATCH, valid_force
from ..types import Alarm, SystemHealth
from ..verbs import borrow_crew
from ..data.companies import RBOCS, for_state
from ..console import wrap
from ..npc import render as render_message
from .session import SessionState

# What the switching control centre at Bedminster watches. The count is the
# simulation's own; that an SCC watched a group of offices from one console
# is what the qualification is for.
SCC_NAME = 'SCC BEDMINSTER'

# Where other offices' alarm identifiers start: above the home office's
# fixed AL-4472..4476.
ALARM_ID_BASE = 4500

# The alarm conditions an office can be standing in. The same five the home
# office is dealt from at startup; kept here so a remote office is dealt
# from the same deck rather than a second invented one.
ALARM_CANDIDATES: Tuple[Dict[str, Any], ...] = (
    {'type': 'TRUNK_DEGRADED', 'severity': 'MINOR', 'system': 'TG-004',
     'description': 'Intermittent failures on trunk group'},
    {'type': 'MEMORY_PARITY', 'severity': 'MAJOR', 'system': '3A-CCU-D',
     'description': 'Central control memory parity errors'},
    {'type': 'CARRIER_LOSS', 'severity': 'CRITICAL', 'system': 'T1',
     'description': 'Loss of carrier signal'},
    {'type': 'POWER_SUPPLY', 'severity': 'MINOR', 'system': 'PWR',
     'description': 'Backup power supply voltage low'},
    {'type': 'RADIO_FADE', 'severity': 'MAJOR', 'system': 'TH3',
     'description': 'Microwave path experiencing excessive fade'},
)

# The lamps an alarm can show, lowest first, and how many shift minutes an
# alarm left standing takes to light the next. Every alarm ripens at its own
# point in that span (see RemoteCommands.lamp), so they do not all rise
# together. What working one costs in shift minutes follows the lamp, and
# another building costs the console two more. The simulation's own figures.
LAMPS = ('MINOR', 'MAJOR', 'CRITICAL')
LAMP_MINUTES = 40
WORK_COST = {'MINOR': 3, 'MAJOR': 5, 'CRITICAL': 8}
WORK_REMOTE = 2

# The counters on the office's own health summary, by the class an alarm
# was counted in when it was dealt.
HEALTH_KEY = {'CRITICAL': 'critical_alarms', 'MAJOR': 'major_alarms',
              'MINOR': 'minor_alarms'}

# Which alarm another is a symptom of: a trunk group fails when the carrier
# under it is lost, a carrier is lost when the microwave span feeding it
# fades, and central control takes parity errors when backup power sags.
# Clearing the cause clears what it explains, with no more time charged.
# The simulation's own reading of how the five relate.
CAUSES = {'TRUNK_DEGRADED': 'CARRIER_LOSS', 'CARRIER_LOSS': 'RADIO_FADE',
          'MEMORY_PARITY': 'POWER_SUPPLY'}

# What a symptom reads while its cause is standing, naming the cause's own
# system so that it can be matched to the alarm it belongs to. Without a
# cause standing an alarm reads its own description.
SYMPTOMS = {
    'TRUNK_DEGRADED': 'Failures are all on trunks riding {cause}',
    'CARRIER_LOSS': 'Carrier drops in step with fades on {cause}',
    'MEMORY_PARITY': 'Parity errors cluster when {cause} sags',
}

# Each alarm in the deck is standing at the start of a tour with this
# chance, and the home building always has at least HOME_FLOOR standing so
# that there is a panel to work. The simulation's own figures.
DEAL_ODDS = 0.3
HOME_FLOOR = 2


class RemoteCommands(SessionState):
    """
    Reaching another office, and knowing whose it is.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- connect(1) -------------------------------------------------------

    def cmd_connect(self, args: Optional[List[str]] = None) -> str:
        """
        Work another office from this console.

        With no argument, list the offices this control centre watches and
        say which one you are on. With a CLLI code or a city name, connect
        to it. ``connect home`` comes back.

        While connected, the commands that read an office - switch, alarm,
        crossbar, trunk, coer - read the one you are connected to. The
        trouble board does not move: a customer loop lands on one frame in
        one building and that is where its report stays.
        """
        args = args or []
        if not args:
            return self._connect_listing()

        wanted = args[0]
        if wanted.lower() in ('home', 'local', 'off'):
            return self._disconnect()
        if wanted.lower() == 'pool':
            return self._draw_pool(args[1:])
        if wanted.lower() == 'work':
            refusal = desk_only(self.position, 'switch', 'connect work')
            return refusal or self._work_alarm(args[1:])

        office = self._find_office(wanted)
        if office is None:
            return (f"connect: {wanted}: no office of that name on this "
                    f"console.\nconnect with no argument lists them.")

        self.remote_office = office
        return self._office_card(office, connecting=True)

    # -- the alarm panel: lamps that rise on the shift clock ----------------

    _lamp_book: Optional[Dict[str, Any]] = None
    _alarms_dealt = 0  # The tour the home building's alarms were dealt for.

    def lamp_book(self) -> Dict[str, Any]:
        """
        What this desk has done with the panel this tour: the alarms it
        cleared, which of those had already lit above their class when it
        did, and which had already stood at the top lamp for a whole span.

        Keyed on the tour, like the NOC's book: the shift clock starts again
        at zero with each tour and the alarms are dealt again, so what was
        cleared on the last one says nothing about this one. ``held`` is
        kept because a late clear must not wipe the lapse: the alarm is gone
        from the panel, but the span it stood at the top lamp is not.
        """
        book = self._lamp_book
        if book is None or book['tour'] != self.career.shift:
            book = {'tour': self.career.shift, 'cleared': [], 'rose': [],
                    'held': []}
            self._lamp_book = book
        return book

    def lamp_state(self) -> Dict[str, Any]:
        """The book as the save file keeps it."""
        book = self.lamp_book()
        return {'tour': book['tour'], 'cleared': list(book['cleared']),
                'rose': list(book['rose']), 'held': list(book['held'])}

    def restore_lamps(self, stored: Any) -> None:
        """
        Put a saved book back, and deal the tour's alarms again without the
        ones it cleared.

        The alarms are dealt from the tour and the building, not from
        chance, so a resume gets the ones that were standing: the same
        identifiers, which age from the same shift minutes. A save from
        before the book existed, from another tour or damaged brings
        nothing back.
        """
        book: Dict[str, Any] = {'tour': self.career.shift, 'cleared': [],
                                'rose': [], 'held': []}
        if isinstance(stored, dict) and stored.get('tour') == book['tour']:
            for key in ('cleared', 'rose', 'held'):
                listed = stored.get(key)
                if isinstance(listed, list):
                    book[key] = [str(n) for n in listed]
        self._lamp_book = book
        self._office_alarms.clear()
        self._alarms_dealt = 0
        self.deal_alarms()
        self.active_alarms[:] = [alarm for alarm in self.active_alarms
                                 if alarm['id'] not in book['cleared']]
        self._recount_health()

    def deal_alarms(self) -> None:
        """
        Deal the home building's alarms for this tour, at the office desk.

        Seeded from the building and the tour, so the same tour in the same
        building always has the same alarms and a new tour has new ones:
        the pressure comes round again, and a resume does not change which
        alarm is which. Once a tour; the alarms cleared since are left out.
        Every other desk keeps the list it was dealt at startup.
        """
        tour = self.career.shift
        if self.position.key != 'switch' or self._alarms_dealt == tour:
            return
        self._alarms_dealt = tour
        generator = random.Random(f"alarms:{self.home_office['clli']}:{tour}")
        rolls = [(generator.random(), generator.randint(5, 480),
                  generator.random() < 0.5) for _ in self.alarm_deck]
        picked = [i for i, roll in enumerate(rolls) if roll[0] < DEAL_ODDS]
        if len(picked) < HOME_FLOOR:
            # The lowest rolls, so a thin deal is topped up the same way
            # every time it is dealt.
            picked = sorted(sorted(range(len(rolls)),
                                   key=lambda i: rolls[i][0])[:HOME_FLOOR])
        cleared = self.lamp_book()['cleared']
        standing: List[Alarm] = []
        for index in picked:
            alarm: Alarm = dict(self.alarm_deck[index])  # type: ignore[assignment]
            if alarm['id'] in cleared:
                continue
            alarm['timestamp'] = self.clock.now() - timedelta(
                minutes=rolls[index][1])
            alarm['acknowledged'] = rolls[index][2]
            standing.append(alarm)
        self.active_alarms[:] = standing
        self._recount_health()

    def _recount_health(self) -> None:
        """The home office's health summary, counted from what is standing."""
        health: Any = self.system_health
        for level, key in HEALTH_KEY.items():
            health[key] = sum(1 for alarm in self.active_alarms
                              if alarm['severity'] == level)
        health['overall_status'] = ('OPERATIONAL'
                                    if len(self.active_alarms) < 3
                                    else 'DEGRADED')

    def _take_off(self, alarm: Alarm, standing: List[Alarm],
                  home: bool) -> None:
        """Clear one alarm off its office, and off the home health count."""
        standing.remove(alarm)
        if home:
            self._recount_health()

    def lamp(self, alarm: Alarm) -> Tuple[str, int]:
        """
        Return the lamp an alarm shows and the shift minutes until the next.

        An alarm that nobody works lights a level higher every LAMP_MINUTES
        of the shift, from its own point in the span so that they ripen at
        different times. Deterministic from the tour and the alarm's
        identifier. It is the shift clock and nothing else, and the first
        tour, the whole of it, is a grace.
        """
        base = LAMPS.index(alarm['severity'])
        if self.career.shift == 1:
            return LAMPS[base], LAMP_MINUTES
        age = self._lamp_age(alarm)
        level = min(len(LAMPS) - 1, base + age // LAMP_MINUTES)
        return LAMPS[level], LAMP_MINUTES - age % LAMP_MINUTES

    def _lamp_age(self, alarm: Alarm) -> int:
        """Shift minutes an alarm has been ripening, from its own start."""
        ripe = random.Random(
            f"lamp:{self.career.shift}:{alarm['id']}").randrange(LAMP_MINUTES)
        return self.shift_minutes + ripe

    def lamp_held(self, alarm: Alarm) -> bool:
        """
        Whether an alarm has stood at the top lamp for a whole span.

        Left that long it is a commitment missed, which the service index
        counts at the handoff. Read only, and the first tour is a grace.
        """
        if self.career.shift == 1:
            return False
        base = LAMPS.index(alarm['severity'])
        return self._lamp_age(alarm) >= (len(LAMPS) - base) * LAMP_MINUTES

    def alarms_overdue(self) -> int:
        """
        Return how many alarms in this building have stood at the top lamp
        for a whole span, standing or cleared since.

        Read only: worked out from the shift clock each time it is asked
        for, so ignoring the panel costs the same whether or not anyone
        looked at it. An alarm cleared after it had been held is in the
        book's ``held`` list and still counts: clearing it late stops the
        count growing, it does not give the span back. Only the office desk
        has a console, and only its own building's alarms count: the
        console watches ten more, and putting every one of them on the
        index would be a score of twenty for a shift's work that cannot be
        done. The other buildings' lamps still rise and still show on the
        panel.
        """
        if self.position.key != 'switch':
            return 0
        home = self.home_office['clli']
        standing = sum(1 for alarm, _, office, *_ in self.lamp_panel()
                       if office['clli'] == home and self.lamp_held(alarm))
        return standing + len(self.lamp_book()['held'])

    def alarms_risen(self) -> int:
        """Alarms whose lamp rose above their class, standing or cleared."""
        standing = sum(1 for alarm, lamp, *_ in self.lamp_panel()
                       if lamp != alarm['severity'])
        return standing + len(self.lamp_book()['rose'])

    def lamp_panel(self) -> List[Tuple[Alarm, str, Any, int, int]]:
        """
        Every alarm standing on the console: the alarm, its lamp, its
        office, the minutes to the next lamp and what working it costs.

        Highest lamp first, then soonest to light. Read only: looking at the
        panel changes nothing on it.
        """
        offices = list(self.watched_offices())
        home = self.home_office
        if home['clli'] not in {o['clli'] for o in offices}:
            offices.insert(0, home)
        rows = []
        for office in offices:
            for alarm in self.office_alarms(office):
                lamp, next_in = self.lamp(alarm)
                cost = WORK_COST[lamp] + (
                    0 if office['clli'] == home['clli'] else WORK_REMOTE)
                rows.append((alarm, lamp, office, next_in, cost))
        rows.sort(key=lambda row: (-LAMPS.index(row[1]), row[3]))
        return rows

    @staticmethod
    def alarm_cause(alarm: Alarm, standing: List[Alarm]) -> Optional[Alarm]:
        """
        The alarm in this office that explains this one, if one is standing.

        The nearest cause up the chain that is on the panel: a trunk group
        failing under a faded microwave span is explained by the span when
        the carrier alarm between them is not standing.
        """
        kind = CAUSES.get(alarm['type'])
        while kind:
            for other in standing:
                if other['type'] == kind:
                    return other
            kind = CAUSES.get(kind)
        return None

    def alarm_symptoms(self, cause: Alarm, standing: List[Alarm]) -> List[Alarm]:
        """Every alarm in this office that clearing the cause would clear."""
        found = [cause]
        for known in found:
            for other in standing:
                if (other not in found
                        and self.alarm_cause(other, standing) is known):
                    found.append(other)
        return found[1:]

    def alarm_reads(self, alarm: Alarm, standing: List[Alarm]) -> str:
        """What the alarm says it is seeing: its cause's system if it has one."""
        cause = self.alarm_cause(alarm, standing)
        if cause is None:
            return alarm['description']
        return SYMPTOMS[alarm['type']].format(cause=cause['system'])

    def _work_alarm(self, args: List[str]) -> str:
        """connect work [ALARM]: the panel, or clear one alarm at its cause."""
        rows = self.lamp_panel()
        if not args:
            lines = [f"ALARM PANEL   {SCC_NAME}",
                     f"Shift time {self.shift_time()}", '=' * 70,
                     f"{'ALARM':<9}{'OFFICE':<14}{'LAMP':<10}{'NEXT':<7}"
                     f"{'COST':<6}SYSTEM", '-' * 70]
            for alarm, lamp, office, next_in, cost in rows:
                rose = '*' if lamp != alarm['severity'] else ' '
                lines.append(
                    f"{alarm['id']:<9}{office['clli']:<14}{lamp + rose:<10}"
                    f"{str(next_in) + 'm':<7}{str(cost) + 'm':<6}"
                    f"{alarm['system'][:20]}")
                reads = self.alarm_reads(alarm, self.office_alarms(office))
                lines.append(f"         reads: {reads}")
            if not rows:
                lines.append("No alarms standing on any office.")
            lines += [
                '-' * 70,
                f"{len(rows)} standing. * marks a lamp that has risen above "
                f"the alarm's class.",
                "",
                "  connect work <ALARM>   Clear it at the cause (COST "
                "minutes)",
                "  alarm status           What the alarm itself says",
                "",
                "An alarm that reads another alarm's system is that alarm's "
                "symptom:",
                "clear the cause and it clears too, for no more time.",
                "",
                f"An alarm nobody works lights one lamp higher every "
                f"{LAMP_MINUTES} shift",
                "minutes, from its own point in them. Acknowledging does "
                "not stop it:",
                "only clearing does. One left a whole span at the top lamp "
                "is a missed",
                "commitment on the index (this building only), and clearing "
                "it late does",
                "not take that back. These figures are the simulation's own.",
            ]
            return '\n'.join(lines)
        wanted = args[0].upper()
        row = next((r for r in rows if r[0]['id'] == wanted), None)
        if row is None:
            return (f"connect work: no alarm '{args[0]}' standing on this "
                    f"console.\n'connect work' lists them.")
        alarm, lamp, office, _, cost = row
        standing = self.office_alarms(office)
        home = office['clli'] == self.home_office['clli']
        cause = self.alarm_cause(alarm, standing)
        freed = self.alarm_symptoms(alarm, standing)
        # Looked at as it was when the alarm was chosen, before the clearing
        # takes its minutes: the alarm cleared was the one the panel showed.
        book = self.lamp_book()
        for gone in [alarm] + freed:
            if self.lamp(gone)[0] != gone['severity']:
                book['rose'].append(gone['id'])
            if home and self.lamp_held(gone):
                book['held'].append(gone['id'])
            book['cleared'].append(gone['id'])
        self._pass_time(cost)
        for gone in [alarm] + freed:
            self._take_off(gone, standing, home)
        lines = [
            f"{alarm['id']}: cleared at the cause on {alarm['system']} in "
            f"{office['clli']}.",
            f"{alarm['description']}.",
            f"It was showing {lamp}"
            + (f" (dealt as {alarm['severity']})."
               if lamp != alarm['severity'] else "."),
            f"That was {cost} minutes of the shift"
            + ("." if home else ", with the console's two for the other "
               "building."),
        ]
        if freed:
            lines.append("It was the cause of " + ', '.join(
                f"{gone['id']} ({gone['type']})" for gone in freed)
                + ", which cleared with it for no more time.")
        if cause is not None:
            lines.append(f"It was only a symptom: {cause['id']} on "
                         f"{cause['system']} is still standing.")
        return '\n'.join(lines)

    def _connect_listing(self) -> str:
        """The offices this console watches, and where you are now."""
        watched = self.watched_offices()
        rows = [f"{SCC_NAME} - OFFICES ON THIS CONSOLE",
                self.clock.timestamp(), '=' * 62, '',
                f"  {'CLLI':<14}{'PLACE':<22}{'SWITCH':<10}COMPANY",
                '  ' + '-' * 58]
        for office in watched:
            company = for_state(STATE_CODES.get(office['state'],
                                                office['state']))
            # By code, not identity: the home office is a different dict
            # carrying the same CLLI.
            here = (' *' if office['clli'] == self.current_office()['clli']
                    else '')
            rows.append(f"  {office['clli']:<14}"
                        f"{office['city'][:20]:<22}"
                        f"{office['switch_type']:<10}"
                        f"{(company.name if company else 'not Bell')[:24]}"
                        f"{here}")
        rows.extend(['  ' + '-' * 58, ''])
        if self.remote_office is not None:
            rows.append(f"Connected to {self.remote_office['clli']}. "
                        f"'connect home' comes back.")
        else:
            rows.append("You are at your own office. 'connect <clli>' "
                        "reaches another.")
        rows.append('')
        rows.append("The trouble board does not travel. A loop lands on one "
                    "frame and its")
        rows.append("report stays in that building; what travels is the "
                    "machine above it.")
        return '\n'.join(rows)

    def _draw_pool(self, args: List[str]) -> str:
        """
        Ask the control centre for the crew it keeps in a pool.

        "On-site work dispatched from a central pool" is what an SCC was
        for, and the wire centre's own five are the usual reason to ask:
        when everybody who answers a category is out, a report dispatched
        to it only waits. The pool has one crew. It goes where you name,
        for the rest of the tour, and it starts the farthest away of
        anybody, so it is the answer to a long wait and not to a short one.
        """
        force = valid_force(' '.join(args)) if args else None
        if force is None:
            return ("connect: usage: connect pool <force>\n"
                    f"Forces: {', '.join(DISPATCH_FORCES)}")
        if not borrow_crew(self.desk, force):
            loaned = self.desk.force.loaned
            if loaned:
                return (f"connect: the pool's one crew is already loaned to "
                        f"{loaned.lower()} until the tour ends.")
            return ("connect: the pool's one crew is still out on its last "
                    "job. It can be loaned again when that is done.")
        self._pass_time(COST_DISPATCH)
        return (f"{SCC_NAME}: the pool crew is yours for {force.lower()} "
                f"until the tour ends.\n"
                f"They are at the far end of the district. Dispatch to "
                f"{force.lower()} as usual; 'force' shows where they are.\n"
                f"{COST_DISPATCH} minutes charged.")

    def _disconnect(self) -> str:
        """Come back to the office you are actually sitting in."""
        if self.remote_office is None:
            return "connect: you are already at your own office."
        was = self.remote_office['clli']
        self.remote_office = None
        return (f"Disconnected from {was}.\n"
                f"Back on {self.home_office['clli']}, which is the one you "
                f"can walk to.")

    # -- what the rest of the terminal asks --------------------------------

    def current_office(self) -> Any:
        """
        The office the machine-side commands should be reading.

        The remote one while connected, and the home one otherwise. Every
        screen that shows a switching machine goes through here.
        """
        return self.remote_office or self.home_office

    def office_is_remote(self) -> bool:
        """Whether the console is currently on somebody else's office."""
        return self.remote_office is not None

    def remote_banner(self) -> str:
        """
        One line to put at the top of a screen that is showing elsewhere.

        Without it, a switching screen for an office three states away is
        indistinguishable from one for the office you are sitting in, which
        is exactly the mistake an SCC console makes possible.
        """
        if self.remote_office is None:
            return ''
        office = self.remote_office
        return (f"[connected: {office['clli']} - {office['city']}, "
                f"{office['state']} - not this building]")

    def watched_offices(self) -> List[Any]:
        """
        The offices this control centre has on its console.

        Drawn from the geographic data around the home office rather than
        invented: a control centre watched a group of buildings, and these
        are the ones nearest in the numbering plan.
        """
        if self._watched is not None:
            return self._watched
        home = self.home_office
        candidates = [office for office in self.central_offices.values()
                      if office['npa'] == home['npa']]
        candidates.sort(key=lambda office: office['nxx'])
        # One entry per building. Several offices in a city can generate the
        # same CLLI - the code identifies a building, not a switch - and a
        # console listing the same code twice is one you cannot connect
        # from, because there would be no way to say which you meant.
        seen: Dict[str, Any] = {}
        for office in candidates:
            seen.setdefault(office['clli'], office)
        self._watched = list(seen.values())[:11] or [home]
        return self._watched

    def _find_office(self, token: str) -> Optional[Any]:
        """Find a watched office by CLLI, by city, or by its number."""
        wanted = token.upper()
        watched = self.watched_offices()
        for office in watched:
            if office['clli'].upper() == wanted:
                return office
        if parse_clli(wanted) is not None:
            for office in self.central_offices.values():
                if office['clli'].upper() == wanted:
                    return office
        for office in watched:
            if office['city'].upper().startswith(wanted):
                return office
        if token.isdigit() and 1 <= int(token) <= len(watched):
            return watched[int(token) - 1]
        return None

    # -- whose office is it ------------------------------------------------

    def _office_card(self, office: Any,
                     connecting: bool = False) -> str:
        """What is in an office, and who it belongs to in January."""
        state = STATE_CODES.get(office['state'], office['state'])
        company = for_state(state)
        rows = []
        if connecting:
            rows.append(f"Connected to {office['clli']}.")
            rows.append('')
        rows.extend([
            f"{office['clli']} - {office['city']}, {state}",
            '=' * 62,
            f"  Switch          {office['switch_name']} "
            f"({office['switch_type']})",
            f"  In service      {office['installation_date']}",
            f"  Lines           {office['capacity']:,} at "
            f"{office['utilization']}% utilisation",
            f"  Trunk groups    {office['trunk_groups']}",
            f"  Maintenance     {office['maintenance_status']}",
            '',
        ])
        rows.extend(self.company_note(state))
        if connecting:
            rows.extend([
                '',
                "switch, alarm, crossbar and coer now read this office.",
                "The trouble board does not: 'connect home' when you are "
                "done.",
            ])
        del company
        return '\n'.join(rows)

    def company_note(self, state: str) -> List[str]:
        """
        Whose office this is, and what happens to it on 1 January.

        The one thing everybody in every one of these buildings actually
        knew about their own company in November 1983.
        """
        company = for_state(state)
        if company is None:
            return ["OPERATING COMPANY",
                    "  Not a wholly owned Bell operating company. AT&T held "
                    "a minority",
                    "  stake, so this office is not part of the "
                    "divestiture and 1 January",
                    "  changes nothing about who runs it."]
        rows = ["OPERATING COMPANY",
                f"  {company.name}",
                f"  Passes to {RBOCS[company.rboc]} on 1 January 1984.",
                '']
        for line in wrap(company.note, 62):
            rows.append(f"  {line}")
        if not company.verified:
            rows.append('')
            rows.append("  (Regional assignment externally sourced; the "
                        "bundled documents")
            rows.append("  give three of the seven groupings in full and "
                        "not this one.)")
        return rows

    def cmd_company(self, args: Optional[List[str]] = None) -> str:
        """
        Whose office you are working, and where it goes in January.

        With no argument, the office you are on. With a two-letter state
        code, that state's operating company. With ``all``, the whole
        table: twenty-one companies going to seven regions in forty-eight
        days.
        """
        args = args or []
        if args and args[0].lower() == 'all':
            return self._company_table()
        if args:
            state = args[0].upper()
            if len(state) != 2:
                return (f"company: {args[0]}: wanted a two-letter state "
                        f"code, or 'all'.")
            company = for_state(state)
            if company is None and state not in ('CT',):
                return f"company: no Bell operating company in {state}."
            return '\n'.join(self.company_note(state))
        office = self.current_office()
        state = STATE_CODES.get(office['state'], office['state'])
        return (f"{office['clli']} - {office['city']}, {state}\n"
                f"{'=' * 62}\n" + '\n'.join(self.company_note(state)))

    def _company_table(self) -> str:
        """The whole divestiture, in one screen."""
        from ..data.companies import COMPANIES
        rows = ["THE OPERATING COMPANIES, AND WHERE THEY GO",
                self.clock.timestamp(), '=' * 62, '',
                "AT&T was sole stockholder in twenty-one operating "
                "companies. On",
                "1 January 1984 they pass to seven regional holding "
                "companies.",
                '',
                f"  {'COMPANY':<38}{'STATES':<10}REGION",
                '  ' + '-' * 58]
        for company in sorted(COMPANIES.values(),
                              key=lambda c: (c.rboc, c.name)):
            mark = '' if company.verified else ' ?'
            states = ','.join(company.states[:3])
            if len(company.states) > 3:
                states += '+'
            rows.append(f"  {company.name[:36]:<38}{states:<10}"
                        f"{company.rboc}{mark}")
        rows.extend([
            '  ' + '-' * 58, '',
            "The Chesapeake and Potomac entry is four separate companies, "
            "one for",
            "the District and one each for Maryland, Virginia and West "
            "Virginia.",
            '',
            "Connecticut and Cincinnati are absent because AT&T held only "
            "a minority",
            "stake in Southern New England Telephone and Cincinnati Bell. "
            "They do",
            "not divest.",
            '',
            "? marks a regional assignment taken from outside the bundled "
            "documents.",
        ])
        return '\n'.join(rows)


    # -- an office has its own alarms --------------------------------------

    def office_alarms(self, office: Any) -> List[Alarm]:
        """
        The alarms standing in a given office.

        A control centre console is only worth having if the offices on it
        are in different states, so each one has its own. Generated
        deterministically from the CLLI and the tour, which means two looks
        at the same building agree - the thing `cosmos jumper` had to be
        fixed for - every office keeps whatever you acknowledge on it, and
        the next tour deals them again.

        The home office keeps the alarm list it was dealt at startup, except
        at the office desk, which is dealt its own each tour (deal_alarms).
        Only the other ten are generated here.
        """
        clli = office['clli']
        if clli == self.home_office['clli']:
            self.deal_alarms()
            return self.active_alarms
        tour = self.career.shift
        if f"{clli}:{tour}" in self._office_alarms:
            return self._office_alarms[f"{clli}:{tour}"]

        generator = random.Random(f"alarms:{clli}:{tour}")
        # Each building owns a block of identifiers as wide as the deck,
        # numbered by its place on the console and starting clear of the
        # home office's AL-4472..4476, so two buildings cannot share one.
        # Not hash(): a str hash is salted per process, so the numbers
        # changed from run to run and the blocks could overlap. An office
        # that is not on the console has no slot, and the lookup raises
        # rather than hand it one that another building could share.
        slot = next(place for place, watched in enumerate(
            self.watched_offices()) if watched['clli'] == clli)
        first_id = ALARM_ID_BASE + slot * len(ALARM_CANDIDATES)
        standing: List[Alarm] = []
        for index, candidate in enumerate(ALARM_CANDIDATES):
            if generator.random() >= 0.3:
                continue
            alarm: Alarm = dict(candidate)  # type: ignore[assignment]
            # An identifier of its own, so acknowledging one office's alarm
            # does not look like acknowledging another's.
            alarm['id'] = f"AL-{first_id + index}"
            alarm['acknowledged'] = False
            alarm['timestamp'] = self.clock.now() - timedelta(
                minutes=generator.randint(12, 400))
            alarm['system'] = f"{alarm['system']}-{clli[:4]}"
            if alarm['id'] in self.lamp_book()['cleared']:
                continue
            standing.append(alarm)
        self._office_alarms[f"{clli}:{tour}"] = standing
        return standing

    def office_health(self, office: Any) -> SystemHealth:
        """Counted from whatever is standing in that office."""
        if office['clli'] == self.home_office['clli']:
            return self.system_health
        standing = self.office_alarms(office)
        counts = {level: sum(1 for a in standing if a['severity'] == level)
                  for level in ('CRITICAL', 'MAJOR', 'MINOR')}
        worst = ('DEGRADED' if counts['CRITICAL'] or counts['MAJOR']
                 else 'OPERATIONAL')
        health: SystemHealth = dict(self.system_health)  # type: ignore[assignment]
        health['overall_status'] = worst
        health['critical_alarms'] = counts['CRITICAL']
        health['major_alarms'] = counts['MAJOR']
        health['minor_alarms'] = counts['MINOR']
        return health


    # -- the control centre gives you one --------------------------------

    def scc_assignment(self) -> Optional[str]:
        """
        The control centre putting an office on you for the tour.

        An SCC watches a group and hands one out when it is in a state
        somebody should be looking at. It picks the worst office on the
        console that is not the one you are sitting in, and only bothers
        you if there is something there - a console that hands you a quiet
        building has told you nothing.

        Returns the message, or None if nothing on the console is worth
        anybody's morning.
        """
        if self._scc_assigned:
            return None
        home = self.home_office['clli']
        elsewhere = [office for office in self.watched_offices()
                     if office['clli'] != home]
        if not elsewhere:
            return None

        def weight(office: Any) -> int:
            """How much an office wants looking at."""
            standing = self.office_alarms(office)
            return sum({'CRITICAL': 4, 'MAJOR': 2}.get(alarm['severity'], 1)
                       for alarm in standing)

        worst = max(elsewhere, key=weight)
        if weight(worst) < 4:
            return None

        self._scc_assigned = worst['clli']
        standing = self.office_alarms(worst)
        critical = [a for a in standing if a['severity'] == 'CRITICAL']
        trouble = (critical[0]['description'].lower() if critical
                   else standing[0]['description'].lower())
        return render_message(self.switchroom.office_assignment(
            self.clock.now(), worst['clli'], worst['city'], trouble,
            len(standing)), self._stamp())

