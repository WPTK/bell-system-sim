"""
Network traffic measurement, forecasting and quality.
"""

import random
from datetime import timedelta
from typing import (
    Any,
    Dict,
    List,
)


from .session import SessionState


class TrafficCommands(SessionState):
    """
    Network traffic measurement, forecasting and quality.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _show_network_hierarchy_analysis(self) -> str:
        """Show Bell System switching hierarchy analysis (Class 1 through Class 5)."""
        hierarchy = [
            ("Class 1", "Regional Center", 10, 0, random.uniform(0.72, 0.84)),
            ("Class 2", "Sectional Center", 52, 0, random.uniform(0.68, 0.80)),
            ("Class 3", "Primary Center", 148, 20, random.uniform(0.64, 0.78)),
            ("Class 4", "Toll Center", 508, 425, random.uniform(0.58, 0.74)),
            ("Class 5", "End Office", 9803, 9000, random.uniform(0.52, 0.70)),
        ]

        output = f"""TNDS Network Hierarchy Analysis
Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}
{'=' * 55}

SWITCHING HIERARCHY (1982 office counts)
{'=' * 62}
Class    Office Type            Bell   Independent    Avg Util
{'-' * 62}"""
        for cls, name, bell, independent, util in hierarchy:
            ind = f"{independent:,}" if independent else "-"
            output += (f"\n{cls:<8} {name:<20} {bell:>6,}  {ind:>11}"
                       f"    {util:>6.1%}")

        output += f"""

FINAL AND HIGH-USAGE GROUPS
{'=' * 62}
Final Trunk Groups:           {random.randint(2400, 2900):,} (hierarchical backbone)
High-Usage Groups:            {random.randint(5200, 6400):,} (direct routes)
Overflow Discipline:          Hierarchical alternate routing
Grade of Service Objective:   P.01 final groups / P.10 high-usage

A call is completed at the lowest level of the hierarchy that can carry it,
using the fewest trunks in tandem. An office joined to a higher class office
by a final group is said to home on it, though not every office homes on the
next class up. When every trunk in a final group is busy the call is blocked
and the caller receives reorder.

Average trunks per toll connection:   slightly over 3, including toll
                                      connecting trunks
Maximum trunks in one connection:     9

TANDEM ROUTING ANALYSIS
{'=' * 45}"""

        for tg_name, tg in self.trunk_groups.items():
            if tg['status'] != 'ACTIVE':
                continue
            route_kind = 'High-usage direct' if tg['utilization'] > 65 else 'Final group'
            output += f"""
{tg_name} ({tg['route']}):
  Group Type:           {route_kind}
  Overflow Path:        {random.choice(['Via Class 3 tandem', 'Via Class 2 sectional', 'Direct final'])}
  Tandem Switches:      {random.randint(1, 3)} in path"""

        output += f"""

HIERARCHY OBSERVATIONS
{'=' * 45}
Offices Homing Correctly:     {random.uniform(0.985, 0.998):.1%}
Misrouted Homing Records:     {random.randint(3, 18)} (referred to Network Planning)
Alternate Route Depth:        {random.randint(2, 4)} levels average

Reference: Notes on the Network, Section 4 (Switching Hierarchy)
Distribution: Network Planning, Traffic Engineering"""
        return output
    def _show_dynamic_routing_analysis(self) -> str:
        """Show dynamic routing performance analysis for the trunk network."""
        active = {n: t for n, t in self.trunk_groups.items() if t['status'] == 'ACTIVE'}
        overflow_total = sum(
            int(t['capacity'] * max(0, t['utilization'] - 70) * 0.12) for t in active.values()
        )

        output = f"""TNDS Dynamic Routing Analysis
Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}
{'=' * 55}

ROUTING PERFORMANCE SUMMARY
{'=' * 45}
Routes Under Analysis:        {len(active)}
Total Overflow Attempts:      {overflow_total:,} (last measurement hour)
First-Route Completion:       {random.uniform(0.88, 0.96):.1%}
Alternate Route Completion:   {random.uniform(0.96, 0.995):.1%}
Network Blocking:             {random.uniform(0.002, 0.012):.3%}

PER-ROUTE ROUTING BEHAVIOR
{'=' * 45}"""

        for tg_name, tg in active.items():
            overflow = int(tg['capacity'] * max(0, tg['utilization'] - 70) * 0.12)
            output += f"""
{tg_name} ({tg['route']}):
  Offered Load:         {int(tg['capacity'] * tg['utilization'] * 0.36)} CCS
  Overflow to Alternate:{overflow:>6,} attempts
  Transmission Quality: {tg['quality']:.3%}
  Routing Decision:     {'Overflow active' if overflow else 'Direct route sufficient'}"""

        output += f"""

TIME-OF-DAY ROUTING
{'=' * 45}
Morning Business Peak:        10:00-11:00 EST ({random.randint(88, 97)}% of capacity)
Afternoon Business Peak:      14:00-15:00 EST ({random.randint(85, 95)}% of capacity)
Evening Residential Peak:     19:00-20:00 EST ({random.randint(70, 85)}% of capacity)
Time-Zone Load Shifting:      {random.uniform(12, 22):.0f}% capacity recovered east-to-west

ROUTING RECOMMENDATIONS
{'=' * 45}
1. Continue load-shifting studies against measured busy hour
2. Review alternate route depth on routes exceeding 85% utilization
3. Coordinate routing pattern changes with Network Planning (NP-8306)

Distribution: Network Operations, Traffic Engineering"""
        return output
    def cmd_traffic(self, args: List[str]) -> str:
        """Enhanced network traffic analysis with real-time monitoring capabilities."""
        import random

        # Update traffic state for realistic behavior
        self._update_traffic_state()

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            # Calculate dynamic metrics from network state
            total_load = sum(tg['utilization'] for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE') // len([tg for tg in self.trunk_groups.values() if tg['status'] == 'ACTIVE'])

            traffic_output = f"""Bell System Network Traffic Analysis
Real-Time Monitoring and Statistics
{current_time}

CURRENT NETWORK STATUS
{'=' * 40}
Total Traffic Load:       {total_load}% of network capacity
Peak Period Today:        {self._get_peak_period()}
Call Completion Rate:     {self.network_metrics['call_completion']:.1%}
Average Hold Time:        {self.traffic_data['avg_duration']:.1f} minutes
Setup Time Average:       {self.network_metrics['setup_time']:.1f} seconds

REAL-TIME CALL VOLUME
{'=' * 40}
Active Calls:             {self.traffic_data['current_calls']:,}
Calls Completed Today:    {self.traffic_data['calls_today']:,}
Revenue Generated:        ${self.traffic_data['revenue_today']:,}
International Traffic:    {self.traffic_data['international_pct']:.1%} of total
Toll Traffic:             {self.traffic_data['toll_pct']:.1%} of total

INTER-OFFICE ROUTE STATUS
{'=' * 40}"""

            # Show major trunk group utilization
            major_routes = [
                ('NYC-WAS', next((tg['utilization'] for name, tg in self.trunk_groups.items() if 'NYC' in name and tg['route'] == 'NYC-WAS'), random.randint(75, 90))),
                ('NYC-BOS', next((tg['utilization'] for name, tg in self.trunk_groups.items() if 'BOS' in name and tg['route'] == 'NYC-BOS'), random.randint(60, 80))),
                ('WAS-ATL', next((tg['utilization'] for name, tg in self.trunk_groups.items() if 'WAS' in name and tg['route'] == 'WAS-ATL'), random.randint(40, 70))),
                ('CHI-NYC', next((tg['utilization'] for name, tg in self.trunk_groups.items() if 'CHI' in name and tg['route'] == 'CHI-NYC'), random.randint(35, 65)))
            ]

            for route, utilization in major_routes:
                status = "HIGH" if utilization > 80 else "NORMAL" if utilization > 40 else "LOW"
                calls_hour = int((utilization / 100) * random.randint(15000, 45000))
                traffic_output += f"\n{route:<15} {utilization:>3}% utilization  {status:<8} ({calls_hour:,} calls/hour)"

            # Regional traffic distribution
            traffic_output += f"""

REGIONAL TRAFFIC DISTRIBUTION
{'=' * 40}"""

            for region, data in self.regional_traffic.items():
                pct = (data['calls'] / self.traffic_data['current_calls']) * 100
                traffic_output += f"\n{region.title():<12} {data['calls']:>8,} calls ({pct:>4.1f}%)  Revenue: ${data['revenue']:,}"

            # Traffic quality metrics
            traffic_output += f"""

QUALITY METRICS
{'=' * 40}
Blocking Rate:            {self.network_metrics['blocking_rate']:.3f} (Target: <0.01)
Post-Dial Delay:          {self.network_metrics['setup_time']:.1f} seconds average
Network Efficiency:       {self.traffic_data['completion_rate']:.1%}
Customer Satisfaction:    {random.uniform(4.1, 4.7):.1f}/5.0 rating

Commands:
  traffic detail <region>   Regional traffic analysis
  traffic forecast          Traffic projection and planning
  traffic routes            Route-specific performance
  traffic peak              Peak period analysis
  traffic quality           Quality metrics and trending"""

            return traffic_output

        elif args[0] == "detail" and len(args) > 1:
            region = args[1].lower()
            return self._show_regional_traffic_detail(region)

        elif args[0] == "forecast":
            return self._generate_traffic_forecast()

        elif args[0] == "routes":
            return self._show_route_performance()

        elif args[0] == "peak":
            return self._show_peak_analysis()

        elif args[0] == "quality":
            return self._show_traffic_quality_metrics()

        else:
            available_commands = ["detail", "forecast", "routes", "peak", "quality"]
            return f"traffic: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"
    def _update_traffic_state(self) -> None:
        """Update traffic state with realistic time-based variations."""

        hour = self.clock.now().hour

        # Adjust traffic patterns based on time of day
        if 8 <= hour <= 10:  # Morning business peak
            multiplier = random.uniform(1.1, 1.3)
        elif 14 <= hour <= 16:  # Afternoon peak
            multiplier = random.uniform(1.2, 1.4)
        elif 19 <= hour <= 21:  # Evening social peak
            multiplier = random.uniform(0.9, 1.1)
        elif 22 <= hour or hour <= 6:  # Overnight
            multiplier = random.uniform(0.3, 0.5)
        else:  # Regular business hours
            multiplier = random.uniform(0.8, 1.0)

        # Update regional traffic with realistic variations
        for region, data in self.regional_traffic.items():
            variation = random.uniform(0.95, 1.05) * multiplier
            data['calls'] = int(data['calls'] * variation)
            data['revenue'] = int(data['revenue'] * variation * random.uniform(0.98, 1.02))
    def _show_regional_traffic_detail(self, region: str) -> str:
        """Show detailed traffic analysis for a specific region."""
        import random

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        if region not in self.regional_traffic:
            available_regions = list(self.regional_traffic.keys())
            return f"traffic: Unknown region '{region}'\nAvailable regions: {', '.join(available_regions)}"

        region_data = self.regional_traffic[region]

        detail_output = f"""Regional Traffic Detail - {region.title()}
Analysis Time: {current_time}

CURRENT ACTIVITY
{'=' * 30}
Active Calls:             {region_data['calls']:,}
Revenue This Hour:        ${region_data['revenue']:,}
Peak Hour Calls:          {int(region_data['calls'] * random.uniform(1.2, 1.5)):,} (estimated)
Market Share:             {(region_data['calls'] / sum(d['calls'] for d in self.regional_traffic.values())) * 100:.1f}% of total network

TRAFFIC PATTERNS
{'=' * 30}"""

        # Generate realistic traffic breakdown by type
        business_pct = random.uniform(0.60, 0.75) if region == 'northeast' else random.uniform(0.45, 0.65)
        residential_pct = 1.0 - business_pct - random.uniform(0.08, 0.15)  # Subtract toll/international

        detail_output += f"""
Business Hours (08:00-17:00):  {business_pct:.1%} of daily volume
Residential (17:00-22:00):     {residential_pct:.1%} of daily volume
Overnight (22:00-08:00):       {(1 - business_pct - residential_pct):.1%} of daily volume

MAJOR DESTINATIONS FROM {region.upper()}
{'=' * 30}"""

        # Define realistic destination patterns by region
        if region == 'northeast':
            destinations = [
                ('Washington DC', random.randint(8000, 15000), random.uniform(1.2, 1.8)),
                ('Boston', random.randint(6000, 12000), random.uniform(0.8, 1.4)),
                ('Philadelphia', random.randint(4000, 8000), random.uniform(0.6, 1.0)),
                ('Chicago', random.randint(3000, 6000), random.uniform(1.5, 2.2))
            ]
        elif region == 'southeast':
            destinations = [
                ('Miami', random.randint(5000, 9000), random.uniform(0.9, 1.5)),
                ('New York', random.randint(4000, 8000), random.uniform(1.8, 2.5)),
                ('Tampa', random.randint(3000, 6000), random.uniform(0.7, 1.2)),
                ('Charlotte', random.randint(2000, 4000), random.uniform(0.8, 1.3))
            ]
        elif region == 'central':
            destinations = [
                ('Detroit', random.randint(6000, 10000), random.uniform(0.8, 1.4)),
                ('New York', random.randint(5000, 9000), random.uniform(2.0, 2.8)),
                ('St. Louis', random.randint(4000, 7000), random.uniform(0.6, 1.1)),
                ('Cleveland', random.randint(3000, 5000), random.uniform(0.7, 1.2))
            ]
        else:  # west
            destinations = [
                ('San Francisco', random.randint(4000, 7000), random.uniform(0.5, 0.9)),
                ('New York', random.randint(3000, 6000), random.uniform(2.8, 3.5)),
                ('Seattle', random.randint(2000, 4000), random.uniform(0.8, 1.4)),
                ('Denver', random.randint(2000, 3500), random.uniform(1.2, 1.8))
            ]

        for i, (dest, calls, avg_rate) in enumerate(destinations, 1):
            revenue = int(calls * avg_rate)
            detail_output += f"\n{i}. {dest:<15} {calls:>6,} calls  ${revenue:>5,} revenue  (${avg_rate:.2f} avg)"

        detail_output += f"""

QUALITY INDICATORS
{'=' * 30}
Service Level:            {random.uniform(0.975, 0.995):.1%}
Call Completion Rate:     {random.uniform(0.970, 0.990):.1%}
Customer Satisfaction:    {random.uniform(4.0, 4.6):.1f}/5.0 rating
Technical Quality:        {'Excellent' if random.random() > 0.3 else 'Good'}

NETWORK UTILIZATION
{'=' * 30}
Trunk Utilization:        {random.randint(65, 85)}% average
Peak Period Load:         {random.randint(85, 95)}%
Overflow Events:          {random.randint(0, 3)} (last 24 hours)
Backup Route Usage:       {random.randint(2, 8)}% of traffic

Use 'trunk detail <TG-xxx>' for specific trunk group analysis"""

        return detail_output
    def _generate_traffic_forecast(self) -> str:
        """Generate traffic forecasting analysis."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        forecast_output = f"""Traffic Forecasting Analysis
Generated: {current_time}

IMMEDIATE FORECAST (Next 4 Hours)
{'=' * 45}"""

        current_hour = self.clock.now().hour
        base_calls = sum(data['calls'] for data in self.regional_traffic.values())

        for i in range(4):
            forecast_hour = (current_hour + i + 1) % 24

            # Apply realistic hourly patterns
            if 8 <= forecast_hour <= 10:
                multiplier = random.uniform(1.15, 1.35)
                period_desc = "Morning Peak"
            elif 14 <= forecast_hour <= 16:
                multiplier = random.uniform(1.25, 1.45)
                period_desc = "Afternoon Peak"
            elif 19 <= forecast_hour <= 21:
                multiplier = random.uniform(0.95, 1.15)
                period_desc = "Evening Social"
            elif 22 <= forecast_hour or forecast_hour <= 6:
                multiplier = random.uniform(0.35, 0.55)
                period_desc = "Overnight"
            else:
                multiplier = random.uniform(0.85, 1.05)
                period_desc = "Regular Business"

            forecast_calls = int(base_calls * multiplier)
            capacity_pct = min(100, int(multiplier * 70))

            forecast_output += f"\n{forecast_hour:02d}:00-{(forecast_hour+1)%24:02d}:00  {forecast_calls:>7,} calls  {capacity_pct:>3}% capacity  {period_desc}"

        forecast_output += f"""

WEEKLY TRENDS ANALYSIS
{'=' * 45}
Monday-Thursday:          Heavy business traffic pattern
Friday:                   Moderate business, increasing personal calls
Saturday:                 Light traffic, family-oriented calls
Sunday:                   Moderate traffic with evening peak

SPECIAL CONSIDERATIONS
{'=' * 45}"""

        # Generate realistic special events
        special_events = []
        if self.clock.now().month == 12:
            special_events.append("Holiday season: +15-20% expected volume")
        if self.clock.now().weekday() == 4:  # Friday
            special_events.append("Weekend effect: +10% Friday evening traffic")
        if random.random() < 0.3:
            special_events.append("Weather system may affect rural areas")
        if random.random() < 0.2:
            special_events.append("Major sporting event: +25% regional traffic expected")

        if special_events:
            for event in special_events:
                forecast_output += f"\n• {event}"
        else:
            forecast_output += "\n• No special events expected"

        forecast_output += f"""

CAPACITY RECOMMENDATIONS
{'=' * 45}
High-Traffic Routes:      Enable overflow routing during peaks
Operator Staffing:        Pre-position additional operators for peak periods
Trunk Monitoring:         Monitor utilization closely on major routes
Load Balancing:           Activate dynamic routing algorithms

GROWTH PROJECTIONS
{'=' * 45}
Next Month:               {random.uniform(3, 7):+.1f}% call volume increase
Quarter Forecast:         {random.uniform(8, 15):+.1f}% growth expected
Annual Growth Rate:       {random.uniform(12, 18):+.1f}% projected

Revenue Impact:           ${random.randint(25000, 45000):,} additional daily revenue
Infrastructure Needs:     {random.randint(2, 4)} new trunk groups by Q2 1984"""

        return forecast_output
    def _show_route_performance(self) -> str:
        """Show route-specific performance analysis."""
        import random

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        route_output = f"""Route Performance Analysis
Updated: {current_time}

MAJOR ROUTE PERFORMANCE
{'=' * 35}"""

        # Define major Bell System routes with realistic performance
        major_routes = [
            ('NYC-WAS', 'Northeast Corridor', random.randint(15000, 25000), random.uniform(0.975, 0.995)),
            ('NYC-BOS', 'New England Route', random.randint(12000, 18000), random.uniform(0.980, 0.998)),
            ('CHI-NYC', 'Central-East Route', random.randint(18000, 28000), random.uniform(0.970, 0.990)),
            ('LAX-SFO', 'California Corridor', random.randint(8000, 15000), random.uniform(0.985, 0.995)),
            ('WAS-ATL', 'Southeast Route', random.randint(10000, 16000), random.uniform(0.975, 0.992)),
            ('CHI-LAX', 'Transcontinental', random.randint(14000, 22000), random.uniform(0.965, 0.985))
        ]

        for route, description, calls_hour, completion in major_routes:
            setup_time = random.uniform(1.5, 2.8)
            revenue_rate = random.randint(25, 45)
            status = "EXCELLENT" if completion > 0.99 else "GOOD" if completion > 0.98 else "FAIR"

            route_output += f"""
{route} ({description})
  Calls/Hour:     {calls_hour:,}
  Completion:     {completion:.1%}
  Setup Time:     {setup_time:.1f} seconds
  Revenue/Hour:   ${calls_hour * revenue_rate // 1000:,}
  Status:         {status}"""

        route_output += f"""

ROUTE QUALITY METRICS
{'=' * 35}
Signal Quality:           {random.uniform(0.92, 0.98):.1%} acceptable or better
Echo Control:             {random.uniform(0.88, 0.96):.1%} within standards
Noise Level:              {random.uniform(0.90, 0.97):.1%} below threshold
Transmission Delay:       {random.uniform(0.85, 0.95):.1%} within limits

ALTERNATE ROUTING STATUS
{'=' * 35}"""

        # Show overflow and alternate routing
        alt_routes = [
            ('NYC-WAS via Philadelphia', random.randint(0, 15)),
            ('CHI-NYC via Cleveland', random.randint(0, 25)),
            ('LAX-SFO via Sacramento', random.randint(0, 8))
        ]

        for alt_route, usage_pct in alt_routes:
            status = "ACTIVE" if usage_pct > 5 else "STANDBY"
            route_output += f"\n{alt_route:<25} {usage_pct:>3}% usage  {status}"

        route_output += f"""

TRAFFIC ENGINEERING NOTES
{'=' * 35}
• Dynamic routing algorithms active on all major routes
• Load balancing optimization in progress
• Capacity planning review scheduled for next quarter
• New routing patterns being tested on select routes

Use 'trunk detail <TG-xxx>' for specific trunk group analysis"""

        return route_output
    def _show_peak_analysis(self) -> str:
        """Show peak period traffic analysis."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        peak_output = f"""Peak Period Traffic Analysis
Generated: {current_time}

TODAY'S PEAK ANALYSIS
{'=' * 30}"""

        # Generate realistic peak periods
        morning_peak: Dict[str, Any] = {
            'time': f"{random.randint(8, 10)}:{random.randint(15, 45):02d}",
            'calls': random.randint(45000, 65000),
            'duration': random.randint(45, 90),
            'completion': random.uniform(0.970, 0.990)
        }

        afternoon_peak: Dict[str, Any] = {
            'time': f"{random.randint(14, 16)}:{random.randint(0, 45):02d}",
            'calls': random.randint(55000, 75000),
            'duration': random.randint(60, 120),
            'completion': random.uniform(0.965, 0.985)
        }

        morning_calls = int(morning_peak['calls'])
        afternoon_calls = int(afternoon_peak['calls'])
        busiest = max(morning_calls, afternoon_calls)

        peak_output += f"""
Morning Peak:
  Time:           {morning_peak['time']} EST
  Call Volume:    {morning_peak['calls']:,} calls/hour
  Duration:       {morning_peak['duration']} minutes
  Completion:     {morning_peak['completion']:.1%}

Afternoon Peak:
  Time:           {afternoon_peak['time']} EST
  Call Volume:    {afternoon_peak['calls']:,} calls/hour
  Duration:       {afternoon_peak['duration']} minutes
  Completion:     {afternoon_peak['completion']:.1%}

PEAK HOUR CAPACITY ANALYSIS
{'=' * 30}
Network Capacity:         {random.randint(75000, 85000):,} calls/hour maximum
Current Peak Load:        {busiest:,} calls/hour
Capacity Utilization:     {(busiest / 80000) * 100:.1f}%
Safety Margin:            {((80000 - busiest) / 80000) * 100:.1f}%

HISTORICAL PEAK TRENDS
{'=' * 30}"""

        # Generate weekly peak trend data
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days:
            peak_calls = random.randint(40000, 70000)
            peak_time = f"{random.randint(14, 16)}:{random.randint(0, 59):02d}"
            trend = random.choice(['+', '+', '-']) + f"{random.uniform(0.5, 5.0):.1f}%"

            peak_output += f"\n{day:<10} {peak_calls:>6,} calls at {peak_time}  ({trend} vs last week)"

        peak_output += f"""

PEAK PERIOD CHALLENGES
{'=' * 30}
Trunk Utilization:        {random.randint(85, 95)}% on major routes during peaks
Operator Wait Times:      {random.uniform(8, 15):.1f} seconds average
System Response:          {random.uniform(2.1, 3.2):.1f} seconds call setup
Overflow Events:          {random.randint(3, 12)} occurrences today

CAPACITY MANAGEMENT
{'=' * 30}
• Dynamic routing activated during peak periods
• Additional operators scheduled for busy hours
• Overflow trunks available on all major routes
• Real-time load monitoring and adjustment active

RECOMMENDATIONS
{'=' * 30}
• Monitor trunk utilization closely during peaks
• Consider capacity expansion for routes exceeding 90%
• Optimize routing algorithms for better load distribution
• Schedule maintenance during off-peak hours only"""

        return peak_output
    def _show_traffic_quality_metrics(self) -> str:
        """Show traffic quality metrics and trending."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        quality_output = f"""Traffic Quality Metrics and Trending
Report Generated: {current_time}

CURRENT QUALITY INDICATORS
{'=' * 40}
Call Completion Rate:     {self.traffic_data['completion_rate']:.2%}
Post-Dial Delay:          {self.network_metrics['setup_time']:.1f} seconds average
Network Blocking:         {self.network_metrics['blocking_rate']:.3f} probability
Signal Quality Index:     {random.uniform(0.92, 0.98):.1%}
Customer Satisfaction:    {random.uniform(4.1, 4.7):.1f}/5.0 rating

QUALITY TREND ANALYSIS (30 Days)
{'=' * 40}"""

        # Generate 30-day quality trends
        metrics = [
            ('Completion Rate', 0.980, '%'),
            ('Setup Time', 2.1, 'sec'),
            ('Blocking Rate', 0.005, ''),
            ('Signal Quality', 0.95, '%'),
            ('Satisfaction', 4.3, '/5.0')
        ]

        for metric_name, baseline, unit in metrics:
            trend_direction = random.choice(['↑', '↑', '↓', '→'])  # Bias toward improvement
            if trend_direction == '↑':
                change = f"+{random.uniform(0.1, 2.5):.1f}"
            elif trend_direction == '↓':
                change = f"-{random.uniform(0.1, 1.5):.1f}"
            else:
                change = "0.0"

            current_value = baseline * random.uniform(0.98, 1.02)
            if unit == '%':
                quality_output += f"\n{metric_name:<18} {current_value:.1%} ({trend_direction} {change}{unit})"
            elif unit == 'sec':
                quality_output += f"\n{metric_name:<18} {current_value:.1f}{unit} ({trend_direction} {change}{unit})"
            elif unit == '/5.0':
                quality_output += f"\n{metric_name:<18} {current_value:.1f}{unit} ({trend_direction} {change})"
            else:
                quality_output += f"\n{metric_name:<18} {current_value:.3f} ({trend_direction} {change})"

        quality_output += f"""

QUALITY BY ROUTE TYPE
{'=' * 40}
Local Calls:              {random.uniform(0.985, 0.995):.1%} completion
Long Distance:            {random.uniform(0.975, 0.990):.1%} completion
International:            {random.uniform(0.960, 0.980):.1%} completion
Operator Assisted:        {random.uniform(0.970, 0.985):.1%} completion

TECHNICAL QUALITY METRICS
{'=' * 40}
Transmission Quality:     {random.uniform(0.88, 0.96):.1%} excellent/good
Echo Control:             {random.uniform(0.85, 0.94):.1%} within standards
Noise Level:              {random.uniform(0.90, 0.97):.1%} below threshold
Cross-Talk:               {random.uniform(0.95, 0.99):.1%} within limits
Frequency Response:       {random.uniform(0.92, 0.98):.1%} acceptable

CUSTOMER EXPERIENCE
{'=' * 40}
Average Hold Time:        {self.traffic_data['avg_duration']:.1f} minutes
Dial Tone Delay:          {random.uniform(0.2, 0.8):.1f} seconds
Wrong Number Rate:        {random.uniform(0.008, 0.025):.3f}
Dropped Call Rate:        {random.uniform(0.002, 0.012):.3f}
Service Difficulty:       {random.uniform(0.005, 0.020):.3f}

QUALITY IMPROVEMENT INITIATIVES
{'=' * 40}
• Digital switching deployment increasing completion rates
• Echo canceller installation on long-haul routes
• Improved operator training reducing handle times
• Network optimization reducing post-dial delay
• Customer feedback system implementation

TARGET PERFORMANCE STANDARDS
{'=' * 40}
Completion Rate Target:   98.5% or better
Setup Time Target:        Under 2.0 seconds
Blocking Target:          Less than 0.01 probability
Quality Index Target:     95% excellent/good ratings
Satisfaction Target:      4.5/5.0 or better

Next Quality Review: {(self.clock.now() + timedelta(days=7)).strftime('%B %d, %Y')}"""

        return quality_output
    def cmd_netplan(self, args: List[str]) -> str:
        """Enhanced network planning with realistic route optimization and capacity analysis."""

        if not args:
            return f"""Bell System Network Planning and Engineering
Route Optimization and Capacity Management
{'=' * 50}

CURRENT PLANNING ACTIVITIES
{'=' * 35}
Active Projects:             {random.randint(8, 15)}
Capacity Studies:            {random.randint(3, 8)} in progress
Route Optimization:          {random.randint(2, 6)} analyses
Equipment Planning:          {random.randint(4, 12)} evaluations

NETWORK GROWTH PROJECTIONS
{'=' * 35}
Annual Traffic Growth:       {random.uniform(12, 18):.1f}%
New Circuit Requirements:    {random.randint(45, 85)} T1 equivalents
Equipment Expansion:         ${random.uniform(2.5, 8.5):.1f}M investment needed
Service Area Growth:         {random.randint(3, 8)} new exchanges

CURRENT STUDIES
{'=' * 35}
NYC-WAS Corridor:           Capacity upgrade analysis
Chicago Hub:                Route diversity study
West Coast Links:           Fiber optic feasibility
Rural Coverage:             Economic analysis

Commands:
  netplan capacity           Network capacity analysis
  netplan routes             Route planning and optimization
  netplan growth             Traffic growth projections
  netplan investment         Capital investment planning"""

        elif args[0] == "capacity":
            return self._show_network_capacity_analysis()

        elif args[0] == "routes":
            return self._show_route_planning()

        elif args[0] == "growth":
            return self._show_traffic_growth_projections()

        elif args[0] == "investment":
            return self._show_investment_planning()

        else:
            available_commands = ["capacity", "routes", "growth", "investment"]
            return f"netplan: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"
    def _show_network_capacity_analysis(self) -> str:
        """Show comprehensive network capacity analysis."""
        import random

        return f"""Network Capacity Analysis
Report Generated: {self.clock.now().strftime('%B %d, %Y %H:%M EST')}

CURRENT NETWORK UTILIZATION
{'=' * 40}
Overall Network Load:        {random.randint(65, 85)}% of capacity
Peak Hour Utilization:      {random.randint(85, 95)}%
Reserve Capacity:           {random.randint(15, 35)}% margin
Critical Routes:            {random.randint(3, 8)} approaching limits

HIGH-UTILIZATION ROUTES
{'=' * 40}
NYC-Washington Corridor:     {random.randint(85, 95)}% utilization
Chicago-New York:           {random.randint(80, 90)}% utilization
Los Angeles-San Francisco:  {random.randint(70, 85)}% utilization
Boston-New York:            {random.randint(75, 88)}% utilization

CAPACITY CONSTRAINTS
{'=' * 40}
Equipment Limitations:       {random.randint(2, 6)} locations
Facility Constraints:        {random.randint(1, 4)} rights-of-way
Economic Thresholds:         {random.randint(3, 7)} marginal routes

EXPANSION RECOMMENDATIONS
{'=' * 40}
Immediate (6 months):        {random.randint(15, 25)} new circuits
Short-term (12 months):      {random.randint(35, 55)} circuit additions
Long-term (24 months):       {random.randint(65, 95)} circuit expansion

Investment Required:         ${random.uniform(15.5, 35.8):.1f}M total
Revenue Impact:              ${random.uniform(8.2, 18.5):.1f}M annually
ROI Projection:             {random.uniform(18, 35):.0f}% over 5 years"""
    def _show_route_planning(self) -> str:
        """Show route planning and optimization analysis."""

        return f"""Route Planning and Optimization
Analysis Date: {self.clock.now().strftime('%B %d, %Y')}

ROUTE OPTIMIZATION STUDIES
{'=' * 40}
Primary Route Analysis:      {random.randint(12, 24)} routes evaluated
Alternate Path Planning:     {random.randint(6, 15)} backup routes
Diversity Requirements:      {random.randint(85, 95)}% geographic separation
Load Balancing Efficiency:  {random.uniform(0.88, 0.95):.1%}

MAJOR ROUTE CORRIDORS
{'=' * 40}
Northeast Corridor:
  Primary Path:              I-95 Fiber Route
  Utilization:              {random.randint(75, 90)}%
  Backup Available:         Microwave diversity
  Expansion Plan:           Additional fiber planned 1984

Transcontinental Routes:
  Northern Route:           CHI-DEN-SFO via I-80
  Southern Route:           CHI-DAL-LAX via I-40
  Utilization Balance:      {random.randint(65, 85)}% / {random.randint(55, 75)}%

ROUTE ECONOMICS
{'=' * 40}
Cost per Circuit Mile:       ${random.randint(285, 450)}
Installation Time:           {random.randint(8, 18)} months average
Permit Acquisition:          {random.randint(3, 12)} months
Environmental Review:        {random.randint(6, 24)} months

TECHNOLOGY PLANNING
{'=' * 40}
Fiber Optic Deployment:     35% of new routes
Digital Microwave:          45% of new routes
Satellite Backup:           20% for remote areas
Copper Retirement:          Systematic replacement program

Next Planning Review: {(self.clock.now() + timedelta(days=90)).strftime('%B %d, %Y')}"""
    def _show_traffic_growth_projections(self) -> str:
        """Show traffic growth projections and forecasting."""
        import random

        return f"""Traffic Growth Projections and Forecasting
Forecast Period: 1984-1988
{'=' * 50}

HISTORICAL GROWTH ANALYSIS
{'=' * 40}
1980-1983 Growth Rate:       {random.uniform(8.5, 15.2):.1f}% annually
Voice Traffic:              {random.uniform(6.2, 12.8):.1f}% annual growth
Data Traffic:               {random.uniform(25.5, 45.8):.1f}% annual growth
International:              {random.uniform(18.2, 28.5):.1f}% annual growth

5-YEAR PROJECTIONS (1984-1988)
{'=' * 40}
Total Call Volume Growth:    {random.uniform(65, 125):.0f}% increase
Peak Hour Calls:            From {random.randint(850, 950)}K to {random.randint(1400, 1800)}K
Data Communication:          {random.uniform(180, 320):.0f}% growth expected
Video Services:             Emerging market - 5% by 1988

TECHNOLOGY IMPACT
{'=' * 40}
Digital Switching:          85% deployment by 1988
Fiber Optic Transmission:  70% of long-haul by 1988
ISDN Services:             15% market penetration
Mobile Communications:      2% of total traffic

CAPACITY REQUIREMENTS
{'=' * 40}
New Switching Capacity:     {random.uniform(2.2, 3.8):.1f}M additional ports
Transmission Expansion:     {random.uniform(45, 75):.0f}% more circuits
Operator Positions:         {random.uniform(-15, -25):.0f}% reduction (automation)
Data Processing:            {random.uniform(250, 450):.0f}% increase

INVESTMENT PROJECTIONS
{'=' * 40}
Total Investment (5-year):  ${random.uniform(12.5, 28.8):.1f}B
Network Expansion:          ${random.uniform(7.2, 15.5):.1f}B
Technology Upgrade:         ${random.uniform(3.8, 8.5):.1f}B
Facilities:                 ${random.uniform(1.5, 4.8):.1f}B

Revenue Projections:        ${random.uniform(45.5, 78.2):.1f}B (1988)
Market Share Target:        {random.uniform(78, 88):.0f}% of US telecommunications"""
    def _show_investment_planning(self) -> str:
        """Show capital investment planning analysis."""

        return f"""Capital Investment Planning Analysis
Planning Horizon: 1984-1988
{'=' * 50}

INVESTMENT CATEGORIES
{'=' * 40}
Network Infrastructure:     ${random.uniform(8.5, 15.2):.1f}B ({random.uniform(45, 65):.0f}%)
Technology Modernization:   ${random.uniform(3.2, 7.8):.1f}B ({random.uniform(18, 28):.0f}%)
Facilities and Buildings:   ${random.uniform(1.8, 4.5):.1f}B ({random.uniform(10, 18):.0f}%)
Research and Development:   ${random.uniform(1.2, 2.8):.1f}B ({random.uniform(8, 15):.0f}%)

PRIORITY PROJECTS
{'=' * 40}
Electronic Switching:       ${random.uniform(4.5, 8.2):.1f}B
  - 5ESS Deployment
  - Legacy System Replacement
  - Digital Feature Enhancement

Fiber Optic Network:        ${random.uniform(2.8, 5.5):.1f}B
  - Long-haul Routes
  - Metropolitan Networks
  - Customer Access

TNDS Expansion:            ${random.uniform(0.8, 1.8):.1f}B
  - Processing Capacity
  - Database Systems
  - Analysis Tools

FINANCIAL PROJECTIONS
{'=' * 40}
Total Capital Required:     ${random.uniform(15.8, 32.5):.1f}B
Financing Sources:
  Internal Cash Flow:       {random.uniform(55, 75):.0f}%
  Long-term Debt:          {random.uniform(20, 35):.0f}%
  Equipment Leasing:       {random.uniform(5, 15):.0f}%

Expected ROI:              {random.uniform(15, 25):.1f}% over 7 years
Payback Period:            {random.uniform(4.2, 6.8):.1f} years average
Risk Assessment:           MODERATE (technology transition)

ECONOMIC IMPACT
{'=' * 40}
Job Creation:              {random.randint(15000, 35000):,} new positions
Economic Stimulus:         ${random.uniform(25.8, 48.5):.1f}B regional impact
Productivity Gain:         {random.uniform(25, 45):.0f}% operational efficiency
Service Quality:           {random.uniform(15, 28):.0f}% improvement target

Regulatory Approval:       Required for major projects
Environmental Impact:      Assessments in progress
Public Service Benefits:   Universal service expansion"""
