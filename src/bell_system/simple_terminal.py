#!/usr/bin/env python3
"""
Bell System UNIX V7 Terminal Simulation - Simplified Interface
=============================================================

Authentic AT&T Internal Operations Workstation (1978-1983).

A compact four-role terminal offering genuine filesystem exploration
(``cat``, ``cd``, ``grep``, ``find``) alongside the core V7 command set.
Four roles: Systems Operator, Switching Technician, Field Liaison, NOC Analyst.
"""

import os
from datetime import datetime


class SimpleTerminal:
    def __init__(self):
        self.current_directory = "/usr/users/sysop"
        self.username = "sysop"
        self.hostname = "bell-unix"
        self.shell = "/bin/sh"
        self.command_history = []
        self.role = None
        self.shift_events = []

        # Bell System specific environment
        self.roles = {
            "sysop": "UNIX Systems Operator",
            "switch": "Switching Station Technician",
            "field": "Field Support Liaison",
            "noc": "National NOC Analyst"
        }

        # Simulate authentic Bell System UNIX file system
        self.filesystem = {
            "/": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 512, "files": ["bin", "dev", "etc", "lib", "tmp", "usr", "home", "root"]},
            "/bin": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 1024, "files": ["sh", "ls", "cat", "cp", "mv", "rm", "mkdir", "rmdir", "ps", "who", "date", "grep", "ed", "cc", "as", "ld"]},
            "/dev": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 256, "files": ["console", "tty00", "tty01", "rp0", "mt0"]},
            "/etc": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 512, "files": ["passwd", "group", "motd", "rc"]},
            "/lib": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 256, "files": ["libc.a", "crt0.o"]},
            "/tmp": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxrwxrwx", "size": 64, "files": []},
            "/usr": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 1024, "files": ["bin", "lib", "include", "src", "doc", "man"]},
            "/usr/bin": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 2048, "files": ["awk", "sed", "sort", "uniq", "wc", "find", "tr", "od", "file", "make", "yacc", "lex", "ratfor", "f77", "adb"]},
            "/usr/lib": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 512, "files": ["libm.a", "liby.a", "libl.a"]},
            "/usr/include": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 256, "files": ["stdio.h", "signal.h", "sys"]},
            "/usr/src": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 128, "files": ["cmd", "lib", "games"]},
            "/home": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwxr-xr-x", "size": 64, "files": []},
            "/root": {"type": "dir", "owner": "root", "group": "wheel", "mode": "drwx------", "size": 128, "files": ["hello.c", ".profile"]},
            "/etc/passwd": {"type": "file", "owner": "root", "group": "wheel", "mode": "-rw-r--r--", "size": 156, "content": "root::0:1::/root:/bin/sh\ndaemon::1:1::/:/bin/sh\nbin::2:2::/bin:\nsys::3:3::/usr/src:\nadm::4:4::/usr/adm:\nuucp::5:5::/usr/spool/uucp:/usr/lib/uucp/uucico\n"},
            "/etc/group": {"type": "file", "owner": "root", "group": "wheel", "mode": "-rw-r--r--", "size": 87, "content": "wheel::0:root\ndaemon::1:daemon\nbin::2:bin\nsys::3:sys\nadm::4:adm\nuucp::5:uucp\n"},
            "/etc/motd": {"type": "file", "owner": "root", "group": "wheel", "mode": "-rw-r--r--", "size": 243, "content": "UNIX Version 7\nBell Telephone Laboratories\nMurray Hill, New Jersey\n\nCopyright (c) 1976 Bell Telephone Laboratories, Incorporated.\nAll rights reserved.\n\nWelcome to the UNIX time-sharing system.\nFor assistance, contact your system administrator.\n\nCurrent system load: light\nUsers currently logged in: 3\n"},
            "/root/hello.c": {"type": "file", "owner": "root", "group": "wheel", "mode": "-rw-r--r--", "size": 78, "content": "#include <stdio.h>\n\nmain()\n{\n    printf(\"hello, world\\n\");\n}\n"},
            "/root/.profile": {"type": "file", "owner": "root", "group": "wheel", "mode": "-rw-r--r--", "size": 112, "content": "# User profile for root\nPATH=/bin:/usr/bin\nexport PATH\nHOME=/root\nexport HOME\nSHELL=/bin/sh\nexport SHELL\n"}
        }

        # Simulate running processes (authentic V7 system processes)
        self.processes = [
            {"pid": 0, "command": "swapper", "tty": "?", "time": "0:00"},
            {"pid": 1, "command": "init", "tty": "?", "time": "0:02"},
            {"pid": 23, "command": "update", "tty": "?", "time": "0:01"},
            {"pid": 45, "command": "sh", "tty": "co", "time": "0:00"},
            {"pid": 67, "command": "getty", "tty": "01", "time": "0:00"},
            {"pid": 89, "command": "sh", "tty": "01", "time": "0:00"},
            {"pid": 102, "command": "cron", "tty": "?", "time": "0:00"},
        ]

        # Bell Labs users from historical documentation
        self.users = [
            {"user": "root", "tty": "console", "login": "Mar 10 08:30"},
            {"user": "dmr", "tty": "01", "login": "Mar 10 09:15"},  # Dennis Ritchie
            {"user": "ken", "tty": "02", "login": "Mar 10 07:45"},  # Ken Thompson
        ]

    def show_banner(self):
        """Display authentic UNIX V7 login banner"""
        print("\n" + "="*60)
        print("UNIX Version 7")
        print("Bell Telephone Laboratories")
        print("Murray Hill, New Jersey")
        print("="*60)
        print("\nCopyright (c) 1976 Bell Telephone Laboratories, Incorporated.")
        print("All rights reserved.")
        print("\nlogin: ", end="")

    def login_sequence(self):
        """Simulate authentic V7 login"""
        username = input().strip()
        if username.lower() == 'root':
            print("Password: ", end="")
            # V7 suppressed the echo here; the value itself is not checked.
            input()
            print()

            # Show message of the day
            if "/etc/motd" in self.filesystem:
                print(self.filesystem["/etc/motd"]["content"])

            print("You have mail.")
            print()
            return True
        else:
            print("Login incorrect.")
            return False

    def get_prompt(self):
        """Return authentic V7 shell prompt"""
        if self.username == "root":
            return "# "
        else:
            return "$ "

    def resolve_path(self, path):
        """Resolve relative paths to absolute paths"""
        if path.startswith('/'):
            return path
        elif path == '.':
            return self.current_directory
        elif path == '..':
            if self.current_directory == '/':
                return '/'
            return '/'.join(self.current_directory.split('/')[:-1]) or '/'
        else:
            if self.current_directory == '/':
                return f'/{path}'
            return f'{self.current_directory}/{path}'

    def format_ls_output(self, files, long_format=False, show_all=False):
        """Format ls output in authentic V7 style"""
        output = []

        if not show_all:
            files = [f for f in files if not f.startswith('.')]

        if long_format:
            total_blocks = 0
            for filename in files:
                filepath = self.resolve_path(filename)
                if filepath in self.filesystem:
                    file_info = self.filesystem[filepath]
                    size = file_info.get('size', 0)
                    total_blocks += (size + 511) // 512  # Round up to blocks

            output.append(f"total {total_blocks}")

            for filename in sorted(files):
                filepath = self.resolve_path(filename)
                if filepath in self.filesystem:
                    file_info = self.filesystem[filepath]
                    mode = file_info.get('mode', '-rw-r--r--')
                    owner = file_info.get('owner', 'root')
                    group = file_info.get('group', 'wheel')
                    size = file_info.get('size', 0)

                    # Format date (simplified)
                    date_str = "Mar 10 12:34"

                    output.append(f"{mode}  1 {owner:<8} {group:<8} {size:>7} {date_str} {filename}")
        else:
            # Simple format - just filenames
            sorted_files = sorted(files)
            # Print in columns like original V7 ls
            if len(sorted_files) <= 5:
                output.append('  '.join(sorted_files))
            else:
                # Multiple columns
                cols = 4
                rows = (len(sorted_files) + cols - 1) // cols
                for i in range(rows):
                    row = []
                    for j in range(cols):
                        idx = i + j * rows
                        if idx < len(sorted_files):
                            row.append(sorted_files[idx].ljust(12))
                    output.append(''.join(row).rstrip())

        return '\n'.join(output)

    def cmd_ls(self, args):
        """Implement ls command"""
        long_format = '-l' in args
        show_all = '-a' in args

        # Remove flags from args to get target directory
        paths = [arg for arg in args if not arg.startswith('-')]
        target_dir = paths[0] if paths else self.current_directory
        target_path = self.resolve_path(target_dir)

        if target_path not in self.filesystem:
            return f"ls: {target_dir}: No such file or directory"

        file_info = self.filesystem[target_path]
        if file_info['type'] == 'file':
            if long_format:
                mode = file_info.get('mode', '-rw-r--r--')
                owner = file_info.get('owner', 'root')
                group = file_info.get('group', 'wheel')
                size = file_info.get('size', 0)
                date_str = "Mar 10 12:34"
                return f"{mode}  1 {owner:<8} {group:<8} {size:>7} {date_str} {target_dir}"
            else:
                return target_dir

        files = file_info.get('files', [])
        if show_all:
            files = ['.', '..'] + files

        return self.format_ls_output(files, long_format, show_all)

    def cmd_cat(self, args):
        """Implement cat command"""
        if not args:
            return "cat: missing file operand"

        output = []
        for filename in args:
            filepath = self.resolve_path(filename)
            if filepath not in self.filesystem:
                output.append(f"cat: {filename}: No such file or directory")
                continue

            file_info = self.filesystem[filepath]
            if file_info['type'] == 'dir':
                output.append(f"cat: {filename}: Is a directory")
                continue

            content = file_info.get('content', '')
            output.append(content)

        return '\n'.join(output)

    def cmd_pwd(self, args):
        """Implement pwd command"""
        return self.current_directory

    def cmd_cd(self, args):
        """Implement cd command"""
        if not args:
            target = "/root"  # cd with no args goes to home
        else:
            target = args[0]

        target_path = self.resolve_path(target)

        if target_path not in self.filesystem:
            return f"cd: {target}: No such file or directory"

        if self.filesystem[target_path]['type'] != 'dir':
            return f"cd: {target}: Not a directory"

        self.current_directory = target_path
        return ""

    def cmd_ps(self, args):
        """Implement ps command"""
        show_all = 'a' in ''.join(args) or '-a' in args

        output = []
        header = "  PID TTY      TIME CMD"
        output.append(header)

        for proc in self.processes:
            if not show_all and proc['tty'] == '?':
                continue

            pid = str(proc['pid']).rjust(5)
            tty = proc['tty'].ljust(8)
            time_str = proc['time'].ljust(8)
            cmd = proc['command']

            output.append(f"{pid} {tty} {time_str} {cmd}")

        return '\n'.join(output)

    def cmd_who(self, args):
        """Implement who command"""
        output = []
        for user in self.users:
            output.append(f"{user['user']:<8} {user['tty']:<8} {user['login']}")
        return '\n'.join(output)

    def cmd_date(self, args):
        """Implement date command"""
        # Format like original V7: "Mon Mar 10 12:34:56 EST 1976"
        now = datetime.now()
        return now.strftime("%a %b %d %H:%M:%S EST %Y")

    def cmd_echo(self, args):
        """Implement echo command"""
        return ' '.join(args)

    def cmd_grep(self, args):
        """Implement grep command (simplified)"""
        if len(args) < 2:
            return "grep: missing operand"

        pattern = args[0]
        filename = args[1]
        filepath = self.resolve_path(filename)

        if filepath not in self.filesystem:
            return f"grep: {filename}: No such file or directory"

        file_info = self.filesystem[filepath]
        if file_info['type'] == 'dir':
            return f"grep: {filename}: Is a directory"

        content = file_info.get('content', '')
        lines = content.split('\n')
        matches = [line for line in lines if pattern in line]

        return '\n'.join(matches)

    def cmd_wc(self, args):
        """Implement wc command"""
        if not args:
            return "wc: missing file operand"

        output = []
        for filename in args:
            filepath = self.resolve_path(filename)
            if filepath not in self.filesystem:
                output.append(f"wc: {filename}: No such file or directory")
                continue

            file_info = self.filesystem[filepath]
            if file_info['type'] == 'dir':
                output.append(f"wc: {filename}: Is a directory")
                continue

            content = file_info.get('content', '')
            lines = len(content.split('\n')) - (1 if content.endswith('\n') else 0)
            words = len(content.split()) if content.strip() else 0
            chars = len(content)

            output.append(f"{lines:>8} {words:>7} {chars:>7} {filename}")

        return '\n'.join(output)

    def cmd_ed(self, args):
        """Implement ed command (line editor)"""
        if args:
            filename = args[0]
            filepath = self.resolve_path(filename)
            if filepath in self.filesystem and self.filesystem[filepath]['type'] == 'file':
                content = self.filesystem[filepath].get('content', '')
                lines = len(content.split('\n'))
                return f"{lines}\n?"
            else:
                return f"{filename}: No such file or directory\n?"
        else:
            return "?\n(enter 'q' to quit editor)"

    def cmd_df(self, args):
        """Implement df command"""
        return """Filesystem    512-blocks      Used Available Capacity  Mounted on
/dev/rp0a           4872      4512       360    93%    /
/dev/rp0g          42760     21736     21024    51%    /usr"""

    def cmd_du(self, args):
        """Implement du command"""
        target = args[0] if args else self.current_directory
        target_path = self.resolve_path(target)

        # Simplified calculation
        total_size = 0
        for path, info in self.filesystem.items():
            if path.startswith(target_path):
                total_size += (info.get('size', 0) + 511) // 512

        return f"{total_size}\t{target_path}"

    def cmd_find(self, args):
        """Implement find command (simplified)"""
        if not args:
            return "find: missing path"

        search_path = self.resolve_path(args[0])
        results = []

        for path in self.filesystem:
            if path.startswith(search_path):
                results.append(path)

        return '\n'.join(sorted(results))

    def cmd_help(self, args):
        """Implement help command"""
        return """Available commands in UNIX Version 7:

File operations:
  ls      - list directory contents
  cat     - display file contents
  pwd     - print working directory
  cd      - change directory
  find    - find files
  wc      - word, line, character count
  grep    - search text patterns

System information:
  ps      - show running processes
  who     - show logged in users
  date    - show current date and time
  df      - display filesystem usage
  du      - display directory usage

Text editors and tools:
  ed      - line editor

Built-in commands:
  help    - show this help message
  man     - display manual pages
  history - show command history
  clear   - clear screen
  exit    - logout and exit

For detailed information on any command, type: man <command>
Example: man ls

This is UNIX Version 7 from Bell Telephone Laboratories (1976)."""

    def cmd_man(self, args):
        """Implement man command"""
        if not args:
            return "man: missing command name"

        command = args[0]

        # Basic manual pages for key commands
        manual_pages = {
            'ls': """LS(1)                    UNIX Programmer's Manual                    LS(1)

NAME
     ls - list contents of directory

SYNOPSIS
     ls [ -acdilrstu ] [ name... ]

DESCRIPTION
     For each directory argument, ls lists the contents of the directory;
     for each file argument, ls repeats its name and any other information
     requested. When no argument is given, the current directory is listed.

     -a   List all entries; in the absence of this option, entries whose
          names begin with a period are not listed.
     -l   List in long format, giving mode, number of links, owner, size
          in bytes, and time of last modification for each file.

Bell Telephone Laboratories        March 1976                           LS(1)""",

            'cat': """CAT(1)                   UNIX Programmer's Manual                   CAT(1)

NAME
     cat - concatenate and print files

SYNOPSIS
     cat [ -u ] file...

DESCRIPTION
     Cat reads each file in sequence and displays it on the standard output.
     Thus 'cat file' displays the file and 'cat file1 file2' concatenates
     the files and displays the result.

Bell Telephone Laboratories        March 1976                          CAT(1)""",

            'ps': """PS(1)                    UNIX Programmer's Manual                    PS(1)

NAME
     ps - process status

SYNOPSIS
     ps [ alx ] [ namelist ]

DESCRIPTION
     Ps prints information about active processes. Without options,
     information is printed about processes associated with the controlling
     terminal.

     a    Include information about processes owned by others.
     l    Long listing.
     x    Include processes not associated with a terminal.

Bell Telephone Laboratories        March 1976                           PS(1)"""
        }

        if command in manual_pages:
            return manual_pages[command]
        else:
            return f"man: {command}: No manual entry"

    def execute_command(self, command_line):
        """Execute a command and return output"""
        if not command_line.strip():
            return ""

        # Add to history
        self.command_history.append(command_line)

        # Parse command
        parts = command_line.strip().split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Built-in commands
        if cmd == 'exit' or cmd == 'logout':
            return "LOGOUT"
        elif cmd == 'clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            return ""
        elif cmd == 'history':
            return '\n'.join(f"{i+1:4d}  {cmd}" for i, cmd in enumerate(self.command_history[-20:]))
        elif cmd == 'help':
            return self.cmd_help(args)

        # File system commands
        command_map = {
            'ls': self.cmd_ls,
            'cat': self.cmd_cat,
            'pwd': self.cmd_pwd,
            'cd': self.cmd_cd,
            'ps': self.cmd_ps,
            'who': self.cmd_who,
            'date': self.cmd_date,
            'echo': self.cmd_echo,
            'grep': self.cmd_grep,
            'wc': self.cmd_wc,
            'ed': self.cmd_ed,
            'df': self.cmd_df,
            'du': self.cmd_du,
            'find': self.cmd_find,
            'man': self.cmd_man,
        }

        if cmd in command_map:
            try:
                result = command_map[cmd](args)
                return result if result else ""
            except Exception as e:
                return f"{cmd}: error - {str(e)}"
        else:
            return f"{cmd}: command not found"

    def run(self):
        """Main terminal loop"""
        # Show login banner and auto-login
        print("\n" + "="*60)
        print("UNIX Version 7")
        print("Bell Telephone Laboratories")
        print("Murray Hill, New Jersey")
        print("="*60)
        print("\nCopyright (c) 1976 Bell Telephone Laboratories, Incorporated.")
        print("All rights reserved.")
        print("\nlogin: root")
        print("Password: ")
        print()

        # Show message of the day
        if "/etc/motd" in self.filesystem:
            print(self.filesystem["/etc/motd"]["content"])

        print("You have mail.")
        print()
        print("Type 'help' for available commands or 'man <command>' for detailed help.")
        print("Type 'exit' or 'logout' to quit.")
        print()

        # Main command loop
        try:
            while True:
                # Show prompt
                prompt = f"{self.hostname}:{self.current_directory}{self.get_prompt()}"
                try:
                    command = input(prompt)
                except EOFError:
                    print("\nlogout")
                    break

                # Execute command
                result = self.execute_command(command)

                if result == "LOGOUT":
                    print("logout")
                    break
                elif result:
                    print(result)

        except KeyboardInterrupt:
            print("\n^C")
            print("logout")

if __name__ == "__main__":
    SimpleTerminal().run()
