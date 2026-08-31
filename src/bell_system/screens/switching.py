"""
Central office switching machines: status, diagnostics and cutover.
"""

import random
from datetime import timedelta
from typing import (
    Any,
    Dict,
    List,
)
from ..data.switching import (
    METROPOLITAN_SWITCHES,
    RURAL_SWITCHES,
    SWITCHING_SYSTEMS,
    available_in,
)


from .session import SessionState


class SwitchingCommands(SessionState):
    """
    Central office switching machines: status, diagnostics and cutover.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _generate_switch_placement(self, city: str) -> Dict[str, Any]:
        """
        Choose a switching machine and a cutover year that could coexist.

        Type and year were previously drawn independently, which produced
        offices like a 5ESS installed in 1965 - seventeen years before the
        first one carried traffic. Here the year is drawn first, only machines
        already in service by then are eligible, and the size class is taken
        from what the machine was actually engineered for.

        Args:
            city: The city the office serves, which decides the size class

        Returns:
            The switch_type, capacity and installation_date fields
        """
        # The simulated present. Offices are cut over some years before it.
        current_year = self.clock.now().year
        installed = random.randint(max(1919, current_year - 40), current_year)

        metropolitan = city in self.METROPOLITAN_CITIES
        pool = METROPOLITAN_SWITCHES if metropolitan else RURAL_SWITCHES
        eligible = available_in(installed, pool)
        if not eligible:
            # Before any machine in the pool existed, step-by-step served.
            eligible = ['SXS']
            installed = max(installed, SWITCHING_SYSTEMS['SXS'].first_service)

        code = random.choice(eligible)
        system = SWITCHING_SYSTEMS[code]
        return {
            'switch_type': code,
            'switch_name': system.name,
            'capacity': random.randint(system.min_lines, system.max_lines),
            'installation_date': str(installed),
        }
    def cmd_switch(self, args: List[str]) -> str:
        """Enhanced switching center management with realistic operational dynamics."""
        import random

        # Update switching system states
        self._update_switching_states()

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            # Calculate dynamic metrics
            total_calls = sum(system["calls_hour"] for system in self.switching_systems.values())
            active_systems = len([s for s in self.switching_systems.values() if s["status"] == "ACTIVE"])
            total_systems = len(self.switching_systems)
            avg_completion = random.uniform(0.975, 0.995)

            status_output = f"""Bell System Switching Center Status
{current_time}

Electronic Switching Systems:"""

            for switch_id, system in self.switching_systems.items():
                load_indicator = f"{system['load']}%" if system["status"] == "ACTIVE" else "OFF"
                uptime_days = system["uptime"] // 24
                status_detail = f"- {system['calls_hour']:,} calls/hour"
                if system["status"] == "TESTING":
                    status_detail = "- Cutover operations in progress"
                elif uptime_days < 7:
                    status_detail = f"- {uptime_days} days uptime"

                status_output += f"\n  {switch_id:<15} {system['status']:<8} {load_indicator:<5} {status_detail}"

            # Add crossbar systems
            status_output += "\n\nCrossbar Systems:"
            for xb_id, xb_system in self.crossbar_systems.items():
                load_indicator = f"{xb_system['load']}%" if xb_system["status"] == "ACTIVE" else "OFF"
                maint_note = " - PM due" if xb_system["maintenance_due"] else " - Normal operation"
                status_output += f"\n  {xb_id:<15} {xb_system['status']:<8} {load_indicator:<5}{maint_note}"

            # System-wide performance metrics
            status_output += f"""

System Performance:
  Active Systems:           {active_systems}/{total_systems} electronic + {len([x for x in self.crossbar_systems.values() if x['status'] == 'ACTIVE'])}/{len(self.crossbar_systems)} crossbar
  Total Call Attempts:      {total_calls:,}/hour
  Call Completion Rate:     {avg_completion:.1%}
  Average Setup Time:       {random.uniform(1.8, 2.4):.1f} seconds
  Network Processor Load:   {sum(s['load'] for s in self.switching_systems.values() if s['status'] == 'ACTIVE') // active_systems}% average

Recent Events:"""

            # Add recent switching events
            events = []
            if any(s["status"] == "TESTING" for s in self.switching_systems.values()):
                events.append("⚡ 5ESS cutover operations scheduled")
            if any(x["maintenance_due"] for x in self.crossbar_systems.values()):
                events.append("🔧 Crossbar maintenance scheduled")
            if not events:
                events.append("✓ All systems operating normally")

            for event in events[:3]:
                status_output += f"\n  {event}"

            status_output += """

Commands:
  switch diagnostics <id>   Run comprehensive diagnostics
  switch performance <id>   Real-time performance monitoring
  switch maintenance <id>   Maintenance schedule and status
  switch cutover <id>       Cutover operations (5ESS only)"""

            return status_output

        elif args[0] == "diagnostics" and len(args) > 1:
            switch_id = args[1].upper()

            # Check if switch exists
            if switch_id not in self.switching_systems and switch_id not in self.crossbar_systems:
                return f"switch: ERROR - Switch {switch_id} not found\nAvailable systems: {', '.join(list(self.switching_systems.keys()) + list(self.crossbar_systems.keys()))}"

            # Determine system type and get data
            if switch_id in self.switching_systems:
                system = self.switching_systems[switch_id]
                is_electronic = True
            else:
                system = self.crossbar_systems[switch_id]
                is_electronic = False

            if system["status"] not in ["ACTIVE", "TESTING"]:
                return f"switch: Cannot run diagnostics on {switch_id} - system status: {system['status']}"

            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            # Simulate realistic diagnostic sequence
            diag_output = f"""Switching System Diagnostics: {switch_id}
Test Sequence Initiated: {current_time}
System Type: {'Electronic Stored Program Control' if is_electronic else 'Crossbar Electromechanical'}

Running Bell System Standard Diagnostic Suite:
"""

            # Different tests for electronic vs crossbar
            if is_electronic:
                tests = [
                    ("Central Processing Unit", 0.98),
                    ("Program Memory", 0.96),
                    ("Call Memory", 0.97),
                    ("I/O Controllers", 0.95),
                    ("Network Interface", 0.94),
                    ("Trunk Interface", 0.93),
                    ("Line Interface", 0.92),
                    ("Signal Processing", 0.96),
                    ("Call Processing Programs", 0.90),
                    ("Administrative Programs", 0.94),
                    ("Maintenance Programs", 0.95),
                    ("Database Integrity", 0.89),
                    ("Real-Time Clock", 0.98),
                    ("Interrupt System", 0.95)
                ]
            else:
                tests = [
                    ("Marker Selection", 0.92),
                    ("Crossbar Switch Matrix", 0.88),
                    ("Register Circuits", 0.90),
                    ("Sender Circuits", 0.87),
                    ("Connector Circuits", 0.85),
                    ("Common Control", 0.91),
                    ("Trunk Circuits", 0.89),
                    ("Line Circuits", 0.86),
                    ("Ringing Circuits", 0.93),
                    ("Power Systems", 0.95)
                ]

            # Run tests with realistic pass/fail based on system condition
            test_results = []
            base_reliability = 0.95 if system["status"] == "ACTIVE" else 0.85

            for test_name, base_pass_rate in tests:
                # Adjust pass rate based on system load and uptime
                if is_electronic:
                    load_factor = max(0.8, 1.0 - (system["load"] - 70) * 0.002) if system["load"] > 70 else 1.0
                    uptime_factor = max(0.9, 1.0 - (system["uptime"] - 8760) * 0.00005) if system["uptime"] > 8760 else 1.0
                else:
                    load_factor = max(0.7, 1.0 - (system["load"] - 60) * 0.003) if system["load"] > 60 else 1.0
                    uptime_factor = 0.85 if system["maintenance_due"] else 1.0

                adjusted_pass_rate = base_pass_rate * base_reliability * load_factor * uptime_factor
                passed = random.random() < adjusted_pass_rate

                # Generate realistic test values
                if passed:
                    if "memory" in test_name.lower():
                        value = f" ({random.randint(95, 100)}% utilized)"
                    elif "processing" in test_name.lower() or "cpu" in test_name.lower():
                        value = f" ({random.uniform(0.8, 2.5):.1f}ms response)"
                    elif "interface" in test_name.lower():
                        value = f" ({random.randint(98, 100)}% availability)"
                    else:
                        value = ""
                    status = f"PASS{value}"
                else:
                    if "memory" in test_name.lower():
                        value = " (parity error detected)"
                    elif "circuit" in test_name.lower():
                        value = " (intermittent failure)"
                    elif "interface" in test_name.lower():
                        value = " (signal degradation)"
                    else:
                        value = " (parameter out of range)"
                    status = f"FAIL{value}"

                progress_bar = "█" * 20
                diag_output += f"\n{test_name:<25} [{progress_bar}] {status}"
                test_results.append(passed)

            # Summary
            passed_count = sum(test_results)
            total_count = len(test_results)
            overall_pass = passed_count >= total_count * 0.9  # 90% pass rate required

            test_end = self.clock.now().strftime("%H:%M:%S")
            duration = random.randint(120, 300)

            diag_output += f"""

Diagnostic Sequence Completed: {test_end}
Total Duration: {duration} seconds

Results Summary:
  Tests Executed: {total_count}
  Tests Passed:   {passed_count}
  Tests Failed:   {total_count - passed_count}
  Success Rate:   {passed_count/total_count:.1%}
  Overall Status: {'OPERATIONAL' if overall_pass else 'DEGRADED'}
"""

            if overall_pass:
                diag_output += f"  Recommendation: {switch_id} certified for continued operation"
                if is_electronic and system["load"] < 85:
                    diag_output += "\n  Performance: Excellent - ready for increased traffic load"
            else:
                diag_output += f"  Recommendation: Schedule maintenance for {switch_id}"
                diag_output += "\n  Action Required: Investigate failed diagnostic phases"
                if not is_electronic and not system["maintenance_due"]:
                    # Mark crossbar for maintenance
                    system["maintenance_due"] = True

            diag_output += f"""

Diagnostic Log: /att/switching/diag/{switch_id.lower()}_{self.clock.now().strftime('%m%d_%H%M')}.log
Next Diagnostic: {(self.clock.now() + timedelta(days=7)).strftime('%B %d, %Y')}

Bell System Practice: BSP-100-300-001 (Electronic Switching Diagnostics)"""

            return diag_output

        elif args[0] == "performance" and len(args) > 1:
            switch_id = args[1].upper()

            if switch_id not in self.switching_systems and switch_id not in self.crossbar_systems:
                return f"switch: ERROR - Switch {switch_id} not found"

            return self._show_switch_performance_monitor(switch_id)

        elif args[0] == "maintenance" and len(args) > 1:
            switch_id = args[1].upper()

            if switch_id not in self.switching_systems and switch_id not in self.crossbar_systems:
                return f"switch: ERROR - Switch {switch_id} not found"

            return self._show_switch_maintenance_status(switch_id)

        elif args[0] == "cutover" and len(args) > 1:
            switch_id = args[1].upper()

            if switch_id not in self.switching_systems:
                return "switch: ERROR - Cutover operations only available for electronic switching systems"

            system = self.switching_systems[switch_id]
            if "5ESS" not in system["type"]:
                return "switch: ERROR - Cutover operations only supported on 5ESS systems"

            return self._perform_switch_cutover(switch_id, system)

        else:
            available_commands = ["diagnostics", "performance", "maintenance", "cutover"]
            return f"switch: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"
    def _update_switching_states(self) -> None:
        """Update switching system states based on operational patterns."""

        for switch_id, system in self.switching_systems.items():
            if system["status"] == "ACTIVE":
                # Vary call processing load
                load_change = random.randint(-2, 4)
                system["load"] = max(30, min(95, system["load"] + load_change))

                # Update call volume against the machine's engineered
                # ceiling, so a rural switch can never report metropolitan
                # traffic and a toll machine is rated on its trunks.
                ceiling = SWITCHING_SYSTEMS[system["type"]].busy_hour_capacity()
                system["calls_hour"] = int(
                    ceiling * (system["load"] / 100) * random.uniform(0.9, 1.1)
                )

                # Increment uptime
                system["uptime"] += random.uniform(0.8, 1.2)
    def _show_switch_performance_monitor(self, switch_id: str) -> str:
        """Show real-time performance monitoring for a switching system."""
        import random

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        if switch_id in self.switching_systems:
            system = self.switching_systems[switch_id]
            is_electronic = True
        else:
            system = self.crossbar_systems[switch_id]
            is_electronic = False

        if system["status"] not in ["ACTIVE", "TESTING"]:
            return f"Performance monitoring unavailable - {switch_id} status: {system['status']}"

        monitor_output = f"""Real-Time Performance Monitor: {switch_id}
Monitor Time: {current_time}
Update Interval: 30 seconds

System Status: {system['status']}"""

        if is_electronic:
            monitor_output += f"""
Current Load: {system['load']}%
Call Processing Rate: {system['calls_hour']:,} calls/hour
Memory Utilization: {random.randint(65, 85)}%

Real-Time Metrics (Last 10 minutes):
Time     CPU%  Mem%  Calls/min  Setup(ms)  Completion%
------   ----  ----  ---------  ---------  -----------"""

            # Generate 10 minutes of performance data
            for i in range(10):
                time_ago = 9 - i
                sample_time = (self.clock.now() - timedelta(minutes=time_ago)).strftime("%H:%M")
                cpu_load = max(40, min(95, system["load"] + random.randint(-5, 5)))
                mem_util = random.randint(60, 90)
                calls_min = system["calls_hour"] // 60 + random.randint(-50, 50)
                setup_time = random.randint(800, 2400)
                completion = random.uniform(0.975, 0.995)

                monitor_output += f"\n{sample_time}    {cpu_load:>3}%  {mem_util:>3}%  {calls_min:>9}  {setup_time:>9}  {completion:>10.1%}"

        else:  # Crossbar system
            monitor_output += f"""
Current Load: {system['load']}%
Marker Busy Time: {random.randint(15, 35)}%
Register Utilization: {random.randint(40, 70)}%

Electromechanical Status:
Crossbar Switches: {random.randint(890, 920)}/920 operational
Markers: {random.randint(18, 20)}/20 in service
Senders: {random.randint(45, 50)}/50 available
Connectors: {random.randint(180, 200)}/200 active"""

        # Add alerts based on performance
        alerts = []
        if is_electronic:
            if system["load"] > 90:
                alerts.append("⚠ CRITICAL: CPU load above 90%")
            elif system["load"] > 80:
                alerts.append("⚠ WARNING: High CPU utilization")
        else:
            if system["load"] > 85:
                alerts.append("⚠ WARNING: High traffic load on electromechanical system")
            if system["maintenance_due"]:
                alerts.append("🔧 NOTICE: Preventive maintenance overdue")

        if alerts:
            monitor_output += "\n\nActive Alerts:"
            for alert in alerts:
                monitor_output += f"\n  {alert}"
        else:
            monitor_output += "\n\n✓ All performance metrics within normal range"

        return monitor_output
    def _show_switch_maintenance_status(self, switch_id: str) -> str:
        """Show maintenance status and schedule for a switching system."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        if switch_id in self.switching_systems:
            system = self.switching_systems[switch_id]
            is_electronic = True
        else:
            system = self.crossbar_systems[switch_id]
            is_electronic = False

        maint_output = f"""Maintenance Status: {switch_id}
Report Generated: {current_time}
System Type: {'Electronic Stored Program Control' if is_electronic else 'Crossbar Electromechanical'}

Current Status: {system['status']}"""

        if is_electronic:
            last_maint = self.clock.now() - timedelta(days=random.randint(30, 180))
            next_maint = self.clock.now() + timedelta(days=random.randint(7, 90))
            uptime_hours = int(system["uptime"])

            maint_output += f"""
Uptime: {uptime_hours // 24} days, {uptime_hours % 24} hours
Last Maintenance: {last_maint.strftime('%B %d, %Y')}
Next Scheduled: {next_maint.strftime('%B %d, %Y %H:%M')}

Maintenance History:
  Program Memory Test: {(self.clock.now() - timedelta(days=7)).strftime('%b %d')} - PASSED
  I/O Controller Check: {(self.clock.now() - timedelta(days=14)).strftime('%b %d')} - PASSED
  Database Backup: {(self.clock.now() - timedelta(days=21)).strftime('%b %d')} - COMPLETED
  Environmental Check: {(self.clock.now() - timedelta(days=28)).strftime('%b %d')} - PASSED

Recommended Actions:"""

            if uptime_hours > 8760:  # More than 1 year
                maint_output += "\n  • Schedule comprehensive maintenance cycle"
            elif system["load"] > 85:
                maint_output += "\n  • Monitor closely due to high utilization"
            else:
                maint_output += "\n  • Continue routine monitoring"

        else:  # Crossbar
            maint_output += f"""
Maintenance Due: {'YES - OVERDUE' if system['maintenance_due'] else 'Current'}
Last Preventive Maintenance: {(self.clock.now() - timedelta(days=random.randint(60, 200))).strftime('%B %d, %Y')}

Mechanical Component Status:
  Crossbar Switches: {'Lubrication due' if system['maintenance_due'] else 'Good condition'}
  Relay Contacts: {'Cleaning required' if system['maintenance_due'] else 'Recently cleaned'}
  Motor Drives: {'Inspection due' if system['maintenance_due'] else 'Operating normally'}
  Wire Spring Relays: {'Testing required' if system['maintenance_due'] else 'Tested recently'}

Scheduled Maintenance Tasks:"""

            if system["maintenance_due"]:
                maint_output += """
  • URGENT: Contact cleaning and adjustment
  • Crossbar switch lubrication
  • Relay timing verification
  • Motor brush inspection
  • Wire spring relay testing"""
            else:
                maint_output += """
  • Routine contact inspection (monthly)
  • Lubrication schedule (quarterly)
  • Timing adjustment check (semi-annual)"""

        maint_output += """

Contact: Central Office Maintenance - ext 4300
Work Order System: Use 'service' command for maintenance requests"""

        return maint_output
    def _perform_switch_cutover(self, switch_id: str, system: dict) -> str:
        """Perform 5ESS cutover operations with realistic procedures."""
        import random

        if system["status"] != "TESTING":
            return f"switch: ERROR - {switch_id} must be in TESTING status for cutover operations"

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        cutover_output = f"""5ESS Cutover Operations: {switch_id}
Cutover Initiated: {current_time}

BELL SYSTEM 5ESS CUTOVER PROCEDURE BSP-100-500-001
⚠ WARNING: This operation will affect live customer traffic

Pre-Cutover Checklist:
✓ All diagnostic tests completed successfully
✓ Customer notification procedures completed
✓ Backup switching arrangements confirmed
✓ Technical staff positioned at critical locations
✓ Emergency rollback procedures verified

Cutover Sequence:"""

        # Simulate realistic cutover steps
        cutover_steps = [
            ("Traffic monitoring baseline established", 0.99),
            ("Administrative data verification", 0.95),
            ("Customer database synchronization", 0.92),
            ("Trunk group configuration transfer", 0.88),
            ("Line equipment initialization", 0.90),
            ("Billing system interface activation", 0.85),
            ("Emergency service verification", 0.98),
            ("Traffic load balancing activation", 0.87),
            ("Final system integration test", 0.83),
            ("Customer service verification", 0.80)
        ]

        all_successful = True
        for step_num, (step_name, success_rate) in enumerate(cutover_steps, 1):
            success = random.random() < success_rate
            status = "COMPLETE" if success else "FAILED"

            if not success:
                all_successful = False

            cutover_output += f"\nStep {step_num:>2}: {step_name:<35} [{status}]"

            if not success:
                cutover_output += f"\n         ERROR: Step {step_num} requires manual intervention"
                break

        completion_time = self.clock.now().strftime("%H:%M:%S EST")

        if all_successful:
            # Successful cutover
            system["status"] = "ACTIVE"
            system["load"] = random.randint(45, 65)  # Start with moderate load
            system["calls_hour"] = random.randint(15000, 25000)

            cutover_output += f"""

Cutover Completed Successfully: {completion_time}
Duration: {random.randint(45, 90)} minutes

POST-CUTOVER STATUS:
  System Status: ACTIVE
  Initial Load: {system['load']}%
  Call Processing: {system['calls_hour']:,} calls/hour
  Customer Impact: NONE - seamless transition achieved

IMMEDIATE ACTIONS:
  ✓ Customer service monitoring activated
  ✓ Performance baseline collection started
  ✓ 24-hour close monitoring period initiated
  ✓ All backup systems returned to standby

Next Review: {(self.clock.now() + timedelta(hours=24)).strftime('%B %d, %Y %H:%M')}
Project Completion: SUCCESSFUL"""

        else:
            # Failed cutover
            cutover_output += f"""

Cutover FAILED: {completion_time}
Status: ROLLBACK INITIATED

EMERGENCY PROCEDURES ACTIVATED:
  • Customer traffic restored to original switching system
  • Technical teams investigating failure points
  • Customer service impact minimized
  • Full investigation procedures initiated

Estimated Resolution: {random.randint(2, 8)} hours
Emergency Contact: Bell System NOC ext 911"""

        return cutover_output
    def cmd_3a(self, args: List[str]) -> str:
        """3A Central Control switching system operations"""
        if not args:
            return """3A Central Control Switching System
Common Control Electronic Switching

Available Commands:
  3a status            - System status and configuration
  3a diagnostics       - Run system diagnostics
  3a traffic           - Traffic load analysis
  3a maintenance       - Maintenance procedures
  3a translations      - Translation table management

Current 3A Systems:
  Systems Operational: 47 of 52 planned
  Call Processing:     Normal operation
  Memory Utilization:  73% of capacity

Project References: SD-1C900-01 (3A Central Control Circuit)"""

        if args[0] == "status":
            return """3A Central Control System Status
November 14, 1983 07:45:30

System Configuration:
  Central Control Units:       4 active, 1 standby
  Program Stores:              8MB ferrite core memory
  Call Stores:                 2MB working memory
  Scanner Units:               16 operational
  Network Control:             Crossbar network attached

Processing Status:
  Call Attempts:               45,892/hour (current)
  Successful Completions:      44,731 (97.5% success rate)
  Busy Hour Traffic:           892 CCS (within capacity)
  Processor Occupancy:         67% (Normal range: 40-80%)

Hardware Status:
  Central Control A:           ACTIVE - Normal operation
  Central Control B:           STANDBY - Ready
  Central Control C:           ACTIVE - Normal operation
  Central Control D:           MAINTENANCE - Scheduled PM

Translation Tables:
  Office Code Translations:    Current - Rev 47.3
  Routing Translations:        Current - Rev 12.8
  Screening Tables:            Current - Rev 6.2

Recent Activity:
  Last Translation Update:     1983-11-12 03:00
  Last Hardware Fault:         None (47 days)
  Performance Optimization:    Completed 1983-11-10"""

        elif args[0] == "diagnostics":
            return """3A Central Control Diagnostic Suite
Test Sequence Initiated: November 14, 1983 07:45:45

Memory Tests:
  Program Store Test:          [████████████████████] PASS
  Call Store Test:             [████████████████████] PASS
  Translation Table Test:      [████████████████████] PASS

Control Unit Tests:
  Central Control A:           [████████████████████] PASS
  Central Control B:           [████████████████████] PASS
  Central Control C:           [████████████████████] PASS
  Central Control D:           [██████████░░░░░░░░░░] MAINTENANCE

Network Interface Tests:
  Scanner Unit Test:           [████████████████████] PASS (16/16)
  Network Control Test:        [████████████████████] PASS
  Trunk Interface Test:        [████████████████████] PASS

Software Tests:
  Call Processing Programs:    [████████████████████] PASS
  Administrative Programs:     [████████████████████] PASS
  Maintenance Programs:        [████████████████████] PASS

Test Results Summary:
  Total Tests Run:             47 tests
  Tests Passed:                47 tests
  Tests Failed:                0 tests
  System Health:               EXCELLENT

Recommended Actions:
  Complete scheduled maintenance on Control Unit D
  Update trunk translation tables (due 11/20/83)
  Performance monitoring - all parameters normal"""

        return f"3a: unknown option '{args[0]}'"
    def cmd_crossbar(self, args: List[str]) -> str:
        """Enhanced crossbar switching system with realistic electromechanical operations."""
        import random

        if not args:
            crossbar_output = f"""Bell System Crossbar Switching Systems
Electromechanical Central Office Equipment
{'=' * 50}

CROSSBAR SYSTEMS STATUS
{'=' * 30}"""

            # Show crossbar systems from our initialized state
            for xb_id, xb_data in self.crossbar_systems.items():
                status_detail = "Normal operation"
                if xb_data["maintenance_due"]:
                    status_detail = "Preventive maintenance due"
                elif xb_data["status"] == "MAINT":
                    status_detail = "Under maintenance"

                crossbar_output += f"""
{xb_id}:
  Status:           {xb_data['status']}
  Load:             {xb_data['load']}%
  Condition:        {status_detail}"""

            crossbar_output += f"""

SYSTEM CHARACTERISTICS
{'=' * 30}
Switch Type:                 Electromechanical Crossbar
Switching Speed:             {random.uniform(0.8, 1.5):.1f} seconds average
Capacity:                    {random.randint(8000, 12000)} lines per system
Reliability:                 {random.uniform(0.985, 0.995):.2%} uptime

MECHANICAL COMPONENTS
{'=' * 30}
Crossbar Switches:           {random.randint(450, 680)} units
Markers:                     {random.randint(18, 24)} active
Senders:                     {random.randint(45, 60)} available
Connectors:                  {random.randint(180, 240)} operational
Registers:                   {random.randint(95, 140)} in service

Commands:
  crossbar status <system>    Detailed system status
  crossbar test <system>      Run mechanical tests
  crossbar maintenance        Maintenance schedule
  crossbar performance        Performance analysis"""

            return crossbar_output

        elif args[0] == "status" and len(args) > 1:
            system_id = args[1].upper()
            return self._show_crossbar_system_status(system_id)

        elif args[0] == "test" and len(args) > 1:
            system_id = args[1].upper()
            return self._run_crossbar_mechanical_test(system_id)

        elif args[0] == "maintenance":
            return self._show_crossbar_maintenance()

        elif args[0] == "performance":
            return self._show_crossbar_performance()

        else:
            available_commands = ["status", "test", "maintenance", "performance"]
            return f"crossbar: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"
    def _show_crossbar_system_status(self, system_id: str) -> str:
        """Show detailed crossbar system status."""

        if system_id not in self.crossbar_systems:
            return f"crossbar: System {system_id} not found\nAvailable systems: {', '.join(self.crossbar_systems.keys())}"

        system = self.crossbar_systems[system_id]
        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        return f"""Crossbar System Status: {system_id}
Status Report: {current_time}

SYSTEM OVERVIEW
{'=' * 25}
System Status:               {system['status']}
Traffic Load:                {system['load']}%
Maintenance Due:             {'YES' if system['maintenance_due'] else 'NO'}
Last Inspection:             {(self.clock.now() - timedelta(days=random.randint(30, 180))).strftime('%B %d, %Y')}

MECHANICAL COMPONENTS
{'=' * 25}
Crossbar Switches:           {random.randint(85, 100)}% operational
Contact Condition:           {'GOOD' if not system['maintenance_due'] else 'REQUIRES ATTENTION'}
Spring Tension:              Within specifications
Relay Response Time:         {random.uniform(15, 35):.1f} milliseconds

TRAFFIC STATISTICS
{'=' * 25}
Calls Processed Today:       {random.randint(15000, 35000):,}
Peak Hour Load:              {random.randint(85, 98)}%
Average Setup Time:          {random.uniform(0.8, 2.2):.1f} seconds
Blocking Rate:               {random.uniform(0.001, 0.015):.3f}

PERFORMANCE METRICS
{'=' * 25}
Call Completion Rate:        {random.uniform(0.92, 0.97):.1%}
Equipment Reliability:       {random.uniform(0.985, 0.995):.2%}
Maintenance Interval:        {'OVERDUE' if system['maintenance_due'] else 'CURRENT'}

{'RECOMMENDATION: Schedule immediate maintenance' if system['maintenance_due'] else 'STATUS: Normal operation'}"""
    def _run_crossbar_mechanical_test(self, system_id: str) -> str:
        """Run mechanical tests on crossbar system."""
        import random

        if system_id not in self.crossbar_systems:
            return f"crossbar: System {system_id} not found"

        system = self.crossbar_systems[system_id]

        return f"""Crossbar Mechanical Test Sequence: {system_id}
Test Initiated: {self.clock.now().strftime('%H:%M:%S EST')}

MECHANICAL TEST SUITE
{'=' * 30}
Contact Resistance Test:     {'PASS' if random.random() > 0.1 else 'FAIL'} ({random.uniform(0.5, 2.8):.1f} ohms)
Spring Tension Check:        {'PASS' if random.random() > 0.15 else 'MARGINAL'} ({random.uniform(28, 35):.1f} grams)
Relay Operation Test:        {'PASS' if random.random() > 0.08 else 'FAIL'} ({random.uniform(18, 45):.1f} ms response)
Switch Matrix Scan:          {'PASS' if random.random() > 0.12 else 'FAIL'} ({random.randint(890, 920)}/920 contacts OK)
Motor Drive Check:           {'PASS' if random.random() > 0.05 else 'FAIL'} (RPM within spec)
Timing Verification:         {'PASS' if random.random() > 0.20 else 'MARGINAL'} (±{random.uniform(2, 8):.1f}% deviation)

LUBRICATION STATUS
{'=' * 30}
Contact Points:              {'ADEQUATE' if not system['maintenance_due'] else 'LOW'}
Pivot Bearings:              {'GOOD' if not system['maintenance_due'] else 'DRY'}
Drive Mechanisms:            {'LUBRICATED' if not system['maintenance_due'] else 'REQUIRES SERVICE'}

Test Duration: {random.randint(45, 180)} seconds
Overall Result: {'PASS - System operational' if not system['maintenance_due'] else 'MARGINAL - Maintenance recommended'}

Use 'crossbar maintenance' for service scheduling."""
    def _show_crossbar_maintenance(self) -> str:
        """Show crossbar maintenance requirements and schedule."""

        maintenance_output = f"""Crossbar System Maintenance Schedule
{'=' * 45}

MAINTENANCE REQUIREMENTS
{'=' * 35}
Contact Cleaning:            Every 6 months
Lubrication:                 Every 3 months
Timing Adjustment:           Annually
Complete Inspection:         Every 18 months

CURRENT MAINTENANCE STATUS
{'=' * 35}"""

        for xb_id, xb_data in self.crossbar_systems.items():
            next_maint = "OVERDUE" if xb_data["maintenance_due"] else f"{random.randint(15, 90)} days"
            maintenance_output += f"""
{xb_id}:
  Last Service:        {(self.clock.now() - timedelta(days=random.randint(60, 200))).strftime('%B %d, %Y')}
  Next Due:            {next_maint}
  Priority:            {'HIGH' if xb_data['maintenance_due'] else 'NORMAL'}"""

        maintenance_output += f"""

MAINTENANCE PROCEDURES
{'=' * 35}
• Contact cleaning with approved solvents
• Spring tension adjustment and calibration
• Relay timing verification and adjustment
• Motor brush inspection and replacement
• Lubrication of all mechanical components
• Complete operational testing

Estimated Service Time: 4-6 hours per system
Maintenance Window: 02:00-06:00 EST (low traffic period)

Contact: Electromechanical Maintenance Team ext 4380"""

        return maintenance_output
    def _show_crossbar_performance(self) -> str:
        """Show crossbar performance analysis."""
        performance_output = f"""Crossbar System Performance Analysis
Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}

PERFORMANCE COMPARISON
{'=' * 35}"""

        for xb_id, xb_data in self.crossbar_systems.items():
            efficiency = random.uniform(0.88, 0.95)
            setup_time = random.uniform(0.9, 2.5)
            performance_output += f"""
{xb_id}:
  Efficiency:          {efficiency:.1%}
  Avg Setup Time:      {setup_time:.1f} seconds
  Reliability:         {random.uniform(0.985, 0.996):.2%}
  Maintenance Score:   {'EXCELLENT' if not xb_data['maintenance_due'] else 'FAIR'}"""

        performance_output += f"""

HISTORICAL TRENDS
{'=' * 35}
Reliability Trend:           {random.choice(['↑ Improving', '→ Stable', '↓ Declining'])}
Maintenance Costs:           ${random.randint(15000, 35000):,} (last quarter)
Service Quality:             {random.uniform(0.92, 0.97):.1%} customer satisfaction

TECHNOLOGY COMPARISON
{'=' * 35}
Crossbar vs Electronic:      Electronic 40% faster setup
Maintenance Requirements:    Crossbar requires 3x more service
Reliability:                 Electronic 15% more reliable
Cost of Operation:           Crossbar 25% higher operating cost

MODERNIZATION PLANNING
{'=' * 35}
Replacement Schedule:        5ESS deployment in progress
Migration Timeline:          24-36 months for complete conversion
Training Requirements:       Technician retraining program active"""

        return performance_output
    def cmd_5ess(self, args: List[str]) -> str:
        """5ESS Electronic Switching System operations"""
        return self._subsystem_unavailable("5ess", "5ESS operations")
    def cmd_alarm(self, args: List[str]) -> str:
        """Central office alarm monitoring and acknowledgement."""
        health = self.system_health

        if args and args[0] == "ack" and len(args) > 1:
            alarm_id = args[1].upper()
            for alarm in self.active_alarms:
                if alarm["id"] == alarm_id:
                    if alarm["acknowledged"]:
                        return f"alarm: {alarm_id} was already acknowledged."
                    alarm["acknowledged"] = True
                    return f"""Alarm Acknowledged
{'=' * 45}
Alarm:            {alarm_id}
Type:             {alarm['type']}
Severity:         {alarm['severity']}
System:           {alarm['system']}
Acknowledged By:  {self.username}
Time:             {self.clock.now().strftime('%B %d, %Y %H:%M EST')}

The alarm remains active until the condition clears."""
            return f"alarm: No active alarm with identifier '{alarm_id}'"

        if args and args[0] not in ("status", "list"):
            return ("alarm: Unknown option '%s'\n"
                    "Available commands: status, list, ack <alarm-id>" % args[0])

        output = f"""Bell System Central Office Alarm Monitor
{self.clock.now().strftime('%B %d, %Y %H:%M EST')}
{'=' * 50}

SYSTEM HEALTH
{'=' * 40}
Overall Status:           {health['overall_status']}
Critical Alarms:          {health['critical_alarms']}
Major Alarms:             {health['major_alarms']}
Minor Alarms:             {health['minor_alarms']}
Continuous Uptime:        {health['uptime_days']} days
Last Service Outage:      {health['last_outage'].strftime('%B %d, %Y')}

ACTIVE ALARMS
{'=' * 40}"""

        if not self.active_alarms:
            output += "\nNo active alarms. All monitored systems normal."
        else:
            for alarm in sorted(
                self.active_alarms,
                key=lambda a: {'CRITICAL': 0, 'MAJOR': 1, 'MINOR': 2}[a['severity']]
            ):
                age = int((self.clock.now() - alarm['timestamp']).total_seconds() / 60)
                output += f"""
{alarm['id']} [{alarm['severity']}]
  Type:               {alarm['type']}
  System:             {alarm['system']}
  Condition:          {alarm['description']}
  Raised:             {alarm['timestamp'].strftime('%H:%M EST')} ({age} minutes ago)
  Acknowledged:       {'YES' if alarm['acknowledged'] else 'NO - REQUIRES ATTENTION'}"""

        unacknowledged = [a for a in self.active_alarms if not a['acknowledged']]
        output += f"""

SUMMARY
{'=' * 40}
Total Active:             {len(self.active_alarms)}
Awaiting Acknowledgement: {len(unacknowledged)}

Commands:
  alarm status              Show this display
  alarm ack <alarm-id>      Acknowledge an alarm

Reference: BSP 660-100-000 (Alarm Surveillance)"""
        return output
