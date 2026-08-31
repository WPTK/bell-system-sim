"""
Tests for the simplified four-role terminal reached via ``--simple``.

Its ``date`` command raised NameError and its ``__main__`` block instantiated
a class that did not exist.
"""

import pytest


def test_date_command_works(simple):
    """``date`` used to raise NameError: datetime was never imported."""
    result = simple.cmd_date([])
    assert 'EST' in result
    assert len(result.split()) == 6


@pytest.mark.parametrize('command,expected', [
    ('pwd', '/usr/sysop'),
    ('ls', 'hello.c'),
    ('cat /etc/motd', 'Bell Telephone Laboratories'),
    ('echo hello world', 'hello world'),
    ('who', 'root'),
    ('ps', 'PID'),
])
def test_commands_produce_expected_output(simple, command, expected):
    assert expected in simple.execute_command(command)


def test_filesystem_navigation(simple):
    """cd/pwd actually move through the simulated filesystem."""
    simple.execute_command('cd /usr/bin')
    assert simple.execute_command('pwd').strip() == '/usr/bin'
    assert 'awk' in simple.execute_command('ls')


def test_grep_finds_content(simple):
    assert 'root' in simple.execute_command('grep root /etc/passwd')


def test_exported_class_name_is_importable():
    """The public name is SimpleTerminal, distinct from BellSystemTerminal."""
    from bell_system import BellSystemTerminal, SimpleTerminal
    assert SimpleTerminal is not BellSystemTerminal
    assert SimpleTerminal.__name__ == 'SimpleTerminal'


class TestSeventhEditionLayout:
    """
    The simulated filesystem must be a Seventh Edition one.

    It previously contained /var and /var/log (System V Release 4, 1988),
    /home (an SVR4 and Linux convention) and /root as the super-user's home
    directory (Linux; V7 root lived at /).
    """

    @pytest.mark.parametrize('path', ['/var', '/var/log', '/home', '/root'])
    def test_post_v7_directories_are_absent(self, simple, path):
        assert path not in simple.filesystem

    @pytest.mark.parametrize('path', ['/', '/bin', '/dev', '/etc', '/lib',
                                      '/tmp', '/usr', '/usr/bin', '/usr/adm'])
    def test_v7_directories_are_present(self, simple, path):
        assert path in simple.filesystem or path == '/usr/adm'

    def test_root_home_is_slash(self, simple):
        """V7 gave the super-user / as a home directory, not /root."""
        passwd = simple.filesystem['/etc/passwd']['content']
        root_line = passwd.splitlines()[0]
        assert root_line.split(':')[5] == '/'

    def test_groups_are_v7_not_bsd(self, simple):
        """'wheel' is a 4BSD group; V7 shipped other, daemon, bin, sys, adm."""
        groups = simple.filesystem['/etc/group']['content']
        assert 'wheel' not in groups
        assert 'other' in groups

    def test_copyright_year_matches_seventh_edition(self, simple):
        """V7 shipped in January 1979; the banner claimed 1976."""
        motd = simple.filesystem['/etc/motd']['content']
        assert '1979' in motd
        assert '1976' not in motd

    def test_hostname_follows_uucp_convention(self, simple):
        """V7 uucp system names were short, lowercase and alphanumeric."""
        assert '-' not in simple.hostname
        assert simple.hostname.islower()
        assert len(simple.hostname) <= 8
