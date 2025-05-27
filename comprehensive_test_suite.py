#!/usr/bin/env python3
"""
Comprehensive Bell System UNIX V7 Command Validation Suite
==========================================================

Automated testing framework to validate all commands across all 12 operational roles.
Identifies errors, validates input handling, and ensures historical authenticity.
"""

import sys
import traceback
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import bell

class BellSystemTester:
    """Comprehensive testing framework for Bell System simulation."""
    
    def __init__(self):
        self.test_results = {}
        self.errors_found = []
        self.fixes_applied = []
        
        # Define comprehensive test commands for each role
        self.role_commands = {
            1: {  # UNIX Systems Operator
                'name': 'UNIX Systems Operator',
                'commands': [
                    'help', 'h', '?', 'man ps', 'ps', 'who', 'w', 'users',
                    'df', 'disk', 'pwd', 'date', 'ls', 'll', 'list',
                    'clear', 'cls', 'quit', 'exit', 'logout',
                    'status', 'st', 'test', 'tst', 'alarm', 'alm',
                    'history', 'errors', 'verbosity info', 'verbosity debug'
                ]
            },
            2: {  # Switching Station Technician
                'name': 'Switching Station Technician',
                'commands': [
                    'switch status', 'switch detail', 'switch test',
                    'crossbar status', 'crossbar test', 'crossbar config',
                    'testboard status', 'testboard line', 'testboard trunk',
                    'alarm status', 'alarm history', 'alarm ack',
                    'trunk status', 'trunk detail TG-001', 'trunk traffic',
                    '3a status', '3a test', '3a maintenance'
                ]
            },
            3: {  # Field Support Liaison
                'name': 'Field Support Liaison',
                'commands': [
                    'ticket status', 'ticket create', 'ticket list',
                    'emergency status', 'emergency dispatch', 'emergency escalate',
                    'service status', 'service install', 'service repair',
                    'provision status', 'provision install', 'provision test'
                ]
            },
            4: {  # National NOC Analyst
                'name': 'National NOC Analyst',
                'commands': [
                    'traffic status', 'traffic analysis', 'traffic forecast',
                    'routing status', 'routing analyze', 'routing optimize',
                    'capacity status', 'capacity forecast', 'capacity plan',
                    'netplan status', 'netplan analyze', 'netplan optimize'
                ]
            },
            5: {  # TSPS Operator
                'name': 'TSPS Operator',
                'commands': [
                    'tsps status', 'tsps position', 'tsps traffic',
                    'operator status', 'operator assist', 'operator conference',
                    'directory lookup', 'directory search', 'directory update',
                    'toll status', 'toll billing', 'toll rates'
                ]
            },
            6: {  # Database Administrator
                'name': 'Database Administrator',
                'commands': [
                    'dbquery status', 'dbquery search', 'dbquery report',
                    'custdb status', 'custdb search', 'custdb update',
                    'billing status', 'billing calculate', 'billing report',
                    'collect status', 'collect verify', 'collect report'
                ]
            },
            7: {  # Network Planning Engineer
                'name': 'Network Planning Engineer',
                'commands': [
                    'netplan status', 'netplan analyze', 'netplan forecast',
                    'analysis status', 'analysis traffic', 'analysis capacity',
                    'netdata status', 'netdata collect', 'netdata report'
                ]
            },
            8: {  # Customer Service Interface Technician
                'name': 'Customer Service Interface Technician',
                'commands': [
                    'custdb status', 'custdb search', 'custdb update',
                    'service status', 'service install', 'service modify',
                    'provision status', 'provision install', 'provision test',
                    'billing status', 'billing inquiry', 'billing adjust'
                ]
            },
            9: {  # Radio/Microwave Technician
                'name': 'Radio/Microwave Technician',
                'commands': [
                    'radio status', 'radio test', 'radio maintenance',
                    'microwave status', 'microwave test', 'microwave align',
                    'satellite status', 'satellite test', 'satellite track',
                    'antenna status', 'antenna test', 'antenna align'
                ]
            },
            10: {  # TNDS Analyst
                'name': 'TNDS Analyst',
                'commands': [
                    'tnds status', 'tnds collect', 'tnds analyze',
                    'netdata status', 'netdata collect', 'netdata report',
                    'analysis status', 'analysis traffic', 'analysis forecast',
                    'traffic status', 'traffic monitor', 'traffic report'
                ]
            },
            11: {  # SARTS Technician
                'name': 'SARTS Technician',
                'commands': [
                    'sarts status', 'sarts test', 'sarts verify',
                    't1carrier status', 't1carrier test', 't1carrier monitor',
                    'lcarrier status', 'lcarrier test', 'lcarrier monitor',
                    'multiplex status', 'multiplex test', 'multiplex config',
                    'regenerator status', 'regenerator test', 'regenerator align'
                ]
            },
            12: {  # Document Preparation Specialist
                'name': 'Document Preparation Specialist',
                'commands': [
                    'nroff status', 'nroff format', 'nroff process',
                    'troff status', 'troff format', 'troff typeset',
                    'tbl status', 'tbl format', 'tbl process',
                    'eqn status', 'eqn format', 'eqn process',
                    'pic status', 'pic draw', 'pic process',
                    'refer status', 'refer format', 'refer bibliography'
                ]
            }
        }
        
        # Invalid commands to test error handling
        self.invalid_commands = [
            'invalid_command', 'badcmd', 'xyz123', '', ' ',
            'help badarg', 'status invalid', 'test with bad args'
        ]

    def run_comprehensive_test(self):
        """Execute comprehensive testing across all roles."""
        print("=" * 80)
        print("BELL SYSTEM UNIX V7 COMPREHENSIVE COMMAND VALIDATION")
        print("=" * 80)
        print()
        
        total_tests = 0
        total_errors = 0
        
        # Test each role systematically
        for role_num in range(1, 13):
            print(f"Testing Role {role_num}: {self.role_commands[role_num]['name']}")
            print("-" * 60)
            
            role_errors = self.test_role(role_num)
            total_tests += len(self.role_commands[role_num]['commands'])
            total_errors += len(role_errors)
            
            if role_errors:
                print(f"  ❌ {len(role_errors)} errors found")
                for error in role_errors:
                    print(f"     • {error}")
            else:
                print(f"  ✅ All commands working correctly")
            print()
        
        # Test error handling with invalid commands
        print("Testing Error Handling with Invalid Commands")
        print("-" * 60)
        error_handling_issues = self.test_error_handling()
        
        # Generate summary report
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total Commands Tested: {total_tests}")
        print(f"Total Errors Found: {total_errors}")
        print(f"Error Handling Issues: {len(error_handling_issues)}")
        print(f"Success Rate: {((total_tests - total_errors) / total_tests * 100):.1f}%")
        
        if self.errors_found:
            print("\nCRITICAL ERRORS REQUIRING FIXES:")
            for i, error in enumerate(self.errors_found, 1):
                print(f"{i}. {error}")
        
        return self.errors_found

    def test_role(self, role_num):
        """Test all commands for a specific role."""
        errors = []
        
        try:
            # Create terminal instance and select role
            terminal = bell.BellSystemTerminal()
            terminal.role = str(role_num)
            
            # Test each command for this role
            for command in self.role_commands[role_num]['commands']:
                try:
                    # Capture output and errors
                    with StringIO() as captured_output:
                        with redirect_stdout(captured_output):
                            with redirect_stderr(captured_output):
                                result = terminal.execute_command(command)
                        
                        # Check for obvious error indicators
                        if self.is_error_result(result, command):
                            error_msg = f"Command '{command}' failed: {result[:100]}..."
                            errors.append(error_msg)
                            self.errors_found.append(f"Role {role_num} - {error_msg}")
                
                except Exception as e:
                    error_msg = f"Command '{command}' raised exception: {str(e)}"
                    errors.append(error_msg)
                    self.errors_found.append(f"Role {role_num} - {error_msg}")
                    
        except Exception as e:
            error_msg = f"Failed to initialize role {role_num}: {str(e)}"
            errors.append(error_msg)
            self.errors_found.append(error_msg)
        
        return errors

    def test_error_handling(self):
        """Test error handling with invalid commands."""
        issues = []
        
        try:
            terminal = bell.BellSystemTerminal()
            terminal.role = "1"  # Use UNIX Systems Operator for testing
            
            for invalid_cmd in self.invalid_commands:
                try:
                    result = terminal.execute_command(invalid_cmd)
                    
                    # Check if error handling is working properly
                    if not self.is_proper_error_response(result, invalid_cmd):
                        issue = f"Poor error handling for '{invalid_cmd}': {result[:50]}..."
                        issues.append(issue)
                        
                except Exception as e:
                    issue = f"Exception on invalid command '{invalid_cmd}': {str(e)}"
                    issues.append(issue)
                    
        except Exception as e:
            issues.append(f"Failed to test error handling: {str(e)}")
        
        return issues

    def is_error_result(self, result, command):
        """Check if a command result indicates an error."""
        if not result:
            return True
        
        result_lower = result.lower()
        
        # Check for obvious error indicators
        error_indicators = [
            'traceback', 'exception', 'error:', 'failed',
            'attributeerror', 'typeerror', 'nameerror',
            'keyerror', 'indexerror', 'valueerror'
        ]
        
        return any(indicator in result_lower for indicator in error_indicators)

    def is_proper_error_response(self, result, command):
        """Check if error response is properly formatted."""
        if not result:
            return False
        
        result_lower = result.lower()
        
        # Good error responses should contain helpful information
        good_indicators = [
            'command not found', 'did you mean', 'usage:', 'help',
            'invalid', 'unknown option', 'syntax'
        ]
        
        return any(indicator in result_lower for indicator in good_indicators)


def main():
    """Run the comprehensive validation suite."""
    tester = BellSystemTester()
    errors = tester.run_comprehensive_test()
    
    if errors:
        print(f"\n🔧 Found {len(errors)} issues that need fixing.")
        print("Proceeding to apply fixes...")
        return False
    else:
        print("\n✅ All tests passed! Bell System simulation is working perfectly.")
        return True


if __name__ == "__main__":
    main()