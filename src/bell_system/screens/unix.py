"""
The Seventh Edition commands the terminal presents around the plant.

The filesystem these read is built in :mod:`bell_system.filesystem`, with the
files whose contents come from the running simulation added here.
"""

import logging
import logging.handlers
from typing import Any, List, Optional

from ..console import clear_screen
from ..constants import BSP_CATEGORIES
from ..filesystem import FILESYSTEM, Node
from ..npc import CRAFT
from .session import SessionState


def _generated(content: Any, owner: str = 'root', group: str = 'other',
               mode: str = '-rw-r--r--') -> Node:
    """Build a file node whose content is produced on demand."""
    return Node('file', owner, group, mode, content)


class UnixCommands(SessionState):
    """
    The Seventh Edition commands the terminal presents around the plant.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _initialize_project_numbers(self) -> None:
        """Initialize Bell System project and work order numbering system."""
        self.project_numbers = {
            "netplan": {
                "current": "NP-8301",
                "name": "Northeast Corridor Expansion Project",
                "budget": "$4.2M",
                "timeline": "Q1-Q4 1983"
            },
            "capacity": {
                "current": "CP-8302",
                "name": "Digital Switching Migration Phase II",
                "budget": "$12.8M",
                "timeline": "1983-1985"
            },
            "crossbar": {
                "current": "XB-8303",
                "name": "Crossbar Modernization Initiative",
                "budget": "$6.5M",
                "timeline": "1983-1984"
            },
            "maintenance": {
                "current": "MT-8304",
                "name": "Preventive Maintenance Program Enhancement",
                "budget": "$2.1M",
                "timeline": "Ongoing"
            },
            "training": {
                "current": "TR-8305",
                "name": "Employee Development and Certification Update",
                "budget": "$890K",
                "timeline": "1983-1984"
            }
        }
    def _initialize_rate_structures(self) -> None:
        """Initialize Bell System tariff and rate structures."""
        self.rate_structures = {
            "interstate": {
                "day": {"first_minute": 0.45, "additional": 0.34},
                "evening": {"first_minute": 0.32, "additional": 0.24},
                "night": {"first_minute": 0.18, "additional": 0.15}
            },
            "intrastate": {
                "day": {"first_minute": 0.28, "additional": 0.22},
                "evening": {"first_minute": 0.21, "additional": 0.17},
                "night": {"first_minute": 0.14, "additional": 0.12}
            },
            "international": {
                "uk": {"first_minute": 2.50, "additional": 1.80},
                "canada": {"first_minute": 0.65, "additional": 0.45},
                "mexico": {"first_minute": 1.20, "additional": 0.85}
            }
        }
    def _initialize_processes(self) -> None:
        """Initialize authentic Bell System processes."""
        self.processes = [
            {"pid": 0, "command": "swapper", "tty": "?", "time": "0:00", "user": "root"},
            {"pid": 1, "command": "init", "tty": "?", "time": "0:02", "user": "root"},
            {"pid": 23, "command": "update", "tty": "?", "time": "0:01", "user": "root"},
            {"pid": 45, "command": "sh", "tty": "co", "time": "0:00", "user": "root"},
            {"pid": 67, "command": "getty", "tty": "01", "time": "0:00", "user": "root"},
            {"pid": 89, "command": "uucico", "tty": "?", "time": "0:00", "user": "uucp"},
            {"pid": 102, "command": "cron", "tty": "?", "time": "0:00", "user": "root"},
            {"pid": 115, "command": "switchd", "tty": "?", "time": "0:03", "user": "switch"},
            {"pid": 127, "command": "uuxqt", "tty": "?", "time": "0:00", "user": "root"},
            {"pid": 138, "command": "tnds", "tty": "?", "time": "0:01", "user": "tnds"},
            {"pid": 145, "command": "sartsd", "tty": "?", "time": "0:00", "user": "sarts"},
            {"pid": 152, "command": "radiod", "tty": "?", "time": "0:02", "user": "radio"}
        ]
    def _initialize_users(self) -> None:
        """
        Populate the logged-on user list from the craft roster.

        who(1) and write(1) read the same people, so anyone the terminal says
        is logged on can actually be written to.
        """
        logins = ('07:30', '07:45', '08:00', '08:15', '08:30', '09:00')
        self.users = [
            {
                "user": person.login,
                "tty": person.tty,
                "login": logins[index % len(logins)],
                "location": person.location,
            }
            for index, person in enumerate(CRAFT.values())
        ]
    def cmd_man(self, args: List[str]) -> str:
        """
        Display manual pages for Bell System commands.

        Provides comprehensive documentation for all commands and sub-commands
        with authentic Bell System formatting and terminology.

        Args:
            args: Command arguments [command_name] or [-k keyword]

        Returns:
            Formatted manual page or search results
        """
        if not args:
            return "Usage: man <command> or man -k <keyword>"

        if args[0] == "-k" and len(args) > 1:
            # Keyword search
            keyword = args[1].lower()
            matches = []
            for cmd, content in self.man_pages.items():
                if keyword in content.lower():
                    matches.append(cmd)

            if matches:
                return f"Manual pages containing '{keyword}':\n" + "\n".join(f"  {cmd}(1)" for cmd in matches)
            else:
                return f"No manual pages found for keyword '{keyword}'"

        command = args[0].lower()
        if command in self.man_pages:
            return self.man_pages[command]
        else:
            return f"No manual entry for {command}"
    def _initialize_filesystem(self) -> None:
        """
        Build the simulated Seventh Edition filesystem.

        A copy, so a session cannot mutate the shared tree, plus the parts
        that are generated from live state.
        """
        self.filesystem = dict(FILESYSTEM)
        self._add_generated_files()

    def _add_generated_files(self) -> None:
        """
        Add the files whose contents come from the running simulation.

        A line record is a file because that is what it was. Reading the
        board with cat(1) and grep(1) is meant to be a real alternative to
        the report(1) screens, not a decoration.
        """
        # /bin and /usr/bin hold what this machine can actually run, taken
        # from the dispatch table rather than a hand-kept list, so a listing
        # can never name a command that does not exist.
        shell_tools = {
            'sh', 'cd', 'ls', 'cat', 'pwd', 'echo', 'grep', 'wc', 'sort',
            'uniq', 'head', 'tail', 'more', 'file', 'cal', 'date', 'who',
            'ps', 'df', 'mail', 'write', 'man', 'history',
        }
        for name in self._command_handlers:
            where = '/bin' if name in shell_tools else '/usr/bin'
            self.filesystem[f'{where}/{name}'] = Node(
                'file', 'bin', 'bin', '-rwxr-xr-x', '')

        self.filesystem['/usr/lmos/board'] = _generated(
            lambda terminal: terminal._render_board_file(),
            owner='sysop', group='craft')
        self.filesystem['/usr/adm/shiftlog'] = _generated(
            lambda terminal: terminal._render_shift_log(),
            owner='adm', group='adm')
        for code, title in sorted(BSP_CATEGORIES.items()):
            self.filesystem[f'/usr/bsp/{code}'] = _generated(
                f"BELL SYSTEM PRACTICE\nDivision {code} - {title}\n"
                f"{'=' * 60}\n\n"
                f"This division covers {title.lower()}.\n\n"
                f"Practices in this division are indexed by section. Use\n"
                f"bsp(1) to search the index by topic.\n")

    def cmd_ps(self, args: Optional[List[str]] = None) -> str:
        """
        Display Bell System processes in authentic UNIX V7 format.

        Shows currently running processes on the Bell System workstation
        including system daemons, switching processes, and user sessions.

        Returns:
            Process listing formatted in traditional ps output style
        """
        output = "  PID TTY  TIME COMMAND\n"
        for proc in self.processes:
            output += f"{proc['pid']:5d} {proc['tty']:>3} {proc['time']:>5} {proc['command']}\n"
        return output
    def cmd_who(self, args: Optional[List[str]] = None) -> str:
        """
        Display currently logged-in Bell System users.

        Shows active user sessions on the Bell System workstation with
        login times and terminal locations for operational awareness.

        Returns:
            User listing with terminals and login information
        """
        output = ""
        for user in self.users:
            person = CRAFT.get(user['user'])
            title = f"  {person.title}" if person else ""
            output += (f"{user['user']:<10} tty{user['tty']:<4} "
                       f"{user['login']:<8} ({user['location']}){title}\n")
        return output
    def cmd_date(self, args: Optional[List[str]] = None) -> str:
        """Display current system date and time in the configured layout."""
        return self.clock.date_command()
    def cmd_df(self, args: Optional[List[str]] = None) -> str:
        """Display filesystem disk space usage."""
        return """/dev/hp0a   1814   431
/dev/hp0g  24661  3902
/dev/hp0h  12572  2317"""
    def cmd_errors(self, args: Optional[List[str]] = None) -> str:
        """Display recent command errors and troubleshooting information."""
        if not self.recent_errors:
            return "No recent errors recorded.\n"

        result = "RECENT COMMAND ERRORS\n"
        result += "=" * 50 + "\n\n"

        recent_errors_list = list(self.recent_errors)[-10:]  # Convert to list and get last 10
        for i, error in enumerate(recent_errors_list, 1):
            timestamp = error['timestamp'].strftime("%H:%M:%S")
            result += f"{i}. [{timestamp}] Command: {error['command']}\n"
            result += f"   Error: {error['error']}\n"
            result += f"   Count: {error['count']} time(s)\n\n"

        # Add troubleshooting tips
        result += "TROUBLESHOOTING TIPS:\n"
        result += "- Type 'help' for available commands\n"
        result += "- Use 'man <command>' for detailed help\n"
        result += "- Check command spelling and syntax\n"
        result += "- Use command aliases (h=help, st=status, etc.)\n"

        return result
    def cmd_verbosity(self, args: List[str]) -> str:
        """Control logging verbosity level."""
        if not args:
            current_level = self.logger.level
            level_names = {10: 'DEBUG', 20: 'INFO', 30: 'WARNING', 40: 'ERROR'}
            current_name = level_names.get(current_level, 'UNKNOWN')
            return f"Current logging level: {current_name} ({current_level})\n" + \
                   "Usage: verbosity [debug|info|warning|error]\n"

        level = args[0].upper()
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }

        if level in level_map:
            self.logger.setLevel(level_map[level])
            self.logger.info(f"Logging level changed to {level}")
            return f"Logging verbosity set to: {level}\n"
        else:
            return f"Invalid level '{args[0]}'. Use: debug, info, warning, error\n"
    def cmd_history(self, args: Optional[List[str]] = None) -> str:
        """Display command history with optional filtering."""
        if not self.command_history:
            return "No command history available.\n"

        result = "COMMAND HISTORY\n"
        result += "=" * 40 + "\n\n"

        # Show last 20 commands by default
        history_slice = list(self.command_history)[-20:]

        for i, cmd in enumerate(history_slice, 1):
            result += f"{i:2d}. {cmd}\n"

        if len(self.command_history) > 20:
            result += f"\n... showing last 20 of {len(self.command_history)} commands\n"

        # Add usage statistics
        if hasattr(self, 'command_counts'):
            result += "\nMOST USED COMMANDS:\n"
            sorted_commands = sorted(self.command_counts.items(),
                                   key=lambda x: x[1], reverse=True)
            for cmd, count in sorted_commands[:5]:
                result += f"  {cmd}: {count} times\n"

        return result
    def cmd_status(self, args: Optional[List[str]] = None) -> str:
        """Display Bell System operational status overview."""
        return """BELL SYSTEM STATUS OVERVIEW
=============================

System Time:           """ + self.clock.timestamp() + """
Session ID:            """ + str(self.session_id) + """
Current Role:          """ + (str(self.role) if self.role else "Not selected") + """
Active Shift:          """ + str(self.current_shift) + """

Network Status:        OPERATIONAL
Switching Centers:     12 active, 0 maintenance
Trunk Groups:          47 active, 3 busy
Emergency Services:    NORMAL

Recent Activity:
- """ + str(len(self.command_history)) + """ commands executed this session
- """ + str(len(self.recent_errors)) + """ errors in last hour
- """ + str(len(self.shift_events)) + """ shift events logged

Type 'help' for available commands.
"""
    def cmd_clear(self, args: Optional[List[str]] = None) -> str:
        """Clear the terminal screen."""
        clear_screen()
        return ""
