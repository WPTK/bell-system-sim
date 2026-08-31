"""
Traffic Service Position System, operator services and directory.
"""

import random
from datetime import timedelta
from typing import (
    List,
)
from ..types import (
    TspsData,
)


from .session import SessionState


class TspsCommands(SessionState):
    """
    Traffic Service Position System, operator services and directory.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _get_tsps_briefing(self) -> str:
        """Get TSPS Operator briefing."""
        return """
TSPS OPERATOR BRIEFING

Primary Responsibilities:
- Traffic Service Position System operations
- Operator-assisted call completion
- Directory assistance coordination
- Collect call processing

Current Priorities:
- Monitor TSPS position utilization (78% busy hour)
- Coordinate operator training session 16:00-17:30
- Review directory assistance accuracy metrics
- Process special billing arrangements

Key Commands: tsps, operator, directory, collect, billing
"""
    def cmd_tsps(self, args: List[str]) -> str:
        """Enhanced Traffic Service Position System with realistic operator management."""

        # Update TSPS state for realistic operational behavior
        self._update_tsps_state()

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            return f"""Traffic Service Position System (TSPS)
Operator Services and Assisted Calling
{current_time}

CURRENT OPERATIONS STATUS
{'=' * 35}
Active Positions:         {self.tsps_data['active_positions']} of {self.tsps_data['total_positions']} staffed
Position Occupancy:       {self.tsps_data['occupancy']:.1f}% ({self._get_tsps_period()})
Queue Length:             {self.tsps_data['queue_length']} calls waiting
Average Work Time:        {self.tsps_data['avg_work_time']:.1f} seconds per call
Answer Time:              {self.tsps_data['answer_time']:.1f} seconds average

OPERATOR FUNCTIONS THIS TOUR
{'=' * 45}
Coin, initial period and overtime:  {self.tsps_data['coin']:>6,} calls
Calling card:                       {self.tsps_data['calling_card']:>6,} calls
Collect:                            {self.tsps_data['collect_calls']:>6,} calls
Bill to third number:               {self.tsps_data['third_number']:>6,} calls
Person to person:                   {self.tsps_data['person_to_person']:>6,} calls
Operator assistance (0-):           {self.tsps_data['assistance']:>6,} calls
Operator number identification:     {self.tsps_data['oni']:>6,} calls
Hotel and motel guest:              {self.tsps_data['hotel_motel']:>6,} calls
International assistance:           {self.tsps_data['international']:>6,} calls
Busy line verification:             {self.tsps_data['verification']:>6,} calls

Directory assistance is not a position function here. It is served by a
separate operator force on 411 and NPA-555-1212, concentrated on an
automatic call distributor.

SERVICE MEASUREMENTS
{'=' * 45}
Speed of answer:          {self.tsps_data['answer_time']:.1f} seconds (objective 2 to 6)
Average work time:        {self.tsps_data['avg_work_time']:.1f} seconds per request
Positions manned:         {self.tsps_data['active_positions']} of {self.tsps_data['total_positions']}
Force requirement:        {self.tsps_data['force_requirement']} positions (Erlang C, next quarter hour)
Force adjustment:         {self.tsps_data['force_adjustment']}
System availability:      {self.tsps_data['system_availability']:.1%}

Commands:
  tsps position <id>      Individual position status
  tsps operators          Operator staffing and performance
  tsps training           Training programs and certification
  tsps queue              Call queue management
  tsps reports            Performance and productivity reports"""

        elif args[0] == "position" and len(args) > 1:
            position_id = args[1]
            return self._show_tsps_position_detail(position_id)

        elif args[0] == "operators":
            return self._show_tsps_operator_status()

        elif args[0] == "training":
            return self._show_tsps_training_programs()

        elif args[0] == "queue":
            return self._show_tsps_queue_management()

        elif args[0] == "reports":
            if len(args) > 1:
                return self._generate_tsps_report(args[1])
            else:
                return self._show_available_tsps_reports()

        else:
            available_commands = ["position", "operators", "training", "queue", "reports"]
            return f"tsps: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"
    def _update_tsps_state(self) -> None:
        """Update TSPS operational state with realistic patterns."""
        import random

        if not hasattr(self, 'tsps_data'):
            # Initialize TSPS operational data
            hour = self.clock.now().hour

            # Adjust staffing and load based on time of day
            if 8 <= hour <= 17:  # Business hours
                base_positions = random.randint(45, 52)
                base_occupancy = random.uniform(75, 90)
            elif 17 <= hour <= 22:  # Evening
                base_positions = random.randint(25, 35)
                base_occupancy = random.uniform(60, 80)
            else:  # Overnight
                base_positions = random.randint(8, 15)
                base_occupancy = random.uniform(40, 65)

            self.tsps_data: TspsData = {
                'total_positions': 52,
                'active_positions': base_positions,
                'occupancy': base_occupancy,
                'queue_length': random.randint(0, 25),
                'avg_work_time': random.uniform(20, 45),
                'answer_time': random.uniform(2.5, 8.0),
                'coin': random.randint(900, 2200),
                'calling_card': random.randint(400, 1100),
                'collect_calls': random.randint(350, 900),
                'third_number': random.randint(120, 400),
                'person_to_person': random.randint(90, 320),
                'assistance': random.randint(200, 700),
                'oni': random.randint(150, 500),
                'hotel_motel': random.randint(40, 180),
                'international': random.randint(20, 110),
                'verification': random.randint(10, 70),
                'force_requirement': base_positions + random.randint(-2, 3),
                'force_adjustment': random.choice([
                    'Within objective',
                    'Calling out additional operators',
                    'Releasing operators to clerical work',
                    'Rescheduling lunches and reliefs',
                ]),
                'service_quality': random.uniform(0.95, 0.99),
                'productivity_rating': random.choice(['Excellent', 'Above Average', 'Average']),
                'system_availability': random.uniform(0.995, 0.999),
                'last_update': self.clock.now()
            }
        else:
            # Update existing data with small variations
            time_since_update = (self.clock.now() - self.tsps_data['last_update']).total_seconds() / 60
            if time_since_update > 2:  # Update every 2 minutes
                self.tsps_data['queue_length'] = max(0, self.tsps_data['queue_length'] + random.randint(-3, 5))
                self.tsps_data['answer_time'] = max(1.0, self.tsps_data['answer_time'] + random.uniform(-0.5, 0.8))
                self.tsps_data['last_update'] = self.clock.now()
    def _get_tsps_period(self) -> str:
        """Get current TSPS period description."""
        hour = self.clock.now().hour
        if 8 <= hour <= 17:
            return "busy hour"
        elif 17 <= hour <= 22:
            return "evening shift"
        else:
            return "night shift"
    def _show_tsps_position_detail(self, position_id: str) -> str:
        """Show detailed status for a specific TSPS position."""
        import random

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Generate realistic operator data
        operators = [
            {"name": "Susan Johnson", "id": "4472", "experience": "3.5 years", "level": "Advanced"},
            {"name": "Mary Williams", "id": "4481", "experience": "2.8 years", "level": "Intermediate"},
            {"name": "Barbara Davis", "id": "4495", "experience": "5.2 years", "level": "Senior"},
            {"name": "Patricia Miller", "id": "4503", "experience": "1.9 years", "level": "Basic"},
            {"name": "Linda Wilson", "id": "4517", "experience": "4.1 years", "level": "Advanced"}
        ]

        operator = random.choice(operators)
        shift_hours = self._get_shift_hours()

        position_output = f"""TSPS Position Status - {position_id}
Query Time: {current_time}

OPERATOR INFORMATION
{'=' * 30}
Operator ID:              {operator['id']}
Name:                     {operator['name']}
Shift:                    {shift_hours}
Experience Level:         {operator['experience']}
Certification:            {operator['level']} Level Certified
Union Local:              Communications Workers Local 1101

CURRENT ACTIVITY
{'=' * 30}
Status:                   {'ACTIVE' if random.random() > 0.1 else 'ON BREAK'}"""

        if random.random() > 0.1:  # Active status
            call_types = ['Person-to-Person NYC to BOS', 'Collect call to Chicago', 'Directory assistance request',
                         'Conference call setup', 'International call to London', 'Billing inquiry']
            current_call = random.choice(call_types)
            position_output += f"""
Call in Progress:         {current_call}
Call Duration:            {random.randint(15, 180)} seconds
Queue Position:           Handling priority call
Customer Location:        {random.choice(['Manhattan, NY', 'Boston, MA', 'Philadelphia, PA', 'Washington, DC'])}

PERFORMANCE TODAY
{'=' * 30}
Calls Handled:            {random.randint(85, 145)}
Average Handle Time:      {random.uniform(25, 40):.1f} seconds
Customer Rating:          {random.uniform(4.5, 5.0):.1f}/5.0
Resolution Rate:          {random.uniform(0.92, 0.98):.1%}
Escalations:              {random.randint(0, 3)}
Break Time Used:          {random.randint(12, 18)} minutes

EQUIPMENT STATUS
{'=' * 30}
Headset:                  OPERATIONAL
Position Terminal:        ONLINE
Conference Bridge:        AVAILABLE
Recording System:         ACTIVE
Billing Interface:        CONNECTED
Directory Database:       ACCESSIBLE

SUPERVISOR NOTES
{'=' * 30}"""

            notes = [
                "Excellent performance maintaining service standards",
                "Assisting with new operator training today",
                "Recommended for advanced certification program",
                "Consistently exceeds productivity targets",
                "Strong customer service skills demonstrated"
            ]
            position_output += f"• {random.choice(notes)}"

        else:  # On break
            position_output += f"""
Break Type:               {random.choice(['Scheduled 15-minute', 'Lunch break', 'Relief break'])}
Return Time:              {(self.clock.now() + timedelta(minutes=random.randint(5, 30))).strftime('%H:%M')}
Coverage:                 Position covered by relief operator"""

        return position_output
    def _show_tsps_operator_status(self) -> str:
        """Show comprehensive operator staffing and performance status."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        operators_output = f"""TSPS Operator Staffing and Performance
Report Generated: {current_time}

STAFFING STATUS
{'=' * 25}
Total Positions:          {self.tsps_data['total_positions']}
Currently Staffed:        {self.tsps_data['active_positions']}
On Duty:                  {self.tsps_data['active_positions'] - random.randint(0, 3)}
On Break:                 {random.randint(0, 3)}
Relief Operators:         {random.randint(2, 5)}
Supervisors:              {random.randint(3, 5)}

SHIFT DISTRIBUTION
{'=' * 25}"""

        # Generate realistic shift data
        shifts = [
            ("Day Shift (08:00-16:00)", random.randint(18, 25)),
            ("Evening Shift (16:00-24:00)", random.randint(12, 18)),
            ("Night Shift (24:00-08:00)", random.randint(6, 12))
        ]

        for shift_name, operators in shifts:
            operators_output += f"\n{shift_name:<25} {operators} operators"

        operators_output += f"""

CERTIFICATION LEVELS
{'=' * 25}
Basic Level:              {random.randint(8, 15)} operators
Intermediate Level:       {random.randint(15, 22)} operators
Advanced Level:           {random.randint(12, 18)} operators
Senior Level:             {random.randint(6, 10)} operators
Supervisor Track:         {random.randint(3, 6)} operators

PERFORMANCE METRICS
{'=' * 25}
Average Experience:       {random.uniform(2.8, 4.2):.1f} years
Productivity Rating:      {random.uniform(0.92, 0.98):.1%} of standard
Quality Score:            {random.uniform(4.3, 4.8):.1f}/5.0 average
Attendance Rate:          {random.uniform(0.94, 0.98):.1%}
Turnover Rate:            {random.uniform(0.08, 0.15):.1%} annually

TOP PERFORMERS (This Month)
{'=' * 25}"""

        top_performers = [
            ("Barbara Davis", "4495", random.uniform(4.8, 5.0), random.randint(125, 145)),
            ("Susan Johnson", "4472", random.uniform(4.7, 4.9), random.randint(120, 140)),
            ("Linda Wilson", "4517", random.uniform(4.6, 4.8), random.randint(115, 135))
        ]

        for name, op_id, rating, calls in top_performers:
            operators_output += f"\n{name:<18} ({op_id})  {rating:.1f}/5.0  {calls} avg calls/day"

        operators_output += f"""

TRAINING AND DEVELOPMENT
{'=' * 25}
New Hires in Training:    {random.randint(2, 6)}
Certification Testing:    {random.randint(4, 8)} operators scheduled
Skills Development:       {random.randint(8, 15)} enrolled in programs
Cross-Training:           {random.randint(5, 12)} operators

SCHEDULING NOTES
{'=' * 25}
Peak Coverage:            14:00-16:00 EST (all positions staffed)
Minimum Staffing:         02:00-06:00 EST ({random.randint(6, 10)} positions)
Holiday Schedule:         Modified staffing for upcoming holidays
Overtime Authorized:      Up to {random.randint(8, 15)} hours per week"""

        return operators_output
    def _show_tsps_training_programs(self) -> str:
        """Show TSPS training programs and certification status."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        training_output = f"""TSPS Training Program Status
Report Generated: {current_time}

ACTIVE TRAINING SESSIONS
{'=' * 35}"""

        training_sessions = [
            ("New Operator Orientation", random.randint(3, 6), "Week 1-2", "Basic"),
            ("Advanced Call Handling", random.randint(4, 8), "Ongoing", "Advanced"),
            ("International Procedures", random.randint(6, 12), "2 weeks", "Intermediate"),
            ("Emergency Protocol Review", random.randint(8, 15), "1 week", "All Levels"),
            ("Customer Service Excellence", random.randint(5, 10), "3 weeks", "Intermediate"),
            ("Technology Update Session", random.randint(10, 18), "1 day", "All Levels")
        ]

        for session, participants, duration, level in training_sessions:
            training_output += f"\n{session:<25} {participants:>2} trainees  {duration:<8} {level}"

        training_output += f"""

CERTIFICATION PROGRAM
{'=' * 35}
Certification Levels:     4 levels (Basic through Senior)
Current Testing Cycle:    {random.choice(['Week 2', 'Week 3', 'Week 4'])} of monthly cycle
Pass Rate:                {random.uniform(0.85, 0.95):.1%} overall
Next Exam Date:           {(self.clock.now() + timedelta(days=random.randint(7, 21))).strftime('%B %d, %Y')}

CERTIFICATION STATUS
{'=' * 35}
Eligible for Testing:     {random.randint(8, 15)} operators
Pending Results:          {random.randint(2, 6)} operators
Recent Certifications:    {random.randint(3, 8)} operators (last 30 days)
Certification Renewals:   {random.randint(5, 12)} operators (next 90 days)

TRAINING EFFECTIVENESS
{'=' * 35}
Post-Training Performance: {random.uniform(15, 25):+.0f}% improvement average
Customer Satisfaction:     {random.uniform(0.3, 0.6):+.1f} point increase
Error Reduction:          {random.uniform(20, 35):.0f}% decrease
Handle Time Improvement:   {random.uniform(8, 18):.0f}% faster
Confidence Rating:         {random.uniform(20, 35):+.0f}% increase

SPECIALIZED TRAINING
{'=' * 35}
Emergency Services:       All operators certified
International Calls:     {random.randint(25, 35)} operators certified
Conference Setup:         {random.randint(20, 30)} operators certified
Billing Systems:          {random.randint(15, 25)} operators certified
Directory Assistance:     All operators certified

UPCOMING TRAINING
{'=' * 35}"""

        upcoming_training = [
            ("New Technology Integration", f"{(self.clock.now() + timedelta(days=random.randint(7, 14))).strftime('%B %d')}"),
            ("Customer Relations Workshop", f"{(self.clock.now() + timedelta(days=random.randint(14, 28))).strftime('%B %d')}"),
            ("Quality Assurance Methods", f"{(self.clock.now() + timedelta(days=random.randint(21, 35))).strftime('%B %d')}"),
            ("Regulatory Compliance Update", f"{(self.clock.now() + timedelta(days=random.randint(28, 42))).strftime('%B %d')}")
        ]

        for training, date in upcoming_training:
            training_output += f"\n{training:<30} {date}"

        training_output += f"""

TRAINING RESOURCES
{'=' * 35}
Training Manuals:         Current (Version 3.2)
Practice Simulators:      {random.randint(8, 12)} systems available
Instructor Staff:         {random.randint(4, 7)} certified trainers
Training Facilities:      2 dedicated training centers

Contact: Training Coordinator ext 4225"""

        return training_output
    def _show_tsps_queue_management(self) -> str:
        """Show TSPS call queue management and statistics."""

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        queue_output = f"""TSPS Call Queue Management
Real-Time Status: {current_time}

CURRENT QUEUE STATUS
{'=' * 30}
Calls in Queue:           {self.tsps_data['queue_length']}
Average Wait Time:        {self.tsps_data['answer_time']:.1f} seconds
Longest Wait:             {max(int(self.tsps_data['answer_time'] * 2), random.randint(45, 180))} seconds
Queue Growth Rate:        {random.choice(['+', '-'])}{random.randint(1, 8)} calls/minute

QUEUE BY SERVICE TYPE
{'=' * 30}"""

        queue_breakdown = [
            ("Person-to-Person", int(self.tsps_data['queue_length'] * 0.25), "HIGH"),
            ("Collect Calls", int(self.tsps_data['queue_length'] * 0.35), "NORMAL"),
            ("Directory Assistance", int(self.tsps_data['queue_length'] * 0.30), "NORMAL"),
            ("Conference Setup", int(self.tsps_data['queue_length'] * 0.05), "LOW"),
            ("International", int(self.tsps_data['queue_length'] * 0.05), "LOW")
        ]

        for service, calls, priority in queue_breakdown:
            queue_output += f"\n{service:<20} {calls:>2} calls  {priority} priority"

        queue_output += f"""

QUEUE PERFORMANCE (Last Hour)
{'=' * 30}
Calls Answered:           {random.randint(280, 450)}
Average Handle Time:      {self.tsps_data['avg_work_time']:.1f} seconds
Service Level:            {random.uniform(0.92, 0.98):.1%} (answered <20 sec)
Abandonment Rate:         {random.uniform(0.02, 0.08):.1%}
Peak Queue Length:        {random.randint(15, 35)} calls

TRAFFIC PATTERNS
{'=' * 30}"""

        # Generate hourly queue patterns
        for hour_offset in range(-3, 1):
            pattern_hour = (self.clock.now().hour + hour_offset) % 24
            if 8 <= pattern_hour <= 17:
                queue_size = random.randint(15, 35)
                pattern = "Business Peak"
            elif 17 <= pattern_hour <= 22:
                queue_size = random.randint(8, 20)
                pattern = "Evening Traffic"
            else:
                queue_size = random.randint(2, 8)
                pattern = "Overnight"

            time_str = f"{pattern_hour:02d}:00"
            queue_output += f"\n{time_str}  {queue_size:>2} calls avg  {pattern}"

        queue_output += f"""

OPERATOR AVAILABILITY
{'=' * 30}
Available Operators:      {self.tsps_data['active_positions'] - random.randint(1, 3)}
Busy Operators:           {random.randint(1, 3)}
On Break:                 {random.randint(0, 2)}
In Training:              {random.randint(0, 1)}

QUEUE MANAGEMENT ALERTS
{'=' * 30}"""

        alerts = []
        if self.tsps_data['queue_length'] > 20:
            alerts.append("⚠ WARNING: Queue length exceeds normal range")
        if self.tsps_data['answer_time'] > 15:
            alerts.append("⚠ NOTICE: Answer time above target")
        if random.random() < 0.3:
            alerts.append("ℹ INFO: Peak traffic period - additional operators requested")

        if alerts:
            for alert in alerts:
                queue_output += f"\n{alert}"
        else:
            queue_output += "\n✓ All queue metrics within normal range"

        queue_output += f"""

RECOMMENDED ACTIONS
{'=' * 30}
• Monitor queue length closely during peak hours
• Request overflow assistance if queue exceeds 25 calls
• Implement call-back service for extended wait times
• Track abandonment rate and adjust staffing accordingly"""

        return queue_output
    def _show_available_tsps_reports(self) -> str:
        """Show available TSPS reporting options."""
        return """Available TSPS Reports:

  tsps reports daily        Daily performance summary
  tsps reports weekly       Weekly productivity analysis
  tsps reports monthly      Monthly operational report
  tsps reports operators    Individual operator performance
  tsps reports quality      Service quality metrics
  tsps reports training     Training effectiveness report

Use 'tsps reports <type>' to generate specific report"""
    def _generate_tsps_report(self, report_type: str) -> str:
        """Generate specific TSPS performance report."""
        import random

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        if report_type == "daily":
            return f"""TSPS Daily Performance Report
Generated: {current_time}

DAILY SUMMARY
{'=' * 20}
Calls Handled:            {random.randint(2800, 4200):,}
Average Handle Time:      {random.uniform(25, 40):.1f} seconds
Service Level:            {random.uniform(0.92, 0.98):.1%}
Customer Satisfaction:    {random.uniform(4.2, 4.8):.1f}/5.0
Operator Utilization:     {random.uniform(0.75, 0.90):.1%}

Peak traffic occurred at {random.randint(14, 16)}:{random.randint(0, 59):02d} with {random.randint(45, 65)} calls in queue."""

        elif report_type == "weekly":
            return f"""TSPS Weekly Productivity Analysis
Generated: {current_time}

WEEKLY PERFORMANCE TRENDS
{'=' * 30}
Total Calls:              {random.randint(18000, 28000):,}
Average Daily Volume:     {random.randint(2800, 4200):,}
Productivity Increase:    {random.uniform(2, 8):+.1f}% vs last week
Quality Improvement:      {random.uniform(0.1, 0.5):+.1f} points
Training Impact:          {random.uniform(5, 15):.0f}% improvement"""

        else:
            return f"tsps: Report type '{report_type}' not implemented\nUse 'tsps reports' for available options"
    def cmd_operator(self, args: List[str]) -> str:
        """Enhanced operator services with realistic assisted calling operations."""

        if not args:
            current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

            return f"""Bell System Operator Services
Assisted Calling and Special Services
{current_time}

CURRENT OPERATIONS STATUS
{'=' * 35}
Active Operators:         {random.randint(25, 45)} (Day Shift)
Call Queue Length:        {random.randint(3, 18)} calls waiting
Average Answer Time:      {random.uniform(3.2, 8.5):.1f} seconds
Service Level:            {random.uniform(0.92, 0.98):.1%} (within 20 seconds)

SERVICE TYPES AVAILABLE
{'=' * 35}
Person-to-Person:         Available
Collect Calls:            Available
Conference Calls:         Available (up to 8 parties)
International:            Available (120+ countries)
Directory Assistance:     Available 24/7
Credit Card Calls:        Available
Time and Weather:         Available

PERFORMANCE METRICS
{'=' * 35}
Calls Completed Today:    {random.randint(2800, 4500):,}
Average Handle Time:      {random.uniform(35, 55):.1f} seconds
Customer Satisfaction:    {random.uniform(4.3, 4.8):.1f}/5.0 rating
First Call Resolution:    {random.uniform(0.88, 0.95):.1%}

Commands:
  operator assist          Request operator assistance
  operator conference      Set up conference call
  operator international   International calling rates
  operator status          Detailed service status"""

        elif args[0] == "assist":
            return self._handle_operator_assistance()

        elif args[0] == "conference":
            return self._setup_conference_call()

        elif args[0] == "international":
            return self._show_international_rates()

        elif args[0] == "status":
            return self._show_operator_detailed_status()

        else:
            available_commands = ["assist", "conference", "international", "status"]
            return f"operator: Unknown option '{args[0]}'\nAvailable commands: {', '.join(available_commands)}"
    def _handle_operator_assistance(self) -> str:
        """Handle operator assistance request."""
        import random

        assistance_types = [
            "Person-to-person call to Chicago",
            "Collect call setup",
            "Conference call arrangement",
            "International call to London",
            "Credit card verification",
            "Directory assistance request"
        ]

        current_request = random.choice(assistance_types)
        wait_time = random.uniform(2.5, 12.0)

        return f"""Operator Assistance Request
{'=' * 30}

Connecting you with the next available operator...

Estimated Wait Time:      {wait_time:.1f} seconds
Queue Position:           {random.randint(1, 8)}
Service Type:             {current_request}

Please hold while we connect your call.
An operator will be with you shortly to assist with your request.

For immediate assistance, dial 0 for the operator, or report to
the Switching Control Center on the emergency order wire."""
    def _setup_conference_call(self) -> str:
        """Set up conference call with realistic procedures."""

        return f"""Bell System Conference Call Setup
{'=' * 40}

Conference Bridge Available: Bridge-{random.randint(1, 12)}
Maximum Participants:        8 parties
Setup Time:                  {random.uniform(2.5, 5.0):.1f} minutes estimated

CONFERENCE PROCEDURES
{'=' * 30}
1. Operator will place calls to each participant
2. Each party will be placed on hold during setup
3. All parties connected simultaneously when ready
4. Conference moderator designated (calling party)
5. Recording available if requested (additional charges apply)

CURRENT RATES
{'=' * 30}
Setup Fee:                   $3.50
Per-Minute Rate:            $0.85 per participant
Overtime Surcharge:         25% after 6:00 PM
Recording Fee:              $8.00 per hour

Estimated Total Cost:       ${random.uniform(15.50, 45.75):.2f} for 30-minute call

To proceed, please provide participant phone numbers when operator connects."""
    def _show_international_rates(self) -> str:
        """Show international calling rates and procedures."""
        import random

        return f"""Bell System International Calling
Rates and Service Information
{'=' * 40}

POPULAR DESTINATIONS (Per Minute)
{'=' * 40}
United Kingdom:              ${random.uniform(1.85, 2.25):.2f}
France:                      ${random.uniform(2.10, 2.45):.2f}
West Germany:                ${random.uniform(1.95, 2.35):.2f}
Japan:                       ${random.uniform(3.25, 3.85):.2f}
Australia:                   ${random.uniform(2.85, 3.25):.2f}
Mexico:                      ${random.uniform(1.25, 1.65):.2f}
Canada:                      ${random.uniform(0.85, 1.15):.2f}

SERVICE OPTIONS
{'=' * 40}
Direct Dial International:   Available to 35+ countries
Operator Assisted:           Available worldwide (120+ countries)
Station-to-Station:          Standard rate
Person-to-Person:           Additional $3.75 charge
Collect Calls:              Accepted by most countries

PEAK/OFF-PEAK RATES
{'=' * 40}
Peak Hours (8 AM - 6 PM):   Standard rates (above)
Off-Peak (6 PM - 8 AM):     25% discount
Weekend (Sat-Sun):          35% discount
Holiday Rates:              Peak rates apply

DIALING PROCEDURES
{'=' * 40}
Direct Dial:                011 + Country Code + Number
Operator Assisted:          0 + Country Code + Number
Emergency International:    Dial 0 for immediate assistance

For current rates to specific countries, dial 0 for operator assistance."""
    def _show_operator_detailed_status(self) -> str:
        """Show detailed operator service status."""

        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        return f"""Detailed Operator Services Status
Report Generated: {current_time}

STAFFING AND CAPACITY
{'=' * 30}
Total Operator Positions:    52
Currently Staffed:          {random.randint(28, 45)}
Available for Calls:        {random.randint(25, 42)}
On Break:                   {random.randint(1, 4)}
In Training:                {random.randint(0, 2)}

CALL VOLUME STATISTICS
{'=' * 30}
Calls Today:                {random.randint(3200, 5800):,}
Average per Hour:           {random.randint(180, 320)}
Peak Hour Volume:           {random.randint(420, 680)} calls
Current Queue Length:       {random.randint(2, 25)} calls

SERVICE QUALITY METRICS
{'=' * 30}
Answer Time Average:        {random.uniform(3.8, 9.2):.1f} seconds
Service Level Target:       85% answered within 20 seconds
Current Service Level:      {random.uniform(0.82, 0.96):.1%}
Customer Satisfaction:      {random.uniform(4.1, 4.7):.1f}/5.0 rating
Call Completion Rate:       {random.uniform(0.94, 0.98):.1%}

SPECIALIZED SERVICES
{'=' * 30}
Conference Calls Setup:     {random.randint(45, 125)} today
International Assistance:   {random.randint(180, 340)} calls
Directory Assistance:       {random.randint(1200, 2100)} requests
Emergency Services:         {random.randint(8, 25)} calls
Credit Verification:        {random.randint(95, 180)} transactions

Next Shift Change: {(self.clock.now() + timedelta(hours=random.randint(2, 6))).strftime('%H:%M EST')}"""
    def cmd_directory(self, args: List[str]) -> str:
        """Enhanced directory assistance with realistic number lookup operations."""
        import random

        if not args:
            return f"""Bell System Directory Assistance
Information Services and Number Lookup
{'=' * 45}

CURRENT SERVICE STATUS
{'=' * 30}
Service:                     Available 24/7
Average Response Time:       {random.uniform(4.5, 8.2):.1f} seconds
Information Accuracy:        {random.uniform(0.96, 0.99):.1%}
Operator Availability:       {random.randint(18, 32)} operators on duty

REQUEST VOLUME TODAY
{'=' * 30}
Directory Requests:          {random.randint(2400, 4200):,}
Business Listings:           {random.randint(1200, 2100):,}
Residential Listings:        {random.randint(1100, 1900):,}
Government Numbers:          {random.randint(95, 180):,}

AVAILABLE SERVICES
{'=' * 30}
Local Directory:             Free within calling area
Long Distance Directory:     $0.50 per request
Business Information:        Free (includes addresses)
Government Listings:         Free
New Listings:               Updated daily
Unlisted Numbers:           Not available

COVERAGE AREAS
{'=' * 30}
Local Exchange:              Complete coverage
Metropolitan Area:           All exchanges covered
Interstate:                  48 states + DC
International:               Major cities only (limited)

To request directory assistance: Dial 411 (local) or 1-Area Code-555-1212 (long distance)"""

        elif args[0] == "lookup" and len(args) > 1:
            return self._perform_directory_lookup(" ".join(args[1:]))

        elif args[0] == "business":
            return self._show_business_directory()

        elif args[0] == "government":
            return self._show_government_directory()

        else:
            available_commands = ["lookup", "business", "government"]
            return f"directory: Unknown option '{args[0] if args else 'missing'}'\nAvailable commands: {', '.join(available_commands)}"
    def _perform_directory_lookup(self, search_term: str) -> str:
        """Perform a realistic directory lookup simulation."""

        # Generate realistic directory entries
        sample_listings = [
            ("JOHNSON, ROBERT", "212-555-4729", "147 W 42ND ST"),
            ("SMITH, MARY E", "212-555-8361", "89 PARK AVE"),
            ("ACME CORPORATION", "212-555-9000", "250 BROADWAY"),
            ("BROWN, JAMES", "617-555-2847", "BOSTON, MA"),
            ("CITY HALL", "212-555-1000", "MUNICIPAL BLDG"),
            ("WILLIAMS, SUSAN", "212-555-5623", "BROOKLYN, NY")
        ]

        found_listing = random.choice(sample_listings)
        search_time = random.uniform(3.5, 8.5)

        return f"""Directory Assistance Lookup Result
{'=' * 40}

Search Term: "{search_term}"
Search Time: {search_time:.1f} seconds

LISTING FOUND
{'=' * 20}
Name:        {found_listing[0]}
Number:      {found_listing[1]}
Address:     {found_listing[2]}

Status:      CURRENT LISTING
Last Update: {(self.clock.now() - timedelta(days=random.randint(1, 90))).strftime('%B %Y')}

Charges: {'Free (local)' if random.random() > 0.3 else '$0.50 (long distance)'}

Would you like this number connected automatically?
Additional charge: $0.25 for direct connection."""
    def _show_business_directory(self) -> str:
        """Show business directory services."""
        import random

        return f"""Business Directory Services
{'=' * 35}

BUSINESS CATEGORIES
{'=' * 25}
Banking and Finance:         {random.randint(180, 320)} listings
Medical Services:            {random.randint(240, 450)} listings
Legal Services:              {random.randint(95, 180)} listings
Restaurants:                 {random.randint(450, 780)} listings
Retail and Shopping:         {random.randint(680, 1200)} listings
Transportation:              {random.randint(120, 220)} listings
Government Services:         {random.randint(85, 150)} listings

FEATURED BUSINESS LISTINGS
{'=' * 35}
ABC TAXI SERVICE            212-555-TAXI (8294)
CITY HOSPITAL               212-555-9911
FIRST NATIONAL BANK         212-555-2100
GRAND CENTRAL STATION       212-555-4455
MACY'S DEPARTMENT STORE     212-555-6700

YELLOW PAGES INFORMATION
{'=' * 35}
Total Business Listings:    {random.randint(8500, 12000):,}
Updated:                    Monthly
Advertising Available:      Contact 212-555-SELL
Directory Distribution:     Free to all customers

For specific business lookups, dial 411 or use 'directory lookup <business name>'"""
    def _show_government_directory(self) -> str:
        """Show government directory listings."""
        return f"""Government Directory Listings
{'=' * 40}

EMERGENCY SERVICES
{'=' * 25}
Police Emergency:            911
Fire Department:             911
Ambulance/EMS:              911
Poison Control:             212-555-1212

FEDERAL GOVERNMENT
{'=' * 25}
Federal Information:         202-555-1212
Internal Revenue Service:    800-555-1040
Social Security Admin:       800-555-1213
Veterans Administration:     212-555-4400

STATE AND LOCAL
{'=' * 25}
City Hall:                  212-555-1000
Department of Motor Vehicles: 212-555-2020
Public Works:               212-555-3000
Building Department:        212-555-3500
Board of Elections:         212-555-8683

COURTS AND LEGAL
{'=' * 25}
Municipal Court:            212-555-7000
County Clerk:               212-555-7500
Legal Aid Society:          212-555-9200

All government directory assistance is provided free of charge."""
