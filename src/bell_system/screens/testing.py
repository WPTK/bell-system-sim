"""
The test board, the test line series and test calls.
"""

from typing import (
    Any,
    List,
    Optional,
)
from ..data.testlines import (
    TEST_LINES,
    TEST_LINE_ORDER,
)
from ..data.trouble import (
    FAULTS,
)
from ..loop_testing import (
    COIN_STATION_CURRENT_MA,
    SUPERVISION_STATES,
    access_test_line,
    design_note,
    distance_to_open,
    measure_loop,
    tone_header,
)
from ..routing import (
    MAX_TRUNKS_IN_CONNECTION,
)
from ..data.signaling import (
    SF_FREQUENCY_HZ,
    SF_IDLE_LEVEL_DBM,
    mf_sequence,
    mf_train_duration_ms,
)


from .session import SessionState


class TestingCommands(SessionState):
    """
    The test board, the test line series and test calls.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def cmd_testboard(self, args: List[str]) -> str:
        """
        Work the local test board: measure loops, reach test lines, read
        supervision.

        The board is where the three testing systems in this simulation meet.
        Loop measurement goes through mechanised loop testing, transmission
        goes through the test line series, and supervision is what single
        frequency signalling shows about a trunk.
        """
        if not args:
            pending = self.desk.pending()
            untested = [report for report in pending if not report.tested]
            return f"""Test Board - {self.home_office['clli']}
{self.clock.timestamp()}
{'=' * 66}

LOOP TESTING
  mlt <report>              Measure a subscriber loop
  testboard loop <report>   The same measurement, from the board
  report faults             What each condition measures like

TRANSMISSION TESTING
  testline                  The test line and responder series
  testline 105 <circuit>    Two-way loss, noise and gain slope
  testboard supervision <circuit>
                            Single frequency supervision state

BOARD STATUS
  Reports on the board      {len(pending)}
  Not yet measured          {len(untested)}
  Service index             {self.career.service_index():.1f} ({self.career.index_band()})

{tone_header()}. Loss objectives are stated at that frequency,
so every loss reading here is taken there."""

        action = args[0].lower()

        if action in ('loop', 'test') and len(args) > 1:
            return self.cmd_mlt([args[1]])

        if action == 'supervision':
            if len(args) < 2:
                return ("testboard: name a circuit.\n"
                        "Usage: testboard supervision <trunk group>")
            return self._show_supervision(args[1].upper())

        if action == 'results':
            return self._show_board_results()

        if action == 'status':
            return self.cmd_testboard([])

        return (f"testboard: unknown option '{args[0]}'\n"
                "Options: loop, supervision, results, status")
    def _show_supervision(self, circuit: str) -> str:
        """
        Show what single frequency signalling says about a trunk.

        The 2600 Hz tone is on an idle trunk and off a seized one. That makes
        the tone a supervisory signal a craftsperson reads: tone present while
        a connection is up is an irregularity, and it is what routine testing
        is looking for.
        """
        group = self.trunk_groups.get(circuit)
        if group is None:
            return (f"testboard: no trunk group {circuit}.\n"
                    f"Groups: {', '.join(sorted(self.trunk_groups))}")

        if group['status'] != 'ACTIVE':
            state = 'IDLE'
        elif group['quality'] < 0.994:
            state = 'ANOMALOUS'
        elif group['utilization'] > 70:
            state = 'CONNECTED'
        else:
            state = 'SEIZED'
        tone, note = SUPERVISION_STATES[state]

        lines = [
            f"Single Frequency Supervision - {circuit}",
            f"{group['route']}   {self.clock.timestamp()}",
            '=' * 66,
            f"  SF frequency        {SF_FREQUENCY_HZ} Hz",
            f"  Idle tone level     {SF_IDLE_LEVEL_DBM:+.1f} dBm",
            f"  Trunk state         {state}",
            f"  Tone                {tone}",
            '',
            f"  {note}",
            '',
            'ALL STATES',
            '-' * 66,
        ]
        for name, (tone_state, description) in SUPERVISION_STATES.items():
            marker = '>' if name == state else ' '
            lines.append(f"{marker} {name:<14} {tone_state:<28} {description}")
        lines.extend([
            '-' * 66,
            '',
            "Routine transmission testing on these groups is run by CAROT, "
            "which prints",
            "its exceptions to the maintenance teletype whether anybody is "
            "reading or not.",
        ])
        return '\n'.join(lines)
    def _show_board_results(self) -> str:
        """Show every measurement taken on the board this session."""
        measured = [
            report for report in self.desk.pending() + self.desk.closed()
            if report.test_notes
        ]
        if not measured:
            return ("No measurements taken this session.\n"
                    "Measure a loop with 'mlt <report>'.")
        lines = ["Measurements taken this session", '=' * 74]
        for report in measured:
            lines.append(f"{report.number}  {report.record.telephone_number}  "
                         f"cable {report.record.cable_pair()}")
            for note in report.test_notes:
                lines.append(f"    {note}")
        return '\n'.join(lines)
    def cmd_test(self, args: Optional[List[str]] = None) -> str:
        """Bell System equipment testing interface."""
        if not args:
            return """BELL SYSTEM TEST INTERFACE
============================

Available Test Categories:
- trunk      Test trunk group connectivity
- switch     Test switching equipment
- line       Test subscriber line equipment
- radio      Test microwave radio systems
- carrier    Test digital carrier systems

Usage: test <category> [options]
Example: test trunk TG-001
"""

        test_type = args[0].lower()

        if test_type == "trunk":
            return """TRUNK GROUP TEST RESULTS
======================
Test Target: """ + (args[1] if len(args) > 1 else "All Groups") + """
Test Time: """ + self.clock.log_stamp() + """

Continuity:    PASS
Signaling:     PASS
Traffic Load:  67% (Normal)
Error Rate:    <0.001% (Excellent)

All trunk circuits operational.
"""
        elif test_type == "switch":
            return """SWITCHING EQUIPMENT TEST
=====================
Equipment: Crossbar No. 5
Status: OPERATIONAL
Test Completed: """ + self.clock.log_stamp() + """

Register Tests:     PASS
Marker Tests:       PASS
Connector Tests:    PASS
Selector Tests:     PASS

All switching functions normal.
"""
        else:
            return f"test: unknown test type '{test_type}'\nUse 'test' for available options"
    def cmd_mlt(self, args: Optional[List[str]] = None) -> str:
        """Measure a subscriber loop and report the readings."""
        args = args or []
        if not args:
            pending = self.desk.pending()
            if not pending:
                return ("mlt: name a report or a telephone number.\n"
                        "Usage: mlt <report number | telephone number>")
            return ("mlt: name a report or a telephone number.\n"
                    "Usage: mlt <report number | telephone number>\n\n"
                    "Pending: "
                    + ', '.join(report.number for report in pending))

        report = self.desk.find(args[0])
        if report is None:
            return (f"mlt: no line record for '{args[0]}'.\n"
                    "Mechanised loop testing works from the loop assignment "
                    "record; a\nnumber with no record on this board cannot be "
                    "reached from here.")
        if report.status == 'CLOSED':
            return f"{report.number} is closed. Nothing to test."

        record = report.record
        name_fault = not self._difficulty().require_test_before_close
        measurement = measure_loop(
            record.telephone_number, record.fault, name_fault=name_fault)

        length_kft = round(measurement.distance_miles * 5.28, 1)
        loop_ohms = measurement.loop_resistance_ohms
        loop_reading = (f"{loop_ohms:>12,} ohms" if loop_ohms is not None
                        else f"{'open':>12}")
        lines = [
            f"MECHANISED LOOP TEST - {record.telephone_number}",
            f"{record.clli}  cable {record.cable_pair()}  "
            f"{self.clock.timestamp()}",
            '=' * 74,
            'INSULATION RESISTANCE (loop open, office battery removed)',
            f"  Tip to ring         {measurement.tip_ring_ohms:>12,} ohms",
            f"  Tip to ground       {measurement.tip_ground_ohms:>12,} ohms",
            f"  Ring to ground      {measurement.ring_ground_ohms:>12,} ohms",
            '',
            'FOREIGN POTENTIAL (office battery removed)',
            f"  DC                  {measurement.dc_volts:>12.1f} volts",
            f"  AC                  {measurement.ac_volts:>12.1f} volts",
            '',
            'LOOP',
            f"  Capacitance         {measurement.capacitance_uf:>12.3f} uF",
            f"  Implied distance    "
            f"{distance_to_open(measurement.capacitance_uf):>12.2f} miles "
            f"({length_kft} kft)",
            f"  Loop resistance     {loop_reading}",
            f"  Loop current        {measurement.loop_current_ma:>12.1f} mA",
            f"  Station termination "
            f"{'present' if measurement.station_termination else 'ABSENT':>12}",
            '',
            f"  {design_note(loop_ohms, length_kft)}",
        ]
        if record.class_of_service == 'COIN':
            lines.append(f"  Coin station: needs {COIN_STATION_CURRENT_MA} mA "
                         f"to operate.")
        lines.extend(['', 'TEST RESULT', f"  {measurement.verdict}"])
        if measurement.suspected:
            suspected = FAULTS[measurement.suspected]
            lines.append(f"  System reads this as: {suspected.name} "
                         f"({suspected.code})")
            lines.append(f"  Dispatch to: {suspected.dispatch}")
        else:
            lines.append("  The system will not name a condition on this "
                         "setting.")
            lines.append("  Match the reading against 'report faults'.")

        loop_note = f"{loop_ohms:,} ohms" if loop_ohms is not None else 'open'
        note = (f"{self.clock.time()} MLT: insulation T-R "
                f"{measurement.tip_ring_ohms:,}, "
                f"T-G {measurement.tip_ground_ohms:,}, "
                f"R-G {measurement.ring_ground_ohms:,}; "
                f"C {measurement.capacitance_uf} uF; loop {loop_note}")
        self.desk.record_test(report, note)

        lines.append('')
        lines.append(f"Charged to {report.number}. "
                     f"{report.age_label()} "
                     f"{'past' if report.overdue() else 'remaining'}.")
        return '\n'.join(lines)
    def cmd_testline(self, args: Optional[List[str]] = None) -> str:
        """Reach a test line or responder on a circuit and read the result."""
        args = args or []
        if not args:
            lines = [
                "Test lines and responders",
                '=' * 74,
                tone_header() + '.',
                '',
                f"{'CODE':<6} {'ACCESS':<8} {'NAME':<34} MEASURES",
                '-' * 74,
            ]
            for code in TEST_LINE_ORDER:
                test_line = TEST_LINES[code]
                lines.append(
                    f"{test_line.code:<6} {test_line.access:<8} "
                    f"{test_line.name:<34} {', '.join(test_line.measures)}"
                )
            lines.extend([
                '-' * 74,
                '',
                "Usage: testline <code> <circuit>",
                "       testline 105 TG-001-NYC",
                '',
                "Access codes are the simulation's own: real ones were local "
                "to each office.",
            ])
            return '\n'.join(lines)

        code = args[0].upper()
        if code not in TEST_LINES:
            return (f"testline: no {args[0]} test line.\n"
                    f"Codes: {', '.join(TEST_LINE_ORDER)}")
        if len(args) < 2:
            test_line = TEST_LINES[code]
            return (f"{test_line.name}\n"
                    f"{'=' * 50}\n"
                    f"Access:    {test_line.access}\n"
                    f"Direction: {test_line.direction}\n"
                    f"Measures:  {', '.join(test_line.measures)}\n\n"
                    f"{test_line.description}\n\n"
                    f"Usage: testline {code.lower()} <circuit>")

        circuit = args[1].upper()
        group = self.trunk_groups.get(circuit)
        degraded = bool(group and (group['status'] != 'ACTIVE'
                                   or group['quality'] < 0.994))
        result = access_test_line(code, circuit, degraded=degraded)
        if result is None:
            return f"testline: no {code} test line."

        lines = [
            f"{result.test_line} - {circuit}",
            f"{tone_header()}   {self.clock.timestamp()}",
            '=' * 74,
        ]
        if result.loss_db is not None:
            label = ('Return loss' if code == 'BAL' else 'Loss at 1004 Hz')
            lines.append(f"  {label:<24}{result.loss_db:>8.1f} dB")
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
        return '\n'.join(lines)
    def cmd_testcall(self, args: Optional[List[str]] = None) -> str:
        """Place a test call through the network and watch every stage of it."""
        args = args or []
        network = self.toll_network

        if not args or args[0].lower() in ('help', 'offices'):
            lines = [
                "Test Call",
                '=' * 74,
                '',
                "A test call is how a trunk is proved. The originating office",
                "seizes it, outpulses the address in multifrequency, the",
                "network advances the call through the hierarchy, and",
                "something at the far end answers so the connection can be",
                "measured. Every stage leaves a signal a craftsperson can",
                "read.",
                '',
                "Usage:",
                "  testcall <from> <to>              Place a call and follow it",
                "  testcall <from> <to> <test line>  Terminate on a test line",
                "                                    and measure the connection",
                '',
                "Test lines: " + ', '.join(TEST_LINE_ORDER),
                '',
                "OFFICES",
                '-' * 74,
            ]
            for office in sorted(network.offices.values(),
                                 key=lambda entry: (entry.switch_class,
                                                    entry.code)):
                lines.append(f"  {office.code:<13} {office.class_name():<22} "
                             f"{office.name}")
            return '\n'.join(lines)

        if len(args) < 2:
            return ("testcall: name an originating and a terminating office.\n"
                    "Usage: testcall <from> <to> [test line]")

        origin, destination = args[0].upper(), args[1].upper()
        for code in (origin, destination):
            if code not in network.offices:
                return (f"testcall: no office {code} in the routing table.\n"
                        f"Type 'testcall offices' for the list.")
        if origin == destination:
            return ("testcall: a test call needs two different offices. A "
                    "call to the office\nit started in never reaches a trunk.")

        test_line = None
        if len(args) > 2:
            code = args[2].upper()
            if code not in TEST_LINES:
                return (f"testcall: no {args[2]} test line.\n"
                        f"Test lines: {', '.join(TEST_LINE_ORDER)}")
            test_line = TEST_LINES[code]

        return self._place_test_call(origin, destination, test_line)
    def _place_test_call(self, origin: str, destination: str,
                         test_line: Optional[Any]) -> str:
        """
        Run a test call from seizure to release and narrate every stage.

        The stages are the real ones: seizure removes the single frequency
        supervisory tone toward the far end, the far end returns a start
        signal, the address goes out in multifrequency bracketed by KP and
        ST, the network advances the call through the hierarchy, and answer
        supervision comes back. Release restores the tone.
        """
        network = self.toll_network
        result = network.route(origin, destination)
        terminating = network.offices[destination]

        # The address outpulsed. A test line has its own access code; a plain
        # trunk test outpulses the terminating office's test number. Both are
        # the simulation's own: real test numbers were office records.
        address = (test_line.access if test_line is not None
                   else self.__class__._test_number_for(terminating.code))
        train = mf_sequence(address)
        train_ms = mf_train_duration_ms(train)
        start_type = self.__class__._start_signal_for(origin)

        lines = [
            f"Test Call  {origin} to {destination}",
            f"{self.clock.timestamp()}",
            '=' * 74,
            '',
            'SUPERVISION AND ADDRESS',
            '-' * 74,
            f"  Seizure              SF tone removed toward the far end "
            f"({SF_FREQUENCY_HZ} Hz)",
            f"  Idle tone level      {SF_IDLE_LEVEL_DBM:+.1f} dBm before "
            f"seizure",
            f"  Start signal         {start_type}",
            "  Address signalling   multifrequency; the talking path is "
            "muted while",
            "                       an office outpulses, which is why MF "
            "needs no",
            "                       protection against the human voice",
            f"  Address outpulsed    "
            f"{' '.join(signal.symbol for signal in train)}",
            f"  Train duration       {train_ms} ms",
            '',
            'ROUTE ADVANCE',
            '-' * 74,
        ]
        for step, attempt in enumerate(result.attempts, 1):
            lines.append(f"  {step}. {attempt}")

        lines.extend(['', 'RESULT', '-' * 74])
        if not result.completed:
            lines.extend([
                "  Outcome              BLOCKED",
                "  Caller receives      reorder",
                f"  Trunks in tandem     {result.trunk_count()} before the "
                f"block",
                '',
                "  Every trunk in a final group was busy. A final group is the",
                "  last route available, so there is nowhere for the call to",
                "  overflow to. Final groups are engineered to P.01 - one call",
                "  in a hundred finds all trunks busy - so this is the one in",
                "  a hundred, not a fault.",
            ])
            return '\n'.join(lines)

        lines.extend([
            "  Outcome              COMPLETED",
            f"  Trunks in tandem     {result.trunk_count()} of "
            f"{MAX_TRUNKS_IN_CONNECTION} permitted",
            "  Answer supervision   returned; SF tone off in both directions",
        ])

        if test_line is None:
            lines.extend([
                '',
                "  The connection is up and the talking path is through. To",
                "  measure it, terminate the call on a test line:",
                f"    testcall {origin} {destination} 105",
                '',
                "  Release              SF tone restored, trunk returned to "
                "idle",
            ])
            return '\n'.join(lines)

        degraded = result.trunk_count() >= 5
        measurement = access_test_line(
            test_line.code, f"{origin}-{destination}", degraded=degraded)
        if measurement is None:  # pragma: no cover - the code is in the table
            lines.append('')
            lines.append(f"  The {test_line.code} test line did not answer.")
            return '\n'.join(lines)

        lines.extend([
            '',
            f'MEASUREMENT - {test_line.name.upper()}',
            '-' * 74,
            f"  {tone_header()}",
        ])
        if measurement.loss_db is not None:
            label = ('Return loss' if test_line.code == 'BAL'
                     else 'Loss at 1004 Hz')
            lines.append(f"  {label:<24}{measurement.loss_db:>8.1f} dB")
        if measurement.noise_dbrnc is not None:
            lines.append(f"  {'Noise':<24}{measurement.noise_dbrnc:>8.1f} "
                         f"dBrnC")
        if measurement.noise_with_tone_dbrnc is not None:
            lines.append(f"  {'Noise with tone':<24}"
                         f"{measurement.noise_with_tone_dbrnc:>8.1f} dBrnC")
        if measurement.slope_db is not None:
            lines.append(f"  {'Gain slope':<24}{measurement.slope_db:>8.1f} dB")

        lines.append('')
        lines.append(f"  {'PASS' if measurement.passed else 'FAIL'}")
        for note in measurement.notes:
            lines.append(f"  {note}")
        if degraded:
            lines.append("  Five trunks in tandem. Loss and noise accumulate "
                         "on every one of them.")
        lines.extend([
            '',
            "  Release              SF tone restored, trunk returned to idle",
        ])
        if not measurement.passed:
            lines.extend([
                '',
                "  A circuit outside its working limits should not go back in",
                "  service. CAROT routines these groups and will find it again",
                "  tonight if you leave it.",
            ])
        return '\n'.join(lines)
    @staticmethod
    def _test_number_for(code: str) -> str:
        """
        Return the seven digit test number an office answers on.

        Real test numbers were carried in office records and varied office to
        office, so this one is the simulation's own, derived from the office
        code so a given office always answers on the same number.
        """
        seed = sum(ord(character) for character in code)
        nxx = 200 + seed % 700
        line = 1100 + seed % 90
        return f"{nxx}{line}"
    @staticmethod
    def _start_signal_for(origin: str) -> str:
        """
        Return the start signal the originating office would see.

        Which start arrangement a trunk group used was an office record, not
        a national rule. The choice here is deterministic on the office code
        so a group answers the same way every time it is tested.
        """
        arrangements = (
            'wink start - far end winks off-hook then on again, register ready',
            'delay dial - far end holds off-hook until its register is free',
            'immediate start - outpulse after a fixed interval, no handshake',
        )
        return arrangements[sum(ord(character) for character in origin)
                            % len(arrangements)]
