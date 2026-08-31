"""
Bell System Practices, and the Programmer's Workbench commands.

nroff, troff, tbl and eqn moved to :mod:`bell_system.screens.docprep`
when they stopped being placeholders. Leaving the stubs here would
have let them win the method resolution order and shadow the real
implementations, which is exactly what happened once.
"""

from typing import (
    List,
)


from .session import SessionState


class DocumentCommands(SessionState):
    """
    Bell System Practices, and the Programmer's Workbench commands.

nroff, troff, tbl and eqn moved to :mod:`bell_system.screens.docprep`
when they stopped being placeholders. Leaving the stubs here would
have let them win the method resolution order and shadow the real
implementations, which is exactly what happened once.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def cmd_bsp(self, args: List[str]) -> str:
        """Bell System Practices - Standard Operating Procedures"""
        if not args:
            return """Bell System Practices (BSP)
Standard Operating Procedures and Technical References

Available Commands:
  bsp search <topic>   - Search BSP procedures
  bsp section <num>    - Display specific BSP section
  bsp recent          - Recently updated procedures
  bsp index           - BSP section index

Current BSP Library:
  Total Procedures:    14,892 sections
  Recent Updates:      47 sections (this month)
  Categories:          156 technical areas

Most Referenced:
  BSP 100-000         Bell System Fundamentals
  BSP 200-000         Switching Systems
  BSP 300-000         Transmission Systems
  BSP 400-000         Network Operations"""

        if args[0] == "search" and len(args) > 1:
            topic = " ".join(args[1:]).lower()
            return f"""BSP Search Results: "{topic}"

Matching Procedures:
  BSP 200-455-100     3A Central Control Maintenance
  BSP 200-455-200     3A System Administration
  BSP 200-455-300     3A Trouble Analysis
  BSP 200-455-400     3A Performance Monitoring

  BSP 300-125-001     TH-3 Microwave Alignment
  BSP 300-125-100     Radio Path Analysis
  BSP 300-125-200     Fade Margin Calculations

  BSP 400-200-001     TNDS Data Collection
  BSP 400-200-100     Traffic Analysis Procedures
  BSP 400-200-200     Network Performance Reports

Use 'bsp section <number>' for detailed procedures"""

        elif args[0] == "section" and len(args) > 1:
            section = args[1]
            return f"""Bell System Practice {section}
Revision Date: November 1983

PROCEDURE: 3A Central Control System Maintenance
CATEGORY: Electronic Switching Systems
DIVISION: Network Operations

SCOPE:
This practice covers routine maintenance procedures for the 3A Central
Control switching system including diagnostic testing, performance
monitoring, and preventive maintenance schedules.

PROCEDURE STEPS:

1. DAILY CHECKS (0800 hours)
   a. Review alarm logs for overnight activity
   b. Check processor occupancy levels
   c. Verify all central control units operational
   d. Review traffic load statistics

2. WEEKLY MAINTENANCE (Sunday 0200-0600)
   a. Run comprehensive diagnostic suite
   b. Exercise standby control units
   c. Update traffic translation tables
   d. Archive performance data

3. MONTHLY PROCEDURES
   a. Ferrite core memory tests
   b. Scanner unit calibration
   c. Network control verification
   d. Documentation updates

SAFETY CONSIDERATIONS:
- Follow lockout/tagout procedures
- Verify redundant systems before maintenance
- Coordinate with traffic engineering

REFERENCE DOCUMENTS:
SD-1C900-01: 3A Central Control Circuit Description
BSP 200-000: Electronic Switching Fundamentals"""

        return f"bsp: unknown option '{args[0]}'"
    # pic(1) and refer(1) used to be declared here as unavailable, and
    # nroff, troff, tbl and eqn before them. Every one of them now has a
    # real implementation in docprep.py, and a stub left here would win the
    # method resolution order and shadow it - which is exactly what happened
    # to nroff once already. There is nothing to put in their place.
    #
    # pwb and rje have gone too, for a different reason: PWB was a system,
    # not a program, and there was no pwb(1) to run. Its remote job entry
    # was reached through send(1) and rjestat(1), which is what this machine
    # now has.
    def cmd_uucp(self, args: List[str]) -> str:
        """UUCP network mail and file transfer"""
        return """UNIX-to-UNIX Copy Protocol (UUCP)
Network mail and file transfer operations

Current Status:
  Queue Status:         47 files pending transfer
  Active Connections:   3 of 8 possible
  Transfer Rate:        Normal operation

Network Links:
  bell-labs:           ACTIVE
  research:            ACTIVE
  btl:                 STANDBY

Use 'uucp status' for detailed queue information"""

