"""
Running things: at(1), make(1), su(1) and the uucp commands.

A terminal you only ever type one command into at a time is not really a
machine you work on. These are the commands that let you set something going
and come back to it: at(1) queues a command against the shift clock and it
fires when the time comes round, make(1) builds what is out of date, and the
uucp family is how this machine talked to the rest of the network - which is
where the netnews under /usr/spool/news arrives from.

su(1) writes to /usr/adm/sulog, because that file is on this machine and
somebody put those entries in it.
"""

from typing import Dict, List, Optional

from ..filesystem import normalise
from .session import SessionState

# The at(1) queue lives in the spool on a real machine. It lives here too,
# so ls(1) finds the jobs and cat(1) reads them.
AT_SPOOL = '/usr/spool/at'

# Sites this machine has a uucp connection to. mhuxco is this machine; the
# rest are the neighbours its L.sys would name. research, ihnp4 and pwba
# appear in /usr/adm/uucplog, which is where these came from.
UUCP_NEIGHBOURS = ('ihnp4', 'mhuxt', 'pwba', 'research')


class JobCommands(SessionState):
    """
    Deferred work, builds, and the uucp network.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- at(1) ------------------------------------------------------------

    def cmd_at(self, args: Optional[List[str]] = None) -> str:
        """
        Run a command later in the shift.

        ``at 1030 report board`` queues that command for half past ten. The
        time is four digits on the twenty-four hour clock, as the Seventh
        Edition at(1) took it. ``at -l`` lists what is queued and ``at -r``
        followed by a job number removes one. Jobs fire as the shift clock
        passes them, and their output arrives on the terminal the way a
        message from anybody else in the building does.
        """
        args = args or []
        if not args or args[0] == '-l':
            return self._at_list()
        if args[0] == '-r':
            return self._at_remove(args[1:])

        moment = self._at_time(args[0])
        if moment is None:
            return f"at: bad time {args[0]}"
        if not args[1:]:
            return "at: usage: at hhmm command"

        now = self.clock.now()
        due = now.replace(hour=moment[0], minute=moment[1],
                          second=0, microsecond=0)
        if due <= now:
            return (f"at: {args[0]} has already gone by; "
                    f"it is {now.strftime('%H%M')}")

        self._at_number += 1
        number = self._at_number
        self._at_jobs.append({
            'number': number,
            'due': due,
            'command': ' '.join(args[1:]),
            'owner': self.username or 'sysop',
        })
        path = f"{AT_SPOOL}/{due.strftime('%y.%j.%H%M')}.{number}"
        self.write_file(path, ' '.join(args[1:]) + '\n')
        return f"job {number} at {due.strftime('%a %b %e %H:%M:%S')} 1983"

    @staticmethod
    def _at_time(text: str) -> Optional[tuple]:
        """Turn 1030 or 10:30 into (10, 30), or return None."""
        digits = text.replace(':', '')
        if not digits.isdigit() or len(digits) not in (3, 4):
            return None
        hour, minute = int(digits[:-2]), int(digits[-2:])
        if hour > 23 or minute > 59:
            return None
        return hour, minute

    def _at_list(self) -> str:
        """Print the queue, soonest first."""
        if not self._at_jobs:
            return "at: no jobs queued"
        rows = []
        for job in sorted(self._at_jobs, key=lambda item: item['due']):
            rows.append(f"{job['number']:>4}  {job['due'].strftime('%H:%M')}  "
                        f"{job['owner']:<10}{job['command']}")
        return '\n'.join(rows)

    def _at_remove(self, wanted: List[str]) -> str:
        """Take jobs back out of the queue."""
        if not wanted:
            return "at: usage: at -r job ..."
        removed = []
        for item in wanted:
            for job in list(self._at_jobs):
                if str(job['number']) == item:
                    self._at_jobs.remove(job)
                    removed.append(item)
        if not removed:
            return f"at: no such job {' '.join(wanted)}"
        return f"at: removed {' '.join(removed)}"

    def at_due(self) -> List[str]:
        """
        Run every queued job whose time has come and return what they said.

        Called once per command from the shift's interruption hook, so a job
        set for half past ten runs when the shift clock reaches half past
        ten and not before.
        """
        now = self.clock.now()
        fired = []
        for job in sorted(self._at_jobs, key=lambda item: item['due']):
            if job['due'] > now:
                continue
            self._at_jobs.remove(job)
            # The queued line runs as an ordinary command. Guarding against
            # a job that queues another job keeps a runaway out of the loop.
            if job['command'].split()[0] in ('at',):
                output = "at: a job may not queue another job"
            else:
                output = self.execute_command(job['command'])
            head = f"[at: job {job['number']} - {job['command']}]"
            fired.append(f"{head}\n{output}".rstrip())
        return fired

    # -- make(1) ----------------------------------------------------------

    def cmd_make(self, args: Optional[List[str]] = None) -> str:
        """
        Bring a target up to date from a makefile.

        Reads ``makefile`` in the working directory. A rule is a target, a
        colon, its prerequisites, and then command lines indented with a tab.
        Anything whose prerequisite does not exist is out of date and gets
        rebuilt; anything already built is left alone, which is the whole
        point of the program.
        """
        args = args or []
        source = 'makefile'
        for index, item in enumerate(args):
            if item == '-f' and index + 1 < len(args):
                source = args[index + 1]
        text = self._read(source)
        if text is None:
            return f"make: cannot open {source}"

        rules, order = self._parse_makefile(text)
        if not order:
            return "make: no targets"
        wanted = [item for item in args
                  if not item.startswith('-') and item != source]
        targets = wanted or [order[0]]

        built: List[str] = []
        lines: List[str] = []
        for target in targets:
            if target not in rules:
                return f"make: don't know how to make {target}"
            self._make_target(target, rules, built, lines, set())
        if not lines:
            return f"`{targets[0]}' is up to date."
        return '\n'.join(lines)

    @staticmethod
    def _parse_makefile(text: str) -> tuple:
        """Return ({target: (prerequisites, commands)}, targets in file order)."""
        rules: Dict[str, tuple] = {}
        order: List[str] = []
        current = None
        for line in text.split('\n'):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            if line.startswith(('\t', '    ')) and current:
                rules[current][1].append(line.strip())
                continue
            if ':' in line:
                name, _, needs = line.partition(':')
                current = name.strip()
                rules[current] = (needs.split(), [])
                order.append(current)
        return rules, order

    def _make_target(self, target: str, rules: Dict[str, tuple],
                     built: List[str], lines: List[str],
                     seen: set) -> bool:
        """
        Build one target, its prerequisites first. Returns True if it ran.

        ``seen`` catches a makefile whose rules refer round to each other,
        which make(1) reports rather than following forever.
        """
        if target in seen:
            lines.append(f"make: circular {target} dependency dropped")
            return False
        seen = seen | {target}
        needs, commands = rules.get(target, ([], []))

        rebuilt = False
        for need in needs:
            if need in rules:
                rebuilt |= self._make_target(need, rules, built, lines, seen)
            elif self._node(need) is None:
                lines.append(f"make: don't know how to make {need}")
                return False

        exists = self._node(target) is not None or target in built
        if exists and not rebuilt:
            return False
        for command in commands:
            lines.append(command)
            output = self.execute_command(command)
            if output.strip():
                lines.append(output.rstrip())
        built.append(target)
        return True

    # -- becoming somebody else -------------------------------------------

    def cmd_su(self, args: Optional[List[str]] = None) -> str:
        """
        Become another user.

        Every attempt lands in /usr/adm/sulog whether it succeeds or not,
        which is what that file on this machine is a record of. Nobody at a
        craft position has the root password, and the log is the reason the
        wire chief knows who tried.
        """
        args = args or []
        who = args[0] if args else 'root'
        passwd = self._read('/etc/passwd') or ''
        known = {line.split(':')[0] for line in passwd.split('\n') if ':' in line}
        stamp = self.clock.now().strftime('%m/%d %H:%M')
        me = self.username or 'sysop'

        if who not in known:
            self._sulog(f"SU {stamp} - tty01 {me}-{who}")
            return f"su: unknown id: {who}"
        if who == 'root':
            self._sulog(f"SU {stamp} - tty01 {me}-root")
            return ("Password:\nsu: Sorry\n\n"
                    "(The attempt is now in /usr/adm/sulog. It stays there.)")
        self._sulog(f"SU {stamp} - tty01 {me}-{who}")
        return "Password:\nsu: Sorry"

    def _sulog(self, line: str) -> None:
        """
        Append one line to the su log.

        Reads the node rather than going through _read, because the log
        denies the rest of the machine and the machine is not the rest of
        the machine. Going the polite way here silently emptied the file
        for anybody who could not read it, which is every craftsperson the
        wire chief has not yet put in the adm group.
        """
        node = self.filesystem.get('/usr/adm/sulog')
        if node is None or node.is_dir:
            return
        existing = node.content if isinstance(node.content, str) else ''
        self.filesystem['/usr/adm/sulog'] = node._replace(
            content=existing + line + '\n')

    def cmd_logname(self, args: Optional[List[str]] = None) -> str:
        """Print the name you logged in under."""
        return (self.username or 'sysop') + '\n'

    # -- uucp -------------------------------------------------------------

    def cmd_uuname(self, args: Optional[List[str]] = None) -> str:
        """
        List the machines this one can call.

        ``uuname -l`` prints the name of this machine instead, which is what
        a script uses to find out where it is running.
        """
        args = args or []
        if args and args[0] == '-l':
            return 'mhuxco\n'
        return '\n'.join(UUCP_NEIGHBOURS) + '\n'

    def cmd_uulog(self, args: Optional[List[str]] = None) -> str:
        """
        Print the uucp log.

        ``uulog -s<site>`` shows only the traffic with one site.
        """
        args = args or []
        text = self._read('/usr/adm/uucplog')
        if text is None:
            return "uulog: cannot open /usr/adm/uucplog"
        for item in args:
            if item.startswith('-s') and item[2:]:
                site = item[2:]
                kept = [line for line in text.split('\n') if site in line]
                if not kept or kept == ['']:
                    return f"uulog: no traffic with {site}"
                return '\n'.join(kept) + '\n'
        return text

    def cmd_uux(self, args: Optional[List[str]] = None) -> str:
        """
        Queue a command to run on another machine.

        ``uux research!date`` asks research to run date and send the answer
        back. Nothing comes back inside a shift: a uucp job waits for the
        next time the two machines happen to be talking, which on this
        machine is the small hours.
        """
        args = args or []
        if not args:
            return "uux: usage: uux site!command"
        request = ' '.join(args)
        site = request.split('!')[0].lstrip('-')
        if '!' not in request:
            return "uux: no site in request"
        if site not in UUCP_NEIGHBOURS:
            return f"uux: {site}: unknown site (uuname lists the ones we call)"
        self._uux_jobs += 1
        name = f"X.{site}N{self._uux_jobs:04d}"
        return (f"uux: queued {name}\n"
                f"uux: {site} is called at 04:00; nothing comes back before then.")

    # -- process bookkeeping ----------------------------------------------

    def cmd_kill(self, args: Optional[List[str]] = None) -> str:
        """
        Send a signal to a process.

        Only what is in the process table can be signalled, and the system
        processes belong to root, which a craft position is not.
        """
        args = args or []
        wanted = [item for item in args if not item.startswith('-')]
        if not wanted:
            return "kill: usage: kill [-signal] pid ..."
        rows = []
        for item in wanted:
            if not item.lstrip('-').isdigit():
                rows.append(f"kill: {item}: arguments must be process ids")
                continue
            process = next((proc for proc in self.processes
                            if str(proc['pid']) == item), None)
            if process is None:
                rows.append(f"kill: {item}: no such process")
            elif process['command'].startswith('-') or process['tty'] == '?':
                rows.append(f"kill: {item}: not owner")
            else:
                rows.append(f"kill: {item}: not owner")
        return '\n'.join(rows)

    def cmd_nice(self, args: Optional[List[str]] = None) -> str:
        """
        Run a command at low priority.

        The command still runs; on a machine this size the priority is the
        only part that is theatre.
        """
        args = args or []
        rest = [item for item in args if not item.startswith('-')]
        if not rest:
            return "nice: usage: nice [-number] command"
        return self.execute_command(' '.join(rest))

    def cmd_time(self, args: Optional[List[str]] = None) -> str:
        """
        Run a command and report how long it took.

        Real, user and system time, in the three-line form time(1) printed.
        """
        args = args or []
        if not args:
            return "time: usage: time command"
        import time as _time
        started = _time.time()
        output = self.execute_command(' '.join(args))
        spent = _time.time() - started
        report = (f"\nreal     {spent:6.1f}\n"
                  f"user     {spent * 0.4:6.1f}\n"
                  f"sys      {spent * 0.6:6.1f}")
        return (output.rstrip() + report) if output.strip() else report.lstrip()

    def cmd_nohup(self, args: Optional[List[str]] = None) -> str:
        """
        Run a command immune to hangups.

        Output goes to nohup.out in the working directory, as it did, which
        means the terminal says nothing except where to look.
        """
        args = args or []
        if not args:
            return "nohup: usage: nohup command"
        output = self.execute_command(' '.join(args))
        path = normalise('nohup.out', self.current_directory)
        error = self.write_file(path, output.rstrip() + '\n')
        if error:
            return error
        return "Sending output to nohup.out"

    # -- remote job entry -------------------------------------------------

    def cmd_send(self, args: Optional[List[str]] = None) -> str:
        """
        Submit a batch job to the host over the RJE link.

        A Bell operations machine did not do its own billing. The message
        detail went to the revenue accounting office on a mainframe, and
        remote job entry is how a job got there: you submitted a file, the
        job went up the link, and the answer came back as a listing hours
        later.

        ``send file`` submits; ``send -h host file`` names the host, which
        this position only has one of.
        """
        args = args or []
        host = 'RAO1'
        rest = []
        index = 0
        while index < len(args):
            if args[index] == '-h' and index + 1 < len(args):
                index += 1
                host = args[index].upper()
            else:
                rest.append(args[index])
            index += 1
        if not rest:
            return "send: usage: send [-h host] file"
        if host != 'RAO1':
            return f"send: {host}: no such host (rjestat lists the link)"

        text = self._read(rest[0])
        if text is None:
            return f"send: cannot open {rest[0]}"
        self._rje_jobs += 1
        cards = -(-len(text.encode('latin-1', 'replace')) // 80)
        name = f"{self.username or 'sysop'}{self._rje_jobs:02d}"
        self._rje_queue.append({'name': name, 'cards': cards,
                                'file': rest[0],
                                'at': self.clock.now()})
        return (f"send: {rest[0]} queued as {name}, {cards} cards\n"
                f"send: RAO1 returns listings on the overnight run.")

    def cmd_rjestat(self, args: Optional[List[str]] = None) -> str:
        """
        Report on the remote job entry link and what is queued on it.

        The line is a 4800 baud dedicated circuit to the revenue accounting
        office. If it is down, nothing you submit goes anywhere, which is
        worth knowing before you spend the morning building a job.
        """
        args = args or []
        rows = ["RJE STATUS",
                "",
                "  Host     RAO1 (revenue accounting office)",
                "  Line     4800 baud dedicated, protocol 2780",
                "  State    ACTIVE",
                ""]
        if not self._rje_queue:
            rows.append("  No jobs queued from this position.")
            return '\n'.join(rows)
        rows.append("  JOB       CARDS  SUBMITTED  FILE")
        for job in self._rje_queue:
            rows.append(f"  {job['name']:<9}{job['cards']:>6}  "
                        f"{job['at'].strftime('%H:%M'):<11}{job['file']}")
        rows.extend(['', "  Nothing returns before the overnight run."])
        return '\n'.join(rows)
