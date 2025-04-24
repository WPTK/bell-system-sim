
import os
import time
from datetime import datetime
from random import choice, random

class UnixTerminal:
    def __init__(self):
        self.username = ""
        self.hostname = "pdp11"
        self.current_dir = "/usr/home"
        self.role = None
        self.mail_messages = [
            {"from": "sysadmin", "subject": "System maintenance", "body": "Scheduled downtime tonight 2300-0200 EDT"},
            {"from": "tech.support", "subject": "New UUCP route", "body": "Added connection to research.att.com"},
            {"from": "operations", "subject": "Load balancing", "subject": "Please monitor /dev/rk1 usage"}
        ]
        self.uucp_nodes = ["research", "murray", "alice", "eagle", "mhuxj", "research"]
        self.roles = {
            "1": "UNIX Systems Operator",
            "2": "Switching Station Technician",
            "3": "Field Support Liaison",
            "4": "National NOC Analyst"
        }
        
    def select_role(self):
        print("\nAvailable Roles:")
        for key, role in self.roles.items():
            print(f"{key}. {role}")
        while True:
            choice = input("\nSelect role (1-4): ").strip()
            if choice in self.roles:
                self.role = self.roles[choice]
                break
            print("Invalid selection. Please try again.")

    def show_login(self):
        print("\033[2J\033[H")  # Clear screen
        print("UNIX Time-Sharing System V7 Release 1.0")
        print("Bell Laboratories")
        print(f"\nLoad average: 1.15, 0.87, 0.67")
        print(f"{self.hostname} login: ", end='', flush=True)
        self.username = input()
        print("Password: ", end='', flush=True)
        input()  # Password simulation
        
        self.select_role()
        
        print("\033[2J\033[H")  # Clear screen
        print("Bell System UNIX/TS 1.0")
        print("Internal Use Only - AT&T Proprietary")
        print(f"Last login: {datetime.now().strftime('%a %b %d %H:%M:%S')}")
        print(f"Role: {self.role}\n")
        
    def generate_event(self):
        events = {
            "UNIX Systems Operator": [
                "NOTICE: High load average detected on node RIDGE-X1",
                "WARNING: /usr/spool/mail approaching capacity",
                "ALERT: uucp connection failure with remote site"
            ],
            "Switching Station Technician": [
                "SVC-07: Route Failure Detected on RIDGE-X1",
                "TRUNK-ALERT: Line test failed on circuit 2317",
                "SW-WARNING: Switching matrix reports timing drift"
            ],
            "Field Support Liaison": [
                "TICKET-NEW: Site RIDGE-X1 reports trunk failure",
                "UPDATE: Field tech dispatched to location",
                "MEMO: Maintenance window scheduled for 0200"
            ],
            "National NOC Analyst": [
                "CRITICAL: Multiple trunk failures in NE sector",
                "ALERT: Weather impact on microwave links",
                "WARNING: Power grid instability detected"
            ]
        }
        
        if random() < 0.2:  # 20% chance of event
            print("\n" + choice(events.get(self.role, [])) + "\n")

    def handle_command(self, cmd):
        if cmd.startswith("cd "):
            dir = cmd[3:].strip()
            if dir in ["bin", "etc", "lib", "tmp", "dev", "home", "usr", "var"]:
                self.current_dir = f"/{dir}"
                return
            print("cd: No such file or directory")
        elif cmd == "uname":
            print("UNIX/TS 1.0")
        elif cmd == "df":
            print("Filesystem  512-blocks  Used   Available  Capacity")
            print("/dev/rk0      192312   143219   49093     75%")
        elif cmd == "uptime":
            print(" 10:32am  up  3:47,  4 users,  load average: 1.15, 0.87, 0.67")
        elif cmd == "help":
            print("\nBell System UNIX Help")
            print("-----------------")
            print("This is a simulation of a PDP-11 running UNIX V7.")
            print("The PDP-11 was the primary computer used at Bell Labs")
            print("where UNIX was developed in the 1970s.")
            print("\nAvailable commands:")
            print("  who     - Show current user")
            print("  pwd     - Print working directory")
            print("  date    - Show current date/time")
            print("  ps      - List processes")
            print("  ls      - List files")
            print("  cd      - Change directory")
            print("  df      - Disk free space")
            print("  uname   - System information")
            print("  uptime  - Show uptime")
            print("  mail    - Read mail messages")
            print("  uucp    - UUCP status and commands")
            print("  uuname  - Show UUCP network nodes")
            print("  exit    - Exit terminal")
        elif cmd == "who":
            print(f"{self.username}  tty1  {datetime.now().strftime('%b %d %H:%M')}")
        elif cmd == "pwd":
            print(self.current_dir)
        elif cmd == "date":
            print(datetime.now().strftime('%a %b %d %H:%M:%S EDT %Y'))
        elif cmd == "ps":
            print("  PID TTY  TIME CMD")
            print("  123 tty1  0:01 sh")
            print("  456 tty1  0:00 ps")
        elif cmd == "ls":
            print("bin    etc    lib    tmp")
            print("dev    home   usr    var")
        elif cmd == "mail":
            print(f"\nBellMail version 2.3")
            print(f"Mail directory: /usr/spool/mail/{self.username}")
            print("\nMessages:")
            for i, msg in enumerate(self.mail_messages, 1):
                print(f"{i}) From: {msg['from']} Subject: {msg['subject']}")
        elif cmd == "uucp":
            print("UUCP Subsystem Status")
            print("=====================")
            print("Active transfers:")
            print("eagle!/usr/spool/news -> pdp11!/usr/spool/news")
            print("research!/usr/src -> pdp11!/usr/src")
        elif cmd == "uuname":
            print("Known UUCP nodes:")
            for node in self.uucp_nodes:
                print(f"{node}")
        elif cmd.startswith("trunk"):
            parts = cmd.split()
            if len(parts) == 1:
                print("Usage: trunk [status|test|reset|log]")
            elif parts[1] == "status":
                print("Circuit Status Report")
                print("--------------------")
                print("2317: FAILED - Timing sync error")
                print("2318: OK - Operating normally")
                print("2319: OK - Operating normally")
            elif parts[1] == "test" and len(parts) > 2:
                print(f"Running diagnostic on circuit {parts[2]}...")
                print("Test results: Timing synchronization failure")
                print("Recommended action: Reset circuit")
            elif parts[1] == "reset" and len(parts) > 2:
                print(f"Resetting circuit {parts[2]}...")
                print("Circuit reset complete")
                print("Status: OK - Operating normally")
            elif parts[1] == "log":
                print("Recent trunk events:")
                print("04/24 18:42 - Circuit 2317 timing failure")
                print("04/24 18:45 - Reset attempt on 2317")
                print("04/24 18:46 - Circuit 2317 restored")
        elif cmd.startswith("switch"):
            parts = cmd.split()
            if len(parts) == 1:
                print("Usage: switch [status|sync|drift|calibrate]")
            elif parts[1] == "status":
                print("Switch Matrix Status")
                print("-------------------")
                print("Primary timing: Active")
                print("Backup timing: Standby")
                print("Drift: 47ms")
            elif parts[1] == "sync":
                print("Synchronizing switch matrix...")
                print("Timing synchronized")
            elif parts[1] == "drift":
                print("Current drift values:")
                print("Primary: +47ms")
                print("Secondary: +52ms")
                print("Tertiary: +41ms")
            elif parts[1] == "calibrate":
                print("Calibrating switch matrix...")
                print("Setting timing baseline...")
                print("Calibration complete")
        elif cmd == "emergency":
            print("EMERGENCY PROCEDURE INITIATED")
            print("Contact NOC immediately at x2317")
            print("Log incident in /usr/adm/errors")
        self.generate_event()

    def run(self):
        self.show_login()
        while True:
            print(f"$ ", end='', flush=True)
            cmd = input().strip()
            if cmd == "exit":
                break
            self.handle_command(cmd)

if __name__ == "__main__":
    terminal = UnixTerminal()
    terminal.run()
