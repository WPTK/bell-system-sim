"""
The toll network, hierarchical alternate routing and dial tone.
"""

import random
from typing import (
    Dict,
    List,
    Optional,
)
from ..routing import (
    MAX_TRUNKS_IN_CONNECTION,
)
from ..data.signaling import (
    MF_FREQUENCIES,
    PROGRESS_TONES,
    SF_FREQUENCY_HZ,
    SF_IDLE_LEVEL_DBM,
    mf_sequence,
    mf_train_duration_ms,
)


from .session import SessionState


class TollCommands(SessionState):
    """
    The toll network, hierarchical alternate routing and dial tone.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def cmd_toll(self, args: Optional[List[str]] = None) -> str:
        """
        The toll network: the class 4 and higher offices and what crosses them.

        Engineering and Operations draws the boundary plainly - "the toll
        network consists of the class 4 and higher offices" - so that is what
        this shows, against the routing engine's own picture of it.
        """
        args = args or []
        network = self.toll_network
        toll_offices = [office for office in network.offices.values()
                        if office.switch_class <= 4]

        if args and args[0].lower() == 'hierarchy':
            lines = [
                "Toll Network Hierarchy",
                '=' * 74,
                "Each office homes on one of higher class by a final group. A",
                "call is completed at the lowest level of the hierarchy that",
                "can carry it, using the fewest trunks in tandem.",
                '',
            ]
            for switch_class in range(1, 5):
                members = sorted(office for office in toll_offices
                                 if office.switch_class == switch_class)
                if not members:
                    continue
                lines.append(f"CLASS {switch_class} - "
                             f"{members[0].class_name().upper()}")
                for office in members:
                    lines.append(f"  {office.code:<13}{office.name:<34}"
                                 f"homes on {office.homes_on or '-'}")
                lines.append('')
            return '\n'.join(lines).rstrip()

        if args and args[0].lower() == 'load':
            lines = [
                "Toll Trunk Group Occupancy",
                f"{self.clock.timestamp()}",
                '=' * 74,
                f"{'GROUP':<16}{'ROUTE':<12}{'CAPACITY':>10}{'IN USE':>9}"
                f"{'OCC':>7}  STATUS",
                '-' * 74,
            ]
            for name, group in sorted(self.trunk_groups.items()):
                in_use = group['capacity'] * group['utilization'] // 100
                lines.append(
                    f"{name:<16}{group['route']:<12}{group['capacity']:>10}"
                    f"{in_use:>9}{group['utilization']:>6}%  {group['status']}")
            lines.append('-' * 74)
            lines.append("Final groups are engineered to P.01, high-usage "
                         "groups to P.10.")
            return '\n'.join(lines)

        by_class: Dict[int, int] = {}
        for office in toll_offices:
            by_class[office.switch_class] = by_class.get(office.switch_class, 0) + 1

        lines = [
            "Toll Network",
            f"{self.clock.timestamp()}",
            '=' * 74,
            '',
            "The toll network consists of the class 4 and higher offices. "
            "Class 5 is",
            "the end office, where subscriber loops terminate, and is not "
            "part of it.",
            '',
            'OFFICES IN THE ROUTING TABLE',
            '-' * 74,
        ]
        for switch_class in sorted(by_class):
            sample = next(office for office in toll_offices
                          if office.switch_class == switch_class)
            lines.append(f"  Class {switch_class}  "
                         f"{sample.class_name():<24}{by_class[switch_class]:>4}")
        lines.append(f"  {'End offices (class 5)':<32}"
                     f"{len(network.offices) - len(toll_offices):>4}")

        active = [group for group in self.trunk_groups.values()
                  if group['status'] == 'ACTIVE']
        occupancy = (sum(group['utilization'] for group in active) // len(active)
                     if active else 0)
        lines.extend([
            '',
            'TRUNKING',
            '-' * 74,
            f"  Trunk groups in service      {len(active):>4}",
            f"  Mean occupancy               {occupancy:>4}%",
            f"  Maximum trunks in tandem     {MAX_TRUNKS_IN_CONNECTION:>4}",
            '',
            "  toll hierarchy    The homing chain, class by class",
            "  toll load         Trunk group occupancy",
            "  routing trace <from> <to>   Offer a call and follow it",
            "  testcall <from> <to>        Prove a trunk end to end",
        ])
        return '\n'.join(lines)
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
            found = PROGRESS_TONES.get(key)
            if found is None:
                return (f"dialtone: no tone named '{args[1]}'\n"
                        f"Available: {', '.join(PROGRESS_TONES)}")
            timing = ('continuous' if found.cadence is None
                      else f'{found.cadence[0]:g}s on / {found.cadence[1]:g}s off')
            return f"""{found.name}
{'=' * 52}
Frequencies:      {' + '.join(f'{hz} Hz' for hz in found.frequencies)}
Timing:           {timing}
Interruptions:    {found.interruptions_per_minute or 'not applicable'} per minute
Level:            {found.level_dbm:g} dBm

{found.meaning}"""

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
