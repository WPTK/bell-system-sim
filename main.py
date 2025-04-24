
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

    def show_boot_sequence(self):
        print("\033[2J\033[H")  # Clear screen
        time.sleep(1)
        print("PDP-11/70 BOOT ROM V2.7")
        time.sleep(0.5)
        print("MEMORY SIZE = 1024K")
        time.sleep(0.5)
        print("MEMORY TEST IN PROGRESS...")
        for i in range(0, 1024, 256):
            print(f"TESTING {i}K - {min(i+256, 1024)}K", end='\r')
            time.sleep(0.3)
        print("\nMEMORY TEST COMPLETE")
        time.sleep(0.5)
        print("\nBOOTING FROM RK05 DISK DRIVE...")
        time.sleep(1)
        print("LOADING UNIX KERNEL...")
        time.sleep(1.5)
        print("\033[2J\033[H")  # Clear screen

    def show_intro(self):
        print("""
BELL SYSTEM UNIX/TS SIMULATOR
============================

This simulator recreates a UNIX Time-Sharing System environment circa 1979,
as used within AT&T Bell System for telecommunications operations.

Available Roles:

1. UNIX Systems Operator
   Responsible for system maintenance, user management, and UUCP network operations.
   Primary tools: ps, df, who, uucp

2. Switching Station Technician
   Manages telephone switching equipment and trunk lines.
   Primary tools: trunk, switch, testboard, toll

3. Field Support Liaison
   Coordinates between field technicians and central office.
   Primary tools: trace, dialtone, emergency

4. National NOC Analyst
   Monitors network-wide operations and manages critical incidents.
   Primary tools: trunk, emergency, switch

This is a historical simulation for educational purposes.
All commands and behaviors are based on original AT&T documentation.
""")
        time.sleep(3)

    def show_login(self):
        self.show_boot_sequence()
        self.show_intro()
        print("\nUNIX Time-Sharing System V7 Release 1.0")
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
                "XBAR: Crosspoint failure on matrix 3B",
                "TOLL: MF receiver group reports high twist",
                "CO-7: Loss of SF signaling on trunk 2317",
                "ESS: Call processing degraded, H-timer expired",
                "TRUNK: Phase jitter exceeds 15 degrees"
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
            print("===================")
            print("This is a simulation of a PDP-11 running UNIX V7.")
            print("\nSystem Commands:")
            print("  uname         - Show system information")
            print("  uptime        - Display system uptime and load")
            print("  ps            - List running processes")
            print("  df            - Show disk free space")
            
            print("\nFile Operations:")
            print("  ls            - List directory contents")
            print("  cd <dir>      - Change to directory")
            print("  pwd           - Print working directory")
            
            print("\nUser Information:")
            print("  who           - Show current user session")
            print("  date          - Display current date/time")
            
            print("\nTelecommunications:")
            print("  trunk <cmd>   - Trunk operations (status|test|reset|log)")
            print("  switch <cmd>  - Switch control (status|sync|drift|calibrate)")
            print("  trace <circ>  - Trace call path for circuit")
            print("  testboard     - Access test board interface")
            print("  toll          - Show toll switch metrics")
            print("  dialtone      - Test local circuit conditions")
            
            print("\nNetwork Services:")
            print("  mail          - Read mail messages")
            print("  uucp          - UUCP status and transfers")
            print("  uuname        - List UUCP network nodes")
            
            print("\nEmergency:")
            print("  emergency     - Initiate emergency procedures")
            print("  exit          - Exit terminal")
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
        elif cmd == "dialtone":
            print("Testing dialtone on local circuits...")
            print("Circuit 1: -48V DC, clean")
            print("Circuit 2: -47.8V DC, noise detected")
            print("Circuit 3: -48.2V DC, clean")
            print("Cross-talk level: -70dB")
        elif cmd.startswith("trace"):
            parts = cmd.split()
            if len(parts) > 1:
                print(f"Tracing call path for circuit {parts[1]}...")
                print("MF tones detected: KP-0-2-1-2-ST")
                print("Route: CO -> tandem -> toll -> destination")
                print("Impedance: 600Ω nominal")
                print("Return loss: -26dB")
            else:
                print("Usage: trace <circuit>")
        elif cmd == "testboard":
            print("Test Board Interface v2.1")
            print("------------------------")
            print("Line conditions:")
            print("Tip-Ring voltage: -48.2V DC")
            print("Loop current: 23mA")
            print("Longitudinal balance: 60dB")
            print("Background noise: -82dBm")
        elif cmd == "emergency":
            print("EMERGENCY PROCEDURE INITIATED")
            print("Contact NOC immediately at x2317")
            print("Log incident in /usr/adm/errors")
        elif cmd == "toll":
            print("Toll Switch Status")
            print("-----------------")
            print("Active trunk groups: 14")
            print("Blocked trunks: 2")
            print("CCS load: 27.4")
            print("Grade of Service: 0.01")
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
