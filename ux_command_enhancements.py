#!/usr/bin/env python3
"""
Bell System Terminal - UX Command Enhancements Module
====================================================

Advanced UX improvements including command autocompletion hints,
enhanced error messages, command history navigation, and user assistance.

Features:
- Intelligent command suggestions
- Context-aware error messages
- Command pattern recognition
- User guidance system
- Enhanced terminal experience

Author: Bell System Operations Simulation Project
Version: 2.1
Date: January 2025
"""

import difflib
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
import re

class CommandEnhancementEngine:
    """
    Advanced command enhancement system for Bell System terminal.
    
    Provides intelligent suggestions, error recovery, and user assistance
    while maintaining the authentic terminal experience.
    """
    
    def __init__(self):
        """Initialize the command enhancement engine."""
        self.command_usage_stats = defaultdict(int)
        self.error_patterns = defaultdict(list)
        self.user_preferences = {}
        self.command_context = []
        
        # Initialize command database
        self._initialize_command_database()
        self._initialize_error_patterns()
        self._initialize_help_system()
    
    def _initialize_command_database(self):
        """Initialize comprehensive command database with metadata."""
        self.command_db = {
            # System commands
            'help': {
                'category': 'system',
                'description': 'Display command help and usage',
                'aliases': ['h', '?'],
                'complexity': 'basic',
                'examples': ['help', 'help trunk', 'help radio']
            },
            'status': {
                'category': 'monitoring',
                'description': 'Display system status information',
                'aliases': ['st', 'stat'],
                'complexity': 'basic',
                'examples': ['status', 'st']
            },
            'quit': {
                'category': 'system',
                'description': 'Exit the terminal session',
                'aliases': ['q', 'exit', 'logout'],
                'complexity': 'basic',
                'examples': ['quit', 'q', 'exit']
            },
            
            # Bell System operations
            'trunk': {
                'category': 'telecom',
                'description': 'Trunk group monitoring and management',
                'aliases': [],
                'complexity': 'intermediate',
                'examples': ['trunk status', 'trunk detail TG-001', 'trunk traffic TG-045'],
                'subcommands': ['status', 'detail', 'traffic', 'history', 'route', 'capacity', 'billing']
            },
            'switch': {
                'category': 'telecom',
                'description': 'Switching center management',
                'aliases': [],
                'complexity': 'intermediate',
                'examples': ['switch status', 'switch config', 'switch traffic'],
                'subcommands': ['status', 'config', 'traffic', 'alarm', 'test']
            },
            'radio': {
                'category': 'transmission',
                'description': 'Radio/microwave system monitoring',
                'aliases': ['rad'],
                'complexity': 'advanced',
                'examples': ['radio status', 'radio path analysis', 'radio fade monitor'],
                'subcommands': ['status', 'path', 'fade', 'diversity', 'alignment', 'maintenance']
            },
            't1carrier': {
                'category': 'transmission',
                'description': 'T1 digital carrier system operations',
                'aliases': ['t1', 'ds1'],
                'complexity': 'advanced',
                'examples': ['t1carrier status', 't1carrier performance', 't1carrier maintenance'],
                'subcommands': ['status', 'performance', 'maintenance', 'provisioning', 'testing']
            },
            'alarm': {
                'category': 'monitoring',
                'description': 'Central office alarm monitoring',
                'aliases': ['alm', 'alert'],
                'complexity': 'intermediate',
                'examples': ['alarm status', 'alarm critical', 'alarm history'],
                'subcommands': ['status', 'critical', 'major', 'minor', 'history', 'acknowledge']
            },
            'ticket': {
                'category': 'operations',
                'description': 'Trouble ticket management',
                'aliases': [],
                'complexity': 'intermediate',
                'examples': ['ticket list', 'ticket detail TT-8001', 'ticket create'],
                'subcommands': ['list', 'detail', 'create', 'update', 'close', 'assign']
            }
        }
    
    def _initialize_error_patterns(self):
        """Initialize common error patterns and their solutions."""
        self.error_solutions = {
            'command_not_found': {
                'pattern': r'.*command.*not found.*',
                'solutions': [
                    'Check spelling of the command',
                    'Use "help" to see available commands',
                    'Try using command aliases (e.g., "h" for help)',
                    'Ensure the command is available for your role'
                ]
            },
            'invalid_arguments': {
                'pattern': r'.*invalid.*argument.*',
                'solutions': [
                    'Use "man command_name" for correct syntax',
                    'Check the number of arguments required',
                    'Verify argument format and values',
                    'Use command examples from help system'
                ]
            },
            'permission_denied': {
                'pattern': r'.*permission.*denied.*',
                'solutions': [
                    'Check if command is available for your role',
                    'Some commands require specific permissions',
                    'Contact system administrator if needed',
                    'Try alternative commands with similar function'
                ]
            },
            'missing_parameters': {
                'pattern': r'.*missing.*parameter.*',
                'solutions': [
                    'Check required parameters with "man command_name"',
                    'Some commands need additional arguments',
                    'Use command examples for proper syntax',
                    'Verify all required fields are provided'
                ]
            }
        }
    
    def _initialize_help_system(self):
        """Initialize context-aware help system."""
        self.help_contexts = {
            'beginner': {
                'focus': 'basic commands and navigation',
                'suggestions': ['help', 'status', 'who', 'date', 'clear'],
                'tips': [
                    'Start with "help" to see available commands',
                    'Use "h" as a shortcut for help',
                    'Try "status" to see system overview',
                    'Use up/down arrows for command history'
                ]
            },
            'intermediate': {
                'focus': 'operational commands and monitoring',
                'suggestions': ['trunk', 'switch', 'alarm', 'ticket', 'events'],
                'tips': [
                    'Most commands have status subcommands',
                    'Use aliases like "st" for status, "alm" for alarm',
                    'Check "events" for current shift activity',
                    'Use "ticket list" to see trouble tickets'
                ]
            },
            'advanced': {
                'focus': 'technical systems and analysis',
                'suggestions': ['radio', 't1carrier', 'lcarrier', 'multiplex', 'tnds'],
                'tips': [
                    'Technical commands often have detailed subcommands',
                    'Use "performance" options for system analysis',
                    'Radio systems have path analysis capabilities',
                    'Carrier systems support maintenance operations'
                ]
            }
        }
    
    def suggest_commands(self, partial_command: str, context: str = 'general') -> List[str]:
        """Generate intelligent command suggestions based on input."""
        suggestions = []
        
        # Exact matches first
        if partial_command in self.command_db:
            suggestions.append(partial_command)
        
        # Alias matches
        for cmd, info in self.command_db.items():
            if partial_command in info.get('aliases', []):
                suggestions.append(cmd)
        
        # Partial matches (commands starting with input)
        partial_matches = [cmd for cmd in self.command_db.keys() 
                          if cmd.startswith(partial_command.lower())]
        suggestions.extend(partial_matches)
        
        # Fuzzy matches using difflib
        if len(partial_command) >= 2:
            fuzzy_matches = difflib.get_close_matches(
                partial_command.lower(), 
                self.command_db.keys(), 
                n=3, 
                cutoff=0.6
            )
            suggestions.extend(fuzzy_matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion)
        
        return unique_suggestions[:5]  # Limit to top 5 suggestions
    
    def analyze_error(self, command: str, error_message: str) -> Dict[str, any]:
        """Analyze command errors and provide helpful feedback."""
        analysis = {
            'error_type': 'unknown',
            'suggestions': [],
            'examples': [],
            'help_hint': '',
            'severity': 'medium'
        }
        
        # Classify error type
        for error_type, pattern_info in self.error_solutions.items():
            if re.search(pattern_info['pattern'], error_message, re.IGNORECASE):
                analysis['error_type'] = error_type
                analysis['suggestions'] = pattern_info['solutions']
                break
        
        # Add command-specific suggestions
        if command in self.command_db:
            cmd_info = self.command_db[command]
            analysis['examples'] = cmd_info.get('examples', [])
            analysis['help_hint'] = f"Try: man {command}"
            
            # Check for subcommands
            if 'subcommands' in cmd_info:
                analysis['suggestions'].append(
                    f"Available subcommands: {', '.join(cmd_info['subcommands'])}"
                )
        
        # Command suggestions for unknown commands
        if analysis['error_type'] == 'unknown' or 'not found' in error_message.lower():
            command_suggestions = self.suggest_commands(command)
            if command_suggestions:
                analysis['suggestions'].append(f"Did you mean: {', '.join(command_suggestions[:3])}")
        
        return analysis
    
    def get_contextual_help(self, user_level: str = 'intermediate') -> str:
        """Provide contextual help based on user experience level."""
        if user_level not in self.help_contexts:
            user_level = 'intermediate'
        
        context = self.help_contexts[user_level]
        
        help_text = f"""
CONTEXTUAL HELP - {user_level.upper()} LEVEL
{'=' * 50}

FOCUS: {context['focus']}

RECOMMENDED COMMANDS:
{chr(10).join(f'  • {cmd}' for cmd in context['suggestions'])}

HELPFUL TIPS:
{chr(10).join(f'  • {tip}' for tip in context['tips'])}

QUICK REFERENCE:
  • Use "help" for command overview
  • Use "man <command>" for detailed help
  • Use up/down arrows for command history
  • Most commands have aliases (e.g., 'h' for help)
  • Type "errors" to see recent error summary
"""
        return help_text
    
    def track_command_usage(self, command: str, success: bool) -> None:
        """Track command usage patterns for better suggestions."""
        self.command_usage_stats[command] += 1
        
        if not success:
            self.error_patterns[command].append({
                'timestamp': time.time(),
                'success': success
            })
    
    def get_popular_commands(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently used commands."""
        return Counter(self.command_usage_stats).most_common(limit)
    
    def generate_command_hints(self, recent_commands: List[str]) -> List[str]:
        """Generate helpful hints based on recent command patterns."""
        hints = []
        
        # Check for common patterns
        if any('help' in cmd for cmd in recent_commands[-5:]):
            hints.append("💡 Remember: Most commands have short aliases (e.g., 'h' for help)")
        
        if any('status' in cmd for cmd in recent_commands[-3:]):
            hints.append("💡 Try: Use 'st' as a quick alias for status commands")
        
        if len(set(recent_commands[-5:])) <= 2:
            hints.append("💡 Explore: Try 'events' to see current shift activity")
        
        # Role-specific hints
        trunk_usage = sum(1 for cmd in recent_commands if 'trunk' in cmd)
        if trunk_usage > 3:
            hints.append("💡 Advanced: Try 'trunk capacity' for utilization analysis")
        
        return hints
    
    def format_enhanced_error(self, command: str, error_message: str, 
                            suggestions: List[str] = None) -> str:
        """Format enhanced error message with helpful information."""
        analysis = self.analyze_error(command, error_message)
        
        formatted_error = f"""
╭─ COMMAND ERROR ─────────────────────────────────────────╮
│ Command: {command:<45} │
│ Error: {error_message[:47]:<47} │
╰─────────────────────────────────────────────────────────╯

SUGGESTIONS:
"""
        
        # Add analysis suggestions
        for i, suggestion in enumerate(analysis['suggestions'][:3], 1):
            formatted_error += f"  {i}. {suggestion}\n"
        
        # Add examples if available
        if analysis['examples']:
            formatted_error += f"\nEXAMPLES:\n"
            for example in analysis['examples'][:2]:
                formatted_error += f"  → {example}\n"
        
        # Add help hint
        if analysis['help_hint']:
            formatted_error += f"\nFor detailed help: {analysis['help_hint']}\n"
        
        return formatted_error

# Example usage and integration
def demonstrate_enhancements():
    """Demonstrate the UX enhancement features."""
    engine = CommandEnhancementEngine()
    
    print("Bell System UX Enhancement Engine Demo")
    print("=" * 50)
    
    # Test command suggestions
    print("\n1. Command Suggestions:")
    suggestions = engine.suggest_commands("tru")
    print(f"   Input: 'tru' → Suggestions: {suggestions}")
    
    suggestions = engine.suggest_commands("rad")
    print(f"   Input: 'rad' → Suggestions: {suggestions}")
    
    # Test error analysis
    print("\n2. Error Analysis:")
    analysis = engine.analyze_error("trunks", "Command not found: trunks")
    print(f"   Error analysis for 'trunks': {analysis['suggestions'][:2]}")
    
    # Test contextual help
    print("\n3. Contextual Help:")
    help_text = engine.get_contextual_help('beginner')
    print(help_text[:200] + "...")
    
    # Test enhanced error formatting
    print("\n4. Enhanced Error Message:")
    formatted = engine.format_enhanced_error("xyz", "Command not found")
    print(formatted)

if __name__ == "__main__":
    demonstrate_enhancements()