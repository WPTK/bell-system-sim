#!/usr/bin/env python3
"""
Bell System UNIX V7 Terminal Simulation - Interactive Tutorial
============================================================

A standalone interactive tutorial for new users to learn the Bell System
terminal simulation. This script is completely separate from the main
simulation and provides step-by-step guided learning.

Run this tutorial BEFORE using the main Bell System simulation.
"""

import sys
import time

from .console import clear_screen
from typing import List


class BellSystemTutorial:
    """Interactive tutorial for Bell System terminal simulation"""

    def __init__(self):
        self.user_progress = {
            'steps_completed': 0,
            'commands_practiced': [],
            'role_selected': None
        }
        self.tutorial_steps = [
            'introduction',
            'role_selection',
            'basic_commands',
            'help_system',
            'event_system',
            'ticket_system',
            'specialized_commands',
            'graduation'
        ]

    def clear_screen(self):
        """Clear terminal screen"""
        clear_screen()

    def type_effect(self, text: str, delay: float = 0.03):
        """Display text with typewriter effect"""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()

    def wait_for_user(self, prompt: str = "Press Enter to continue...") -> str:
        """Wait for user input with custom prompt"""
        return input(f"\n{prompt} ").strip()

    def validate_input(self, user_input: str, expected: List[str],
                      case_sensitive: bool = False) -> bool:
        """Validate user input against expected responses"""
        if not case_sensitive:
            user_input = user_input.lower()
            expected = [exp.lower() for exp in expected]

        return user_input in expected

    def show_progress(self):
        """Display tutorial progress"""
        completed = self.user_progress['steps_completed']
        total = len(self.tutorial_steps)
        progress_bar = "█" * completed + "░" * (total - completed)

        print(f"\nTutorial Progress: [{progress_bar}] {completed}/{total} steps")

    def run(self):
        """Run the complete interactive tutorial"""
        self.clear_screen()
        print("=" * 70)
        print("     BELL SYSTEM UNIX V7 TERMINAL SIMULATION TUTORIAL")
        print("=" * 70)

        for step in self.tutorial_steps:
            method_name = f"step_{step}"
            if hasattr(self, method_name):
                getattr(self, method_name)()
                self.user_progress['steps_completed'] += 1
                self.show_progress()
            else:
                print(f"Tutorial step '{step}' not implemented.")

        self.show_completion_certificate()

    def step_introduction(self):
        """Introduction to Bell System simulation"""
        self.clear_screen()

        self.type_effect("""
WELCOME TO THE BELL SYSTEM UNIX V7 TERMINAL SIMULATION TUTORIAL
================================================================

This tutorial will teach you how to operate an authentic Bell System
workstation from the period 1978-1983, before the AT&T divestiture.

You'll learn to:
• Navigate the authentic UNIX V7 command structure
• Manage Bell System operational roles and responsibilities
• Handle network events, trouble tickets, and maintenance procedures
• Use period-accurate equipment and terminology

This tutorial takes approximately 15-20 minutes to complete.
""")

        response = self.wait_for_user("Are you ready to begin? (yes/no)")

        while not self.validate_input(response, ['yes', 'y']):
            if self.validate_input(response, ['no', 'n']):
                print("Tutorial cancelled. Run again when ready.")
                sys.exit(0)
            response = self.wait_for_user("Please enter 'yes' or 'no'")

        print("\n✅ Excellent! Let's begin your Bell System training...")

    def step_role_selection(self):
        """Learn about Bell System roles"""
        self.clear_screen()

        self.type_effect("""
STEP 1: UNDERSTANDING BELL SYSTEM OPERATIONAL ROLES
==================================================

The Bell System operated with specialized roles, each with specific
responsibilities and command access. Let's explore the 12 available roles:
""")

        roles = [
            "1. UNIX Systems Operator - Manages computer systems",
            "2. Switching Station Technician - Operates telephone switches",
            "3. Field Support Liaison - Customer service interface",
            "4. National NOC Analyst - Network monitoring center",
            "5. TSPS Operator - Traffic Service Position System",
            "6. Database Administrator - Manages customer databases",
            "7. Network Planning Engineer - Plans network capacity",
            "8. Customer Service Interface - Handles service orders",
            "9. Radio/Microwave Technician - Maintains transmission systems",
            "10. TNDS Analyst - Total Network Data System operations",
            "11. SARTS Technician - Special service testing",
            "12. Document Preparation Specialist - Technical documentation"
        ]

        for role in roles:
            print(f"   {role}")
            time.sleep(0.5)

        print("\nFor this tutorial, we'll use the Radio/Microwave Technician role")
        print("because it has comprehensive transmission system commands.")

        response = self.wait_for_user("Which role interests you most? (1-12)")

        try:
            role_num = int(response)
            if 1 <= role_num <= 12:
                self.user_progress['role_selected'] = role_num
                print(f"\n✅ Great choice! Role {role_num} selected for reference.")
            else:
                print("Invalid role number, but that's okay - this is just for learning!")
        except ValueError:
            print("That's not a number, but no worries - this is practice!")

    def step_basic_commands(self):
        """Practice basic UNIX commands"""
        self.clear_screen()

        self.type_effect("""
STEP 2: BASIC UNIX V7 COMMANDS
=============================

Let's practice the fundamental commands you'll use daily:

• help     - Show available commands
• man      - Display manual pages
• ps       - Show running processes
• who      - Display logged-in users
• date     - Show current date/time
• events   - View shift events
""")

        basic_commands = ['help', 'man', 'ps', 'who', 'date', 'events']

        for cmd in basic_commands:
            print(f"\nPractice typing: {cmd}")
            user_input = self.wait_for_user("Type the command")

            if user_input.lower() == cmd:
                print("✅ Perfect! Command typed correctly.")
                self.user_progress['commands_practiced'].append(cmd)
            else:
                print(f"❌ You typed '{user_input}', but the command was '{cmd}'")
                print("No worries - practice makes perfect!")

        commands_learned = len(self.user_progress['commands_practiced'])
        print(f"\n🎯 You successfully practiced {commands_learned}/{len(basic_commands)} commands!")

    def step_help_system(self):
        """Learn the help system"""
        self.clear_screen()

        self.type_effect("""
STEP 3: MASTERING THE HELP SYSTEM
=================================

The Bell System simulation has a comprehensive help system:

1. 'help' - Shows all available commands for your role
2. 'help <command>' - Shows specific command help
3. 'man <command>' - Full manual page with examples

Let's practice using help commands:
""")

        help_examples = [
            ("help", "Shows all available commands"),
            ("help radio", "Shows help for radio command"),
            ("man t1carrier", "Full manual for T1 carrier systems")
        ]

        for cmd, description in help_examples:
            print(f"\nCommand: {cmd}")
            print(f"Purpose: {description}")

            user_input = self.wait_for_user(f"Type: {cmd}")

            if user_input.lower() == cmd.lower():
                print("✅ Excellent! This would show:")
                if cmd == "help":
                    print("   → List of all commands for your role")
                elif "help radio" in cmd:
                    print("   → Radio system command options")
                elif "man" in cmd:
                    print("   → Complete manual page with examples")
            else:
                print(f"❌ You typed '{user_input}', try again!")

        print("\n💡 TIP: Always use 'help' when you're unsure about commands!")

    def step_event_system(self):
        """Learn about shift events"""
        self.clear_screen()

        self.type_effect("""
STEP 4: BELL SYSTEM SHIFT EVENTS
================================

During your shift, operational events occur that require attention:

• Events have unique IDs (EV-8001, EV-8002, etc.)
• Priority levels: CRITICAL, HIGH, MEDIUM, LOW
• You can view details and work on events

Key commands:
• events              - List all current events
• events detail EV-8001 - View specific event details
• events work EV-8001   - Start working on an event
• events priority HIGH  - Filter by priority level
""")

        # Simulate event interaction
        print("\nSIMULATED EVENT SCENARIO:")
        print("Event EV-8040: TH-3 microwave fade detected on NYC-WAS path")
        print("Priority: HIGH")
        print("Status: MONITORING")

        scenarios = [
            ("events", "List all events"),
            ("events detail EV-8040", "View event details"),
            ("events work EV-8040", "Start working the event")
        ]

        for cmd, purpose in scenarios:
            print(f"\nTo {purpose.lower()}, you would type: {cmd}")
            user_response = self.wait_for_user(f"Practice typing: {cmd}")

            if user_response.lower() == cmd.lower():
                print("✅ Perfect! This would:")
                if "detail" in cmd:
                    print("   → Show technical details about the fade event")
                elif "work" in cmd:
                    print("   → Start troubleshooting procedures")
                else:
                    print("   → Display all active events")
            else:
                print(f"❌ Close! The correct command was: {cmd}")

        print("\n⚡ Events drive your daily workflow - check them frequently!")

    def step_ticket_system(self):
        """Learn trouble ticket management"""
        self.clear_screen()

        self.type_effect("""
STEP 5: TROUBLE TICKET SYSTEM
=============================

Bell System uses trouble tickets to track and resolve issues:

• Ticket IDs: T-83047, T-83048, etc.
• Work Orders: WO-83051, WO-83052, etc.
• Status tracking: OPEN, ASSIGNED, IN PROGRESS, CLOSED

Essential ticket commands:
• ticket create        - Create new trouble ticket
• ticket status        - View all tickets
• ticket T-83047       - View specific ticket details
• ticket assign T-83047 - Assign ticket to technician
""")

        print("\nTICKET SCENARIO:")
        print("Customer reports no dial tone on 212-555-1234")

        ticket_workflow = [
            "ticket create",
            "ticket status",
            "ticket T-83047"
        ]

        for cmd in ticket_workflow:
            user_input = self.wait_for_user(f"What command would you use? (Hint: {cmd.split()[0]}...)")

            if cmd.lower() in user_input.lower():
                print(f"✅ Correct! '{cmd}' would handle this step.")
            else:
                print(f"❌ The command was: {cmd}")
                print("   Try to remember the ticket command structure!")

        print("\n📋 Tickets ensure nothing gets lost and problems are tracked!")

    def step_specialized_commands(self):
        """Learn role-specific commands"""
        self.clear_screen()

        self.type_effect("""
STEP 6: SPECIALIZED TECHNICAL COMMANDS
=====================================

Each role has specialized commands for their equipment and responsibilities.
Let's explore some transmission system commands:

RADIO/MICROWAVE SYSTEMS:
• radio status      - Overall radio system status
• radio fade        - Fade event monitoring
• radio weather     - Weather impact analysis
• radio path NYC-WAS - Specific path analysis

DIGITAL TRANSMISSION:
• t1carrier status  - T1 digital carrier systems
• t1carrier test DS1-NYC-001 - Test specific circuit
• lcarrier status   - Coaxial cable systems

NETWORK ANALYSIS:
• tnds status       - Total Network Data System
• traffic analysis  - Network traffic patterns
""")

        speciality_commands = [
            ("radio status", "Check radio system health"),
            ("t1carrier status", "Monitor digital circuits"),
            ("tnds status", "Network data analysis")
        ]

        print("\nLet's practice some specialized commands:")

        for cmd, purpose in speciality_commands:
            print(f"\nCommand: {cmd}")
            print(f"Purpose: {purpose}")

            user_input = self.wait_for_user("Type this command")

            if user_input.lower() == cmd.lower():
                print("✅ Excellent! You're mastering technical commands!")
            else:
                print(f"❌ You typed: {user_input}")
                print(f"   Correct: {cmd}")

        print("\n🔧 These specialized commands are the core of your daily work!")

    def step_graduation(self):
        """Complete the tutorial"""
        self.clear_screen()

        self.type_effect("""
CONGRATULATIONS! TUTORIAL COMPLETE
=================================

You have successfully completed the Bell System UNIX V7 Terminal
Simulation tutorial! You're now ready to begin authentic Bell System
operations.

WHAT YOU'VE LEARNED:
✅ Bell System operational roles and responsibilities
✅ Basic UNIX V7 command structure
✅ Help system navigation (help, man commands)
✅ Shift event monitoring and response
✅ Trouble ticket creation and management
✅ Specialized technical commands for your role

NEXT STEPS:
1. Run the main simulation: python bell.py
2. Select your preferred operational role
3. Check 'events' to see current shift activities
4. Use 'help' whenever you need assistance
5. Practice with different commands and scenarios

REMEMBER:
• Type 'help' anytime you need command assistance
• Use 'events' to stay aware of operational activities
• 'man <command>' provides detailed documentation
• Take your time - accuracy is more important than speed
""", delay=0.02)

        final_score = len(self.user_progress['commands_practiced'])
        role_selected = self.user_progress.get('role_selected', 'Not selected')

        print("\nYOUR TUTORIAL RESULTS:")
        print(f"Commands Practiced: {final_score}")
        print(f"Preferred Role: {role_selected}")
        print(f"Steps Completed: {self.user_progress['steps_completed']}")

        self.wait_for_user("Press Enter to receive your certificate")

    def show_completion_certificate(self):
        """Display completion certificate"""
        self.clear_screen()

        certificate = f"""
╔════════════════════════════════════════════════════════════════╗
║                    BELL SYSTEM LABORATORIES                    ║
║                        TRAINING DIVISION                       ║
║                                                                ║
║                     CERTIFICATE OF COMPLETION                  ║
║                                                                ║
║    UNIX V7 Terminal Simulation Training Program               ║
║                                                                ║
║    This certifies that the operator has successfully          ║
║    completed the Bell System terminal simulation tutorial     ║
║    and is qualified to operate authentic Bell System          ║
║    workstation equipment circa 1978-1983.                     ║
║                                                                ║
║    Date: {time.strftime('%B %d, %Y'):>20}                           ║
║    Training Program: UNIX V7 Operations                       ║
║    Commands Mastered: {len(self.user_progress['commands_practiced']):>2}                                   ║
║                                                                ║
║    ________________________                                    ║
║    Training Supervisor                                         ║
║    Bell System Operations Training                             ║
╚════════════════════════════════════════════════════════════════╝
"""

        print(certificate)
        print("\n🎉 Welcome to the Bell System operations team!")
        print("\nYou are now ready to run the main simulation.")
        print("Execute: python bell.py")

def main():
    """Main tutorial entry point"""
    print("Bell System UNIX V7 Terminal Simulation Tutorial")
    print("=" * 50)

    try:
        tutorial = BellSystemTutorial()
        tutorial.run()
    except KeyboardInterrupt:
        print("\n\nTutorial interrupted. You can restart anytime by running:")
        print("python bell_system_tutorial.py")
    except Exception as e:
        print(f"\nTutorial error: {e}")
        print("Please report this issue to the training coordinator.")

if __name__ == "__main__":
    main()
