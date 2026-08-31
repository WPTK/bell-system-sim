"""
Hierarchical alternate routing through the toll network.

Routing in the Bell System followed one rule above all: complete the
connection at the lowest level of the hierarchy that can carry it, using the
fewest trunks in tandem. An office offers a call first to a high-usage group -
a direct route engineered to overflow - and only when every trunk there is
busy does it hand the call up its homing chain on a final group. Final groups
are the last resort: when every trunk in one is busy the call is blocked and
the caller hears reorder.

The distinction between direct and tandem groups (topology) and between
high-usage and final groups (how traffic is offered to them) is real and was
easy to conflate: a direct group is not necessarily a high-usage group.

Engineering and Operations in the Bell System records that the average toll
connection used slightly over three trunks including toll connecting trunks,
and that no connection could use more than nine. A minimum toll connection is
three: up a toll connecting trunk, across one intertoll group, and back down.

Grade of service is engineered per group, not end to end. Each final group
meets P.01 - one call in a hundred finds every trunk busy in the busy hour -
so a connection crossing several groups blocks more often than any one of
them does. That accumulation is a property of the real engineering, not an
artefact of this model.
"""

import random
from typing import Dict, List, NamedTuple, Optional, Tuple

# No connection in the network could exceed this many trunks in tandem.
MAX_TRUNKS_IN_CONNECTION = 9

# Grade of service objectives. Final groups are engineered so that one call
# in a hundred finds every trunk busy; high-usage groups are deliberately
# allowed to overflow far more often, because overflow is their purpose.
FINAL_GROUP_BLOCKING = 0.01
HIGH_USAGE_BLOCKING = 0.10

# Share of CALLS offered to an end office toll trunk, which bypasses the toll
# centre entirely. The documented statistic - roughly 36,000 of the 168,000
# trunks carrying New Jersey toll traffic at the end of 1982 - counts trunks
# provisioned, not calls routed, and the two are not interchangeable. This
# value is a model parameter, chosen so the mean connection length reproduces
# the documented average of slightly over three trunks; it is calibration,
# not a figure taken from a source.
END_OFFICE_TOLL_TRUNK_SHARE = 0.05
END_OFFICE_TOLL_TRUNK_SHARE_OF_TRUNKS = 0.21

# Shared source of randomness when a caller does not supply one. Assigning
# the random module itself would type as a module rather than a generator.
_DEFAULT_RNG = random.Random()

CLASS_NAMES: Dict[int, str] = {
    1: 'Regional Center',
    2: 'Sectional Center',
    3: 'Primary Center',
    4: 'Toll Center',
    5: 'End Office',
}


class Office(NamedTuple):
    """A switching office and its place in the hierarchy."""

    code: str
    name: str
    switch_class: int
    homes_on: Optional[str]

    def class_name(self) -> str:
        """Return the name of this office's hierarchy class."""
        return CLASS_NAMES[self.switch_class]


class RouteLeg(NamedTuple):
    """One trunk group traversed by a connection."""

    from_office: str
    to_office: str
    group_type: str
    blocked: bool
    utilization: int


class RouteResult(NamedTuple):
    """The outcome of offering a call to the network."""

    completed: bool
    legs: List[RouteLeg]
    attempts: List[str]
    reason: str

    def trunk_count(self) -> int:
        """Return how many trunks the connection used."""
        return len(self.legs)


class TollNetwork:
    """
    A small hierarchical network the routing engine can search.

    The mechanics are those the Bell System used; the particular offices are
    the simulation's own, since the identities of the real regional centres
    are not established by any source consulted here.
    """

    def __init__(self, offices: Dict[str, Office]):
        self.offices = offices

    def homing_chain(self, code: str) -> List[str]:
        """
        Return the chain of offices from one office up to its regional centre.

        An office homes on the office its final group runs to, which is not
        always the next class up.
        """
        chain = [code]
        seen = {code}
        current = self.offices.get(code)
        while current is not None and current.homes_on:
            if current.homes_on in seen:
                break
            chain.append(current.homes_on)
            seen.add(current.homes_on)
            current = self.offices.get(current.homes_on)
        return chain

    def common_point(self, origin: str, destination: str) -> Optional[str]:
        """
        Return the lowest office at which both homing chains meet.

        Regional centres were fully interconnected with one another, so two
        chains that reach different regional centres still meet: the call
        crosses between them at the top of the hierarchy.
        """
        upward = self.homing_chain(destination)
        for code in self.homing_chain(origin):
            if code in upward:
                return code
        return None

    def regional_centre(self, code: str) -> Optional[str]:
        """Return the regional centre an office ultimately homes on."""
        chain = self.homing_chain(code)
        top = self.offices.get(chain[-1])
        return top.code if top and top.switch_class == 1 else None

    def route(self, origin: str, destination: str,
              rng: Optional[random.Random] = None) -> RouteResult:
        """
        Offer a call to the network and follow it through.

        A toll call from one end office to another rides a toll connecting
        trunk up to its toll centre, crosses the intertoll network, and comes
        back down a toll connecting trunk at the far end. Some end offices
        had end office toll trunks that bypassed their toll centre entirely -
        in New Jersey at the end of 1982 roughly 36,000 of 168,000 trunks
        carrying toll traffic were of that kind - and those are tried first
        when both ends have them.

        Args:
            origin: Originating office code
            destination: Terminating office code
            rng: Source of randomness for trunk occupancy

        Returns:
            The path taken, or why the call was blocked
        """
        generator = rng if rng is not None else _DEFAULT_RNG
        attempts: List[str] = []

        if origin not in self.offices or destination not in self.offices:
            return RouteResult(False, [], attempts, 'Office not in routing table')
        if origin == destination:
            return RouteResult(False, [], attempts,
                               'Origin and destination are the same office')

        legs: List[RouteLeg] = []
        origin_office = self.offices[origin]
        destination_office = self.offices[destination]

        # An end office toll trunk bypasses the toll centre altogether. It is
        # a high-usage group like any other and overflows to the hierarchy.
        both_end_offices = (origin_office.switch_class == 5
                            and destination_office.switch_class == 5)
        if both_end_offices and generator.random() < END_OFFICE_TOLL_TRUNK_SHARE:
            overflowed = generator.random() < HIGH_USAGE_BLOCKING
            utilization = generator.randint(92, 100) if overflowed else generator.randint(55, 91)
            attempts.append(
                f'End office toll trunk {origin}-{destination}: '
                f'{utilization}% occupied'
            )
            if not overflowed:
                leg = RouteLeg(origin, destination, 'End office toll trunk',
                               False, utilization)
                return RouteResult(True, [leg], attempts,
                                   'Completed on an end office toll trunk')
            attempts.append('End office toll trunk busy; routing via the toll centre')

        # Toll connecting trunk up from the originating end office.
        intertoll_origin = origin
        if origin_office.switch_class == 5 and origin_office.homes_on:
            leg, blocked = self._offer(origin, origin_office.homes_on,
                                       'Toll connecting', attempts, generator)
            legs.append(leg)
            if blocked:
                return RouteResult(False, legs, attempts,
                                   f'All trunks busy on toll connecting group '
                                   f'{origin}-{origin_office.homes_on}; '
                                   'caller receives reorder')
            intertoll_origin = origin_office.homes_on

        # Toll connecting trunk down to the terminating end office, worked
        # out now so the intertoll segment knows where it must reach.
        intertoll_destination = destination
        final_leg: Optional[Tuple[str, str]] = None
        if destination_office.switch_class == 5 and destination_office.homes_on:
            intertoll_destination = destination_office.homes_on
            final_leg = (destination_office.homes_on, destination)

        intertoll = self._route_intertoll(intertoll_origin, intertoll_destination,
                                          attempts, generator)
        if intertoll is None:
            return RouteResult(False, legs, attempts,
                               'No common point in the homing chains')
        intertoll_legs, blocked_leg = intertoll
        legs.extend(intertoll_legs)
        if blocked_leg is not None:
            return RouteResult(False, legs, attempts,
                               f'All trunks busy on final group '
                               f'{blocked_leg[0]}-{blocked_leg[1]}; '
                               'caller receives reorder')

        if final_leg is not None:
            leg, blocked = self._offer(final_leg[0], final_leg[1],
                                       'Toll connecting', attempts, generator)
            legs.append(leg)
            if blocked:
                return RouteResult(False, legs, attempts,
                                   f'All trunks busy on toll connecting group '
                                   f'{final_leg[0]}-{final_leg[1]}; '
                                   'caller receives reorder')

        if len(legs) > MAX_TRUNKS_IN_CONNECTION:
            return RouteResult(
                False, legs, attempts,
                f'Connection would exceed {MAX_TRUNKS_IN_CONNECTION} trunks in tandem',
            )

        return RouteResult(True, legs, attempts,
                           'Completed through the toll network')

    def _offer(self, first: str, second: str, group_type: str,
               attempts: List[str], rng: random.Random) -> Tuple[RouteLeg, bool]:
        """Offer a call to one final or toll connecting group."""
        blocked = rng.random() < FINAL_GROUP_BLOCKING
        utilization = rng.randint(97, 100) if blocked else rng.randint(40, 96)
        attempts.append(
            f'{group_type} group {first}-{second}: {utilization}% occupied'
            + (' - ALL TRUNKS BUSY' if blocked else '')
        )
        return RouteLeg(first, second, group_type, blocked, utilization), blocked

    def _route_intertoll(self, origin: str, destination: str,
                         attempts: List[str], rng: random.Random):
        """
        Route between two toll offices, trying the direct group first.

        Returns the legs and, if one blocked, which group it was.
        """
        if origin == destination:
            return [], None

        overflowed = rng.random() < HIGH_USAGE_BLOCKING
        utilization = rng.randint(92, 100) if overflowed else rng.randint(55, 91)
        attempts.append(
            f'High-usage group {origin}-{destination}: {utilization}% occupied'
        )
        if not overflowed:
            return [RouteLeg(origin, destination, 'High-usage direct',
                             False, utilization)], None

        attempts.append('Direct group busy; overflowing to the homing chain')

        meeting = self.common_point(origin, destination)
        if meeting is not None:
            up = self.homing_chain(origin)
            down = self.homing_chain(destination)
            path = (up[:up.index(meeting) + 1]
                    + list(reversed(down[:down.index(meeting)])))
        else:
            # Different regions. Every regional centre had a final group to
            # every other, so the call climbs to its own regional centre,
            # crosses at that level, and descends the far chain.
            origin_region = self.regional_centre(origin)
            destination_region = self.regional_centre(destination)
            if origin_region is None or destination_region is None:
                return None
            attempts.append(
                f'Crossing regions {origin_region} to {destination_region} '
                'on the interregional final group'
            )
            path = (self.homing_chain(origin)
                    + list(reversed(self.homing_chain(destination))))

        legs: List[RouteLeg] = []
        for first, second in zip(path, path[1:]):
            leg, blocked = self._offer(first, second, 'Final', attempts, rng)
            legs.append(leg)
            if blocked:
                return legs, (first, second)
        return legs, None


def build_default_network() -> TollNetwork:
    """
    Build the toll network the simulation routes over.

    Two regional centres, sectional and primary centres beneath them, and
    toll centres serving end offices - enough depth for alternate routing to
    behave as it did, without asserting the identity of any real site.
    """
    offices: Dict[str, Office] = {}

    def add(code: str, name: str, switch_class: int, homes_on: Optional[str]) -> None:
        offices[code] = Office(code, name, switch_class, homes_on)

    add('RC-EAST', 'Eastern Regional Center', 1, None)
    add('RC-CENT', 'Central Regional Center', 1, None)

    add('SC-NYC', 'New York Sectional Center', 2, 'RC-EAST')
    add('SC-WAS', 'Washington Sectional Center', 2, 'RC-EAST')
    add('SC-CHI', 'Chicago Sectional Center', 2, 'RC-CENT')

    add('PC-NYC', 'New York Primary Center', 3, 'SC-NYC')
    add('PC-BOS', 'Boston Primary Center', 3, 'SC-NYC')
    add('PC-PHL', 'Philadelphia Primary Center', 3, 'SC-WAS')
    add('PC-CHI', 'Chicago Primary Center', 3, 'SC-CHI')
    add('PC-DET', 'Detroit Primary Center', 3, 'SC-CHI')

    add('TC-NYC', 'New York Toll Center', 4, 'PC-NYC')
    add('TC-BOS', 'Boston Toll Center', 4, 'PC-BOS')
    add('TC-PHL', 'Philadelphia Toll Center', 4, 'PC-PHL')
    add('TC-WAS', 'Washington Toll Center', 4, 'SC-WAS')
    add('TC-CHI', 'Chicago Toll Center', 4, 'PC-CHI')
    add('TC-DET', 'Detroit Toll Center', 4, 'PC-DET')

    # End offices. A toll connection is measured from end office to end
    # office and so includes a toll connecting trunk at each end, which is
    # why the documented average is slightly over three trunks rather than
    # the one or two an intertoll path alone would suggest.
    add('EO-NYC-01', 'New York Canal Street', 5, 'TC-NYC')
    add('EO-NYC-02', 'New York Murray Hill', 5, 'TC-NYC')
    add('EO-BOS-01', 'Boston Kenmore', 5, 'TC-BOS')
    add('EO-PHL-01', 'Philadelphia Locust', 5, 'TC-PHL')
    add('EO-WAS-01', 'Washington Metropolitan', 5, 'TC-WAS')
    add('EO-CHI-01', 'Chicago Wabash', 5, 'TC-CHI')
    add('EO-CHI-02', 'Chicago Superior', 5, 'TC-CHI')
    add('EO-DET-01', 'Detroit Woodward', 5, 'TC-DET')

    return TollNetwork(offices)
