"""
The practical for each sign-off after Loop.

A count says you have closed enough reports. It does not say you can do the
thing the sign-off is for, and Halloran signs the sheet. So past the count he
stages one report on the live board, one that needs the verb the sign-off adds,
and he does not sign until it is worked.

A practical is data: the report it stages, what he says about it, what he looks
at when you hand it in, and what he says if it is not there. The terminal
that runs one is screens/practical.py; the verbs it asks for are verbs.py.

Nothing here is saved. What a stage changes on the board is either on the
report (which the shift save carries) or put back when the practical ends.
"""

from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

from ..field import POOL_CREW, Assignment

# The outside plant crews' standing excuse, while the scc practical is on.
_TIED_UP = 'a cable failure on the east side'


class Scene(NamedTuple):
    """What a practical is allowed to look at and touch."""

    desk: Any
    report: Any
    groups: Dict[str, Any]
    # Minutes into the tour, on the clock the crews run on.
    now: int


class Practical(NamedTuple):
    """One sign-off's practical."""

    key: str
    title: str
    # The condition the staged report carries.
    fault: str
    # What the customer says. Empty keeps whatever the desk drew.
    symptom: str
    # What Halloran says. {number}, {tn} and {extra} are filled in.
    brief: Tuple[str, ...]
    # Shape the board for it. Returns a sentence for the brief, or ''.
    stage: Callable[[Scene], str]
    # What was missed, in his voice. Nothing missed is a pass.
    check: Callable[[Scene], List[str]]
    # Put back whatever the stage moved, pass or fail.
    strike: Callable[[Scene], None]
    # The nudges 'hint' gives during it, smallest first.
    hints: Tuple[Tuple[str, ...], ...]


def _nothing(scene: Scene) -> str:
    """A stage with nothing to move."""
    del scene
    return ''


def _put_back(scene: Scene) -> None:
    """A strike with nothing to put back."""
    del scene


def _active(scene: Scene) -> List[str]:
    """The trunk groups in service, by name."""
    return [name for name, group in scene.groups.items()
            if group['status'] == 'ACTIVE']


def _sent_a_truck(scene: Scene) -> List[str]:
    """Said when a truck went to a trouble that no truck can reach."""
    if scene.report.dispatched_to:
        return ["You sent a truck. Nothing a truck can reach is wrong "
                "with this one, and that is the lesson in it."]
    return []


# -- frame ------------------------------------------------------------------


def _check_frame(scene: Scene) -> List[str]:
    """The jumper has to come down."""
    if scene.report.record.frame_defect is None:
        return []
    missed = ["The trouble is still on the frame. A line that measures good "
              "and will not complete a call can be a jumper or a protector, "
              "and the frame is where you look: cosmos jumper, then "
              "cosmos fix."]
    return missed + _sent_a_truck(scene)


# -- office -----------------------------------------------------------------


def _check_office(scene: Scene) -> List[str]:
    """The line has to be moved off the bad line equipment."""
    if any(note.startswith('office:') for note in scene.report.test_notes):
        return []
    missed = [f"The false cross or ground is still on line equipment "
              f"{scene.report.record.line_equipment}. The loop is not the "
              f"trouble; the switch is. switch clear moves the line off it."]
    return missed + _sent_a_truck(scene)


# -- scc --------------------------------------------------------------------


def _stage_pool(scene: Scene) -> str:
    """Send every local outside plant crew out on something long."""
    force = scene.desk.force
    # One loan a tour. A tour that has spent it on something else would
    # have no way to pass this, so the practical gives the pool crew back.
    if POOL_CREW.key not in force.out:
        force.loaned = None
    for crew in force.crews_for('Outside plant'):
        force.out[crew.key] = Assignment(crew, _TIED_UP, 40, 180, scene.now)
    return ("Both outside plant crews are tied up on " + _TIED_UP + ".")


def _check_pool(scene: Scene) -> List[str]:
    """The pool crew has to have gone."""
    report, force = scene.report, scene.desk.force
    if report.crew == POOL_CREW.name:
        return []
    if force.loaned is None:
        return ["You never asked the control centre for the pool crew. "
                "With your own crews out, dispatch only waits: "
                "connect pool outside plant."]
    if force.loaned.lower() != 'outside plant':
        return [f"The pool crew is yours for {force.loaned.lower()}. The "
                f"trouble was outside plant, so they sat."]
    return ["The pool crew is here and nobody sent them. Dispatch to "
            "outside plant as you always do: they are the crew free."]


# -- trunk ------------------------------------------------------------------

# How bad the stuck group is. Below any group the sim draws.
_STUCK_QUALITY = 0.80
_REPAIRED_QUALITY = 0.985


def _stage_trunk(scene: Scene) -> str:
    """Put a member that will not release into one trunk group."""
    names = _active(scene)
    if names:
        worst = min(names, key=lambda name: scene.groups[name]['quality'])
        scene.groups[worst]['quality'] = _STUCK_QUALITY
    return ''


def _check_trunk(scene: Scene) -> List[str]:
    """The bad group has to have been found and busied out."""
    if any(note.startswith('trunk:') for note in scene.report.test_notes):
        return []
    missed = ["Nobody tested the trunks. The loop measured good and the "
              "customer says the calls do not complete: the calls reached "
              "something that was not. trunk trace tests the route and "
              "busies out the bad member."]
    return missed + _sent_a_truck(scene)


def _strike_trunk(scene: Scene) -> None:
    """Bring the group back to what a repaired trunk measures."""
    names = _active(scene)
    if names:
        worst = min(names, key=lambda name: scene.groups[name]['quality'])
        group = scene.groups[worst]
        group['quality'] = max(group['quality'], _REPAIRED_QUALITY)


# -- toll -------------------------------------------------------------------

_BUSY = 96
_SPARE = 38
_NORMAL = (72, 55)


def _loaded(scene: Scene) -> Tuple[Optional[str], Optional[str]]:
    """The busiest group and the next one, which is its alternate."""
    names = sorted(_active(scene),
                   key=lambda name: scene.groups[name]['utilization'],
                   reverse=True)
    return (names[0] if names else None,
            names[1] if len(names) > 1 else None)


def _stage_toll(scene: Scene) -> str:
    """Load one route to the point where calls give up, with room beside it."""
    busy, spare = _loaded(scene)
    if busy is None or spare is None:
        return ''
    scene.groups[busy]['utilization'] = _BUSY
    scene.groups[spare]['utilization'] = _SPARE
    return (f"{busy} is at {_BUSY}% and {spare}, which can carry what "
            f"overflows it, is at {_SPARE}%.")


def _check_toll(scene: Scene) -> List[str]:
    """The right control has to be on."""
    control = scene.desk.control
    if control == 'reroute':
        return []
    if control == 'block':
        return ["You blocked the route. That throws away calls the "
                "alternate had room for. Block is for a route with nowhere "
                "to send them; this one had somewhere."]
    return ["Nothing is on the route. The no-trouble reports are the "
            "customers reaching a route that is full, and they will keep "
            "coming. toll control reroute puts the overflow where there is "
            "room."]


def _strike_toll(scene: Scene) -> None:
    """Take the practical's control off and let the routes settle."""
    scene.desk.control = None
    busy, spare = _loaded(scene)
    if busy is not None and spare is not None:
        scene.groups[busy]['utilization'] = _NORMAL[0]
        scene.groups[spare]['utilization'] = _NORMAL[1]


PRACTICALS: Dict[str, Practical] = {practical.key: practical for practical in (
    Practical(
        key='frame', title='Main Distributing Frame',
        fault='CO_EQUIP', symptom='Calls do not complete',
        brief=(
            "{number}, {tn}. The customer says calls do not complete.",
            "The loop measures good. I have been down to the frame about",
            "this one before. Go and see what is on it, and put it right.",
        ),
        stage=_nothing, check=_check_frame, strike=_put_back,
        hints=(
            ("The loop is fine. A good loop and a line that will not "
             "complete is somebody's work at the frame.",),
            ("cosmos jumper {number} shows what is on the frame for the "
             "line.",),
            ("cosmos fix {number} takes it down and runs it right. Then "
             "qual submit.",),
        )),
    Practical(
        key='office', title='Central Office Switching',
        fault='FCG', symptom='Calls do not complete',
        brief=(
            "{number}, {tn}. Calls do not complete.",
            "The frame is clean and the loop is good. That leaves the",
            "line equipment, and you do not send a truck to that.",
        ),
        stage=_nothing, check=_check_office, strike=_put_back,
        hints=(
            ("The loop and the frame are clean. What is left is on the "
             "switch side.",),
            ("A false cross or ground sits in the line equipment. switch "
             "runs diagnostics on it.",),
            ("switch clear {number} moves the line off it. Then qual "
             "submit.",),
        )),
    Practical(
        key='scc', title='Switching Control Center',
        fault='OPEN', symptom='',
        brief=(
            "{number}, {tn}. A cut cable, and an outside plant crew is what",
            "it needs. {extra}",
            "Get somebody there. Waiting for your own crews is the long way.",
        ),
        stage=_stage_pool, check=_check_pool, strike=_put_back,
        hints=(
            ("Dispatch will only put it on the list while your own crews "
             "are out. 'force' shows where they are.",),
            ("The control centre keeps one crew for exactly this: connect "
             "pool, and the category.",),
            ("connect pool outside plant, then report dispatch {number} "
             "outside plant. Then qual submit.",),
        )),
    Practical(
        key='trunk', title='Interoffice Trunks',
        fault='NONE', symptom='Calls do not complete',
        brief=(
            "{number}, {tn}. Calls do not complete. The line is good,",
            "I have measured it twice. One trunk group has a member that",
            "is not releasing. Find it and take it out of service.",
        ),
        stage=_stage_trunk, check=_check_trunk, strike=_strike_trunk,
        hints=(
            ("Nothing is wrong with the line. The calls are going "
             "somewhere that is.",),
            ("'trunk' lists the groups and how each one is measuring. "
             "One of them is not like the others.",),
            ("trunk trace {number} tests the route and busies out the "
             "bad member. Then qual submit.",),
        )),
    Practical(
        key='toll', title='Toll Network',
        fault='NONE', symptom='Calls do not complete',
        brief=(
            "{number}, {tn}. Calls do not complete, and it is the second",
            "one this hour that tests good. {extra}",
            "Put a control on that does the customers some good.",
        ),
        stage=_stage_toll, check=_check_toll, strike=_strike_toll,
        hints=(
            ("A route that is full gives you reports that test good. "
             "'traffic routes' shows which.",),
            ("A control can hold calls off a route or send the overflow "
             "elsewhere. One of those throws calls away.",),
            ("toll control reroute. Then qual submit; I will take it off "
             "myself.",),
        )),
)}
