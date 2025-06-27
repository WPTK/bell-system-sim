#!/usr/bin/env python3
"""
Bell System UNIX V7 Terminal Simulation - Basic Usage Examples
==============================================================

Demonstrates programmatic usage of the Bell System terminal simulation
for automated operations and scripting.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bell import BellSystemTerminal
from unix_terminal import BellSystemTerminal as SimpleBellSystemTerminal


def example_sysop_operations():
    """Example: UNIX Systems Operator automated tasks."""
    print("=== UNIX Systems Operator Example ===")
    
    terminal = BellSystemTerminal()
    terminal.current_role = "sysop"
    terminal.role_name = "UNIX Systems Operator"
    
    # Simulate system status checks
    commands = ["status", "who", "df", "ps"]
    
    for cmd in commands:
        print(f"\n$ {cmd}")
        try:
            result = terminal.handle_command(cmd.split())
            print(result)
        except Exception as e:
            print(f"Error: {e}")


def example_switching_technician():
    """Example: Switching Station Technician operations."""
    print("\n=== Switching Station Technician Example ===")
    
    terminal = BellSystemTerminal()
    terminal.current_role = "switch"
    terminal.role_name = "Switching Station Technician"
    
    # Simulate switching operations
    commands = [
        "switch status",
        "trunk status", 
        "testboard status",
        "alarm status"
    ]
    
    for cmd in commands:
        print(f"\n$ {cmd}")
        try:
            result = terminal.handle_command(cmd.split())
            print(result)
        except Exception as e:
            print(f"Error: {e}")


def example_simplified_interface():
    """Example: Using the simplified four-role interface."""
    print("\n=== Simplified Interface Example ===")
    
    terminal = SimpleBellSystemTerminal()
    terminal.role = "sysop"
    
    # Demonstrate basic commands
    commands = ["help", "ps", "who", "date"]
    
    for cmd in commands:
        print(f"\n$ {cmd}")
        try:
            result = terminal.handle_command(cmd)
            print(result)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("Bell System UNIX V7 Terminal Simulation - Usage Examples")
    print("=" * 60)
    
    example_sysop_operations()
    example_switching_technician()
    example_simplified_interface()
    
    print("\n" + "=" * 60)
    print("For interactive mode, run: bell-system")
    print("For tutorial mode, run: bell-system --tutorial")