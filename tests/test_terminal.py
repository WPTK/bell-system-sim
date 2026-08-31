"""
Behavioural tests for the main Bell System terminal.

Unlike the suite these replace, every check here asserts on real output, so a
regression fails the run rather than being counted as a success.
"""

import pytest

from bell_system.terminal import BELL_SYSTEM_ROLES, BellSystemTerminal

NOT_FOUND = 'command not found'


def test_all_twelve_roles_start(isolated_state):
    """Each of the 12 advertised roles initialises and reports a briefing."""
    assert len(BELL_SYSTEM_ROLES) == 12
    for role_num, (role_key, role_name) in BELL_SYSTEM_ROLES.items():
        term = BellSystemTerminal()
        term.select_role(role_num)
        assert term.role == role_key
        assert term.role_name == role_name
        assert term.username == role_key


@pytest.mark.parametrize('command', [
    'ps', 'who', 'ls', 'pwd', 'date', 'df', 'help', 'status',
    'trunk', 'switch', 'testboard', 'toll', 'trace', 'dialtone',
    'ticket', 'trouble', 'uucp', 'traffic', 'routing', 'crossbar',
    'lmos', 'tnds', 'sarts', 'radio', 'microwave', 'alarm', 'pwb',
])
def test_core_commands_produce_output(terminal, command):
    """Core commands return substantive output, not an error."""
    result = terminal.execute_command(command)
    assert result, f'{command} produced no output'
    assert NOT_FOUND not in result, f'{command} was not dispatched'


@pytest.mark.parametrize('alias', ['ll', 'la', 'dir', 'st', 'h', 'w', 'proc'])
def test_aliases_dispatch(terminal, alias):
    """Aliases reach a working handler rather than failing to resolve."""
    result = terminal.execute_command(alias)
    assert result, f'{alias} produced no output'
    assert NOT_FOUND not in result


@pytest.mark.parametrize('alias', ['ll', 'la', 'dir'])
def test_directory_aliases_match_ls(terminal, alias):
    """ls, ll, la and dir all list the current directory."""
    assert terminal.execute_command(alias) == terminal.execute_command('ls')


def test_unknown_command_is_reported_not_raised(terminal):
    """An unknown command produces a message, never an exception."""
    result = terminal.execute_command('definitelynotacommand')
    assert NOT_FOUND in result


def test_command_history_records_each_command_once(terminal):
    """
    A command is recorded once.

    It was previously appended in both run() and execute_command().
    """
    terminal.execute_command('ps')
    terminal.execute_command('who')
    history = list(terminal.command_history)
    assert history.count('ps') == 1
    assert history.count('who') == 1


def test_command_history_is_bounded(terminal):
    """History is capped, so a long session cannot grow without limit."""
    for i in range(1200):
        terminal.command_history.append(f'cmd{i}')
    assert len(terminal.command_history) <= 1000


def test_history_command_renders(terminal):
    """The history command formats a bounded deque without raising."""
    for i in range(30):
        terminal.execute_command('ps')
    result = terminal.execute_command('history')
    assert 'ps' in result


class TestTroubleTicketEngine:
    """The procedural ticket engine, previously unreachable from dispatch."""

    def test_dashboard_is_reachable(self, terminal):
        result = terminal.execute_command('trouble')
        assert NOT_FOUND not in result
        assert 'ticket' in result.lower()

    def test_tickets_are_generated_at_startup(self, terminal):
        assert terminal.active_tickets, 'no tickets generated'
        for ticket in terminal.active_tickets:
            assert ticket['priority'] in {'CRITICAL', 'MAJOR', 'MINOR'}
            assert ticket['status']
            assert ticket['id'].startswith('TK-')

    def test_list_and_detail_agree(self, terminal):
        ticket_id = terminal.active_tickets[0]['id']
        assert ticket_id in terminal.execute_command('trouble list')
        assert ticket_id in terminal.execute_command(f'trouble detail {ticket_id}')

    def test_manual_ticket_creation_adds_a_ticket(self, terminal):
        before = len(terminal.active_tickets)
        category = next(iter(terminal.ticket_categories))
        result = terminal.execute_command(
            f'trouble create {category} MAJOR Water in cable at Elm St'
        )
        assert len(terminal.active_tickets) == before + 1
        assert 'Water in cable' in result
        assert terminal.active_tickets[-1]['priority'] == 'MAJOR'

    def test_manual_ticket_rejects_unknown_category(self, terminal):
        before = len(terminal.active_tickets)
        result = terminal.execute_command('trouble create nonsense MAJOR test')
        assert 'Unknown category' in result
        assert len(terminal.active_tickets) == before

    def test_assignment_is_recorded(self, terminal):
        ticket = terminal.active_tickets[0]
        terminal.execute_command(f"trouble assign {ticket['id']} Cable Repair Team")
        assert ticket['assigned_team'] == 'Cable Repair Team'
        assert ticket['resolution_steps'], 'assignment left no audit trail'


class TestTndsReports:
    """The eight TNDS branches that previously raised AttributeError."""

    @pytest.mark.parametrize('subcommand', [
        'hierarchy', 'routing', 'reports', 'export',
        'forecast', 'collect', 'analysis', 'status',
    ])
    def test_subcommands_produce_output(self, terminal, subcommand):
        result = terminal.execute_command(f'tnds {subcommand}')
        assert result and NOT_FOUND not in result

    @pytest.mark.parametrize('report', [
        'traffic', 'blocking', 'quality', 'capacity', 'monthly',
    ])
    def test_named_reports_render(self, terminal, report):
        result = terminal.execute_command(f'tnds reports {report}')
        assert len(result) > 200, f'{report} report looks empty'

    @pytest.mark.parametrize('fmt', ['tape', 'cards', 'rje', 'print'])
    def test_export_formats_are_accepted(self, terminal, fmt):
        result = terminal.execute_command(f'tnds export {fmt}')
        assert 'QUEUED' in result

    def test_unknown_report_is_reported(self, terminal):
        assert 'Unknown report' in terminal.execute_command('tnds reports nonsense')

    def test_unknown_export_format_is_reported(self, terminal):
        assert 'Unknown format' in terminal.execute_command('tnds export nonsense')


class TestCrossbarReports:
    """Crossbar output previously stopped at a bare header."""

    def test_overview_includes_system_data(self, terminal):
        result = terminal.execute_command('crossbar')
        assert 'CROSSBAR SYSTEMS STATUS' in result
        for system_id in terminal.crossbar_systems:
            assert system_id in result
        assert 'SYSTEM CHARACTERISTICS' in result

    def test_maintenance_includes_per_system_detail(self, terminal):
        result = terminal.execute_command('crossbar maintenance')
        assert 'MAINTENANCE PROCEDURES' in result
        for system_id in terminal.crossbar_systems:
            assert system_id in result

    def test_performance_includes_per_system_detail(self, terminal):
        result = terminal.execute_command('crossbar performance')
        assert 'HISTORICAL TRENDS' in result
        for system_id in terminal.crossbar_systems:
            assert system_id in result


class TestManualPages:
    """Man page text lives in bell_system.data, not inside the terminal class."""

    def test_pages_are_loaded(self, terminal):
        assert len(terminal.man_pages) > 50

    def test_every_command_has_a_man_page(self, terminal):
        """Every dispatchable command documents itself."""
        undocumented = sorted(set(terminal._command_handlers) - set(terminal.man_pages))
        assert not undocumented, f'commands with no man page: {undocumented}'

    def test_no_orphan_man_pages(self, terminal):
        """Every man page describes a command that exists."""
        orphans = sorted(set(terminal.man_pages) - set(terminal._command_handlers))
        assert not orphans, f'man pages for nonexistent commands: {orphans}'

    @pytest.mark.parametrize('command', ['trunk', 'switch', 'ps', 'tnds', 'uucp', 'trouble'])
    def test_man_renders_a_page(self, terminal, command):
        result = terminal.execute_command(f'man {command}')
        assert 'NAME' in result
        assert command in result

    def test_man_reports_unknown_pages(self, terminal):
        result = terminal.execute_command('man definitelynotacommand')
        assert 'no manual entry' in result.lower() or 'not found' in result.lower()

    def test_pages_are_per_session(self, terminal, isolated_state):
        """One session mutating its pages must not affect the next."""
        original = terminal.man_pages['trunk']
        terminal.man_pages['trunk'] = 'MUTATED'
        assert BellSystemTerminal().man_pages['trunk'] == original


def test_state_is_written_outside_the_working_directory(terminal, tmp_path):
    """Logs go to the state directory, not a CWD-relative logs/ folder."""
    from bell_system.terminal import state_dir
    assert str(tmp_path) in state_dir()
