"""
Interoffice trunk groups: occupancy, testing and maintenance.
"""

import random
from datetime import timedelta
from ..types import TrunkGroup
from typing import (
    List,
)


from .session import SessionState


class TrunkCommands(SessionState):
    """
    Interoffice trunk groups: occupancy, testing and maintenance.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def cmd_trunk(self, args: List[str]) -> str:
        """Enhanced trunk status and management with realistic state-aware behavior."""

        # Update trunk states based on time and network conditions
        self._update_trunk_states()

        if not args or args[0] == "status":
            # Dynamic trunk status with real-time variability
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")
            active_count = len([tg for tg in self.trunk_groups.values() if tg["status"] == "ACTIVE"])
            total_count = len(self.trunk_groups)
            avg_utilization = sum(tg["utilization"] for tg in self.trunk_groups.values() if tg["status"] == "ACTIVE") // active_count

            # Add realistic alerts and warnings
            alerts = []
            for tg_name, tg_data in self.trunk_groups.items():
                if tg_data["utilization"] > 85:
                    alerts.append(f"HIGH UTIL: {tg_name} at {tg_data['utilization']}%")
                elif tg_data["quality"] < 0.995:
                    alerts.append(f"QUALITY: {tg_name} below threshold")

            status_output = f"""Bell System Trunk Group Status Summary
{current_time}

Trunk Group      Capacity   Utilization   Status      Route        Quality
-----------      --------   -----------   ------      -----        -------"""

            for tg_name, tg_data in self.trunk_groups.items():
                util_status = "HIGH" if tg_data["utilization"] > 80 else "NORMAL" if tg_data["utilization"] > 30 else "LOW"
                if tg_data["status"] == "MAINT":
                    util_status = "MAINT"
                quality_pct = f"{tg_data['quality']:.3f}" if tg_data["quality"] > 0 else "N/A"
                status_output += f"\n{tg_name:<16} {tg_data['capacity']:<10} {tg_data['utilization']:>3}%        {util_status:<8}    {tg_data['route']:<12} {quality_pct}"

            status_output += f"""

Network Summary:
  Active Trunk Groups:     {active_count}/{total_count}
  Average Utilization:     {avg_utilization}%
  Peak Traffic Period:     {self._get_peak_period()}
  Revenue This Hour:       ${self.network_metrics['revenue_hour']:,}

System Alerts:"""

            if alerts:
                for alert in alerts[:3]:  # Show up to 3 alerts
                    status_output += f"\n  ⚠ {alert}"
            else:
                status_output += "\n  ✓ All systems operating normally"

            status_output += """

Commands:
  trunk detail <TG-xxx>     Detailed analysis and diagnostics
  trunk test <TG-xxx>       Initiate testing sequence
  trunk traffic <TG-xxx>    Real-time traffic monitoring
  trunk maintenance         Scheduled maintenance status"""

            return status_output

        elif args[0] == "detail" and len(args) > 1:
            tg_name = args[1].upper()
            if tg_name not in self.trunk_groups:
                return f"trunk: ERROR - Trunk group {tg_name} not found\nAvailable groups: {', '.join(self.trunk_groups.keys())}"

            tg = self.trunk_groups[tg_name]
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            # Calculate realistic metrics
            active_channels = int(tg["capacity"] * tg["utilization"] / 100) if tg["status"] == "ACTIVE" else 0
            setup_time = random.uniform(0.8, 2.4)
            error_rate = random.uniform(0.0001, 0.01) if tg["quality"] < 0.998 else random.uniform(0.00001, 0.0001)

            detail_output = f"""Detailed Trunk Group Analysis: {tg_name}
Analysis Time: {current_time}

Configuration:
  Trunk Group:        {tg_name}
  Circuit Type:       T1 Digital Carrier System
  Total Capacity:     {tg["capacity"]} voice channels
  Route:              {tg["route"]} Direct
  Equipment:          Western Electric D4 Channel Bank

Current Performance:
  Active Calls:       {active_channels} of {tg["capacity"]} channels
  Utilization:        {tg["utilization"]}% ({'Normal' if 40 <= tg["utilization"] <= 80 else 'High' if tg["utilization"] > 80 else 'Low'} range)
  Answer/Seizure:     {tg["quality"]:.1%} (Target: >95.0%)
  Post-Dial Delay:    {setup_time:.1f} seconds average

Traffic Analysis:
  Busy Hour CCS:      {int(active_channels * 36)} (within capacity)
  Peak Utilization:   {min(100, tg["utilization"] + random.randint(5, 15))}% at {random.randint(14, 16)}:{random.randint(0, 59):02d}
  Average Hold Time:  {random.uniform(2.8, 4.2):.1f} minutes
  Overflow Events:    {random.randint(0, 3)} (last 24 hours)

Quality Metrics:
  Bit Error Rate:     {error_rate:.2e} ({'Excellent' if error_rate < 0.0001 else 'Good' if error_rate < 0.001 else 'Marginal'})
  Noise Level:        {random.randint(-72, -60)} dBm (Good)
  Echo Return Loss:   {random.randint(32, 38)} dB (Acceptable)
  Jitter:             {random.uniform(0.1, 0.8):.1f} ms (Normal)

Maintenance Status:
  Last Test:          {(self.clock.now() - timedelta(days=random.randint(1, 7))).strftime('%B %d, %Y %H:%M')}
  Next Scheduled:     {(self.clock.now() + timedelta(days=random.randint(1, 14))).strftime('%B %d, %Y %H:%M')}
  Known Issues:       {'None' if tg["quality"] > 0.995 else 'Minor performance degradation'}
  Alarm Status:       {'Clear' if tg["status"] == 'ACTIVE' and tg["quality"] > 0.995 else 'Active alarms present'}

Recommendations:"""

            if tg["utilization"] > 85:
                detail_output += f"\n  • URGENT: Monitor closely - utilization at {tg['utilization']}%"
                detail_output += "\n  • Consider immediate capacity upgrade or load balancing"
            elif tg["utilization"] > 75:
                detail_output += f"\n  • Monitor during peak hours - current utilization {tg['utilization']}%"

            if tg["quality"] < 0.995:
                detail_output += "\n  • Quality below standard - investigate circuit issues"
                detail_output += "\n  • Schedule comprehensive testing"

            if tg["status"] == "MAINT":
                detail_output += "\n  • Trunk group in maintenance mode"
                detail_output += "\n  • Verify completion before returning to service"

            if not any([tg["utilization"] > 75, tg["quality"] < 0.995, tg["status"] == "MAINT"]):
                detail_output += "\n  • Continue normal monitoring procedures"
                detail_output += "\n  • Performance within acceptable parameters"

            return detail_output

        elif args[0] == "test" and len(args) > 1:
            tg_name = args[1].upper()
            if tg_name not in self.trunk_groups:
                return f"trunk: ERROR - Trunk group {tg_name} not found"

            tg = self.trunk_groups[tg_name]
            if tg["status"] == "MAINT":
                return f"trunk: Cannot test {tg_name} - trunk group in maintenance mode"

            # Simulate realistic testing sequence with variable results
            test_results: List[bool] = []
            test_start = self.clock.now().strftime("%H:%M:%S")

            # Various test phases with realistic pass/fail rates
            tests = [
                ("Signal continuity", 0.98),
                ("Noise level analysis", 0.95),
                ("Crosstalk measurement", 0.93),
                ("Timing verification", 0.97),
                ("Echo return loss", 0.92),
                ("Digital error rate", 0.90),
                ("Synchronization", 0.96),
                ("Power level check", 0.99)
            ]

            test_output = f"""Initiating comprehensive test sequence for {tg_name}...
Test started: {test_start}

Running Bell System Standard Test Suite BSP-100-120-001:
"""

            overall_pass = True
            for test_name, pass_rate in tests:
                # Degrade pass rate based on trunk quality
                adjusted_pass_rate = pass_rate * tg["quality"]
                passed = random.random() < adjusted_pass_rate
                status = "PASS" if passed else "FAIL"
                if not passed:
                    overall_pass = False

                # Add realistic test values
                if "noise" in test_name.lower():
                    value = f" ({random.randint(-72, -60)} dBm)"
                elif "error" in test_name.lower():
                    value = f" ({random.uniform(0.00001, 0.001):.2e})"
                elif "echo" in test_name.lower():
                    value = f" ({random.randint(30, 40)} dB)"
                else:
                    value = ""

                test_output += f"\nPhase {len(test_results)+1}: {test_name:<20} [{status}]{value}"
                test_results.append(passed)

            test_end = self.clock.now().strftime("%H:%M:%S")

            test_output += f"""

Test completed: {test_end}
Duration: {random.randint(45, 180)} seconds

Results Summary:
  Tests Passed: {sum(test_results)}/{len(test_results)}
  Overall Status: {'PASS' if overall_pass else 'FAIL'}
  Quality Rating: {tg["quality"]:.1%}
"""

            if overall_pass:
                test_output += f"  Recommendation: {tg_name} certified for continued operation"
                # Slightly improve quality on successful test
                tg["quality"] = min(0.999, tg["quality"] + 0.001)
            else:
                test_output += f"  Recommendation: Schedule maintenance for {tg_name}"
                test_output += "\n  Action Required: Investigate failed test phases"
                # Degrade quality on failed test
                tg["quality"] = max(0.980, tg["quality"] - 0.005)

            test_output += f"""

Test log saved: /att/network/tests/{tg_name.lower()}_{self.clock.now().strftime('%m%d_%H%M')}.log
Next test due: {(self.clock.now() + timedelta(days=30)).strftime('%B %d, %Y')}"""

            return test_output

        elif args[0] == "traffic" and len(args) > 1:
            tg_name = args[1].upper()
            if tg_name not in self.trunk_groups:
                return f"trunk: ERROR - Trunk group {tg_name} not found"

            tg = self.trunk_groups[tg_name]
            return self._show_trunk_traffic_monitor(tg_name, tg)

        elif args[0] == "maintenance":
            return self._show_trunk_maintenance_schedule()

        else:
            available_commands = ["status", "detail", "test", "traffic", "maintenance"]
            return f"trunk: Unknown option '{args[0]}'\nAvailable commands: {', '.join(available_commands)}"
    def _update_trunk_states(self) -> None:
        """Update trunk group states based on time and network conditions."""
        import random

        # Simulate realistic state changes over time
        for tg_name, tg_data in self.trunk_groups.items():
            if tg_data["status"] == "ACTIVE":
                # Small random variations in utilization
                change = random.randint(-3, 5)
                tg_data["utilization"] = max(0, min(100, tg_data["utilization"] + change))

                # Quality can degrade slowly over time
                if random.random() < 0.05:  # 5% chance of quality change
                    quality_change = random.uniform(-0.002, 0.001)
                    tg_data["quality"] = max(0.990, min(0.999, tg_data["quality"] + quality_change))
    def _get_peak_period(self) -> str:
        """Get peak traffic period based on current time."""
        hour = self.clock.now().hour
        if 8 <= hour <= 10:
            return "Morning Business (08:00-10:00)"
        elif 14 <= hour <= 16:
            return "Afternoon Peak (14:00-16:00)"
        elif 19 <= hour <= 21:
            return "Evening Social (19:00-21:00)"
        else:
            return "Off-Peak Period"
    def _show_trunk_traffic_monitor(self, tg_name: str,
                                    tg_data: TrunkGroup) -> str:
        """Show real-time traffic monitoring for a trunk group."""
        import random

        if tg_data["status"] == "MAINT":
            return f"Traffic monitoring unavailable - {tg_name} in maintenance mode"

        current_time = self.clock.now().strftime("%H:%M:%S")
        active_channels = int(tg_data["capacity"] * tg_data["utilization"] / 100)

        # Generate realistic traffic pattern
        traffic_samples = []
        for i in range(12):  # Last 12 5-minute intervals
            time_offset = (11 - i) * 5
            sample_time = (self.clock.now() - timedelta(minutes=time_offset)).strftime("%H:%M")
            utilization = max(0, min(100, tg_data["utilization"] + random.randint(-10, 10)))
            traffic_samples.append((sample_time, utilization))

        monitor_output = f"""Real-Time Traffic Monitor: {tg_name}
Monitor Time: {current_time}
Update Interval: 5 minutes

Current Status:
  Active Channels:    {active_channels}/{tg_data["capacity"]}
  Utilization:        {tg_data["utilization"]}%
  Call Rate:          {random.randint(45, 180)} calls/hour
  Revenue Rate:       ${random.randint(250, 850)}/hour

Traffic History (Last Hour):
Time    Util%   Channels   Revenue/5min
----    -----   --------   ------------"""

        for sample_time, utilization in traffic_samples:
            channels = int(tg_data["capacity"] * utilization / 100)
            revenue = random.randint(20, 80)
            monitor_output += f"\n{sample_time}   {utilization:>3}%    {channels:>2}/{tg_data['capacity']:<2}       ${revenue}"

        # Add real-time alerts
        alerts = []
        if tg_data["utilization"] > 90:
            alerts.append("⚠ CRITICAL: Utilization above 90% - overflow risk")
        elif tg_data["utilization"] > 80:
            alerts.append("⚠ WARNING: High utilization - monitor closely")

        if tg_data["quality"] < 0.995:
            alerts.append("⚠ QUALITY: Performance below threshold")

        if alerts:
            monitor_output += "\n\nActive Alerts:"
            for alert in alerts:
                monitor_output += f"\n  {alert}"
        else:
            monitor_output += "\n\n✓ No active alerts - normal operation"

        monitor_output += f"\n\nPress 'trunk detail {tg_name}' for comprehensive analysis"

        return monitor_output
    def _show_trunk_maintenance_schedule(self) -> str:
        """Show trunk group maintenance schedule."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M")

        schedule_output = f"""Bell System Trunk Group Maintenance Schedule
Generated: {current_time}

Scheduled Maintenance (Next 30 Days):
Date           Time        Trunk Group    Type              Duration
----           ----        -----------    ----              --------"""

        # Generate realistic maintenance schedule
        for i in range(5):
            maint_date = self.clock.now() + timedelta(days=random.randint(1, 30))
            maint_time = f"{random.randint(1, 4):02d}:{random.choice(['00', '30'])}"
            tg_name = random.choice(list(self.trunk_groups.keys()))
            maint_type = random.choice(["Preventive", "Calibration", "Upgrade", "Testing"])
            duration = f"{random.randint(2, 6)} hours"

            schedule_output += f"\n{maint_date.strftime('%b %d')}        {maint_time}       {tg_name}      {maint_type:<12}      {duration}"

        # Show current maintenance
        maint_trunks = [tg for tg, data in self.trunk_groups.items() if data["status"] == "MAINT"]
        if maint_trunks:
            schedule_output += "\n\nCurrently in Maintenance:"
            for tg_name in maint_trunks:
                schedule_output += f"\n  {tg_name}: Scheduled maintenance in progress"
                schedule_output += f"\n           Expected completion: {(self.clock.now() + timedelta(hours=random.randint(1, 4))).strftime('%H:%M')}"

        schedule_output += """

Maintenance Procedures:
  • All maintenance during low-traffic periods (01:00-05:00)
  • Automatic rerouting activated during maintenance
  • 24-hour advance notification to Network Operations
  • Emergency override procedures available

Contact: Central Maintenance Office ext 4200"""

        return schedule_output
