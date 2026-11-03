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
from typing import Callable, Dict, List, NamedTuple, Optional, Set, Tuple

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

# The crew the switching control centre lends. Not on the wire centre's
# roster: it answers a category only while it is on loan to this one.
POOL_CREW = Crew('pool', 'Pool crew', 'Loaned from the control centre',
                 'SCC pool',
                 'Sent from wherever the control centre had a truck.')


class Assignment(NamedTuple):
    """One crew, out on one job."""

    crew: Crew
    report: str
    travel: int
    work: int
    # Minutes into the tour when the crew rolled. Everything in this module
    # is measured on the shift clock, the one the player's own work moves,
    # so that "back at" means the same thing as the commitment times do.
    left: int

    def back_at(self) -> int:
        """Minutes into the tour when this crew is available again."""
        return self.left + self.travel + self.work


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
        self.at[POOL_CREW.key] = 'FAR'
        # Keys of the crews who are away for this tour (npc.py ``AWAY``), by
        # whoever holds the tour. The only thing here that keeps a crew from
        # being sent; the watch they are on does not, since a crew is called
        # out.
        self.absent: Callable[[], Set[str]] = lambda: set()
        self.out: Dict[str, Assignment] = {}
        self.log: List[Assignment] = []
        # The category the pool crew is answering this tour, if it is here.
        self.loaned: Optional[str] = None

    # -- who is where ----------------------------------------------------

    def crews_for(self, force: str) -> List[Crew]:
        """Every crew that answers a dispatch category."""
        away = self.absent()
        crews = [crew for crew in CREWS if crew.force.lower() == force.lower()
                 and crew.key not in away]
        if self.loaned and self.loaned.lower() == force.lower():
            crews.append(POOL_CREW)
        return crews

    def roster(self) -> List[Crew]:
        """Everybody here: the wire centre's own, and the pool if it is."""
        away = self.absent()
        return ([crew for crew in CREWS if crew.key not in away]
                + ([POOL_CREW] if self.loaned else []))

    def borrow(self, force: str) -> bool:
        """
        Take the pool crew for a category. One a tour.

        Returns False when it is already here, or still out from the last
        tour's job: there is one truck in the pool and it cannot be two
        places.
        """
        if self.loaned or POOL_CREW.key in self.out:
            return False
        self.loaned = force
        self.at[POOL_CREW.key] = 'FAR'
        return True

    def free(self, force: str, now: int) -> List[Crew]:
        """Crews for a category who are not out on something else."""
        self._return_anybody_due(now)
        return [crew for crew in self.crews_for(force)
                if crew.key not in self.out]

    def busy(self, now: int) -> List[Assignment]:
        """Everybody currently out, soonest back first."""
        self._return_anybody_due(now)
        return sorted(self.out.values(), key=lambda job: job.back_at())

    def _return_anybody_due(self, now: int) -> None:
        """Bring back every crew whose job has finished."""
        for key, job in list(self.out.items()):
            if job.back_at() <= now:
                del self.out[key]
                # They come back to the garage unless they work inside.
                self.at[key] = self._home(job.crew)

    @staticmethod
    def _home(crew: Crew) -> str:
        """Where a crew stands when it has nothing on."""
        if crew.key == POOL_CREW.key:
            return 'FAR'
        return 'OFFICE' if crew.force == 'Central office' else 'GARAGE'

    # -- sending them ----------------------------------------------------

    def travel_minutes(self, crew: Crew) -> int:
        """How long this crew takes to reach a job from where they are."""
        low, high = LOCATIONS[self.at[crew.key]].minutes
        return self.rng.randint(low, high)

    def send(self, force: str, report: str, work: int,
             now: int) -> Tuple[Optional[Crew], int, str]:
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
            now: Minutes into the tour when the call went out

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

    def new_tour(self, elapsed: int) -> None:
        """
        Start a new tour's clock at zero, ``elapsed`` minutes after the old one.

        A crew still out at the handoff is still out in the morning, by
        however much of the job is left. The clocks are all measured from the
        start of a tour, so every assignment is moved back by what passed.
        """
        rebased = {}
        for key, job in self.out.items():
            moved = job._replace(left=job.left - elapsed)
            if moved.back_at() > 0:
                rebased[key] = moved
            else:
                self.at[key] = self._home(job.crew)
        self.out = rebased
        # The loan is for the tour. A job it is still out on carries over,
        # and it goes home when it is done.
        self.loaned = None

    def soonest_free(self, force: str, now: int) -> Optional[Assignment]:
        """The job that has to finish before this category is free again."""
        answering = {crew.key for crew in self.crews_for(force)}
        out = [job for job in self.busy(now) if job.crew.key in answering]
        return out[0] if out else None
