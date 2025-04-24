
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
        print("UNIX Time-Sharing System V7")
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
        if cmd == "who":
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
