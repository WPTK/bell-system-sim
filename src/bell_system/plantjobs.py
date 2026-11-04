"""
Jobs the plant opens for itself.

A pressure alarm is not a customer's trouble. It has no line, no telephone
number and no commitment, and a splicer sent to it used to be sent on some
customer's report, which paid for the trip with that customer's clock and
was judged for it. The alarm now opens a job of its own. A splicer is
dispatched to the job with the same cable and binder group a dispatch to a
report names, and what the trip costs is charged to the job: the shift
clock moves, and no report's commitment or record does.

The job names the cable and never the group. Finding the group is the work,
and a dry one is a wrong trip like any other, charged here and to nobody.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .cable import binder_colour
from .data.trouble import FAULTS

if TYPE_CHECKING:  # pragma: no cover
    from .reports import ReportDesk

PREFIX = 'PJ-'


class PlantJob:
    """A sheath the contactor has alarmed on, as work to be sent to."""

    def __init__(self, number: str, cable: int, binder: int,
                 opened: datetime):
        self.number = number
        self.cable = cable
        self.binder = binder
        self.opened = opened
        # Time spent at the desk on it, for the shift clock to charge.
        self.desk_minutes = 0

    def out(self) -> Dict[str, Any]:
        """Write the job for the save."""
        return {'number': self.number, 'cable': self.cable,
                'binder': self.binder, 'opened': self.opened.isoformat(),
                'desk_minutes': self.desk_minutes}

    @classmethod
    def read(cls, stored: Dict[str, Any]) -> 'PlantJob':
        """Read a job back, or raise if it will not read."""
        job = cls(str(stored['number']), int(stored['cable']),
                  int(stored['binder']),
                  datetime.fromisoformat(stored['opened']))
        job.desk_minutes = int(stored['desk_minutes'])
        return job


def open_job(desk: 'ReportDesk', cable: int, binder: int,
             now: datetime) -> PlantJob:
    """Open the job for an alarm on a sheath, and return it."""
    job = PlantJob(f"{PREFIX}{len(desk.jobs) + 1:03d}", cable, binder, now)
    desk.jobs.append(job)
    return job


def find_job(desk: 'ReportDesk', token: str) -> Optional[PlantJob]:
    """The job a number names, if it names one."""
    for job in desk.jobs:
        if job.number == token.upper():
            return job
    return None


def is_open(desk: 'ReportDesk', job: PlantJob) -> bool:
    """
    Whether the sheath the job was opened for is still unrepaired.

    A later leak in the same group is another sheath with another alarm, and
    it opens a job of its own; it does not bring this one back.
    """
    section = desk.plant.open_section(job.cable, job.binder)
    return section is not None and section.opened <= job.opened


def job_at(desk: 'ReportDesk', cable: int,
           binder: int) -> Optional[PlantJob]:
    """The open job for a cable and binder group, if the alarm has one."""
    for job in desk.jobs:
        if job.cable == cable and job.binder == binder and is_open(desk, job):
            return job
    return None


def open_missing(desk: 'ReportDesk') -> None:
    """
    Open a job for every alarm that is standing without one.

    A shift saved before there were jobs has its alarmed sheaths and no
    jobs, and the alarm will not sound again to open them.
    """
    for section in desk.plant.open_sections():
        if section.alarmed and job_at(
                desk, section.cable, section.binder) is None:
            open_job(desk, section.cable, section.binder, section.opened)


def listing(desk: 'ReportDesk') -> List[str]:
    """The open jobs, one line each, for the board to print."""
    return [f"{job.number}  pressure alarm, cable {job.cable:04d}  "
            f"opened {job.opened.strftime('%H:%M')}"
            for job in desk.jobs if is_open(desk, job)]


def work(desk: 'ReportDesk', job: PlantJob, force: str,
         section: Optional[Tuple[int, int]], now: int, required: bool,
         name_fault: bool) -> Tuple[str, bool]:
    """
    Send a force to a job, and say what the field found and whether it went.

    Args:
        desk: The report desk, which holds the plant and the crews
        job: The job
        force: The force's name as the desk spells it
        section: The cable and binder group the splicer is told to open
        now: Minutes into the tour on the shift clock
        required: Whether the splicers will not go without a group named
        name_fault: Whether the crew says what it was

    Returns:
        The field's answer, and whether a crew went. Nothing is charged to
        a refusal.
    """
    if force.lower() != 'cable repair':
        return (f"{job.number} is cable plant. Only Cable repair works it.",
                False)
    if not is_open(desk, job):
        return (f"{job.number}: cable {job.cable} has been opened and "
                f"resealed. Nothing is left to do.", False)
    if section is None:
        if required:
            return ("The splicers will not open a sheath on a guess. "
                    "Which one?\n"
                    f"  report dispatch {job.number} cable <cable>/<binder>",
                    False)
        section = (job.cable, job.binder)
    if section[0] != job.cable:
        return (f"{job.number} is an alarm on cable {job.cable}, and a "
                f"splicer is not sent to another cable on it.", False)

    wet = desk.plant.open_section(*section)
    low, high = FAULTS['WET'].typical_minutes
    repair = desk.rng.randint(low, high)
    from .reports import (
        COST_DISPATCH, COST_WRONG_DISPATCH, COST_WRONG_DISPATCH_DESK,
    )
    cost = repair if wet is not None else COST_WRONG_DISPATCH
    crew, travel, came_from = desk.force.send(force, job.number, cost, now)
    if crew is None:
        waiting = desk.force.soonest_free(force, now)
        job.desk_minutes += COST_DISPATCH
        if waiting is None:  # pragma: no cover - no crew for the category
            return f"Nobody answers {force} from this position.", False
        return (f"Nobody free on {force.lower()}. {waiting.crew.name} is "
                f"on {waiting.report}.\n{job.number} stays open.", False)
    went = (f"{crew.name} ({crew.title.lower()}) rolled from {came_from}, "
            f"{travel} minutes.")
    if wet is None:
        job.desk_minutes += COST_DISPATCH + COST_WRONG_DISPATCH_DESK
        return (f"{went}\n{crew.name} opened cable {section[0]}, binder "
                f"{section[1]} ({binder_colour(section[1])}) and found it "
                f"dry.\n{COST_WRONG_DISPATCH + travel} minutes on the trip, "
                f"and {crew.name} is now out on nothing. No customer's "
                f"commitment is charged for it.", True)
    job.desk_minutes += COST_DISPATCH
    # The reports on this sheath are not cleared with it. A trip sent to a
    # job is nobody's dispatch, and a report that closed on it would never
    # have been judged for one; each is dispatched, and judged, on its own.
    desk.clear_sheath(wet, job.opened, flag=False)
    found = 'water in' if name_fault else 'trouble in'
    lines = [went,
             f"{crew.name} reports {found} cable {wet.cable}, binder "
             f"{wet.binder} ({wet.colour()}), pairs {wet.first_pair}-"
             f"{wet.last_pair}.",
             f"Sheath opened, dried and resealed. {repair} minutes on the "
             f"job."]
    return '\n'.join(lines), True
