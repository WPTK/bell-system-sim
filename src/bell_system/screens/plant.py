"""
The plant: what a call rides over, and what the equipment is.

Five commands that had been declaring themselves unavailable since the
beginning. Four of them turned out to have real data already in the
simulation sitting behind them - the toll network the routing engine
searches, the offices it holds, the radio routes - and were unavailable
only because nobody had joined the two up.

The Western Electric reference is externally sourced and marked as such
where the entries say so. Anything the sources consulted do not settle is
absent rather than guessed at, which is why the table is short.
"""

import os
import random
from typing import Dict, List, NamedTuple, Optional

from ..data.trouble import DISPATCH_FORCES
from ..field import CREWS, LOCATIONS
from ..data.signaling import PROGRESS_TONES
from ..data.switching import SWITCHING_SYSTEMS
from ..settings import state_dir
from .. import tones
from ..weather import CONDITIONS
from .session import SessionState


class Equipment(NamedTuple):
    """One piece of Western Electric plant, and what it was for."""

    name: str
    introduced: str
    kind: str
    note: str


# Western Electric was the Bell System's manufacturing arm and made nearly
# everything in the plant. The dates are externally sourced and are the year
# the type entered service, not the year it was designed. Anything whose date
# the sources consulted disagreed on or did not settle is not in the table.
EQUIPMENT: Dict[str, Equipment] = {
    '302': Equipment(
        'Model 302 telephone set', '1937', 'station',
        'Metal and then thermoplastic housing, ringer and induction coil '
        'inside the set rather than in a separate subscriber set.'),
    '500': Equipment(
        'Model 500 telephone set', '1949', 'station',
        'The rotary set most of the country had. Still being installed when '
        'this shift starts, and still the set a repair report is usually '
        'about.'),
    '1500': Equipment(
        'Model 1500 telephone set', '1963', 'station',
        'The first Touch-Tone set, ten buttons. The twelve-button 2500 '
        'followed and took over.'),
    '2500': Equipment(
        'Model 2500 telephone set', '1968', 'station',
        'Twelve-button Touch-Tone. The star and octothorpe keys are on it '
        'for services that mostly did not exist yet.'),
    '1a2': Equipment(
        '1A2 key telephone system', '1964', 'station',
        'Multi-line key equipment: buttons, hold, and a lamp per line, with '
        'the working parts in a KSU on the wall rather than in the set.'),
    'no1xbar': Equipment(
        'No. 1 Crossbar switching system', '1938', 'switching',
        'Common control with crossbar switches and markers. The marker sets '
        'up a path and lets go, so one marker serves many calls.'),
    'no5xbar': Equipment(
        'No. 5 Crossbar switching system', '1948', 'switching',
        'The crossbar office built for local service, and the one most '
        'likely to be behind a report on this board.'),
    '1ess': Equipment(
        'No. 1 ESS', '1965', 'switching',
        'The first stored program switching system in service, cut over at '
        'Succasunna, New Jersey. Reed relay network, program in read-only '
        'memory.'),
    '1aess': Equipment(
        'No. 1A ESS', '1976', 'switching',
        'The 1ESS with the faster 1A processor. Most of the electronic '
        'local offices in service now are these.'),
    '4ess': Equipment(
        'No. 4 ESS', '1976', 'switching',
        'The first digital toll switch, cut over in Chicago. Time division '
        'through the network rather than metal contacts.'),
    '5ess': Equipment(
        'No. 5 ESS', '1982', 'switching',
        'Digital local switching, first service at Seneca, Illinois. The '
        'newest thing in the plant by a year and a half.'),
    't1': Equipment(
        'T1 carrier', '1962', 'transmission',
        'Twenty-four voice channels on two pairs, 1.544 megabits, '
        'regenerators every six thousand feet. Built to get more out of '
        'exchange cable already in the ground.'),
    'd4': Equipment(
        'D4 channel bank', '1977', 'transmission',
        'Digital channel bank, forty-eight channels, the terminal equipment '
        'at each end of a T-carrier span.'),
    'l4': Equipment(
        'L4 coaxial carrier', '1967', 'transmission',
        'Long-haul coaxial system, 3600 voice channels to a tube.'),
    'td2': Equipment(
        'TD-2 microwave radio', '1950', 'transmission',
        'The first transcontinental microwave system, four gigahertz, and '
        'what put long-haul traffic in the air instead of on cable.'),
    'th3': Equipment(
        'TH-3 microwave radio', '1968', 'transmission',
        'Six gigahertz long-haul radio. The routes this position watches '
        'are TH-3.'),
}


class PlantCommands(SessionState):
    """
    Tracing a call, and the equipment it goes through.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- trace(1) ---------------------------------------------------------

    def cmd_trace(self, args: Optional[List[str]] = None) -> str:
        """
        Follow a call through the toll network.

        With two office codes, offer a call between them and print every
        trunk group it takes, in order, with what each was carrying. With
        one, print that office's homing chain: the route a call from it
        takes upward until it finds a common point with wherever it is
        going. With none, list the offices.

        This is the routing engine the toll screens already search, printed
        one leg at a time.
        """
        args = args or []
        network = self.toll_network
        if not args:
            return self._trace_offices()

        origin = args[0].upper()
        if origin not in network.offices:
            return (f"trace: {origin}: not in the routing table\n"
                    f"trace with no arguments lists the offices.")
        if len(args) == 1:
            chain = network.homing_chain(origin)
            rows = [f"HOMING CHAIN FOR {origin}", '']
            for depth, code in enumerate(chain):
                office = network.offices[code]
                rows.append(f"{'  ' * depth}{code:<12}{office.name} "
                            f"(class {office.switch_class}, "
                            f"{office.class_name()})")
            rows.extend(['', "A call climbs this until it reaches an office "
                             "the far end also homes on."])
            return '\n'.join(rows)

        destination = args[1].upper()
        if destination not in network.offices:
            return f"trace: {destination}: not in the routing table"
        if origin == destination:
            return "trace: origin and destination are the same office"

        result = network.route(origin, destination,
                               random.Random(f"{origin}{destination}"))
        rows = [f"CALL TRACE  {origin} to {destination}",
                self.clock.timestamp(), '=' * 62, '']
        common = network.common_point(origin, destination)
        if common:
            rows.append(f"Common point:  {common} "
                        f"({network.offices[common].class_name()})")
            rows.append('')

        if result.attempts:
            rows.append("ROUTES OFFERED")
            for attempt in result.attempts:
                rows.append(f"  {attempt}")
            rows.append('')

        if not result.completed:
            rows.append(f"CALL BLOCKED: {result.reason}")
            rows.append("The caller receives reorder.")
            return '\n'.join(rows)

        rows.append("PATH TAKEN")
        rows.append(f"  {'FROM':<12}{'TO':<12}{'GROUP':<20}OCCUPANCY")
        for leg in result.legs:
            rows.append(f"  {leg.from_office:<12}{leg.to_office:<12}"
                        f"{leg.group_type:<20}{leg.utilization}%")
        rows.extend(['', f"{result.trunk_count()} trunks in tandem."])
        return '\n'.join(rows)

    def _trace_offices(self) -> str:
        """List what is in the routing table, by class."""
        network = self.toll_network
        rows = ["OFFICES IN THE ROUTING TABLE", '']
        by_class: Dict[int, List[str]] = {}
        for code, office in sorted(network.offices.items()):
            by_class.setdefault(office.switch_class, []).append(
                f"  {code:<12}{office.name}")
        for switch_class in sorted(by_class):
            name = network.offices[
                by_class[switch_class][0].split()[0]].class_name()
            rows.append(f"Class {switch_class} - {name}")
            rows.extend(by_class[switch_class])
            rows.append('')
        rows.append("trace <office>            homing chain")
        rows.append("trace <office> <office>   route a call between them")
        return '\n'.join(rows)

    # -- western(1) -------------------------------------------------------

    def cmd_western(self, args: Optional[List[str]] = None) -> str:
        """
        Look up Western Electric equipment.

        Western Electric was the Bell System's manufacturing arm and made
        nearly everything in the plant. Named without an argument, the
        listing is by kind; with one, the entry.
        """
        args = args or []
        if not args:
            rows = ["WESTERN ELECTRIC EQUIPMENT", '']
            for kind in ('station', 'switching', 'transmission'):
                rows.append(kind.upper())
                for key, item in EQUIPMENT.items():
                    if item.kind == kind:
                        rows.append(f"  {key:<10}{item.introduced}  {item.name}")
                rows.append('')
            rows.append("western <name> for one of them.")
            return '\n'.join(rows)

        wanted = args[0].lower().replace('-', '').replace('.', '')
        if wanted not in EQUIPMENT:
            near = [key for key in EQUIPMENT if wanted in key]
            if len(near) != 1:
                return (f"western: no entry for {args[0]}\n"
                        f"western with no argument lists what is here.")
            wanted = near[0]
        item = EQUIPMENT[wanted]
        return (f"{item.name}\n{'=' * len(item.name)}\n\n"
                f"In service:   {item.introduced}\n"
                f"Kind:         {item.kind}\n\n{item.note}")

    # -- 5ess(1) ----------------------------------------------------------

    def cmd_5ess(self, args: Optional[List[str]] = None) -> str:
        """
        The No. 5 ESS, and what it means for this building.

        The newest switching system in the plant, in service since 1982.
        There is not one in this office; the point of the command is that
        you can find out what is coming and what it replaces.
        """
        item = EQUIPMENT['5ess']
        return f"""No. 5 ESS - DIGITAL LOCAL SWITCHING
{self.clock.timestamp()}
{'=' * 62}

In service since {item.introduced}. {item.note}

NOT IN THIS OFFICE
{'=' * 62}
This position works {self._office_label(None) or 'a crossbar office'}.
There is no 5ESS on this frame and there will not be one this year.

WHAT IT CHANGES
{'=' * 62}
A crossbar office switches a call by closing metal contacts and holding
them closed for its duration. A digital office carries the call as
numbers and switches it by moving them into a different time slot. No
path is held. Nothing wears.

WHAT THAT MEANS FOR THE JOB
{'=' * 62}
Half of what is on this board is contacts: dirty, misaligned, or worn.
That half of the work does not exist in a digital office. The other half
is the loop - the pair from here to the customer's station - and that is
copper in the ground either way, and it will still be wet in April.

The frame is not going away. The marker is.

SEE ALSO
{'=' * 62}
western 5ess, western 4ess, western no5xbar, crossbar
"""

    # -- capacity(1) ------------------------------------------------------

    def cmd_capacity(self, args: Optional[List[str]] = None) -> str:
        """
        Report what the trunk groups are carrying against what they hold.

        A final group is engineered to P.01 - one call in a hundred finds
        every trunk busy - and a high usage group to P.10, because
        overflowing is what it is for. A high usage group running quiet is
        not good news; it means traffic is not being offered to it.
        """
        groups = sorted(self.trunk_groups.items())
        if not groups:
            return "capacity: no trunk groups on this position"

        rows = ["TRUNK GROUP CAPACITY", self.clock.timestamp(), '=' * 62, '',
                f"  {'GROUP':<16}{'TRUNKS':>7}{'BUSY':>7}{'OCC':>6}"
                f"   {'OBJECTIVE':<16}STATE"]
        strained = []
        for name, group in groups:
            total = group['capacity']
            occupancy = group['utilization']
            busy = round(total * occupancy / 100)
            # A group carrying more than half its capacity at a routine hour
            # is a final group in all but name: the high-usage groups are the
            # ones engineered to overflow, and these are the office's own
            # trunks, so P.01 is the objective that applies.
            objective = 'P.01 final'
            state = 'OVER' if occupancy > 85 else 'normal'
            if state == 'OVER':
                strained.append(name)
            rows.append(f"  {name:<16}{total:>7}{busy:>7}{occupancy:>5}%"
                        f"   {objective:<16}{state}")

        rows.append('')
        if strained:
            rows.append(f"Over objective: {', '.join(strained)}")
            rows.append("Traffic engineering wants a count before it will "
                        "add trunks.")
        else:
            rows.append("Every group within its objective.")
        rows.append('')
        rows.append("traffic(1) has the hourly counts; trunk(1) has one "
                    "group in detail.")
        return '\n'.join(rows)

    # -- coer(1) ----------------------------------------------------------

    def cmd_coer(self, args: Optional[List[str]] = None) -> str:
        """
        Central office equipment report.

        What is in each office, how it homes, and what is in trouble. The
        report a wire chief signed at the end of a tour and sent up.
        """
        args = args or []
        network = self.toll_network
        if args and args[0].upper() in network.offices:
            return self._coer_office(args[0].upper())

        counts: Dict[str, int] = {}
        for office in network.offices.values():
            counts[office.class_name()] = counts.get(office.class_name(), 0) + 1

        alarms = [alarm for alarm in self.active_alarms
                  if getattr(alarm, 'severity', '') in ('MAJOR', 'CRITICAL')]
        rows = ["CENTRAL OFFICE EQUIPMENT REPORT",
                self.clock.timestamp(), '=' * 62, '',
                "OFFICES BY CLASS"]
        for name, count in sorted(counts.items()):
            rows.append(f"  {name:<28}{count:>4}")
        rows.extend(['', "EQUIPMENT IN TROUBLE"])
        if alarms:
            for alarm in alarms:
                rows.append(f"  {getattr(alarm, 'severity', '?'):<10}"
                            f"{getattr(alarm, 'location', '?'):<20}"
                            f"{getattr(alarm, 'description', '')}")
        else:
            rows.append("  Nothing above minor.")
        rows.extend(['', "REPAIR SERVICE",
                     f"  Reports pending           "
                     f"{len(self.desk.pending()):>4}",
                     f"  Closed this tour          "
                     f"{len(self.desk.closed()):>4}",
                     '', "coer <office> for one office."])
        return '\n'.join(rows)

    def _coer_office(self, code: str) -> str:
        """Report on one office in the routing table."""
        network = self.toll_network
        office = network.offices[code]
        chain = network.homing_chain(code)
        homing = 'nothing: it is a regional centre'
        rows = [f"CENTRAL OFFICE EQUIPMENT REPORT - {code}",
                self.clock.timestamp(), '=' * 62, '',
                f"  Name          {office.name}",
                f"  Class         {office.switch_class} "
                f"({office.class_name()})",
                f"  Homes on      {office.homes_on or homing}",
                f"  Chain         {' -> '.join(chain)}",
                '']
        if office.switch_class == 5:
            rows.append("An end office. Subscriber loops terminate here and "
                        "nowhere above it.")
        elif office.switch_class == 1:
            rows.append("A regional centre. Every chain ends at one of "
                        "these, which is what makes the hierarchy finite.")
        else:
            rows.append("A toll office. It carries traffic between offices")
            rows.append("and has no subscribers of its own.")
        return '\n'.join(rows)

    # -- microwave(1) and satellite(1) ------------------------------------

    def cmd_microwave(self, args: Optional[List[str]] = None) -> str:
        """
        Long-haul microwave radio, which is what most toll traffic rides.

        The routes this position watches are TH-3 at six gigahertz. radio(1)
        has the path-by-path detail; this is the summary a shift starts with.
        """
        item = EQUIPMENT['th3']
        routes = self.radio_routes if hasattr(self, 'radio_routes') else {}
        rows = ["LONG-HAUL MICROWAVE RADIO", self.clock.timestamp(),
                '=' * 62, '',
                f"System        {item.name}, in service since "
                f"{item.introduced}",
                "Band          6 GHz",
                "Spacing       Repeaters roughly every 25 to 30 miles, "
                "line of sight",
                '']
        if routes:
            rows.append("ROUTES ON THIS POSITION")
            for name, route in sorted(routes.items()):
                state = getattr(route, 'status', None) or (
                    route.get('status') if isinstance(route, dict) else '?')
                rows.append(f"  {name:<20}{state}")
        else:
            rows.append("radio status has the routes and their fade margins.")
        rows.extend(['',
                     "WHY IT MATTERS TODAY",
                     "Rain absorbs at six gigahertz and heavy rain on a long "
                     "hop takes the",
                     "margin with it. A path that fades is not a fault and "
                     "there is nothing",
                     "on the ground to go and fix; diversity switches to the "
                     "protection",
                     "channel and you watch it until the weather goes over.",
                     '',
                     "radio(1), antenna(1), western th3"])
        return '\n'.join(rows)

    def cmd_satellite(self, args: Optional[List[str]] = None) -> str:
        """
        Satellite circuits, and why the toll network mostly does not use them.

        A geostationary hop is about 22,300 miles up and the same back down,
        so the round trip costs roughly half a second before anything else.
        On a telephone call people talk over each other.
        """
        return f"""SATELLITE CIRCUITS
{self.clock.timestamp()}
{'=' * 62}

NONE ON THIS POSITION
{'=' * 62}
Nothing this office switches goes by satellite. The routes here are
microwave radio and coaxial cable, and that is a decision rather than an
omission.

THE REASON
{'=' * 62}
A geostationary satellite sits about 22,300 miles above the equator. Up
and down again is roughly a quarter of a second, and a round trip is
half a second before the switching at either end has done anything.

On a data circuit that is a number you engineer around. On a telephone
call it is two people talking over each other and then both stopping,
which is what an echo suppressor is for and why one is on every circuit
that has been near a satellite.

That is the whole reason a call from here to Chicago goes overland when
there is a perfectly good transponder available.

SEE ALSO
{'=' * 62}
microwave(1), radio(1), trace(1)
"""

    # -- weather(1) -------------------------------------------------------

    def cmd_weather(self, args: Optional[List[str]] = None) -> str:
        """
        What it is doing outside, and what that means for the plant.

        This is not scenery. Wet cable is documented as worsening with rain,
        and on this position that is a literal mechanism: water in an
        unrepaired binder group takes another pair faster the harder it is
        raining, and each pair that goes is another report on your board.
        """
        weather = self.desk.weather
        sections = self.desk.plant.open_sections()
        rows = ["WEATHER", self.clock.timestamp(), '=' * 62, '',
                f"  Now           {weather.label()}",
                f"  Outlook       {weather.outlook()}",
                '',
                f"  {weather.condition.note}",
                '']

        if weather.history and len(weather.history) > 1:
            rows.append("THROUGH THE TOUR")
            for minutes, key in weather.history:
                rows.append(f"  {minutes // 60 + 8:02d}:00  "
                            f"{CONDITIONS[key].label}")
            rows.append('')

        rows.append("WHAT IT IS DOING TO THE PLANT")
        if not sections:
            rows.append("  No wet sheath on this board. Rain costs you "
                        "nothing today.")
        elif not weather.wet:
            rows.append(f"  {len(sections)} wet sheath"
                        f"{'' if len(sections) == 1 else 's'} open, and "
                        f"nothing falling on {'it' if len(sections) == 1 else 'them'}.")
            rows.append("  Water already in a sheath does not dry out on "
                        "its own, but it")
            rows.append("  spreads slower when it is not being fed.")
        else:
            rows.append(f"  {len(sections)} wet sheath"
                        f"{'' if len(sections) == 1 else 's'} open and it is "
                        f"raining on {'it' if len(sections) == 1 else 'them'}.")
            rows.append("  Expect more pairs off the same cables. A splicer "
                        "trip now costs")
            rows.append("  one dispatch; the same water tomorrow costs "
                        "several.")
        for section in sections:
            rows.append(f"    {section.describe()}")
            if section.alarming():
                rows.append("      pressure contactor alarming on this "
                            "sheath")
        rows.extend(['', "lmos cable groups the board by binder group."])
        return '\n'.join(rows)

    # -- force(1) ---------------------------------------------------------

    def cmd_force(self, args: Optional[List[str]] = None) -> str:
        """
        Who is available to go out, and who is already on something.

        Dispatching used to go to a category, and a category is never busy.
        This wire centre has five people. When they are all out, the job
        waits, and knowing that before you promise a customer a time is the
        whole reason to look.
        """
        force = self.desk.force
        now = self.clock.now()
        rows = ["FIELD FORCE", self.clock.timestamp(), '=' * 62, '',
                f"  {'WHO':<16}{'TITLE':<32}STATE",
                '  ' + '-' * 60]
        for crew in CREWS:
            job = force.out.get(crew.key)
            if job is None:
                state = f"free, {LOCATIONS[force.at[crew.key]].standing}"
            else:
                state = (f"out on {job.report}, back "
                         f"{job.back_at().strftime('%H:%M')}")
            rows.append(f"  {crew.name:<16}{crew.title:<32}{state}")

        rows.append('')
        short = [category for category in DISPATCH_FORCES
                 if force.crews_for(category)
                 and not force.free(category, now)]
        if short:
            rows.append("NOBODY FREE ON")
            for category in short:
                waiting = force.soonest_free(category, now)
                when = waiting.back_at().strftime('%H:%M') if waiting else '?'
                rows.append(f"  {category:<20}next in at {when}")
            rows.append('')
            rows.append("A report dispatched to one of those stays on the "
                        "board. It is not")
            rows.append("lost; it is queued, and the queue runs on the "
                        "customer's commitment.")
        else:
            rows.append("Somebody is free on every category.")
        return '\n'.join(rows)

    # -- tone(1) ----------------------------------------------------------

    def cmd_tone(self, args: Optional[List[str]] = None) -> str:
        """
        Write a signalling tone to a file you can listen to.

        Every frequency, level and cadence in the tone plan has been in
        this simulation's data since it was written, described in words and
        never heard. A craftsperson told a busy from a reorder by ear -
        they are the same two frequencies and differ only in how fast they
        are interrupted - and reading that off a table is not the same
        skill.

        ``tone`` lists what can be made. ``tone busy`` writes it. ``tone mf
        KP212ST`` pulses an address the way a switch would, and ``tone dtmf
        5551212`` the way a Touch-Tone set would.
        """
        args = args or []
        if not args or args[0] in ('list', '-l'):
            return self._tone_listing()

        normalise = '-n' in args
        rest = [item for item in args if not item.startswith('-')]
        what = rest[0].lower()
        argument = rest[1] if len(rest) > 1 else None

        try:
            samples = tones.render(what, argument, seconds=3.0)
        except KeyError:
            return (f"tone: {rest[0]}: nothing of that name.\n"
                    f"tone with no argument lists what can be made.")

        # A wave file is not something this machine could have made, so it
        # does not go in the simulated tree. It goes where the rest of this
        # session's real files go, and the path printed is a real one you
        # can play.
        folder = os.path.join(state_dir(), 'tones')
        name = f"{what}{'-' + argument if argument else ''}.wav"
        try:
            os.makedirs(folder, exist_ok=True)
            path = tones.write(os.path.join(folder, name), samples,
                               normalise=normalise)
        except OSError as problem:
            return f"tone: cannot write {name}: {problem}"

        seconds = len(samples) / tones.SAMPLE_RATE
        rows = [f"tone: wrote {path}",
                f"      {seconds:.2f} seconds, "
                f"{tones.SAMPLE_RATE} samples a second, "
                f"{tones.SAMPLE_WIDTH * 8} bit"]
        if what in PROGRESS_TONES:
            rows.append(f"      {PROGRESS_TONES[what].describe()}")
            rows.append(f"      {PROGRESS_TONES[what].meaning}")
        if normalise:
            rows.append("      normalised for listening: the levels in the "
                        "table are")
            rows.append("      relative to each other and a busy tone is "
                        "genuinely quiet.")
        rows.append('')
        rows.append("A wave file is not something this machine could make. "
                    "It is written")
        rows.append("outside the simulation, where you can play it.")
        return '\n'.join(rows)

    def _tone_listing(self) -> str:
        """Everything that can be rendered."""
        rows = ["SIGNALLING TONES", self.clock.timestamp(), '=' * 62, '',
                "A craftsperson identified a call's fate by ear. Busy and",
                "reorder are the same two frequencies and differ only in "
                "how fast",
                "they are interrupted, which is the whole reason the tone "
                "plan is",
                "precise.",
                '',
                f"  {'NAME':<14}WHAT IT IS",
                '  ' + '-' * 58]
        for name, description in tones.catalogue():
            rows.append(f"  {name:<14}{description[:44]}")
        rows.extend([
            '  ' + '-' * 58, '',
            "  tone <name>            write it here as a wave file",
            "  tone mf KP212ST        an address pulsed the way a switch "
            "would",
            "  tone dtmf 5551212      the way a Touch-Tone set would",
            "  tone <name> -n         normalised, for listening",
            '',
            "Levels are those in the tone plan and are relative to each "
            "other,",
            "so a busy tone really does render eleven dB below dial tone.",
        ])
        return '\n'.join(rows)

    # -- era(1) -----------------------------------------------------------

    def cmd_era(self, args: Optional[List[str]] = None) -> str:
        """
        What network the date you are set to actually produces.

        The epoch is a setting, and moving it moves the plant: a shift set
        to 1955 finds step-by-step and crossbar and no electronic switching
        anywhere, because no ESS had entered service. That is not a
        decoration - the office generator reads the first-service year of
        every system and will not place one that does not exist yet.

        What does NOT move is the writing. The message of the day, the
        divestiture memo and the netnews spool are November 1983, and this
        says so rather than letting you find out by reading a 1984
        divestiture notice on a 1955 machine.
        """
        year = self.clock.now().year
        kinds: Dict[str, int] = {}
        for office in self.central_offices.values():
            kinds[office['switch_type']] = kinds.get(office['switch_type'], 0) + 1

        rows = [f"THE NETWORK IN {year}", self.clock.timestamp(),
                '=' * 62, '',
                f"  {len(self.central_offices):,} offices in the numbering "
                f"plan this session loaded.", '',
                f"  {'SYSTEM':<10}{'IN SERVICE':<13}{'OFFICES':>9}   NAME",
                '  ' + '-' * 58]
        for code, count in sorted(
                kinds.items(),
                key=lambda item: SWITCHING_SYSTEMS[item[0]].first_service):
            system = SWITCHING_SYSTEMS[code]
            rows.append(f"  {code:<10}{system.first_service:<13}{count:>9}"
                        f"   {system.name}")
        rows.append('  ' + '-' * 58)

        absent = [code for code, system in SWITCHING_SYSTEMS.items()
                  if system.first_service > year]
        rows.append('')
        if absent:
            rows.append("NOT YET BUILT")
            for code in absent:
                system = SWITCHING_SYSTEMS[code]
                rows.append(f"  {code:<10}{system.first_service}   "
                            f"{system.name}")
            rows.append('')
            rows.append("The office generator reads the first-service year "
                        "of every system")
            rows.append("and will not place one that does not exist yet.")
        else:
            rows.append("Every system in the table is in service by "
                        f"{year}.")

        if year != 1983:
            rows.extend([
                '',
                "WHAT HAS NOT MOVED WITH YOU",
                '=' * 62,
                "The plant follows the date. The writing does not. The "
                "message of the",
                "day, /usr/doc/divestiture and the netnews spool are all "
                "November 1983,",
                f"so a shift set to {year} is a {year} network with 1983 "
                f"words on it.",
                '',
                "'set date.epoch 1983-11-14' puts them back together.",
            ])
        return '\n'.join(rows)
