#!/usr/bin/env python3
"""
Bell System UNIX V7 Terminal Simulation - Direct Launcher
=========================================================

Direct execution launcher for the Bell System terminal simulation.
"""

import sys
import os
import argparse

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bell import BellSystemTerminal
from bell_system_tutorial import BellSystemTutorial
from unix_terminal import BellSystemTerminal as SimpleBellSystemTerminal


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Bell System UNIX V7 Terminal Simulation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 bell-system.py                    Start interactive simulation
  python3 bell-system.py --tutorial         Learn Bell System operations
  python3 bell-system.py --role 1          Start as UNIX Systems Operator
  python3 bell-system.py --simple          Use simplified interface
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Bell System UNIX V7 Terminal Simulation v2.0'
    )
    
    parser.add_argument(
        '--tutorial',
        action='store_true',
        help='Start interactive tutorial system'
    )
    
    parser.add_argument(
        '--role',
        type=int,
        choices=range(1, 13),
        help='Start with specific role (1-12)'
    )
    
    parser.add_argument(
        '--simple',
        action='store_true',
        help='Use simplified four-role interface'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run comprehensive test suite'
    )
    
    args = parser.parse_args()
    
    try:
        if args.test:
            # Import and run test suite
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))
            import comprehensive_test_suite
            tester = comprehensive_test_suite.BellSystemTester()
            tester.run_comprehensive_test()
            
        elif args.tutorial:
            # Start tutorial system
            tutorial = BellSystemTutorial()
            tutorial.run()
            
        elif args.simple:
            # Start simplified interface
            terminal = SimpleBellSystemTerminal()
            terminal.run()
            
        else:
            # Start main Bell System simulation
            terminal = BellSystemTerminal()
            if args.role:
                from bell import BELL_SYSTEM_ROLES
                terminal.current_role = BELL_SYSTEM_ROLES[args.role][0]
                terminal.role_name = BELL_SYSTEM_ROLES[args.role][1]
            terminal.run()
            
    except KeyboardInterrupt:
        print("\nSimulation terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()