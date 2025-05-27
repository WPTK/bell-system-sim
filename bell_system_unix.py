#!/usr/bin/env python3
"""
Bell System UNIX V7 Terminal Simulation
Authentic AT&T Internal Operations Workstation (1978-1983)
Four Role Simulation: Systems Operator, Switching Technician, Field Liaison, NOC Analyst
"""

import os
import sys
import time
import random
from datetime import datetime, timedelta

class BellSystemTerminal:
    def __init__(self):
        self.current_directory = "/usr/users/sysop"
        self.username = "sysop"
        self.hostname = "bell-unix"
        self.shell = "/bin/sh"
        self.command_history = []
        self.role = None
        self.shift_events = []
        self.tickets = []
        self.current_shift = 1
        
        # Bell System specific environment
        self.roles = {
            "sysop": "UNIX Systems Operator",
            "switch": "Switching Station Technician", 
            "field": "Field Support Liaison",
            "noc": "National NOC Analyst"
        }
        
        # Bell System file system with authentic AT&T structure
        self.filesystem = {
            "/": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxr-xr-x", "size": 512, "files": ["bin", "dev", "etc", "lib", "tmp", "usr", "var", "att"]},
            "/bin": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxr-xr-x", "size": 1024, "files": ["sh", "ls", "cat", "ps", "who", "uucp", "mail", "wall", "write"]},
            "/usr": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxr-xr-x", "size": 2048, "files": ["bin", "lib", "users", "spool", "att"]},
            "/usr/bin": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxr-xr-x", "size": 2048, "files": ["trunk", "switch", "testboard", "toll", "trace", "dialtone", "emergency", "ticket"]},
            "/usr/users": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxr-xr-x", "size": 1024, "files": ["sysop", "switch", "field", "noc"]},
            "/usr/users/sysop": {"type": "dir", "owner": "sysop", "group": "bell", "mode": "drwx------", "size": 512, "files": ["mail", "tickets", "logs", ".profile"]},
            "/usr/spool": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxrwxrwx", "size": 1024, "files": ["uucp", "mail", "tickets"]},
            "/att": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxr-xr-x", "size": 1024, "files": ["switch", "network", "maintenance", "tickets"]},
            "/att/tickets": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxrwxrwx", "size": 2048, "files": ["open", "pending", "closed"]},
            "/var": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxr-xr-x", "size": 512, "files": ["log", "msg", "run"]},
            "/var/log": {"type": "dir", "owner": "root", "group": "bell", "mode": "drwxr-xr-x", "size": 1024, "files": ["system", "switch", "uucp", "mail"]},
            "/etc/passwd": {"type": "file", "owner": "root", "group": "bell", "mode": "-rw-r--r--", "size": 245, "content": "root::0:1:System Administrator:/root:/bin/sh\nsysop::100:10:UNIX Systems Operator:/usr/users/sysop:/bin/sh\nswitch::101:10:Switching Technician:/usr/users/switch:/bin/sh\nfield::102:10:Field Support Liaison:/usr/users/field:/bin/sh\nnoc::103:10:NOC Analyst:/usr/users/noc:/bin/sh\nuucp::5:5:UUCP Network:/usr/spool/uucp:/usr/lib/uucp/uucico\n"},
            "/etc/motd": {"type": "file", "owner": "root", "group": "bell", "mode": "-rw-r--r--", "size": 387, "content": "AT&T Bell System UNIX V7\nInternal Operations Terminal\n\nRestricted to authorized Bell System personnel only.\nAll activities are logged and monitored.\n\nCurrent system load: moderate\nNetwork status: operational\nSwitch centers online: 47/48\n\nFor technical support contact: BELLCORE-TECH\nFor emergency escalation use: emergency command\n\nShift briefings available in /att/tickets/briefing\n"}
        }
        
        # Authentic Bell System processes
        self.processes = [
            {"pid": 0, "command": "swapper", "tty": "?", "time": "0:00", "user": "root"},
            {"pid": 1, "command": "init", "tty": "?", "time": "0:02", "user": "root"},
            {"pid": 23, "command": "update", "tty": "?", "time": "0:01", "user": "root"},
            {"pid": 45, "command": "sh", "tty": "co", "time": "0:00", "user": "root"},
            {"pid": 67, "command": "getty", "tty": "01", "time": "0:00", "user": "root"},
            {"pid": 89, "command": "uucpd", "tty": "?", "time": "0:00", "user": "uucp"},
            {"pid": 102, "command": "cron", "tty": "?", "time": "0:00", "user": "root"},
            {"pid": 115, "command": "switchd", "tty": "?", "time": "0:03", "user": "switch"},
            {"pid": 127, "command": "mailq", "tty": "?", "time": "0:00", "user": "root"},
        ]
        
        # Bell System users with authentic roles
        self.users = [
            {"user": "sysop", "tty": "01", "login": "08:30", "location": "MURRAY_HILL"},
            {"user": "switch", "tty": "02", "login": "08:15", "location": "CENTRAL_OFF"},
            {"user": "noc", "tty": "03", "login": "07:45", "location": "BELLCORE"},
            {"user": "field", "tty": "04", "login": "09:00", "location": "FIELD_SUP"},
        ]
        
        # Initialize shift with authentic Bell System events
        self.generate_shift_events()

    def generate_shift_events(self):
        """Generate authentic Bell System operational events"""
        events = [
            {
                "time": "08:45",
                "type": "SYSTEM",
                "message": "Daily system backup initiated - /att/backup/daily_080283",
                "priority": "LOW"
            },
            {
                "time": "09:15", 
                "type": "SWITCH",
                "message": "RIDGE-X1 switching center reporting intermittent trunk failures",
                "priority": "MEDIUM",
                "ticket": "SW-2847"
            },
            {
                "time": "10:30",
                "type": "UUCP",
                "message": "Network mail queue backup detected - 47 messages pending",
                "priority": "MEDIUM"
            },
            {
                "time": "11:45",
                "type": "FIELD",
                "message": "Field tech dispatch required - Equipment failure at DOWNTOWN-CO",
                "priority": "HIGH",
                "ticket": "FD-1293"
            }
        ]
        self.shift_events = events

    def select_role(self):
        """Allow user to select their Bell System role"""
        print("\nBell System Internal Operations")
        print("Select your role:")
        print()
        print("1. UNIX Systems Operator")
        print("   - System maintenance and UUCP operations")
        print("   - Tools: ps, df, who, uucp, mail")
        print()
        print("2. Switching Station Technician") 
        print("   - Telephone switching equipment management")
        print("   - Tools: trunk, switch, testboard, toll")
        print()
        print("3. Field Support Liaison")
        print("   - Coordinate field technicians and central office")
        print("   - Tools: trace, dialtone, emergency, ticket")
        print()
        print("4. National NOC Analyst")
        print("   - Network operations and critical incident management")
        print("   - Tools: trunk, emergency, switch, ticket")
        print()
        
        while True:
            choice = input("Enter role number (1-4): ").strip()
            if choice == "1":
                self.username = "sysop"
                self.role = "sysop"
                self.current_directory = "/usr/users/sysop"
                break
            elif choice == "2":
                self.username = "switch"
                self.role = "switch" 
                self.current_directory = "/usr/users/switch"
                break
            elif choice == "3":
                self.username = "field"
                self.role = "field"
                self.current_directory = "/usr/users/field"
                break
            elif choice == "4":
                self.username = "noc"
                self.role = "noc"
                self.current_directory = "/usr/users/noc"
                break
            else:
                print("Invalid selection. Please enter 1-4.")

    def show_shift_briefing(self):
        """Display shift briefing based on role"""
        briefings = {
            "sysop": """
=== SHIFT BRIEFING - UNIX Systems Operator ===
Date: March 10, 1983  Shift: Day (08:00-16:00)

HANDOFF FROM NIGHT SHIFT:
- System load normal, all daemons running
- UUCP mail queue processed, 12 messages routed
- No critical alerts overnight

TODAY'S PRIORITIES:
1. Monitor system performance (df, ps commands)
2. Process incoming UUCP mail queue
3. Maintain user accounts and permissions
4. Backup verification at 14:00

CONTACT INFO:
- Supervisor: BELLCORE-SUP ext 4421
- Night shift: NIGHT-OPS ext 4455
""",
            "switch": """
=== SHIFT BRIEFING - Switching Station Technician ===
Date: March 10, 1983  Shift: Day (08:00-16:00)

HANDOFF FROM NIGHT SHIFT:
- All switching centers operational
- Minor trunk issues at RIDGE-X1 (monitoring)
- Scheduled maintenance DOWNTOWN-CO at 15:00

TODAY'S PRIORITIES:
1. Monitor trunk performance (trunk status)
2. Run scheduled line tests (testboard)
3. Handle switching alarms and diagnostics
4. Coordinate with field techs on equipment issues

EQUIPMENT STATUS:
- 1A ESS: 47/48 centers online
- 5ESS: All centers operational
- Test equipment: Available

CONTACT INFO:
- Central Office: CO-DISPATCH ext 5511
- Field Support: FIELD-SUP ext 5522
""",
            "field": """
=== SHIFT BRIEFING - Field Support Liaison ===
Date: March 10, 1983  Shift: Day (08:00-16:00)

HANDOFF FROM NIGHT SHIFT:
- 3 pending field dispatches
- Equipment delivery scheduled for MIDTOWN-CO
- Weather advisory: possible storms this PM

TODAY'S PRIORITIES:
1. Assign pending tickets to field technicians
2. Coordinate equipment deliveries and installations
3. Monitor field tech locations and status
4. Handle emergency dispatches

PENDING TICKETS:
- FD-1291: Cable fault WESTSIDE-CO (assigned)
- FD-1292: Power supply replacement needed
- FD-1293: Equipment failure DOWNTOWN-CO (urgent)

CONTACT INFO:
- Field Supervisor: FIELD-MGR ext 6633
- Emergency Dispatch: EMERGENCY ext 6611
""",
            "noc": """
=== SHIFT BRIEFING - National NOC Analyst ===
Date: March 10, 1983  Shift: Day (08:00-16:00)

HANDOFF FROM NIGHT SHIFT:
- Network integrity: 99.7% operational
- No major outages or incidents
- Routine maintenance window at 02:00 completed

TODAY'S PRIORITIES:
1. Monitor multi-state trunk performance
2. Coordinate response to major incidents
3. Maintain communication with regional centers
4. Weather monitoring (storm system approaching)

NETWORK STATUS:
- East Coast: Operational
- Central Region: Operational  
- West Coast: Operational
- Satellite links: All nominal

CONTACT INFO:
- Regional NOCs: NOC-REGIONAL ext 7711
- Emergency Coordinator: NOC-EMERGENCY ext 7799
"""
        }
        
        if self.role in briefings:
            print(briefings[self.role])

    # Bell System specific commands
    def cmd_trunk(self, args):
        """Trunk status and management command"""
        if not args:
            return """Trunk Status Report - Bell System Network
Time: {time}

Trunk Group    Status    Traffic   Alarms
TG-001-NYC     ACTIVE    67%       NONE
TG-002-BOS     ACTIVE    45%       NONE  
TG-003-PHI     ACTIVE    78%       NONE
TG-004-WAS     ACTIVE    23%       MINOR
TG-005-CHI     ACTIVE    89%       NONE
TG-006-DET     MAINT     0%        SCHED
TG-007-STL     ACTIVE    34%       NONE

Total Active Trunks: 847/920
System Load: 63% (NORMAL)

Use 'trunk detail <group>' for detailed analysis
Use 'trunk test <group>' to initiate diagnostics""".format(time=datetime.now().strftime("%H:%M"))
        
        elif args[0] == "detail" and len(args) > 1:
            group = args[1].upper()
            return f"""Detailed Trunk Analysis - {group}
Last Updated: {datetime.now().strftime("%H:%M:%S")}

Circuit Details:
- Primary Path: OPERATIONAL
- Backup Path: STANDBY
- Error Rate: 0.002% (EXCELLENT)
- Signal Level: -12dBm (NOMINAL)
- Last Test: 07:30 (PASSED)

Recent Activity:
07:15 - Routine test completed
06:45 - Traffic load peak: 89%
06:30 - Automatic failover test PASSED

Recommendations: NONE"""
        
        elif args[0] == "test" and len(args) > 1:
            group = args[1].upper()
            return f"""Initiating trunk test for {group}...
Test sequence started at {datetime.now().strftime("%H:%M:%S")}

Phase 1: Signal continuity.......... PASS
Phase 2: Noise level analysis....... PASS  
Phase 3: Crosstalk measurement...... PASS
Phase 4: Timing verification........ PASS

Test completed successfully.
Results logged to /att/network/tests/{group.lower()}_{datetime.now().strftime("%m%d")}.log"""

        return "trunk: invalid option. Use 'trunk', 'trunk detail <group>', or 'trunk test <group>'"

    def cmd_switch(self, args):
        """Switching center management command"""
        if not args:
            return """Switching Center Status
Updated: {time}

Center ID    Type    Status     Load    Alarms
RIDGE-X1     1AESS   ACTIVE     78%     MINOR
DOWNTOWN     5ESS    ACTIVE     45%     NONE
MIDTOWN      1AESS   ACTIVE     67%     NONE
WESTSIDE     5ESS    ACTIVE     23%     NONE
EASTGATE     1AESS   MAINT      0%      SCHED
NORTHEND     5ESS    ACTIVE     89%     NONE

Overall System Health: OPERATIONAL
Call Completion Rate: 99.4%

Use 'switch status <center>' for detailed information
Use 'switch alarm <center>' to view alarms""".format(time=datetime.now().strftime("%H:%M"))
        
        elif args[0] == "status" and len(args) > 1:
            center = args[1].upper()
            return f"""Switch Center Status - {center}
Query Time: {datetime.now().strftime("%H:%M:%S")}

Equipment Status:
- Central Processor: OPERATIONAL
- Memory Modules: ALL ACTIVE
- Trunk Interfaces: 23/24 ACTIVE
- Line Interfaces: 1847/1920 ACTIVE

Performance Metrics:
- Call Attempts: 15,847 (last hour)
- Successful Calls: 15,762 (99.5%)
- Average Setup Time: 1.2 seconds
- System Load: 67%

Last Maintenance: March 8, 02:00-04:00
Next Scheduled: March 15, 02:00-04:00"""

        elif args[0] == "alarm" and len(args) > 1:
            center = args[1].upper()
            if center == "RIDGE-X1":
                return """Active Alarms - RIDGE-X1
Priority: MINOR

Alarm ID: AL-4472
Time: 09:15:33
Type: TRUNK_DEGRADED  
Description: Intermittent failures on trunk group TG-004
Action: Field technician dispatched
Status: PENDING

No other active alarms."""
            else:
                return f"No active alarms for {center}"

        return "switch: invalid option. Use 'switch', 'switch status <center>', or 'switch alarm <center>'"

    def cmd_testboard(self, args):
        """Line testing equipment command"""
        if not args:
            return """Test Board Status
Available Test Equipment:

TB-01: Line Test Set     AVAILABLE
TB-02: Trunk Test Set    IN USE
TB-03: Tone Generator    AVAILABLE  
TB-04: Protocol Analyzer AVAILABLE
TB-05: Signal Generator  MAINTENANCE

Use 'testboard run <equipment> <target>' to start test
Use 'testboard results <test_id>' to view results"""
        
        elif args[0] == "run" and len(args) > 2:
            equipment = args[1]
            target = args[2]
            test_id = f"T{random.randint(1000,9999)}"
            return f"""Test initiated with {equipment.upper()}
Target: {target}
Test ID: {test_id}
Started: {datetime.now().strftime("%H:%M:%S")}

Running diagnostics...
Test will complete in approximately 3 minutes.
Use 'testboard results {test_id}' to check status."""

        elif args[0] == "results" and len(args) > 1:
            test_id = args[1]
            return f"""Test Results - {test_id}
Completed: {datetime.now().strftime("%H:%M:%S")}

Line Quality Assessment:
- Signal Strength: -8dBm (GOOD)
- Noise Level: -45dBm (EXCELLENT)
- Impedance: 600 ohms (NOMINAL)
- Frequency Response: FLAT
- Crosstalk: MINIMAL

Overall Result: PASS
Recommendation: Line suitable for service

Report saved to /att/switch/tests/{test_id.lower()}.rpt"""

        return "testboard: invalid option"

    def cmd_toll(self, args):
        """Toll switching and billing command"""
        return """Toll Switch Status
Last Updated: {time}

Active Toll Calls: 1,247
Queue Depth: 23 calls
Average Hold Time: 14 seconds

Revenue Summary (Today):
- Interstate Calls: $14,572.34
- Intrastate Calls: $8,934.12  
- International: $2,847.95
- Total: $26,354.41

Billing System: OPERATIONAL
Next Rate Period: {next_hour}:00

Use 'toll summary' for detailed statistics""".format(
    time=datetime.now().strftime("%H:%M"),
    next_hour=(datetime.now().hour + 1) % 24
)

    def cmd_trace(self, args):
        """Call tracing and routing analysis"""
        if not args:
            return "trace: requires phone number or circuit ID"
        
        target = args[0]
        return f"""Call Trace Analysis
Target: {target}
Trace ID: TR{random.randint(100,999)}
Time: {datetime.now().strftime("%H:%M:%S")}

Route Analysis:
Origin Switch: DOWNTOWN-5ESS
Destination: {target}
Route Type: DIRECT_TRUNK

Path Verification:
Hop 1: DOWNTOWN -> TG-003-PHI...... SUCCESS
Hop 2: TG-003-PHI -> MIDTOWN........ SUCCESS  
Hop 3: MIDTOWN -> DESTINATION....... SUCCESS

Call Quality:
- Signal Loss: 2.1dB (ACCEPTABLE)
- Echo Level: -35dB (GOOD)
- Delay: 45ms (NORMAL)

Status: TRACE_COMPLETE
Estimated Setup Time: 2.8 seconds"""

    def cmd_dialtone(self, args):
        """Dial tone testing and verification"""
        return """Dial Tone Test Results
Test Stations: 47/48 OPERATIONAL

Station Status Summary:
NYC-01: ACTIVE    BOS-02: ACTIVE    PHI-03: ACTIVE
WAS-04: ACTIVE    CHI-05: ACTIVE    DET-06: MAINT
STL-07: ACTIVE    

Signal Parameters:
- Frequency: 350Hz + 440Hz (STANDARD)
- Level: -13dBm (NOMINAL)
- Cadence: CONTINUOUS
- THD: 0.5% (EXCELLENT)

Problem Areas:
DET-06: Scheduled maintenance (Return: 15:30)

Overall System: 97.9% OPERATIONAL
Last Full Test: {time}""".format(time=datetime.now().strftime("%H:%M"))

    def cmd_emergency(self, args):
        """Emergency dispatch and escalation system"""
        if not args:
            return """Emergency Command Center
Status: STANDBY

Active Emergencies: 0
Standby Personnel: 12
Response Teams: 4 available

Emergency Levels:
1. MINOR    - Local equipment failure
2. MAJOR    - Service affecting multiple customers  
3. CRITICAL - Regional outage
4. DISASTER - Multi-state emergency

Use 'emergency alert <level> <description>' to create alert
Use 'emergency status' for current situation
Use 'emergency teams' for response team status"""
        
        elif args[0] == "alert" and len(args) > 2:
            level = args[1].upper()
            description = " ".join(args[2:])
            alert_id = f"EM{random.randint(100,999)}"
            return f"""EMERGENCY ALERT CREATED
Alert ID: {alert_id}
Level: {level}
Time: {datetime.now().strftime("%H:%M:%S")}
Description: {description}

Notification sent to:
- Emergency Coordinator
- Regional NOC
- Field Supervisor
- On-call Manager

Response team assignment: AUTOMATIC
Expected response time: 15 minutes

Alert logged in /att/emergency/{alert_id.lower()}.log"""

        elif args[0] == "status":
            return f"""Emergency Status Report
Generated: {datetime.now().strftime("%H:%M:%S")}

Current Situation: NORMAL
Active Alerts: 0
Resolved Today: 2

Recent Activity:
06:30 - Minor equipment failure resolved (EM847)
04:15 - Scheduled maintenance completed (EM845)

Personnel Status:
- Emergency Coordinator: ON_DUTY
- Field Teams: 4/4 AVAILABLE  
- NOC Coverage: FULL

Weather Advisory: Thunderstorms possible 14:00-18:00
Preparedness Level: NORMAL"""

        elif args[0] == "teams":
            return """Response Team Status
Last Updated: {time}

Team Alpha (ELECTRONICS):
Status: AVAILABLE
Location: CENTRAL_DEPOT
Personnel: 3/3
Equipment: FULL

Team Beta (SWITCHING):  
Status: AVAILABLE
Location: DOWNTOWN_CO
Personnel: 4/4
Equipment: FULL

Team Gamma (TRANSMISSION):
Status: AVAILABLE  
Location: WESTSIDE_CO
Personnel: 3/3
Equipment: FULL

Team Delta (POWER):
Status: AVAILABLE
Location: MOBILE_UNIT_1
Personnel: 2/2
Equipment: FULL

All teams at full readiness.""".format(time=datetime.now().strftime("%H:%M"))

        return "emergency: invalid option"

    def cmd_ticket(self, args):
        """Trouble ticket management system"""
        if not args:
            return """Trouble Ticket System
Current Status: {status}

Open Tickets: 23
Pending: 12  
Assigned: 8
Closed Today: 15

Priority Breakdown:
HIGH: 3 tickets
MEDIUM: 12 tickets  
LOW: 8 tickets

Use 'ticket list' to view all tickets
Use 'ticket show <id>' for ticket details
Use 'ticket create' to open new ticket
Use 'ticket assign <id> <tech>' to assign ticket""".format(
    status="OPERATIONAL" if datetime.now().hour < 17 else "NIGHT_MODE"
)
        
        elif args[0] == "list":
            return """Open Trouble Tickets

ID      Priority  Status    Description                    Assigned
------  --------  --------  ----------------------------   ----------
SW-2847 MEDIUM    PENDING   Trunk failures RIDGE-X1       UNASSIGNED
FD-1293 HIGH      ASSIGNED  Equipment failure DOWNTOWN-CO  TECH-47
NW-5512 LOW       PENDING   UUCP mail delay                UNASSIGNED  
PS-7734 MEDIUM    ASSIGNED  Power alarm MIDTOWN-CO        TECH-23
SW-2848 LOW       PENDING   Minor switching delay          UNASSIGNED

Use 'ticket show <id>' for full details"""

        elif args[0] == "show" and len(args) > 1:
            ticket_id = args[1].upper()
            if ticket_id == "SW-2847":
                return f"""Ticket Details: SW-2847
Created: {datetime.now().strftime("%m/%d/%Y %H:%M")}
Priority: MEDIUM
Status: PENDING
Category: SWITCHING

Description:
Intermittent trunk failures reported at RIDGE-X1 switching center.
Affecting approximately 12% of outbound calls on trunk group TG-004.
Customer complaints received regarding call setup delays.

Technical Details:
- Error Rate: 8.7% (normal <2%)
- Affected Circuits: 12 of 144
- Time Pattern: Peak hours only
- Test Results: Inconclusive

Actions Taken:
09:15 - Initial alarm received
09:20 - Remote diagnostics initiated  
09:30 - Field technician notified

Next Steps:
- Dispatch field tech for physical inspection
- Schedule trunk group testing
- Consider traffic rerouting if needed

Assigned To: UNASSIGNED
Target Resolution: 14:00"""

        elif args[0] == "create":
            new_id = f"TK{random.randint(1000,9999)}"
            return f"""New Ticket Created: {new_id}
Time: {datetime.now().strftime("%H:%M:%S")}

Please provide details via standard form.
Ticket logged in /att/tickets/open/{new_id.lower()}.tkt

Use 'ticket show {new_id}' to view details
Use 'ticket assign {new_id} <technician>' to assign"""

        elif args[0] == "assign" and len(args) > 2:
            ticket_id = args[1].upper()
            tech = args[2].upper()
            return f"""Ticket Assignment Updated
Ticket: {ticket_id}
Assigned To: {tech}
Time: {datetime.now().strftime("%H:%M:%S")}

Notification sent to assigned technician.
Assignment logged in ticket history."""

        return "ticket: invalid option"

    def cmd_uucp(self, args):
        """UUCP network mail and file transfer"""
        if not args:
            return f"""UUCP Network Status
Last Poll: {datetime.now().strftime("%H:%M")}

Connected Systems:
bellcore!unix     ACTIVE    Last: 08:45
attlab!research   ACTIVE    Last: 09:12  
btl!murray        ACTIVE    Last: 08:30
whippany!sys      ACTIVE    Last: 09:05

Mail Queue Status:
Outbound: 12 messages
Inbound: 3 messages  
Retry Queue: 2 messages

Use 'uucp queue' to view mail queue
Use 'uucp send <system> <file>' to queue transfer
Use 'uucp poll <system>' to force connection"""
        
        elif args[0] == "queue":
            return f"""UUCP Mail Queue
Updated: {datetime.now().strftime("%H:%M:%S")}

Outbound Messages:
bellcore!unix: 3 messages (next poll: 10:30)
attlab!research: 5 messages (next poll: 10:15)
btl!murray: 2 messages (next poll: 10:45)
whippany!sys: 2 messages (next poll: 10:20)

Inbound Messages:
From bellcore!unix: 2 pending delivery
From attlab!research: 1 pending delivery

Retry Queue:
bellcore!unix: 1 message (connection timeout)
attlab!research: 1 message (system busy)"""

        elif args[0] == "poll" and len(args) > 1:
            system = args[1]
            return f"""Polling {system}...
Connection established at {datetime.now().strftime("%H:%M:%S")}

Exchanging mail...
Sending: 3 messages
Receiving: 1 message

File transfers: 0 pending

Connection completed successfully.
Next automatic poll: {(datetime.now() + timedelta(minutes=30)).strftime("%H:%M")}"""

        return "uucp: invalid option"

    def run(self):
        """Main Bell System terminal session"""
        # Show Bell System banner
        print("\n" + "="*60)
        print("AT&T Bell System UNIX Version 7")
        print("Internal Operations Terminal")
        print("Murray Hill, New Jersey")
        print("="*60)
        print("\nRestricted to authorized Bell System personnel only.")
        print("All activities are logged and monitored.")
        print()
        
        # Role selection
        self.select_role()
        
        print(f"\nWelcome, {self.roles[self.role]}")
        print(f"Logged in as: {self.username}@{self.hostname}")
        print()
        
        # Show shift briefing
        self.show_shift_briefing()
        print()
        print("Type 'help' for available commands")
        print("Type 'exit' to logout")
        print()
        
        # Command loop
        try:
            while True:
                prompt = f"{self.hostname}:{self.current_directory}$ "
                try:
                    command = input(prompt)
                except EOFError:
                    print("\nlogout")
                    break
                
                result = self.execute_command(command)
                if result == "LOGOUT":
                    print("logout")
                    break
                elif result:
                    print(result)
                    
        except KeyboardInterrupt:
            print("\n^C")
            print("logout")

    def execute_command(self, command_line):
        """Execute Bell System commands"""
        if not command_line.strip():
            return ""
            
        self.command_history.append(command_line)
        parts = command_line.strip().split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Standard UNIX commands (simplified for Bell System context)
        if cmd == "exit" or cmd == "logout":
            return "LOGOUT"
        elif cmd == "help":
            return self.cmd_help()
        elif cmd == "ps":
            return self.cmd_ps()
        elif cmd == "who":
            return self.cmd_who()
        elif cmd == "ls":
            return self.cmd_ls(args)
        elif cmd == "pwd":
            return self.current_directory
        elif cmd == "date":
            return datetime.now().strftime("%a %b %d %H:%M:%S EST %Y")
        
        # Bell System specific commands
        elif cmd == "trunk":
            return self.cmd_trunk(args)
        elif cmd == "switch":
            return self.cmd_switch(args)
        elif cmd == "testboard":
            return self.cmd_testboard(args)
        elif cmd == "toll":
            return self.cmd_toll(args)
        elif cmd == "trace":
            return self.cmd_trace(args)
        elif cmd == "dialtone":
            return self.cmd_dialtone(args)
        elif cmd == "emergency":
            return self.cmd_emergency(args)
        elif cmd == "ticket":
            return self.cmd_ticket(args)
        elif cmd == "uucp":
            return self.cmd_uucp(args)
        else:
            return f"{cmd}: command not found"

    def cmd_help(self):
        """Show available commands based on role"""
        base_help = """Bell System UNIX V7 Commands:

Standard UNIX:
  ls      - list directory contents
  pwd     - print working directory
  ps      - show processes
  who     - show logged users
  date    - show current date/time
  help    - show this help
  exit    - logout

Bell System Operations:"""
        
        role_commands = {
            "sysop": """
  uucp    - UUCP network operations
  ticket  - trouble ticket system
  
Systems Operator Tools:
  ps      - monitor system processes
  who     - check user sessions
  uucp    - network mail management""",
            
            "switch": """
  trunk     - trunk status and testing
  switch    - switching center management
  testboard - line testing equipment
  toll      - toll switching status
  
Switching Technician Tools:
  trunk     - monitor trunk performance
  switch    - switching center diagnostics
  testboard - run line/equipment tests
  toll      - toll billing system""",
            
            "field": """
  trace     - call tracing and analysis
  dialtone  - dial tone testing
  emergency - emergency dispatch
  ticket    - field ticket management
  
Field Support Tools:
  trace     - analyze call routing
  emergency - emergency coordination
  ticket    - manage field dispatches""",
            
            "noc": """
  trunk     - network trunk monitoring  
  emergency - emergency management
  switch    - switching center status
  ticket    - incident management
  
NOC Analyst Tools:
  trunk     - monitor network performance
  emergency - coordinate emergency response
  switch    - oversee switching operations
  ticket    - manage critical incidents"""
        }
        
        return base_help + role_commands.get(self.role, "")

    def cmd_ps(self):
        """Show Bell System processes"""
        output = ["  PID TTY      TIME CMD"]
        for proc in self.processes:
            pid = str(proc['pid']).rjust(5)
            tty = proc['tty'].ljust(8)
            time_str = proc['time'].ljust(8)
            cmd = proc['command']
            output.append(f"{pid} {tty} {time_str} {cmd}")
        return '\n'.join(output)

    def cmd_who(self):
        """Show Bell System users"""
        output = []
        for user in self.users:
            output.append(f"{user['user']:<8} {user['tty']:<8} {user['login']:<8} ({user['location']})")
        return '\n'.join(output)

    def cmd_ls(self, args):
        """Simple ls command for Bell System"""
        path = self.current_directory
        if path in self.filesystem and 'files' in self.filesystem[path]:
            files = self.filesystem[path]['files']
            return '  '.join(files)
        return f"ls: {path}: No such file or directory"

if __name__ == "__main__":
    terminal = BellSystemTerminal()
    terminal.run()