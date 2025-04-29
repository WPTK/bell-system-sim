import os
from datetime import datetime
import time
from random import choice, random

class UnixTerminal:
    def __init__(self):
        self.username = ""
        self.hostname = "pdp11"
        self.diagnostics = []
        self.paper_tape_buffer = []
        self.hardware_health = {
            "cpu": 100,
            "memory": 100,
            "disk": 100,
            "tape": 100
        }
        self.banner = """
        ==================================
           BELL SYSTEM UNIX/TS RELEASE 7
        ==================================
                    ,@@@@@@@,
                ,@@@@@@/@@,  .@@@@@,
            ,@@@@@@@@@@@@  @@@@@@@@@@,
         ,@@@@@@@@@@@@@@  @@@@@@@@@@@@@
       ,@@@@@@@@@@@@@@@  @@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@  @@@@@@@@@@@@@@@@@
     @@@@@@@@@@@@@@@&  &@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@@&  &@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@@&  &@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@@(  ,@@@@@@@@@@@@@@@@@@@@@
    @@@@@@@@@@@@(  ,@@@@@@@@@@@@@@@@@@@@@@
     @@@@@@@@@@@   @@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@&  &@@@@@@@@@@@@@@@@@@@/
       *@@@@@@  @@@@@@@@@@@@@@@@@@@@
          @@@  @@@@@@@@@@@@@@@@@@
              @@@@@@@@@@@@@@@@
                 AT&T BELL
        """
        self.system_status = {
            "cpu_temp": "Normal",
            "memory": "OK",
            "disk": "OK",
            "network": "OK"
        }
        self.current_dir = "/usr/home"
        self.role = None
        self.error_log = []
        self.incidents = []
        self.incident_counter = 1000
        self.work_items = {
            "UNIX Systems Operator": [
                "Check UUCP queues for stuck jobs",
                "Monitor disk space on /usr partition",
                "Review system logs for errors",
                "Backup /usr/spool directory"
            ],
            "Switching Station Technician": [
                "Test trunk group 2317-2320",
                "Calibrate MF receivers",
                "Check crosspoint resistance",
                "Verify timing synchronization"
            ],
            "Field Support Liaison": [
                "Follow up on RIDGE-X1 outage",
                "Update maintenance schedule",
                "Contact field team about trunk 2317",
                "Review emergency procedures"
            ],
            "National NOC Analyst": [
                "Monitor NE sector trunk status",
                "Update incident reports",
                "Check weather alerts",
                "Review power grid status"
            ]
        }
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

    def log_error(self, error_msg):
        timestamp = time.strftime("%m/%d %H:%M")
        self.error_log.append(f"{timestamp} - {error_msg}")

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
            error_msg = choice(events.get(self.role, []))
            print(f"\n{error_msg}\n")
            self.log_error(error_msg)
            print("(Use 'errors' command to view error log)")

    def handle_command(self, cmd):
        parts = cmd.split()
        base_cmd = parts[0] if parts else ""

        if base_cmd == "help":
            print("\nBell System UNIX Help")
            print("===================")
            print("UNIX/TS Version 7 (V7)")
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
            print("  testboard     - Access 1-141A1 test board interface")
            print("  test <cmd>    - Run tests (loop|tone)")
            print("  toll          - Show 5ESS toll switch metrics")
            print("  crossbar      - Display crossbar switch status")
            print("  dialtone      - Test local circuit conditions")

            print("\nNetwork Services:")
            print("  mail          - Read mail messages")
            print("  uucp          - UUCP operations")
            print("  uuname        - List UUCP network nodes")

            print("\nEmergency:")
            print("  emergency     - Initiate emergency procedures")
            print("  exit          - Exit terminal")

        elif base_cmd == "ls":
            print("total 3")
            print("drwxr-xr-x  2 root     system    512 Apr 24 10:17 bin")
            print("drwxr-xr-x  2 root     system    512 Apr 24 10:17 etc")
            print("drwxr-xr-x  2 root     system    512 Apr 24 10:17 usr")
        elif base_cmd == "pwd":
            print(self.current_dir)
        elif base_cmd == "cd":
            if len(parts) > 1:
                self.current_dir = parts[1]
        elif base_cmd == "date":
            print(time.strftime("%a %b %d %H:%M:%S EDT %Y"))
        elif base_cmd == "who":
            print(f"{self.username}\ttty01\t{time.strftime('%b %d %H:%M')}")
        elif base_cmd == "ps":
            print("  PID TTY  STAT  TIME COMMAND")
            print("  123 tty1  R     0:01 sh")
            print("  456 tty1  R     0:00 ps")
            print("  789 tty1  S     0:05 cron")
        elif cmd == "uname":
            print("UNIX/TS 1.0")
        elif cmd == "df":
            print("Filesystem  512-blocks  Used   Available  Capacity")
            print("/dev/rk0      192312   143219   49093     75%")
        elif cmd == "uptime":
            print(" 10:32am  up  3:47,  4 users,  load average: 1.15, 0.87, 0.67")
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
        elif cmd == "chmod":
            if len(parts) < 3:
                print("usage: chmod mode file ...")
                return
            print(f"Changed mode of {parts[2]}")
        elif cmd == "chown":
            if len(parts) < 3:
                print("usage: chown owner file ...")
                return
            print(f"Changed owner of {parts[2]}")
        elif cmd == "cron":
            print("usage: /usr/lib/cron")
            print("daemon active, /usr/lib/crontab exists")
        elif cmd == "fsck":
            print("Checking /dev/rk0 ...")
            print("/dev/rk0: file system clean, 384 files, 143219 used, 49093 free")
        elif cmd == "getty":
            print("getty: /dev/tty1 started")
        elif cmd == "grep":
            if len(parts) < 2:
                print("usage: grep pattern [file] ...")
                return
            print("grep: pattern not found")
        elif cmd == "kill":
            if len(parts) < 2:
                print("usage: kill [-9] pid ...")
                return
            print(f"kill: {parts[1]}: No such process")
        elif cmd == "login":
            print("login: Permission denied")
        elif cmd == "lpd":
            print("line printer daemon active")
        elif cmd == "mount":
            print("/dev/rk0 on / type rk05 (rw)")
        elif cmd == "passwd":
            print("Changing password for {self.username}")
            print("Permission denied")
        elif cmd == "ps":
            print("  PID TTY  STAT  TIME COMMAND")
            print("  123 tty1  R     0:01 sh")
            print("  456 tty1  R     0:00 ps")
            print("  789 tty1  S     0:05 cron")
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
            print("5ESS Toll Switch Status")
            print("---------------------")
            print("Active trunk groups: 14")
            print("Blocked trunks: 2")
            print("CCS load: 27.4")
            print("Grade of Service: 0.01")
            print("MF receivers: 12/16 idle")
            print("CAMA position: Active")
            print("E&M signaling: Normal")
        elif cmd == "testboard":
            print("1-141A1 Test Board Interface")
            print("--------------------------")
            print("Line conditions:")
            print("Tip-Ring voltage: -48.2V DC")
            print("Loop current: 23mA")
            print("Longitudinal balance: 60dB")
            print("Background noise: -82dBm")
            print("Type 'test loop' for loop test")
            print("Type 'test tone' for test tone")
        elif cmd.startswith("test"):
            parts = cmd.split()
            if len(parts) > 1:
                if parts[1] == "loop":
                    print("Running 1004Hz loop test...")
                    print("Loss: -1.5dB")
                    print("Noise metallic: 20dBrnc")
                    print("Noise to ground: 50dBrnc")
                elif parts[1] == "tone":
                    print("Sending 1004Hz test tone...")
                    print("Level: 0dBm")
                    print("Duration: 30 seconds")
        elif cmd == "tape":
            print("Paper Tape Reader Interface")
            print("==========================")
            print("1. Read tape")
            print("2. Punch tape")
            print("3. Load program")
            choice = input("Select operation: ")
            if choice == "1":
                print("*whirring noise*")
                time.sleep(1)
                print("Reading paper tape...")
                time.sleep(2)
                if self.paper_tape_buffer:
                    print("Data:", "".join(self.paper_tape_buffer))
                else:
                    print("No data on tape")
            elif choice == "2":
                data = input("Enter data to punch: ")
                print("*mechanical clicking*")
                time.sleep(1)
                print("Punching tape...")
                time.sleep(2)
                self.paper_tape_buffer = list(data)
                print("Data punched successfully")
            elif choice == "3":
                print("*loading sounds*")
                time.sleep(2)
                print("Load failed - Check reader alignment")

        elif cmd == "hardware":
            print("\nHardware Status Report")
            print("=====================")
            for component, health in self.hardware_health.items():
                status = "OK" if health > 80 else "WARNING" if health > 50 else "CRITICAL"
                print(f"{component.upper()}: {health}% ({status})")
                if random.random() < 0.1:  # 10% chance of degradation
                    self.hardware_health[component] = max(0, health - random.randint(5, 15))

        elif cmd == "crossbar":
            print("Crossbar Switch Status")
            print("--------------------")
            print("Markers: 4/6 available")
            print("Junctor groups: Normal")
            print("Line links: Operating")
            print("Trunk links: Operating")
        elif cmd == "getwork":
            if self.role in self.work_items:
                print(f"\nPending work items for {self.role}:")
                print("================================")
                for i, item in enumerate(self.work_items[self.role], 1):
                    print(f"{i}. {item}")
            else:
                print("No work items found for your role.")
        elif cmd == "worklist":
            print("\nAll work categories:")
            print("==================")
            for role in self.work_items:
                print(f"\n{role}:")
                print("-" * len(role))
                for item in self.work_items[role]:
                    print(f"* {item}")
        elif cmd == "errors":
            if self.error_log:
                print("\nSystem Error Log:")
                print("================")
                for error in self.error_log[-10:]:  # Show last 10 errors
                    print(error)
            else:
                print("No errors logged.")
        elif cmd == "diagnose":
            print("\nSystem Diagnostics:")
            print("=================")
            for component, status in self.system_status.items():
                print(f"{component.upper()}: {status}")
            if self.diagnostics:
                print("\nRecent Diagnostics:")
                for diag in self.diagnostics[-5:]:
                    print(diag)
        elif cmd == "fix":
            component = input("Enter component to repair (cpu/memory/disk/network): ").lower()
            if component in self.system_status:
                print(f"Attempting repair of {component}...")
                time.sleep(1)
                self.system_status[component] = "OK"
                self.diagnostics.append(f"{time.strftime('%m/%d %H:%M')} - Repaired {component}")
                print("Repair complete")
            else:
                print("Invalid component")
        elif cmd.startswith("incident"):
            parts = cmd.split()
            if len(parts) == 1:
                print("Usage: incident [create|list|update|close] [id] [status]")
            elif parts[1] == "create":
                desc = input("Enter incident description: ")
                self.incidents.append({
                    "id": self.incident_counter,
                    "description": desc,
                    "status": "OPEN",
                    "created": time.strftime("%m/%d %H:%M"),
                    "owner": self.username
                })
                print(f"Created incident #{self.incident_counter}")
                self.incident_counter += 1
            elif parts[1] == "list":
                if not self.incidents:
                    print("No active incidents")
                else:
                    print("\nActive Incidents:")
                    print("================")
                    for inc in self.incidents:
                        print(f"#{inc['id']} - {inc['status']}")
                        print(f"Owner: {inc['owner']}")
                        print(f"Created: {inc['created']}")
                        print(f"Description: {inc['description']}")
                        print("---")
            elif parts[1] == "update" and len(parts) >= 4:
                inc_id = int(parts[2])
                new_status = parts[3].upper()
                for inc in self.incidents:
                    if inc['id'] == inc_id:
                        inc['status'] = new_status
                        print(f"Updated incident #{inc_id} status to {new_status}")
                        break
            elif parts[1] == "close" and len(parts) >= 3:
                inc_id = int(parts[2])
                for inc in self.incidents:
                    if inc['id'] == inc_id:
                        inc['status'] = "CLOSED"
                        print(f"Closed incident #{inc_id}")
                        break
        self.generate_event()

    def show_login(self):
        self.show_boot_sequence()
        self.show_intro()
        print(self.banner)
        print("\nUNIX Time-Sharing System V7 Release 1.0")
        print("Bell Laboratories")
        print("\n*disk drive spinning up*")
        time.sleep(1)
        print(f"\nLoad average: 1.15, 0.87, 0.67")
        print(f"{self.hostname} login: ", end='', flush=True)
        self.username = input().strip()
        print("Password: ", end='', flush=True)
        input()  # Password simulation

        self.select_role()

        print("\033[2J\033[H")  # Clear screen
        print("Bell System UNIX/TS 1.0")
        print("Internal Use Only - AT&T Proprietary")
        print(f"Last login: {datetime.now().strftime('%a %b %d %H:%M:%S')}")
        print(f"Role: {self.role}\n")


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