"""
Total Network Data System: collection, analysis and forecasting.
"""

import random
from datetime import timedelta
from typing import (
    List,
)
from ..types import (
    TndsData,
)


from .session import SessionState


class TndsCommands(SessionState):
    """
    Total Network Data System: collection, analysis and forecasting.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _get_tnds_briefing(self) -> str:
        """Get TNDS Analyst briefing."""
        return """
TNDS ANALYST BRIEFING

Primary Responsibilities:
- Total Network Data System operations
- Traffic data collection and analysis
- Network performance measurement
- Capacity planning data preparation

Current Priorities:
- Complete TNDS data collection cycle 1 of 4
- Generate traffic analysis reports for planning
- Monitor network performance against objectives
- Prepare capacity forecasting models

Key Commands: tnds, netdata, analysis, forecast, modeling, traffic
"""
    def cmd_tnds(self, args: List[str]) -> str:
        """Enhanced Total Network Data System with realistic operational dynamics."""

        # Update TNDS state based on current time and network conditions
        self._update_tnds_state()

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")
            cycle = self._get_current_collection_cycle()

            return f"""Total Network Data System (TNDS) - Version 3.2A
Bell System Network Traffic Data Collection and Analysis
{current_time}

Current Operations Status:
  Collection Cycle:        {cycle['name']} ({cycle['time_range']})
  Data Points Collected:   {self.tnds_data['records_today']:,} (today)
  Processing Status:       {self.tnds_data['processing_status']}
  Storage Utilization:     {self.tnds_data['storage_used']}% of {self.tnds_data['storage_capacity']}GB

System Performance:
  Collection Success Rate: {self.tnds_data['collection_success']:.1%}
  Processing Efficiency:   {self.tnds_data['processing_efficiency']:.1%}
  Data Quality Index:      {self.tnds_data['data_quality']:.1%}
  Forecast Accuracy:       {self.tnds_data['forecast_accuracy']:.1%}

Available Commands:
  tnds status             - Detailed system operational status
  tnds collect            - Data collection operations and control
  tnds analysis           - Traffic analysis reports and statistics
  tnds forecast           - Traffic growth forecasting models
  tnds hierarchy          - Network hierarchy analysis
  tnds routing            - Dynamic routing analysis
  tnds reports            - Generate standardized reports
  tnds export             - Data export for engineering studies

Current Priority: {self._get_tnds_priority_task()}
Next Scheduled Operation: {self._get_next_tnds_operation()}

Project References: NP-8306 (TNDS Phase III Implementation)
Work Orders: WO-83054 (Data quality improvement initiatives)"""

        elif args[0] == "status":
            return self._show_tnds_detailed_status()

        elif args[0] == "collect":
            if len(args) > 1:
                return self._handle_tnds_collection_command(args[1:])
            else:
                return self._show_tnds_collection_status()

        elif args[0] == "analysis":
            if len(args) > 1:
                return self._generate_tnds_analysis_report(args[1])
            else:
                return self._generate_tnds_analysis_report("standard")

        elif args[0] == "forecast":
            if len(args) > 1:
                return self._generate_tnds_forecast(args[1])
            else:
                return self._generate_tnds_forecast("monthly")

        elif args[0] == "hierarchy":
            return self._show_network_hierarchy_analysis()

        elif args[0] == "routing":
            return self._show_dynamic_routing_analysis()

        elif args[0] == "reports":
            if len(args) > 1:
                return self._generate_tnds_report(args[1])
            else:
                return self._show_available_tnds_reports()

        elif args[0] == "export":
            if len(args) > 1:
                return self._handle_tnds_export(args[1:])
            else:
                return self._show_tnds_export_options()

        else:
            available_commands = ["status", "collect", "analysis", "forecast", "hierarchy", "routing", "reports", "export"]
            return f"tnds: Unknown option '{args[0]}'\nAvailable commands: {', '.join(available_commands)}"
    def _update_tnds_state(self) -> None:
        """Update TNDS operational state based on time and network conditions."""
        import random

        if not hasattr(self, 'tnds_data'):
            # Initialize TNDS operational data
            hour = self.clock.now().hour
            base_records = 2800000  # Base daily record count

            self.tnds_data: TndsData = {
                'records_today': int(base_records * (hour / 24) * random.uniform(0.95, 1.05)),
                'processing_status': random.choice(['Normal operation', 'High volume processing', 'Backlog processing']),
                'storage_used': random.randint(65, 85),
                'storage_capacity': random.choice([50, 75, 100]),  # GB capacity
                'collection_success': random.uniform(0.995, 0.999),
                'processing_efficiency': random.uniform(0.92, 0.98),
                'data_quality': random.uniform(0.996, 0.999),
                'forecast_accuracy': random.uniform(0.94, 0.97),
                'collection_points': random.randint(1240, 1260),
                'active_streams': random.randint(45, 50),
                'last_update': self.clock.now()
            }
        else:
            # Update existing data with small variations
            time_since_update = (self.clock.now() - self.tnds_data['last_update']).total_seconds() / 60
            if time_since_update > 5:  # Update every 5 minutes
                self.tnds_data['records_today'] += random.randint(1000, 5000)
                self.tnds_data['storage_used'] = min(95, self.tnds_data['storage_used'] + random.randint(-1, 2))
                self.tnds_data['last_update'] = self.clock.now()
    def _get_current_collection_cycle(self) -> dict:
        """Get current TNDS collection cycle information."""
        hour = self.clock.now().hour

        if 0 <= hour < 6:
            return {"name": "Cycle 1", "time_range": "00:00-06:00", "description": "Overnight processing"}
        elif 6 <= hour < 12:
            return {"name": "Cycle 2", "time_range": "06:00-12:00", "description": "Morning business traffic"}
        elif 12 <= hour < 18:
            return {"name": "Cycle 3", "time_range": "12:00-18:00", "description": "Peak traffic period"}
        else:
            return {"name": "Cycle 4", "time_range": "18:00-24:00", "description": "Evening traffic analysis"}
    def _get_tnds_priority_task(self) -> str:
        """Get current TNDS priority task based on time and conditions."""
        import random

        hour = self.clock.now().hour

        priority_tasks = {
            "morning": ["Peak traffic forecast validation", "Overnight data processing completion", "System health verification"],
            "business": ["Real-time traffic monitoring", "Capacity utilization analysis", "Performance optimization"],
            "peak": ["Traffic load balancing analysis", "Overflow pattern monitoring", "Revenue optimization tracking"],
            "evening": ["Daily report generation", "Archive preparation", "Forecast model updates"]
        }

        if 6 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "peak"
        elif 18 <= hour < 22:
            period = "evening"
        else:
            period = "business"

        return random.choice(priority_tasks[period])
    def _get_next_tnds_operation(self) -> str:
        """Get next scheduled TNDS operation."""

        next_ops = [
            f"Archive cycle: {(self.clock.now() + timedelta(hours=random.randint(2, 8))).strftime('%H:%M')}",
            f"Forecast update: {(self.clock.now() + timedelta(hours=random.randint(1, 4))).strftime('%H:%M')}",
            f"Report generation: {(self.clock.now() + timedelta(hours=random.randint(4, 12))).strftime('%H:%M')}",
            f"Data quality check: {(self.clock.now() + timedelta(hours=random.randint(1, 6))).strftime('%H:%M')}"
        ]

        return random.choice(next_ops)
    def _show_tnds_detailed_status(self) -> str:
        """Show detailed TNDS system status."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")
        cycle = self._get_current_collection_cycle()

        status_output = f"""TNDS System Status - Detailed Operations Report
Generated: {current_time}

Data Collection Status:
  Collection Points Online:    {self.tnds_data['collection_points']} of 1,255 total ({self.tnds_data['collection_points']/1255:.1%})
  Data Streams Active:         {self.tnds_data['active_streams']} trunk groups monitored
  Collection Interval:         5-minute samples (standard)
  Current Cycle:              {cycle['name']} - {cycle['description']}
  Collection Success Rate:     {self.tnds_data['collection_success']:.2%}

Processing Infrastructure:
  Data Processor A:            {'ACTIVE' if random.random() > 0.1 else 'MAINTENANCE'} - Primary processing unit
  Data Processor B:            {'STANDBY' if random.random() > 0.2 else 'ACTIVE'} - Backup/overflow processing
  Storage System:              {self.tnds_data['storage_used']}% utilized ({self.tnds_data['storage_capacity']}GB capacity)
  Analysis Engine:             {self.tnds_data['processing_status']}
  Database Server:             {'Online' if random.random() > 0.05 else 'Performance degraded'}

Current Data Flow (Last Hour):
  Call Detail Records:         {random.randint(45000, 85000):,} records
  Traffic Measurements:        {random.randint(8000, 15000):,} samples
  Network Performance Data:    {random.randint(3000, 8000):,} measurements
  Billing Records:             {random.randint(18000, 35000):,} transactions
  Equipment Status Reports:    {random.randint(500, 1200):,} status updates

Quality Metrics:
  Data Completeness:           {self.tnds_data['data_quality']:.2%}
  Validation Error Rate:       {(1 - self.tnds_data['data_quality']):.3%}
  Missing Timestamps:          {random.uniform(0.001, 0.01):.3%}
  Format Compliance:           {random.uniform(0.998, 0.999):.2%}
  Cross-Reference Accuracy:    {random.uniform(0.994, 0.998):.2%}

Performance Indicators:
  Processing Efficiency:       {self.tnds_data['processing_efficiency']:.1%}
  Average Response Time:       {random.uniform(0.8, 2.1):.1f} seconds
  Peak Hour Capacity:          {random.randint(85, 95)}% of maximum
  Forecast Accuracy:           {self.tnds_data['forecast_accuracy']:.1%} (30-day average)

Network Analysis Results:
  Peak Traffic Hour:           {random.randint(14, 16)}:{random.randint(0, 59):02d} - {random.randint(16, 18)}:{random.randint(0, 59):02d} EST
  Current Network Load:        {sum(tg['utilization'] for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE') // len([tg for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE'])}% of capacity
  Blocking Probability:        {random.uniform(0.001, 0.008):.3f} (Target: <0.01)
  Revenue per Hour:            ${random.randint(45000, 85000):,}

Scheduled Operations:
  Next Archive Cycle:          {(self.clock.now() + timedelta(hours=random.randint(4, 8))).strftime('%A %H:%M')}
  Forecast Model Update:       Daily at 18:00 EST
  Weekly Report Generation:    Monday 08:00 EST
  Database Maintenance:        Sunday 02:00-04:00 EST

Active Alerts:"""

        # Generate realistic alerts
        alerts = []
        if self.tnds_data['storage_used'] > 85:
            alerts.append("⚠ WARNING: Storage utilization above 85%")
        if self.tnds_data['collection_success'] < 0.998:
            alerts.append("⚠ NOTICE: Collection success rate below target")
        if random.random() < 0.2:
            alerts.append("ℹ INFO: High volume processing due to peak traffic")

        if alerts:
            for alert in alerts:
                status_output += f"\n  {alert}"
        else:
            status_output += "\n  ✓ All systems operating within normal parameters"

        status_output += """

Contact Information:
  TNDS Operations Center:      ext 4800
  Database Administration:     ext 4825
  Network Analysis Team:       ext 4850"""

        return status_output
    def _show_tnds_collection_status(self) -> str:
        """Show TNDS data collection operations status."""

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        collection_output = f"""TNDS Data Collection Operations
Status Report: {current_time}

Collection Infrastructure:
  Remote Collection Points:    {self.tnds_data['collection_points']} locations
  Data Communication Links:    T1 dedicated circuits
  Collection Frequency:        5-minute intervals (288 samples/day)
  Backup Collection System:    {'Active' if random.random() > 0.9 else 'Standby'}

Current Collection Status:
  Points Responding:           {self.tnds_data['collection_points'] - random.randint(0, 8)} of {self.tnds_data['collection_points']}
  Data Streams Active:         {self.tnds_data['active_streams']} trunk groups
  Collection Success Rate:     {self.tnds_data['collection_success']:.2%}
  Average Response Time:       {random.uniform(0.5, 1.8):.1f} seconds

Collection Volume (Last 24 Hours):
  Call Detail Records:         {random.randint(850000, 1200000):,}
  Traffic Measurements:        {random.randint(180000, 250000):,}
  Performance Metrics:         {random.randint(65000, 95000):,}
  Equipment Status:            {random.randint(12000, 18000):,}
  Billing Transactions:        {random.randint(420000, 580000):,}

Collection Points by Region:
  Northeast Corridor:          {random.randint(280, 320)} points (NYC, BOS, PHL, WAS)
  Southeast Region:            {random.randint(180, 220)} points (ATL, MIA, TAM, CHA)
  Central Region:              {random.randint(220, 260)} points (CHI, DET, STL, CLE)
  Western Region:              {random.randint(160, 200)} points (LAX, SFO, SEA, DEN)
  Southwest Region:            {random.randint(140, 180)} points (DAL, HOU, PHX, SAN)

Data Quality Assessment:
  Format Validation:           {random.uniform(0.998, 0.999):.3%} pass rate
  Timestamp Accuracy:          {random.uniform(0.999, 1.000):.3%} compliance
  Cross-Reference Check:       {random.uniform(0.995, 0.998):.3%} validation
  Completeness Index:          {self.tnds_data['data_quality']:.2%}

Collection Schedule:
  Standard Collection:         Continuous 24/7 operation
  Peak Period Enhancement:     14:00-16:00 EST (1-minute intervals)
  Maintenance Window:          Sunday 02:00-04:00 EST
  Archive Transfer:            Daily 01:00 EST to Bell Labs

Commands:
  tnds collect start           Initiate collection cycle
  tnds collect stop            Halt collection (emergency only)
  tnds collect test            Test collection point connectivity
  tnds collect status <region> Regional collection status"""

        return collection_output
    def _generate_tnds_analysis_report(self, report_type: str) -> str:
        """Generate TNDS traffic analysis report with realistic data patterns."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        if report_type == "standard":
            period = "November 7-14, 1983"
            days = 7
        elif report_type == "monthly":
            period = "November 1983"
            days = 30
        elif report_type == "weekly":
            period = f"Week of {(self.clock.now() - timedelta(days=7)).strftime('%B %d, %Y')}"
            days = 7
        else:
            period = "Custom Period"
            days = 7

        # Generate realistic traffic metrics
        base_calls = 850000 * days
        completion_rate = random.uniform(0.975, 0.995)
        total_attempts = int(base_calls * random.uniform(0.95, 1.05))
        successful_calls = int(total_attempts * completion_rate)

        analysis_output = f"""TNDS Traffic Analysis Report
Generated: {current_time}
Analysis Period: {period}

NETWORK PERFORMANCE SUMMARY
{'=' * 50}
Total Call Attempts:          {total_attempts:,}
Successful Completions:       {successful_calls:,} ({completion_rate:.1%})
Average Call Setup Time:      {random.uniform(1.8, 2.4):.1f} seconds
Network Efficiency:           {random.uniform(0.94, 0.97):.1%}
Revenue Generated:            ${random.randint(450000 * days, 650000 * days):,}

TRAFFIC PATTERNS ANALYSIS
{'=' * 50}"""

        # Generate daily peak traffic data
        peak_hours = []
        for day in range(min(days, 7)):  # Show up to 7 days of peaks
            day_name = (self.clock.now() - timedelta(days=day)).strftime('%A')
            peak_time = f"{random.randint(14, 16)}:{random.randint(0, 59):02d}"
            peak_ccs = random.randint(850, 950)
            peak_hours.append((day_name, peak_time, peak_ccs))

        for day_name, peak_time, peak_ccs in peak_hours:
            analysis_output += f"\n{day_name:<12} Peak: {peak_time} EST ({peak_ccs} CCS)"

        analysis_output += f"""

Busy Season Factor:           {random.uniform(1.10, 1.20):.2f} (Holiday adjustment)
Growth Rate vs Previous:      {random.uniform(2.8, 4.2):+.1f}% call volume change
Weekend Traffic Factor:       {random.uniform(0.65, 0.75):.2f} of weekday volume

TRUNK GROUP UTILIZATION
{'=' * 50}
Average Network Utilization:  {sum(tg['utilization'] for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE') // len([tg for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE'])}%"""

        # Show top utilized trunk groups
        sorted_trunks = sorted([(name, tg['utilization'], tg['route']) for name, tg in self.trunk_groups.items() if tg['status'] == 'ACTIVE'],
                              key=lambda x: x[1], reverse=True)

        for i, (tg_name, utilization, route) in enumerate(sorted_trunks[:5]):
            utilization_status = "HIGH" if utilization > 80 else "NORMAL" if utilization > 40 else "LOW"
            analysis_output += f"\n{i+1}. {tg_name:<12} {utilization:>3}% ({utilization_status:<6}) {route}"

        analysis_output += f"""

Overflow Events:              {random.randint(8, 25)} occurrences (all recovered <30 sec)
Peak Trunk Utilization:       {max(tg['utilization'] for tg in self.trunk_groups.values())}%
Load Balancing Efficiency:    {random.uniform(0.91, 0.96):.1%}

REVENUE AND ECONOMIC ANALYSIS
{'=' * 50}
Revenue per Call:             ${random.uniform(0.45, 0.75):.2f} average
Peak Hour Revenue Rate:       ${random.randint(25000, 45000):,}/hour
Interstate Long Distance:     {random.uniform(0.35, 0.45):.1%} of total revenue
International Traffic:        {random.uniform(0.08, 0.15):.1%} of total revenue
Operator Assisted:            {random.uniform(0.12, 0.18):.1%} of total revenue

FORECASTING RESULTS
{'=' * 50}
Next Month Peak Forecast:     {random.randint(920, 980)} CCS ({random.uniform(5, 8):+.1f}% vs current)
Capacity Requirements:        {random.randint(2, 5)} additional trunk groups recommended
Investment Requirement:       ${random.uniform(1.0, 2.5):.1f}M for network expansion
Growth Projection (6 months): {random.uniform(12, 18):+.1f}% call volume increase

RECOMMENDATIONS
{'=' * 50}"""

        # Generate realistic recommendations
        recommendations = []
        high_util_trunks = [name for name, tg in self.trunk_groups.items() if tg['utilization'] > 80 and tg['status'] == 'ACTIVE']

        if high_util_trunks:
            recommendations.append(f"1. Monitor {high_util_trunks[0]} for immediate capacity upgrade")
        else:
            recommendations.append("1. All trunk groups operating within capacity")

        recommendations.extend([
            "2. Implement Dynamic Non-Hierarchical Routing (DNHR) on high-traffic routes",
            "3. Schedule capacity planning review for Q1 1984",
            "4. Continue TNDS data quality improvement initiatives",
            f"5. Evaluate load balancing effectiveness on {random.choice(['Route 1', 'Route 3', 'Eastern Corridor'])}"
        ])

        for rec in recommendations:
            analysis_output += f"\n{rec}"

        analysis_output += f"""

Report Distribution:
  Network Planning Engineering: Copy 1
  Traffic Engineering: Copy 2
  Revenue Analysis: Copy 3
  Bell Laboratories: Copy 4 (for research)

Next Analysis Report: {(self.clock.now() + timedelta(days=7)).strftime('%B %d, %Y')}"""

        return analysis_output
    def _handle_tnds_collection_command(self, args: List[str]) -> str:
        """Handle TNDS data collection subcommands (start, stop, verify, poll)."""
        action = args[0].lower()
        timestamp = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        if action == "start":
            self.tnds_data['processing_status'] = 'Normal operation'
            return f"""TNDS Data Collection - Start Request
{'=' * 50}
Requested: {timestamp}

EADAS collection scheduler ACKNOWLEDGED
Collection points activated:  {self.tnds_data['collection_points']} of 1,255
Active data streams:          {self.tnds_data['active_streams']} trunk groups
Polling interval:             300 seconds (5 minute registers)

Status: COLLECTION ACTIVE
Authorization: WO-83054"""

        if action == "stop":
            self.tnds_data['processing_status'] = 'Collection suspended'
            return f"""TNDS Data Collection - Stop Request
{'=' * 50}
Requested: {timestamp}

WARNING: Halting collection creates gaps in the traffic record.
Peak-hour data cannot be reconstructed once the interval closes.

Collection points quiesced:   {self.tnds_data['collection_points']}
Records buffered for flush:   {random.randint(400, 2200):,}

Status: COLLECTION SUSPENDED
Resume with: tnds collect start"""

        if action == "verify":
            error_rate = 1 - self.tnds_data['data_quality']
            return f"""TNDS Collection Verification
{'=' * 50}
Verification Run: {timestamp}

REGISTER INTEGRITY
{'=' * 35}
Collection Points Polled:     {self.tnds_data['collection_points']}
Points Responding:            {self.tnds_data['collection_points'] - random.randint(0, 4)}
Success Rate:                 {self.tnds_data['collection_success']:.3%}
Validation Error Rate:        {error_rate:.3%}

DATA QUALITY
{'=' * 35}
Completeness Index:           {self.tnds_data['data_quality']:.3%}
Records Accepted Today:       {self.tnds_data['records_today']:,}
Records Rejected:             {int(self.tnds_data['records_today'] * error_rate):,}

Verification Result: {'PASS' if self.tnds_data['data_quality'] > 0.995 else 'REVIEW REQUIRED'}"""

        if action == "poll":
            target = args[1].upper() if len(args) > 1 else "ALL"
            polled = [t for t in self.trunk_groups if target in ("ALL", t)] or list(self.trunk_groups)
            output = f"""TNDS On-Demand Poll
{'=' * 50}
Poll Initiated: {timestamp}
Target: {target}

TRUNK GROUP REGISTERS
{'=' * 35}"""
            for tg_name in polled:
                tg = self.trunk_groups[tg_name]
                ccs = int(tg['capacity'] * tg['utilization'] * 0.36)
                output += f"""
{tg_name}:
  Route:              {tg['route']}
  Usage:              {ccs} CCS
  Utilization:        {tg['utilization']}%
  Register Status:    {'READ OK' if tg['status'] == 'ACTIVE' else 'OUT OF SERVICE'}"""
            output += f"\n\nPoll complete. {len(polled)} register set(s) read."
            return output

        return (f"tnds collect: Unknown action '{args[0]}'\n"
                "Available actions: start, stop, verify, poll [trunk-group]")
    def _generate_tnds_forecast(self, period: str) -> str:
        """Generate a TNDS traffic growth forecast for the requested period."""
        horizons = {
            "monthly": ("Monthly", 1, 30),
            "quarterly": ("Quarterly", 3, 90),
            "annual": ("Annual", 12, 365),
        }
        label, months, days = horizons.get(period.lower(), ("Monthly", 1, 30))
        growth = random.uniform(0.9, 1.8) * months
        current_ccs = sum(
            int(tg['capacity'] * tg['utilization'] * 0.36)
            for tg in self.trunk_groups.values()
        )
        projected_ccs = int(current_ccs * (1 + growth / 100))
        target = (self.clock.now() + timedelta(days=days)).strftime('%B %Y')

        output = f"""TNDS Traffic Forecast - {label} Model
Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}
Forecast Horizon: {target}
{'=' * 55}

MODEL PARAMETERS
{'=' * 40}
Forecast Method:              Exponential smoothing with seasonal index
Historical Base:              36 months of EADAS register data
Model Accuracy (backtest):    {self.tnds_data['forecast_accuracy']:.1%}
Confidence Interval:          {random.uniform(90, 95):.0f}%

AGGREGATE PROJECTION
{'=' * 40}
Current Measured Load:        {current_ccs:,} CCS
Projected Load ({label}):     {projected_ccs:,} CCS
Growth Rate:                  {growth:+.1f}%
Busy Hour Shift:              {random.choice(['None', '+30 min later', '-15 min earlier'])}

PER-ROUTE FORECAST
{'=' * 40}"""

        for tg_name, tg in self.trunk_groups.items():
            if tg['status'] != 'ACTIVE':
                continue
            route_growth = growth * random.uniform(0.6, 1.5)
            projected_util = min(100, tg['utilization'] * (1 + route_growth / 100))
            flag = 'BLOCKING RISK' if projected_util > 85 else 'WITHIN CAPACITY'
            output += f"""
{tg_name} ({tg['route']}):
  Current Utilization:  {tg['utilization']}%
  Projected:            {projected_util:.0f}%
  Growth:               {route_growth:+.1f}%
  Assessment:           {flag}"""

        at_risk = [
            n for n, t in self.trunk_groups.items()
            if t['status'] == 'ACTIVE' and t['utilization'] * (1 + growth / 100) > 85
        ]
        output += f"""

CAPACITY RECOMMENDATIONS
{'=' * 40}"""
        if at_risk:
            for i, name in enumerate(at_risk, 1):
                output += f"\n{i}. Augment {name} before {target} - projected blocking above P.01 grade of service"
            output += f"\n{len(at_risk) + 1}. Submit trunk order via TIRKS for affected routes"
        else:
            output += "\n1. No augmentation required within forecast horizon"
            output += "\n2. Continue routine quarterly capacity review"

        output += f"""

Distribution: Network Planning, Traffic Engineering
Project Reference: NP-8306 (TNDS Phase III)
Next Forecast Run: {(self.clock.now() + timedelta(days=days)).strftime('%B %d, %Y')}"""
        return output
    def _show_available_tnds_reports(self) -> str:
        """Show the catalog of standard TNDS reports available for generation."""
        return f"""TNDS Standard Report Catalog
{'=' * 55}

AVAILABLE REPORTS
{'=' * 45}
  tnds reports traffic        Traffic Usage Summary (TUS-1)
  tnds reports blocking       Blocking and Overflow Report (BOR-3)
  tnds reports quality        Data Quality Assurance Report (DQA-2)
  tnds reports capacity       Capacity Exhaust Projection (CEP-4)
  tnds reports monthly        Monthly Network Summary (MNS-1)

REPORT CHARACTERISTICS
{'=' * 45}
Source Data:                  EADAS collection registers
Retention Period:             36 months on-line, 7 years archived
Standard Distribution:        Network Planning, Traffic Engineering,
                              Revenue Accounting, Bell Laboratories
Generation Time:              2-6 minutes depending on period

SCHEDULING
{'=' * 45}
Daily Reports:                Generated 02:00 EST
Weekly Reports:               Generated Monday 03:00 EST
Monthly Reports:              Generated first business day 04:00 EST
Last Generation Run:          {(self.clock.now() - timedelta(hours=random.randint(2, 20))).strftime('%B %d, %Y %H:%M EST')}

Usage: tnds reports <report-name>"""
    def _generate_tnds_report(self, report_name: str) -> str:
        """Generate a named standard TNDS report."""
        name = report_name.lower()
        stamp = self.clock.now().strftime('%B %d, %Y %H:%M EST')
        active = {n: t for n, t in self.trunk_groups.items() if t['status'] == 'ACTIVE'}

        if name == "traffic":
            total_ccs = sum(int(t['capacity'] * t['utilization'] * 0.36) for t in active.values())
            output = f"""Traffic Usage Summary (TUS-1)
Generated: {stamp}
{'=' * 55}

NETWORK TOTALS
{'=' * 45}
Measured Trunk Groups:        {len(active)}
Total Offered Load:           {total_ccs:,} CCS
Average Utilization:          {sum(t['utilization'] for t in active.values()) / max(1, len(active)):.1f}%
Records Processed:            {self.tnds_data['records_today']:,}

PER-GROUP USAGE
{'=' * 45}"""
            for tg_name, tg in active.items():
                output += (f"\n{tg_name:<12} {tg['route']:<10} "
                           f"{int(tg['capacity'] * tg['utilization'] * 0.36):>6,} CCS  "
                           f"{tg['utilization']:>3}%")
            return output + "\n\nDistribution: Traffic Engineering, Network Planning"

        if name == "blocking":
            output = f"""Blocking and Overflow Report (BOR-3)
Generated: {stamp}
{'=' * 55}

GRADE OF SERVICE OBJECTIVE: P.01 (final groups)
{'=' * 45}"""
            for tg_name, tg in active.items():
                blocking = max(0.0001, (tg['utilization'] - 60) / 4000)
                status = 'OBJECTIVE MET' if blocking <= 0.01 else 'OBJECTIVE EXCEEDED'
                output += f"""
{tg_name} ({tg['route']}):
  Utilization:          {tg['utilization']}%
  Measured Blocking:    {blocking:.3%}
  Assessment:           {status}"""
            return output + "\n\nDistribution: Network Operations, Traffic Engineering"

        if name == "quality":
            error_rate = 1 - self.tnds_data['data_quality']
            return f"""Data Quality Assurance Report (DQA-2)
Generated: {stamp}
{'=' * 55}

COLLECTION INTEGRITY
{'=' * 45}
Collection Success Rate:      {self.tnds_data['collection_success']:.3%}
Data Completeness:            {self.tnds_data['data_quality']:.3%}
Validation Error Rate:        {error_rate:.3%}
Processing Efficiency:        {self.tnds_data['processing_efficiency']:.1%}

EXCEPTION SUMMARY
{'=' * 45}
Records Rejected:             {int(self.tnds_data['records_today'] * error_rate):,}
Missing Register Reads:       {random.randint(0, 12)}
Out-of-Range Values:          {random.randint(2, 30)}
Duplicate Records Purged:     {random.randint(0, 8)}

Assessment: {'WITHIN STANDARD' if error_rate < 0.005 else 'REVIEW REQUIRED'}
Distribution: Data Administration, Bell Laboratories"""

        if name == "capacity":
            output = f"""Capacity Exhaust Projection (CEP-4)
Generated: {stamp}
{'=' * 55}

PROJECTED EXHAUST BY ROUTE
{'=' * 45}"""
            for tg_name, tg in active.items():
                months = max(1, int((90 - tg['utilization']) / random.uniform(0.8, 2.2)))
                exhaust = (self.clock.now() + timedelta(days=months * 30)).strftime('%B %Y')
                output += f"""
{tg_name} ({tg['route']}):
  Current Utilization:  {tg['utilization']}%
  Months to Exhaust:    {months}
  Projected Exhaust:    {exhaust}
  Action:               {'Trunk order required' if months <= 6 else 'Monitor'}"""
            return output + "\n\nDistribution: Network Planning, Capital Planning"

        if name == "monthly":
            return f"""Monthly Network Summary (MNS-1)
Generated: {stamp}
Reporting Period: {self.clock.now().strftime('%B %Y')}
{'=' * 55}

VOLUME SUMMARY
{'=' * 45}
Total Records Collected:      {self.tnds_data['records_today'] * 30:,}
Collection Points:            {self.tnds_data['collection_points']} of 1,255
Active Data Streams:          {self.tnds_data['active_streams']}
Storage Utilization:          {self.tnds_data['storage_used']}% of {self.tnds_data['storage_capacity']}GB

SERVICE SUMMARY
{'=' * 45}
Average Network Utilization:  {sum(t['utilization'] for t in active.values()) / max(1, len(active)):.1f}%
Trunk Groups In Service:      {len(active)} of {len(self.trunk_groups)}
Groups Under Maintenance:     {len(self.trunk_groups) - len(active)}
Forecast Model Accuracy:      {self.tnds_data['forecast_accuracy']:.1%}

Distribution: Network Planning, Traffic Engineering, Revenue Accounting"""

        return (f"tnds reports: Unknown report '{report_name}'\n"
                "Use 'tnds reports' to list the available reports.")
    def _show_tnds_export_options(self) -> str:
        """Show available TNDS data export formats and destinations."""
        return f"""TNDS Data Export Options
{'=' * 55}

EXPORT FORMATS
{'=' * 45}
  tnds export tape            9-track tape, 1600 BPI, EBCDIC
  tnds export cards           80-column card image deck
  tnds export rje             Remote Job Entry to Bell Labs
  tnds export print           Line printer listing (132 column)

DESTINATIONS
{'=' * 45}
Network Planning:             Murray Hill, NJ
Traffic Engineering:          Holmdel, NJ
Bell Laboratories:            Whippany, NJ (research studies)
Revenue Accounting:           Regional accounting centers

DATA SETS AVAILABLE
{'=' * 45}
Trunk Group Usage:            {len(self.trunk_groups)} groups, 36 months history
Collection Registers:         {self.tnds_data['collection_points']} points
Records Available Today:      {self.tnds_data['records_today']:,}

Note: Exports require authorization under WO-83054.
Usage: tnds export <format> [destination]"""
    def _handle_tnds_export(self, args: List[str]) -> str:
        """Handle a TNDS data export request."""
        fmt = args[0].lower()
        destination = " ".join(args[1:]) if len(args) > 1 else "Network Planning"
        formats = {
            "tape": ("9-track tape, 1600 BPI, EBCDIC", "TAPE-" + str(random.randint(1000, 9999))),
            "cards": ("80-column card image deck", "DECK-" + str(random.randint(100, 999))),
            "rje": ("Remote Job Entry stream", "RJE-" + str(random.randint(1000, 9999))),
            "print": ("132-column line printer listing", "LP-" + str(random.randint(100, 999))),
        }

        if fmt not in formats:
            return (f"tnds export: Unknown format '{args[0]}'\n"
                    "Available formats: tape, cards, rje, print")

        description, volume_id = formats[fmt]
        records = self.tnds_data['records_today']
        return f"""TNDS Data Export - Request Accepted
{'=' * 55}
Submitted: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}

EXPORT PARAMETERS
{'=' * 45}
Format:                       {description}
Volume Identifier:            {volume_id}
Destination:                  {destination}
Records Selected:             {records:,}
Estimated Volume:             {records * 80 / 1_000_000:.1f} MB

PROCESSING
{'=' * 45}
Queue Position:               {random.randint(1, 5)}
Estimated Completion:         {(self.clock.now() + timedelta(minutes=random.randint(15, 90))).strftime('%H:%M EST')}
Operator Notification:        Console message on completion

Authorization: WO-83054
Status: QUEUED FOR PROCESSING"""
