#!/usr/bin/env python3
"""
Measure what the service index actually does over many shifts.

The three penalty weights - 55 for a wrong disposition, 35 for a repeat, 20
for a missed commitment - were the simulation's own and untested. They were
apportioned by argument (a wrong close is worst because it leaves a customer
out of service believing they have been dealt with) and nobody had ever run
the loop enough times to see what they produce.

This runs it. Three players of different competence work a few hundred
shifts each against the real report desk, and the script prints where their
indexes land and whether the bands separate them.

WHAT A GOOD ANSWER LOOKS LIKE

The bands are EXCELLENT at 95, SATISFACTORY at 88, MARGINAL at 78. For
those to mean anything:

  - a careful player should mostly be EXCELLENT and never below SATISFACTORY
  - an ordinary player should sit around SATISFACTORY, going either way
  - a careless one should be below MARGINAL more often than not

If every player scores 97 the index is not measuring anything. If a careful
player can land in MARGINAL the penalties are too sharp for a single shift.

Run it with:

    python3 tools/index_calibration.py [shifts]
"""

import random
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from bell_system.cable import binder_of                       # noqa: E402
from bell_system.clock import career_progress                 # noqa: E402
from bell_system.data.trouble import FAULTS, REAL_FAULTS      # noqa: E402
from bell_system.progression import (                         # noqa: E402
    DIFFICULTIES,
    MISSED_COMMITMENT_WEIGHT,
    REPEAT_REPORT_WEIGHT,
    WRONG_DISPOSITION_WEIGHT,
)
from bell_system.reports import MAX_PENDING, ReportDesk       # noqa: E402
from bell_system.screens.position import CAREER_DEPTH         # noqa: E402

SHIFT_START = datetime(1983, 11, 14, 8, 0)
SHIFT_MINUTES = 480


class Player:
    """
    One way of working a board, played out against a real report desk.

    Three behaviours decide everything: whether they measure before closing,
    whether they read the board for a cable pattern before dispatching, and
    how reliably they name the fault they were shown.
    """

    def __init__(self, name: str, tests: bool, reads_the_board: bool,
                 accuracy: float, dawdles: int = 0):
        self.name = name
        self.tests = tests
        self.reads_the_board = reads_the_board
        self.accuracy = accuracy
        # Extra minutes spent on every report before closing it. Isolates the
        # missed-commitment penalty from the other two: a player who is
        # accurate but slow should lose only that one.
        self.dawdles = dawdles

    def close_as(self, truth: str, tested: bool,
                 rng: random.Random) -> Tuple[int, str]:
        """
        Decide how this player closes a report.

        A player who measured knows the truth and mostly says it. One who
        did not is guessing from the customer's words, which is exactly the
        situation the disposition codes exist to distinguish.
        """
        if tested and rng.random() < self.accuracy:
            return (8, None) if truth == 'NONE' else (5, truth)
        if rng.random() < 0.5:
            # The commonest wrong call: nothing found, close it out.
            return 8, None
        return 5, rng.choice(REAL_FAULTS)


PLAYERS = (
    Player('careful', tests=True, reads_the_board=True, accuracy=0.97),
    Player('ordinary', tests=True, reads_the_board=False, accuracy=0.86),
    Player('careless', tests=False, reads_the_board=False, accuracy=0.40),
    # Two players who fail in exactly one way, so each penalty can be seen
    # on its own rather than tangled with the other two.
    Player('slow', tests=True, reads_the_board=True, accuracy=0.97,
           dawdles=90),
    # Measures every line and then names the wrong fault anyway: isolates
    # the wrong-disposition penalty from the not-testing one.
    Player('guesser', tests=True, reads_the_board=True, accuracy=0.45),
)


def play_shift(player: Player, difficulty, seed: int,
               tour: int = 1) -> Dict[str, int]:
    """
    Work one shift and return what the career record would have counted.

    The desk is the real one: the same generator, the same commitments, the
    same cable plant. What differs is only what the player does with it,
    and which tour of the career it is - a later tour carries a deeper
    board and wetter weather, and this is where that gets measured rather
    than assumed.
    """
    rng = random.Random(seed)
    desk = ReportDesk('201', '555', 'NWRKNJ02', rng,
                      wet_bias=career_progress(tour))
    desk.depth_limit = round(MAX_PENDING + CAREER_DEPTH * career_progress(tour))
    desk.open_shift(SHIFT_START, difficulty.commitment_slack_minutes)

    now = SHIFT_START
    counts = {'closed': 0, 'wrong': 0, 'repeats': 0, 'missed': 0,
              'dispatches': 0}
    repeated: set = set()

    while now < SHIFT_START + timedelta(minutes=SHIFT_MINUTES):
        pending = desk.pending()
        if not pending:
            if desk.full():
                break
            desk.receive(now, difficulty.commitment_slack_minutes)
            continue

        report = pending[0]
        truth = report.record.fault

        if player.tests:
            desk.record_test(report, 'measured')
        if player.dawdles:
            report.spend(player.dawdles)

        # A player who reads the board dispatches once to a sheath. One who
        # does not sends somebody to every wet pair separately.
        needs_field = FAULTS[truth].dispatch not in ('None',
                                                     'None - customer contact')
        if needs_field and not report.sheath_repaired:
            if player.reads_the_board and truth == 'WET':
                group = [held for held in pending
                         if held.record.fault == 'WET'
                         and held.record.cable == report.record.cable
                         and binder_of(held.record.pair)
                         == binder_of(report.record.pair)]
                report = group[0]
            desk.dispatch(report, FAULTS[report.record.fault].dispatch, now)
            counts['dispatches'] += 1

        disposition, found = player.close_as(
            report.record.fault, report.tested, rng)
        correct = desk.close(report, disposition, found, now,
                             difficulty.count_missed_commitments)
        counts['closed'] += 1
        if not correct:
            counts['wrong'] += 1
        if report.missed_commitment:
            counts['missed'] += 1
        if desk.should_repeat(report, difficulty.repeat_report_chance):
            if report.number not in repeated:
                repeated.add(report.number)
                desk.repeat(report, now, difficulty.commitment_slack_minutes)
                counts['repeats'] += 1

        now += timedelta(minutes=max(1, report.desk_minutes))
        if not desk.full() and rng.random() < 0.4:
            desk.receive(now, difficulty.commitment_slack_minutes)

    return counts


def index_from(counts: Dict[str, int], difficulty) -> float:
    """Score a shift the way the career record scores it."""
    closed = counts['closed']
    if not closed:
        return 100.0
    wrong = counts['wrong'] / closed
    repeat = min(1.0, counts['repeats'] / closed)
    missed = (min(1.0, counts['missed'] / closed)
              if difficulty.count_missed_commitments else 0.0)
    penalty = (wrong * WRONG_DISPOSITION_WEIGHT
               + repeat * REPEAT_REPORT_WEIGHT
               + missed * MISSED_COMMITMENT_WEIGHT) * difficulty.index_penalty
    return max(0.0, round(100.0 - penalty, 1))


def band(index: float) -> str:
    """The band an index falls in, as the career record labels it."""
    if index >= 95:
        return 'EXCELLENT'
    if index >= 88:
        return 'SATISFACTORY'
    if index >= 78:
        return 'MARGINAL'
    return 'UNSATISFACTORY'


def report(shifts: int) -> None:
    """Run every player on every difficulty and print the distribution."""
    print(f"Service index over {shifts} shifts per player per difficulty")
    print(f"weights: wrong {WRONG_DISPOSITION_WEIGHT}  "
          f"repeat {REPEAT_REPORT_WEIGHT}  "
          f"missed {MISSED_COMMITMENT_WEIGHT}")
    print()

    for difficulty in DIFFICULTIES.values():
        print(f"{difficulty.name}  (penalty x{difficulty.index_penalty}, "
              f"commitments {'counted' if difficulty.count_missed_commitments else 'not counted'})")
        print(f"  {'player':<10}{'median':>8}{'mean':>8}{'p10':>7}{'p90':>7}"
              f"   {'closed':>7}   bands")
        for player in PLAYERS:
            indexes: List[float] = []
            closed: List[int] = []
            bands: Dict[str, int] = {}
            for seed in range(shifts):
                counts = play_shift(player, difficulty, seed)
                score = index_from(counts, difficulty)
                indexes.append(score)
                closed.append(counts['closed'])
                bands[band(score)] = bands.get(band(score), 0) + 1
            indexes.sort()
            spread = ' '.join(
                f"{name[:4]} {100 * count // shifts:>2}%"
                for name, count in sorted(bands.items(),
                                          key=lambda item: -item[1]))
            print(f"  {player.name:<10}"
                  f"{statistics.median(indexes):>8.1f}"
                  f"{statistics.fmean(indexes):>8.1f}"
                  f"{indexes[len(indexes) // 10]:>7.1f}"
                  f"{indexes[9 * len(indexes) // 10]:>7.1f}"
                  f"   {statistics.fmean(closed):>7.1f}   {spread}")
        print()




def sweep(shifts: int) -> None:
    """
    Try other penalty multipliers and print where each player lands.

    The question this answers is whether a setting's multiplier lets the
    bands mean anything. A multiplier that puts an ordinary player in
    EXCELLENT most of the time is not forgiving, it is uninformative.
    """
    print(f"Penalty multiplier sweep, {shifts} shifts, commitments not "
          f"counted")
    print(f"  {'x':<6}" + ''.join(f"{player.name:>22}"
                                  for player in PLAYERS[:3]))
    base = DIFFICULTIES['fun']
    for multiplier in (0.4, 0.5, 0.6, 0.7, 0.8, 1.0):
        difficulty = base._replace(index_penalty=multiplier)
        cells = []
        for player in PLAYERS[:3]:
            indexes = sorted(index_from(play_shift(player, difficulty, seed),
                                        difficulty)
                             for seed in range(shifts))
            top = sum(1 for score in indexes if score >= 95)
            cells.append(f"{statistics.median(indexes):>10.1f}"
                         f" {100 * top // shifts:>3}% exc")
        print(f"  {multiplier:<6}" + ''.join(f"{cell:>22}" for cell in cells))


if __name__ == '__main__':
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    report(count)
    sweep(count)
