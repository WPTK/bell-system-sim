"""
Behavioural tests for the main Bell System terminal.

Unlike the suite these replace, every check here asserts on real output, so a
regression fails the run rather than being counted as a success.
"""

import pytest

from bell_system.terminal import (
    BELL_SYSTEM_ROLES,
    UNIMPLEMENTED_COMMANDS,
    BellSystemTerminal,
)

NOT_FOUND = 'command not found'

# Commands that end the session or clear the screen rather than returning text.
SESSION_CONTROL = {'quit', 'clear', 'test'}


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


class TestSubsystemHonesty:
    """
    Unimplemented commands say so plainly.

    They previously returned the internal placeholder string
    'implementation follows pattern', which reads like real output.
    """

    def test_no_placeholder_text_leaks_to_users(self, terminal):
        for command in terminal._command_handlers:
            if command in SESSION_CONTROL:
                continue
            result = terminal.execute_command(command)
            assert 'implementation follows pattern' not in result, command

    @pytest.mark.parametrize('command', sorted(UNIMPLEMENTED_COMMANDS))
    def test_unimplemented_commands_report_themselves(self, terminal, command):
        result = terminal.execute_command(command)
        assert 'not available in this release' in result
        assert f'man {command}' in result

    def test_unimplemented_list_matches_reality(self, terminal):
        """
        Every name in UNIMPLEMENTED_COMMANDS is a real command, and no command
        outside the list emits the unavailable notice.
        """
        assert UNIMPLEMENTED_COMMANDS <= set(terminal._command_handlers)
        for command in set(terminal._command_handlers) - UNIMPLEMENTED_COMMANDS:
            if command in SESSION_CONTROL:
                continue
            result = terminal.execute_command(command)
            assert 'not available in this release' not in result, (
                f'{command} is listed as implemented but reports otherwise'
            )


class TestStateWiredToCommands:
    """Data structures that were built at startup and never read."""

    def test_alarm_command_reports_real_alarm_state(self, terminal):
        result = terminal.execute_command('alarm')
        assert terminal.system_health['overall_status'] in result
        for alarm in terminal.active_alarms:
            assert alarm['id'] in result

    def test_alarm_acknowledgement_mutates_state(self, terminal):
        pending = [a for a in terminal.active_alarms if not a['acknowledged']]
        if not pending:
            pytest.skip('no unacknowledged alarms in this session')
        alarm = pending[0]
        terminal.execute_command(f"alarm ack {alarm['id']}")
        assert alarm['acknowledged'] is True

    def test_alarm_acknowledgement_rejects_unknown_id(self, terminal):
        assert 'No active alarm' in terminal.execute_command('alarm ack AL-0000')

    def test_handoff_reports_the_previous_shift(self, terminal):
        result = terminal.execute_command('handoff')
        previous = terminal.shift_handoff['previous_shift']
        assert previous['operator'] in result
        assert previous['special_instructions'] in result

    def test_tariff_reports_real_rates(self, terminal):
        result = terminal.execute_command('tariff interstate')
        rate = terminal.rate_structures['interstate']['day']['first_minute']
        assert f'{rate:.2f}' in result

    def test_tariff_rejects_unknown_category(self, terminal):
        assert 'Unknown category' in terminal.execute_command('tariff nonsense')


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


class TestSettingsCommand:
    """The settings screen, and settings taking effect in the simulation."""

    def test_screen_lists_every_option(self, terminal):
        from bell_system.settings import OPTIONS
        screen = terminal.execute_command('set')
        for option in OPTIONS:
            assert option.key in screen

    def test_screen_reports_accuracy_when_untouched(self, terminal):
        assert 'All settings are period-accurate' in terminal.execute_command('set')

    def test_screen_flags_a_deviation(self, terminal):
        terminal.execute_command('set display.charset unicode')
        screen = terminal.execute_command('set')
        assert 'depart from period-accurate' in screen
        assert 'display.charset' in screen

    def test_setting_one_value_reports_it(self, terminal):
        assert 'date.format = iso' in terminal.execute_command('set date.format iso')

    def test_departing_from_accuracy_warns(self, terminal):
        result = terminal.execute_command('set date.source real')
        assert "period-accurate value is 'simulated'" in result

    def test_neutral_setting_does_not_warn(self, terminal):
        result = terminal.execute_command('set date.seconds off')
        assert 'period-accurate value' not in result

    def test_detail_view_explains_a_setting(self, terminal):
        detail = terminal.execute_command('set date.format')
        assert 'Permitted' in detail and 'iso' in detail

    def test_unknown_setting_is_reported(self, terminal):
        assert 'no such setting' in terminal.execute_command('set date.nonsense')

    def test_invalid_value_is_reported_not_raised(self, terminal):
        assert 'not valid' in terminal.execute_command('set date.clock 37')

    def test_reset_restores_accuracy(self, terminal):
        terminal.execute_command('set display.charset unicode')
        terminal.execute_command('set reset')
        assert terminal.settings.deviations() == []

    @pytest.mark.parametrize('alias', ['options', 'settings', 'config'])
    def test_aliases_reach_the_screen(self, terminal, alias):
        assert 'Simulation Settings' in terminal.execute_command(alias)


class TestClockIsWiredIn:
    """Timestamps come from the simulated clock, not the host."""

    def test_date_command_reports_the_period(self, terminal):
        assert '1983' in terminal.execute_command('date')

    def test_date_command_default_is_v7_order(self, terminal):
        assert terminal.execute_command('date').startswith('Mon Nov 14')

    def test_date_format_setting_changes_the_date_command(self, terminal):
        terminal.execute_command('set date.format iso')
        assert terminal.execute_command('date').startswith('1983-11-14')

    def test_clock_setting_changes_the_date_command(self, terminal):
        terminal.execute_command('set date.clock 12')
        assert 'AM' in terminal.execute_command('date')

    def test_real_source_reports_the_host_year(self, terminal):
        from datetime import datetime
        terminal.execute_command('set date.source real')
        assert str(datetime.now().year) in terminal.execute_command('date')

    def test_no_command_reports_the_host_year_by_default(self, terminal):
        """
        The host year must not leak into any command's output.

        This is the defect that broke the period on the first command typed.
        """
        from datetime import datetime
        host_year = str(datetime.now().year)
        leaked = []
        for command in sorted(terminal._command_handlers):
            if command in SESSION_CONTROL:
                continue
            if host_year in (terminal.execute_command(command) or ''):
                leaked.append(command)
        assert not leaked, f'commands leaking the host year: {leaked}'


class TestPromptStyle:
    def test_default_prompt_is_the_bourne_shell_prompt(self, terminal):
        """V7 sh prompted with a bare '$ ' - no user, host or path."""
        assert terminal.shell_prompt() == '$ '

    def test_root_gets_a_hash_prompt(self, terminal):
        terminal.username = 'root'
        assert terminal.shell_prompt() == '# '

    def test_verbose_prompt_restores_orientation(self, terminal):
        terminal.execute_command('set display.prompt verbose')
        prompt = terminal.shell_prompt()
        assert terminal.username in prompt and terminal.hostname in prompt


class TestOutputCharacterSet:
    def test_no_command_emits_non_ascii_by_default(self, terminal):
        """Every command's output is printable 7-bit ASCII as shipped."""
        from bell_system.console import non_ascii_characters, render
        charset = terminal.settings.get('display.charset')
        offenders = {}
        for command in sorted(terminal._command_handlers):
            if command in SESSION_CONTROL:
                continue
            rendered = render(terminal.execute_command(command) or '', charset)
            found = non_ascii_characters(rendered)
            if found:
                offenders[command] = found
        assert not offenders, f'non-ASCII in output: {offenders}'

    def test_no_man_page_emits_non_ascii_by_default(self, terminal):
        from bell_system.console import non_ascii_characters, render
        charset = terminal.settings.get('display.charset')
        offenders = {}
        for command in sorted(terminal.man_pages):
            rendered = render(terminal.execute_command(f'man {command}'), charset)
            found = non_ascii_characters(rendered)
            if found:
                offenders[command] = found
        assert not offenders, f'non-ASCII in man pages: {offenders}'

    def test_emit_transliterates(self, terminal, capsys):
        terminal.emit('bar ███')
        assert capsys.readouterr().out.strip() == 'bar ###'

    def test_emit_passes_unicode_through_when_asked(self, terminal, capsys):
        terminal.execute_command('set display.charset unicode')
        terminal.emit('bar ███')
        assert '███' in capsys.readouterr().out


class TestDiagnosticLogging:
    def test_log_records_do_not_reach_the_terminal(self, terminal, capsys):
        """
        A mistyped command used to print a Python log record with an ISO
        timestamp and a file:line reference into the simulated terminal.
        """
        capsys.readouterr()
        terminal.execute_command('definitelynotacommand')
        captured = capsys.readouterr()
        assert 'BellSystem' not in captured.err
        assert 'WARNING' not in captured.err
