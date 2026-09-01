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
from ..types import Alarm, SystemHealth
from ..data.companies import RBOCS, for_state
from ..npc import render as render_message
from .session import SessionState

# What the switching control centre at Bedminster watches. The count is the
# simulation's own; that an SCC watched a group of offices from one console
# is what the qualification is for.
SCC_NAME = 'SCC BEDMINSTER'

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

        office = self._find_office(wanted)
        if office is None:
            return (f"connect: {wanted}: no office of that name on this "
                    f"console.\nconnect with no argument lists them.")

        self.remote_office = office
        return self._office_card(office, connecting=True)

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
        for line in _wrap(company.note, 62):
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
        deterministically from the CLLI, which means two looks at the same
        building agree - the thing `cosmos jumper` had to be fixed for -
        and every office keeps whatever you acknowledge on it.

        The home office keeps the alarm list it was dealt at startup. Only
        the other ten are generated here.
        """
        clli = office['clli']
        if clli == self.home_office['clli']:
            return self.active_alarms
        if clli in self._office_alarms:
            return self._office_alarms[clli]

        generator = random.Random(f"alarms:{clli}")
        standing: List[Alarm] = []
        for index, candidate in enumerate(ALARM_CANDIDATES):
            if generator.random() >= 0.3:
                continue
            alarm: Alarm = dict(candidate)  # type: ignore[assignment]
            # An identifier of its own, so acknowledging one office's alarm
            # does not look like acknowledging another's.
            alarm['id'] = f"AL-{abs(hash(clli)) % 9000 + 1000 + index}"
            alarm['acknowledged'] = False
            alarm['timestamp'] = self.clock.now() - timedelta(
                minutes=generator.randint(12, 400))
            alarm['system'] = f"{alarm['system']}-{clli[:4]}"
            standing.append(alarm)
        self._office_alarms[clli] = standing
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


def _wrap(text: str, width: int) -> List[str]:
    """Wrap a note to the console's measure."""
    words = text.split()
    lines: List[str] = []
    line = ''
    for word in words:
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines
