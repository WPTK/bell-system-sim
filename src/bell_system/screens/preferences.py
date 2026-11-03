"""
The settings screen and the set command.

Settings are declared as data in :mod:`bell_system.settings`, and the assists
that bend a difficulty profile in :mod:`bell_system.progression`. This is only
the terminal's side of them: showing them, changing one, and taking account
of a change that needs more than being stored.
"""

from typing import List, Optional

from ..progression import ASSISTS_BY_KEY, PROFILE
from ..settings import OPTIONS, OPTIONS_BY_KEY
from .session import SessionState


class PreferenceCommands(SessionState):
    """
    The set command.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    def cmd_set(self, args: Optional[List[str]] = None) -> str:
        """Display and change simulation settings."""
        args = args or []

        if not args:
            return self._show_settings_screen()

        if args[0].lower() == 'reset':
            if len(args) > 1:
                key = args[1].lower()
                try:
                    self.settings.reset(key)
                except KeyError:
                    return self._unknown_setting(key)
                self._apply_setting(key)
                return f"{key} reset to {self.settings.get(key)}"
            self.settings.reset()
            for option in OPTIONS:
                self._apply_setting(option.key)
            return "All settings reset to period-accurate defaults."

        key = args[0].lower()
        if key not in OPTIONS_BY_KEY:
            return self._unknown_setting(key)

        if len(args) == 1:
            return self._describe_setting(key)

        value = ' '.join(args[1:])
        try:
            stored = self.settings.set(key, value)
        except ValueError as exc:
            return f"set: {exc}"

        self._apply_setting(key)
        option = OPTIONS_BY_KEY[key]
        result = f"{key} = {stored}"
        if key == 'game.difficulty':
            difficulty = self.career.difficulty
            result += f"\n\n{difficulty.name}: {difficulty.summary}"
            if difficulty.require_test_before_close:
                result += ("\n\nFrom here on, a report cannot be closed until "
                           "the loop has been measured,\nand mechanised loop "
                           "testing will no longer name the fault for you.")
        if key in ASSISTS_BY_KEY:
            name = self.career.difficulty.name
            if stored == PROFILE:
                result += f"\n\n{name} sets this again."
            else:
                result += (f"\n\n{option.summary}: {stored} takes the place "
                           f"of what {name} sets.")
        if option.accurate is not None and stored != option.accurate:
            result += (f"\n\nNote: the period-accurate value is "
                       f"'{option.accurate}'. This setting now departs from "
                       f"1978-1983 behaviour.")
        return result

    def _apply_setting(self, key: str) -> None:
        """Take account of a setting whose change needs more than storage."""
        if key == 'date.epoch':
            self.clock.reset_session()
        elif key == 'display.log_console':
            self._setup_logging()
        elif key == 'game.difficulty':
            self.career.set_difficulty(self.settings.get('game.difficulty'))
        elif key in ASSISTS_BY_KEY:
            self.career.set_assists(self.settings.assist_overrides())

    def _unknown_setting(self, key: str) -> str:
        """Report an unrecognised setting name."""
        return (f"set: no such setting '{key}'\n"
                f"Available settings: {', '.join(sorted(OPTIONS_BY_KEY))}\n"
                f"Type 'set' with no arguments for the settings screen.")

    def _describe_setting(self, key: str) -> str:
        """Show one setting in detail."""
        option = OPTIONS_BY_KEY[key]
        current = self.settings.get(key)
        choices = ', '.join(option.choices) if option.choices else '(free text)'
        accurate = option.accurate or 'not applicable'
        lines = [
            f"{option.key}",
            '=' * 50,
            f"Current value:     {current}",
            f"Default:           {option.default}",
            f"Permitted:         {choices}",
            f"Period-accurate:   {accurate}",
            '',
            option.summary + '.',
        ]
        if option.detail:
            lines.append(option.detail)
        lines.append('')
        lines.append(f"Usage: set {option.key} <value>")
        return '\n'.join(lines)

    def _show_settings_screen(self) -> str:
        """Render the full settings screen."""
        deviations = self.settings.deviations()
        assists = self.settings.assist_departures()
        width = max(len(option.key) for option in OPTIONS)

        lines = [
            "Bell System Terminal - Simulation Settings",
            '=' * 60,
            '',
            "The simulation runs period-accurate by default. Each setting",
            "below may be moved away from that where a modern terminal makes",
            "the accurate behaviour less playable.",
            '',
            f"{'SETTING'.ljust(width)}  {'CURRENT'.ljust(12)}  OPTIONS",
            '-' * 60,
        ]

        for option in OPTIONS:
            current = self.settings.get(option.key)
            choices = '/'.join(option.choices) if option.choices else 'YYYY-MM-DD'
            marker = (' *' if option.key in deviations
                      else ' +' if option.key in assists else '  ')
            lines.append(
                f"{option.key.ljust(width)}  {current.ljust(12)}{marker}{choices}"
            )

        lines.extend([
            '-' * 60,
            '',
        ])

        if deviations:
            lines.append(
                f"* {len(deviations)} setting(s) depart from period-accurate "
                f"behaviour: {', '.join(deviations)}"
            )
        else:
            lines.append("All settings are period-accurate.")
        if assists:
            lines.append(
                f"+ {len(assists)} assist(s) override the "
                f"{self.career.difficulty.name} profile: {', '.join(assists)}"
            )

        lines.extend([
            '',
            "Current shift time: " + self.clock.timestamp(),
            '',
            "Commands:",
            "  set <setting>            Explain one setting in detail",
            "  set <setting> <value>    Change a setting",
            "  set reset [<setting>]    Restore period-accurate defaults",
            '',
            "Settings persist between sessions.",
        ])
        return '\n'.join(lines)
