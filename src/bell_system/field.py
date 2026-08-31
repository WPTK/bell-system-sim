"""
The field force: who goes out, from where, and how long it takes them.

Dispatching used to go to a category. "Cable repair" would take the job and
report back, and however many jobs you gave it, all of them were worked at
once by nobody in particular. That is not what a wire centre had. It had
four or five people, each of them somewhere, each of them already doing
something, and the answer to "can somebody go" depended on which of those
things was true.

WHAT IS GROUNDED

The craft titles are real Bell System job titles - cable splicer, station
installer, lineman, switching equipment technician - and the division of
work between them is the division the dispatch categories already carry:
the splicer owns the sheath, the installer owns the station and the drop,
the switchman owns everything on the office side of the protector.

WHAT IS THE SIMULATION'S OWN

The people. The garage and its travel times. A wire centre's actual force
size varied with the plant it served and no source consulted here fixes a
number, so five is a working figure chosen to make the queue matter without
making it the whole game.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, NamedTuple, Optional, Tuple

class Place(NamedTuple):
    """Somewhere a crew can be, and how long it takes them to leave it."""

    key: str
    # Reads after "rolled from".
    came_from: str
    # Reads on its own in a listing.
    standing: str
    minutes: Tuple[int, int]


# Where a crew can be, and how long it takes them to get to a job from
# there. The simulation's own working figures, in minutes, chosen so that
# the difference between a crew in the garage and a crew across the
# district is worth a moment's thought and not more.
LOCATIONS: Dict[str, Place] = {
    'GARAGE': Place('GARAGE', 'the garage', 'in the garage', (5, 15)),
    'OFFICE': Place('OFFICE', 'upstairs', 'in the building', (0, 5)),
    'DISTRICT': Place('DISTRICT', 'out in the district',
                      'somewhere in the district', (15, 40)),
    'FAR': Place('FAR', 'the far end of the district',
                 'at the far end of the district', (35, 70)),
}


class Crew(NamedTuple):
    """One person or two-hand crew the position can send."""

    key: str
    name: str
    title: str
    # Which of the four dispatch categories this crew answers.
    force: str
    note: str


# The force this wire centre has. Titles are real; the people are not, and
# the module docstring says so.
CREWS: Tuple[Crew, ...] = (
    Crew('okafor', 'Okafor, L.', 'Cable Splicer', 'Cable repair',
         'Opens sheaths. The only one who can, and knows it.'),
    Crew('sandoval', 'Sandoval, J.', 'Cable Splicer', 'Cable repair',
         'Second splicer. Newer, and slower on a big sheath.'),
    Crew('bright', 'Bright, A.', 'Lineman', 'Outside plant',
         'Aerial and buried plant between the office and the drop.'),
    Crew('finch', 'Finch, W.', 'Station Installer', 'Station',
         'Drop, protector and set. Everything the customer can see.'),
    Crew('nakamura', 'Nakamura, T.', 'Switching Equipment Technician',
         'Central office', 'In the building. Travel time is the stairs.'),
)

CREWS_BY_KEY: Dict[str, Crew] = {crew.key: crew for crew in CREWS}


class Assignment(NamedTuple):
    """One crew, out on one job."""

    crew: Crew
    report: str
    travel: int
    work: int
    left: datetime

    def back_at(self) -> datetime:
        """When this crew is available again."""
        return self.left + timedelta(minutes=self.travel + self.work)


class FieldForce:
    """
    Where everybody is, and what it costs to send them.

    Holds no reports. The desk asks it who can take a job and it answers
    with a crew, a travel time, and where they were when the call came.
    """

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        # Where each crew is standing right now.
        self.at: Dict[str, str] = {}
        for crew in CREWS:
            self.at[crew.key] = ('OFFICE' if crew.force == 'Central office'
                                 else self.rng.choice(('GARAGE', 'GARAGE',
                                                       'DISTRICT')))
        self.out: Dict[str, Assignment] = {}
        self.log: List[Assignment] = []

    # -- who is where ----------------------------------------------------

    def crews_for(self, force: str) -> List[Crew]:
        """Every crew that answers a dispatch category."""
        return [crew for crew in CREWS if crew.force.lower() == force.lower()]

    def free(self, force: str, now: datetime) -> List[Crew]:
        """Crews for a category who are not out on something else."""
        self._return_anybody_due(now)
        return [crew for crew in self.crews_for(force)
                if crew.key not in self.out]

    def busy(self, now: datetime) -> List[Assignment]:
        """Everybody currently out, soonest back first."""
        self._return_anybody_due(now)
        return sorted(self.out.values(), key=lambda job: job.back_at())

    def _return_anybody_due(self, now: datetime) -> None:
        """Bring back every crew whose job has finished."""
        for key, job in list(self.out.items()):
            if job.back_at() <= now:
                del self.out[key]
                # They come back to the garage unless they work inside.
                self.at[key] = ('OFFICE'
                                if job.crew.force == 'Central office'
                                else 'GARAGE')

    # -- sending them ----------------------------------------------------

    def travel_minutes(self, crew: Crew) -> int:
        """How long this crew takes to reach a job from where they are."""
        low, high = LOCATIONS[self.at[crew.key]].minutes
        return self.rng.randint(low, high)

    def send(self, force: str, report: str, work: int,
             now: datetime) -> Tuple[Optional[Crew], int, str]:
        """
        Send somebody, and say who and from where.

        Returns the crew, the travel time in minutes, and where they were
        when the call came. A crew is None when everybody who answers that
        category is already out, which is a real answer and not a failure:
        the job waits, and waiting is what a finite force costs.

        Args:
            force: One of the four dispatch categories
            report: The report number, for the record
            work: How long the repair itself will take, in minutes
            now: When the call went out

        Returns:
            (crew or None, travel minutes, where they came from)
        """
        available = self.free(force, now)
        if not available:
            return None, 0, ''
        # The nearest free crew goes, which is what a dispatcher would do.
        available.sort(key=lambda crew: LOCATIONS[self.at[crew.key]].minutes[0])
        crew = available[0]
        came_from = LOCATIONS[self.at[crew.key]].came_from
        travel = self.travel_minutes(crew)
        job = Assignment(crew, report, travel, work, now)
        self.out[crew.key] = job
        self.log.append(job)
        self.at[crew.key] = 'DISTRICT'
        return crew, travel, came_from

    def soonest_free(self, force: str, now: datetime) -> Optional[Assignment]:
        """The job that has to finish before this category is free again."""
        out = [job for job in self.busy(now)
               if job.crew.force.lower() == force.lower()]
        return out[0] if out else None
