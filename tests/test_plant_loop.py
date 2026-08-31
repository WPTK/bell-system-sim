"""
Cable, weather and the field force: the outside plant as a place.

Three things the report engine could not do before. Water was a pair fault,
so several reports off one sheath never arrived and the advice the previous
tour left could not be taken. Rain did not exist, so the fault documented as
worsening with rain never worsened. And dispatch went to a category, and a
category is never busy.
"""

import random
from datetime import datetime, timedelta

import pytest

from bell_system.cable import (
    BINDERS_PER_UNIT,
    CablePlant,
    PAIRS_PER_BINDER,
    binder_colour,
    binder_of,
)
from bell_system.field import CREWS, FieldForce
from bell_system.reports import ReportDesk
from bell_system.weather import CONDITIONS, SEQUENCE, Weather

SHIFT_START = datetime(1983, 11, 14, 8, 0)


@pytest.fixture
def desk():
    """A report desk with a fixed generator, so a test can reason about it."""
    return ReportDesk('201', '555', 'NWRKNJ02', random.Random(1983))


class TestCableStructure:
    """The 25-pair colour code, which is where the binder groups come from."""

    def test_a_binder_group_is_twenty_five_pairs(self):
        assert PAIRS_PER_BINDER == 25

    def test_six_hundred_pairs_is_where_the_scheme_stops(self):
        """
        Twenty-four groups of twenty-five. Violet-slate is a real pair
        colour and is never used as a binder, which is why it is 24 and
        not 25.
        """
        assert BINDERS_PER_UNIT == 24
        assert BINDERS_PER_UNIT * PAIRS_PER_BINDER == 600
        assert binder_colour(BINDERS_PER_UNIT) == 'Violet-Brown'
        assert binder_colour(25) == 'Violet-Slate'

    @pytest.mark.parametrize('binder,colour', [
        (1, 'White-Blue'), (2, 'White-Orange'), (5, 'White-Slate'),
        (6, 'Red-Blue'), (11, 'Black-Blue'), (24, 'Violet-Brown'),
    ])
    def test_the_colour_code_runs_tip_then_ring(self, binder, colour):
        assert binder_colour(binder) == colour

    @pytest.mark.parametrize('pair,binder', [
        (1, 1), (25, 1), (26, 2), (50, 2), (51, 3), (600, 24),
    ])
    def test_a_pair_falls_in_the_group_it_should(self, pair, binder):
        assert binder_of(pair) == binder


class TestWaterIsASheathFault:
    """Several reports off one binder group, which is what water looks like."""

    def test_wet_pairs_land_in_the_same_group(self, desk):
        reports = [desk.receive(SHIFT_START, fault='WET') for _ in range(4)]
        groups = {(report.record.cable, binder_of(report.record.pair))
                  for report in reports}
        assert len(groups) < len(reports), (
            'four wet reports landed in four different binder groups')

    def test_no_two_wet_reports_share_a_pair(self, desk):
        reports = [desk.receive(SHIFT_START, fault='WET') for _ in range(12)]
        pairs = [(report.record.cable, report.record.pair)
                 for report in reports]
        assert len(set(pairs)) == len(pairs)

    def test_a_dry_fault_never_lands_in_an_open_wet_group(self, desk):
        for _ in range(4):
            desk.receive(SHIFT_START, fault='WET')
        for _ in range(20):
            report = desk.receive(SHIFT_START, fault='OPEN')
            record = report.record
            assert desk.plant.section_at(record.cable, record.pair) is None

    def test_a_section_stops_taking_pairs_when_it_is_full(self):
        plant = CablePlant(random.Random(5))
        for _ in range(60):
            cable, pair = plant.wet_pair(SHIFT_START)
            plant.attach(cable, pair, 'TR-00001')
        for section in plant.sections:
            assert len(section.pairs) <= section.capacity

    def test_pressure_falls_as_pairs_go(self, desk):
        first = desk.receive(SHIFT_START, fault='WET')
        section = desk.plant.section_at(first.record.cable, first.record.pair)
        before = section.psi
        for _ in range(2):
            desk.receive(SHIFT_START, fault='WET')
        assert section.psi < before

    def test_enough_pairs_sets_the_contactor_alarming(self, desk):
        first = desk.receive(SHIFT_START, fault='WET')
        section = desk.plant.section_at(first.record.cable, first.record.pair)
        while not section.full:
            pair = section.take_pair(section.pairs and desk.rng or desk.rng)
            if pair is None:
                break
            section.reserve(pair)
        assert section.alarming()


class TestOneTripRepairsTheSheath:
    """The payoff: a splicer opens the sheath once."""

    def wet_group(self, desk, count=4):
        """Return several reports that landed in one binder group."""
        made = [desk.receive(SHIFT_START, fault='WET') for _ in range(8)]
        first = made[0]
        key = (first.record.cable, binder_of(first.record.pair))
        return [report for report in made
                if (report.record.cable, binder_of(report.record.pair)) == key]

    def test_a_dispatch_names_the_binder_group(self, desk):
        group = self.wet_group(desk)
        result = desk.dispatch(group[0], 'Cable repair', SHIFT_START)
        assert 'binder' in result
        assert 'pairs' in result

    def test_it_clears_every_other_pair_in_the_group(self, desk):
        group = self.wet_group(desk)
        if len(group) < 2:
            pytest.skip('this seed put one pair in the group')
        desk.dispatch(group[0], 'Cable repair', SHIFT_START)
        for other in group[1:]:
            assert other.sheath_repaired
            assert other.field_finding == 'WET'

    def test_it_says_which_reports_it_cleared(self, desk):
        group = self.wet_group(desk)
        if len(group) < 2:
            pytest.skip('this seed put one pair in the group')
        result = desk.dispatch(group[0], 'Cable repair', SHIFT_START)
        for other in group[1:]:
            assert other.number in result

    def test_a_second_trip_to_a_dry_sheath_is_refused(self, desk):
        group = self.wet_group(desk)
        if len(group) < 2:
            pytest.skip('this seed put one pair in the group')
        desk.dispatch(group[0], 'Cable repair', SHIFT_START)
        result = desk.dispatch(group[1], 'Cable repair', SHIFT_START)
        assert 'Nobody needs to go' in result
        assert group[1].dispatched_to is None

    def test_the_cleared_reports_close_correctly(self, desk):
        group = self.wet_group(desk)
        if len(group) < 2:
            pytest.skip('this seed put one pair in the group')
        desk.dispatch(group[0], 'Cable repair', SHIFT_START)
        assert desk.close(group[1], 5, 'WET', SHIFT_START, True)

    def test_one_trip_costs_less_than_two(self, desk):
        """
        The whole argument for reading the board first: six trips to six
        pairs repairs the same water six times over.
        """
        group = self.wet_group(desk)
        if len(group) < 2:
            pytest.skip('this seed put one pair in the group')
        desk.dispatch(group[0], 'Cable repair', SHIFT_START)
        before = group[1].minutes_spent
        desk.dispatch(group[1], 'Cable repair', SHIFT_START)
        assert group[1].minutes_spent == before


class TestWeather:
    """Rain, and what it does to water already in a sheath."""

    def test_every_condition_has_a_rain_value_and_a_note(self):
        for key, condition in CONDITIONS.items():
            assert 0.0 <= condition.rain <= 1.0
            assert condition.note.endswith('.')
            assert key in SEQUENCE

    def test_the_sequence_runs_driest_to_wettest(self):
        rains = [CONDITIONS[key].rain for key in SEQUENCE]
        assert rains == sorted(rains)

    def test_it_does_not_change_inside_an_hour(self):
        weather = Weather(random.Random(1))
        assert weather.advance(30) is None
        assert weather.advance(59) is None

    def test_it_never_jumps_more_than_one_step(self):
        weather = Weather(random.Random(4))
        for minutes in range(0, 601, 60):
            was = SEQUENCE.index(weather.key)
            weather.advance(minutes)
            assert abs(SEQUENCE.index(weather.key) - was) <= 1

    def test_a_change_is_worth_saying_out_loud(self):
        """Every advance that changes the weather returns a line, and no
        advance that does not returns one."""
        weather = Weather(random.Random(9))
        for minutes in range(0, 1201, 60):
            was = weather.key
            line = weather.advance(minutes)
            assert (line is not None) == (weather.key != was)

    def test_rain_makes_water_spread_faster(self):
        """
        The documented claim the whole module exists to honour: wet cable
        worsens with rain. Run the same plant dry and soaking and count.
        """
        def spread_over(rain):
            plant = CablePlant(random.Random(2))
            cable, pair = plant.wet_pair(SHIFT_START)
            plant.attach(cable, pair, 'TR-00001')
            # Room left in the group, or nothing can spread into it.
            plant.sections[0].capacity = PAIRS_PER_BINDER
            plant.rng = random.Random(77)
            return sum(plant.spread(10, rain) for _ in range(200))

        assert spread_over(1.0) > spread_over(0.0)

    def test_a_full_binder_group_does_not_spread(self):
        """Water takes the pairs it is going to take and then stops."""
        plant = CablePlant(random.Random(2))
        cable, pair = plant.wet_pair(SHIFT_START)
        plant.attach(cable, pair, 'TR-00001')
        plant.sections[0].capacity = 1
        assert sum(plant.spread(60, 1.0) for _ in range(50)) == 0

    def test_a_repaired_sheath_does_not_spread(self):
        plant = CablePlant(random.Random(2))
        cable, pair = plant.wet_pair(SHIFT_START)
        plant.attach(cable, pair, 'TR-00001')
        plant.repair(plant.sections[0], SHIFT_START)
        assert sum(plant.spread(60, 1.0) for _ in range(50)) == 0


class TestFieldForce:
    """Five people, each of them somewhere."""

    def test_every_crew_answers_a_real_dispatch_category(self):
        from bell_system.data.trouble import DISPATCH_FORCES
        for crew in CREWS:
            assert crew.force in DISPATCH_FORCES

    def test_every_category_has_somebody(self):
        from bell_system.data.trouble import DISPATCH_FORCES
        force = FieldForce(random.Random(1))
        for category in DISPATCH_FORCES:
            assert force.crews_for(category), category

    def test_sending_somebody_takes_them_out(self):
        force = FieldForce(random.Random(1))
        crew, travel, came_from = force.send(
            'Cable repair', 'TR-00001', 120, SHIFT_START)
        assert crew is not None
        assert travel > 0
        assert came_from
        assert crew.key in force.out

    def test_they_come_back_when_the_job_is_done(self):
        force = FieldForce(random.Random(1))
        crew, travel, _ = force.send(
            'Central office', 'TR-00001', 30, SHIFT_START)
        later = SHIFT_START + timedelta(minutes=travel + 31)
        assert crew in force.free('Central office', later)

    def test_a_category_with_everybody_out_sends_nobody(self):
        force = FieldForce(random.Random(1))
        for index in range(4):
            force.send('Cable repair', f'TR-0000{index}', 600, SHIFT_START)
        crew, _, _ = force.send('Cable repair', 'TR-00009', 60, SHIFT_START)
        assert crew is None

    def test_it_says_who_has_to_finish_first(self):
        force = FieldForce(random.Random(1))
        for index in range(4):
            force.send('Cable repair', f'TR-0000{index}', 600, SHIFT_START)
        waiting = force.soonest_free('Cable repair', SHIFT_START)
        assert waiting is not None
        assert waiting.back_at() > SHIFT_START

    def test_the_nearest_free_crew_goes(self):
        force = FieldForce(random.Random(1))
        force.at['okafor'] = 'FAR'
        force.at['sandoval'] = 'GARAGE'
        crew, _, _ = force.send('Cable repair', 'TR-00001', 60, SHIFT_START)
        assert crew.key == 'sandoval'


class TestTheDeskUsesThem:
    """The three joined to the report loop."""

    def test_a_dispatch_names_who_went(self, desk):
        report = desk.receive(SHIFT_START, fault='GROUND')
        result = desk.dispatch(report, 'Outside plant', SHIFT_START)
        assert report.crew is not None
        assert report.crew in result
        assert 'rolled from' in result

    def test_travel_is_charged_against_the_commitment(self, desk):
        report = desk.receive(SHIFT_START, fault='GROUND')
        before = report.minutes_spent
        desk.dispatch(report, 'Outside plant', SHIFT_START)
        assert report.travel_minutes > 0
        assert report.minutes_spent - before > report.travel_minutes

    def test_a_report_nobody_can_take_stays_on_the_board(self, desk):
        held = [desk.receive(SHIFT_START, fault='GROUND') for _ in range(3)]
        for report in held:
            desk.dispatch(report, 'Outside plant', SHIFT_START)
        last = desk.receive(SHIFT_START, fault='GROUND')
        result = desk.dispatch(last, 'Outside plant', SHIFT_START)
        assert 'Nobody free' in result
        assert last in desk.pending()
        assert last.dispatched_to is None

    def test_the_desk_carries_a_plant_and_a_weather(self, desk):
        assert desk.plant is not None
        assert desk.weather is not None
        assert desk.force is not None
