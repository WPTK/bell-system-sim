"""
Trouble tickets: the dashboard, detail, assignment and escalation.
"""

import random
from ..types import TroubleTicket
from typing import (
    List,
    Optional,
)


from .session import SessionState


class TicketCommands(SessionState):
    """
    Trouble tickets: the dashboard, detail, assignment and escalation.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def cmd_ticket(self, args: List[str]) -> str:
        """Trouble ticket management system"""
        if not args:
            return """Bell System Trouble Ticket Management
Customer Service and Network Operations

Available Commands:
  ticket create        - Create new trouble ticket
  ticket status <ID>   - Display ticket status
  ticket update <ID>   - Update ticket information
  ticket escalate <ID> - Escalate ticket priority
  ticket close <ID>    - Close completed ticket

Current Ticket Summary:
  Open Tickets:        23 active
  Pending Review:      8 tickets
  Closed Today:        67 tickets
  Average Resolution:  4.2 hours

Priority Distribution:
  CRITICAL: 2    HIGH: 7    MEDIUM: 14    LOW: 8"""

        if args[0] == "status" and len(args) > 1:
            ticket_id = args[1].upper()
            return f"""Trouble Ticket Status: {ticket_id}
Last Updated: November 14, 1983 07:30:15

Ticket Information:
  Priority:           HIGH
  Customer Class:     BUSINESS-CRITICAL
  Reported Problem:   No dial tone - 555-0123
  Location:           123 Main St, New York, NY

Assignment:
  Assigned To:        Field Team 7
  Dispatch Time:      07:15
  ETA:                08:30

Progress Notes:
  07:15 - Ticket created, team dispatched
  07:30 - Team en route to location
  07:45 - Cable pair fault suspected

Escalation:
  Response Time SLA:  60 minutes
  Time Remaining:     45 minutes
  Next Escalation:    08:15 (Level 2)

Status: IN PROGRESS"""

        elif args[0] == "create":
            new_ticket = f"SW-{random.randint(2800, 2999)}"
            return f"""New Trouble Ticket Created: {new_ticket}
Creation Time: November 14, 1983 07:46:45

Ticket Type: [To be specified]
Priority: [To be assigned]
Customer Information: [To be entered]

Please provide:
1. Customer phone number or service address
2. Problem description
3. Customer class (RESIDENTIAL/BUSINESS/GOVERNMENT)
4. Urgency level

Use 'ticket update {new_ticket}' to add information"""

        return f"ticket: unknown option '{args[0]}'"
    def cmd_trouble(self, args: List[str]) -> str:
        """Enhanced trouble ticket management with authentic Bell System operations."""

        if not args:
            return self._show_trouble_ticket_dashboard()

        elif args[0] == "list":
            priority_filter = args[1] if len(args) > 1 else None
            return self._list_trouble_tickets(priority_filter)

        elif args[0] == "detail" and len(args) > 1:
            ticket_id = args[1].upper()
            return self._show_trouble_ticket_detail(ticket_id)

        elif args[0] == "assign" and len(args) > 2:
            ticket_id = args[1].upper()
            team = " ".join(args[2:])
            return self._assign_trouble_ticket(ticket_id, team)

        elif args[0] == "update" and len(args) > 2:
            ticket_id = args[1].upper()
            status = args[2].upper()
            return self._update_trouble_ticket(ticket_id, status)

        elif args[0] == "escalate" and len(args) > 1:
            ticket_id = args[1].upper()
            return self._escalate_trouble_ticket(ticket_id)

        elif args[0] == "resolve" and len(args) > 1:
            ticket_id = args[1].upper()
            return self._resolve_trouble_ticket(ticket_id)

        elif args[0] == "create":
            return self._create_manual_ticket(args[1:] if len(args) > 1 else [])

        elif args[0] == "geographic":
            return self._show_geographic_trouble_overview()

        elif args[0] == "priority":
            return self._show_priority_analysis()

        else:
            available_commands = ["list", "detail", "assign", "update", "escalate", "resolve", "create", "geographic", "priority"]
            return f"trouble: Unknown option '{args[0]}'\nAvailable commands: {', '.join(available_commands)}"
    def _show_trouble_ticket_dashboard(self) -> str:
        """Show comprehensive trouble ticket dashboard with real-time status."""
        current_time = self.clock.now().strftime("%B %d, %Y %H:%M:%S EST")

        # Calculate ticket statistics
        critical_tickets = [t for t in self.active_tickets if t['priority'] == 'CRITICAL']
        major_tickets = [t for t in self.active_tickets if t['priority'] == 'MAJOR']
        minor_tickets = [t for t in self.active_tickets if t['priority'] == 'MINOR']

        # Calculate customer impact
        total_customers_affected = sum(t['customer_impact'] for t in self.active_tickets)
        revenue_impact = sum(t['business_impact']['revenue_loss_hour'] for t in self.active_tickets)

        dashboard = f"""Bell System Trouble Ticket Management System
Real-Time Operations Dashboard
{current_time}

ACTIVE TROUBLE TICKETS
{'=' * 40}
Critical Priority:        {len(critical_tickets)} tickets
Major Priority:           {len(major_tickets)} tickets
Minor Priority:           {len(minor_tickets)} tickets
Total Active:             {len(self.active_tickets)} tickets

CUSTOMER IMPACT ANALYSIS
{'=' * 40}
Customers Affected:       {total_customers_affected:,}
Revenue Impact (hourly):  ${revenue_impact:,}
Service Quality Impact:   {'SEVERE' if len(critical_tickets) > 2 else 'MODERATE' if len(major_tickets) > 5 else 'MINIMAL'}

RECENT CRITICAL ISSUES
{'=' * 40}"""

        # Show most recent critical tickets
        recent_critical = sorted(critical_tickets, key=lambda x: x['created_time'], reverse=True)[:3]

        if recent_critical:
            for ticket in recent_critical:
                age = self.clock.now() - ticket['created_time']
                age_str = f"{int(age.total_seconds() // 3600)}h{int((age.total_seconds() % 3600) // 60)}m"
                dashboard += f"\n{ticket['id']:<8} {age_str:<6} {ticket['affected_office']['city']:<12} {ticket['title'][:45]}"
        else:
            dashboard += "\n✓ No critical issues currently active"

        # Geographic distribution
        geographic_impact = {}
        for ticket in self.active_tickets:
            state = ticket['affected_office']['state']
            if state not in geographic_impact:
                geographic_impact[state] = 0
            geographic_impact[state] += 1

        dashboard += f"""

GEOGRAPHIC DISTRIBUTION
{'=' * 40}"""

        for state, count in sorted(geographic_impact.items(), key=lambda x: x[1], reverse=True)[:8]:
            dashboard += f"\n{state:<4} {count:>2} active tickets"

        dashboard += f"""

OPERATIONAL METRICS
{'=' * 40}
Average Resolution Time:  {sum(t['estimated_duration'] for t in self.completed_tickets[-20:]) // max(len(self.completed_tickets[-20:]), 1) if self.completed_tickets else 180} minutes
Escalation Rate:          {len([t for t in self.active_tickets if t['escalation_level'] > 1]) / max(len(self.active_tickets), 1) * 100:.1f}%
On-Time Resolution:       {85 + random.randint(-5, 10):.1f}%

Commands:
  trouble list [priority]     List tickets by priority
  trouble detail <id>         Show detailed ticket information
  trouble assign <id> <team>  Assign ticket to team
  trouble escalate <id>       Escalate ticket priority
  trouble geographic          Geographic trouble overview
  trouble priority            Priority analysis and trends"""

        return dashboard
    def _list_trouble_tickets(self, priority_filter: Optional[str] = None) -> str:
        """List trouble tickets with optional priority filtering."""
        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Filter tickets if priority specified
        if priority_filter:
            priority_filter = priority_filter.upper()
            filtered_tickets = [t for t in self.active_tickets if t['priority'] == priority_filter]
            title = f"Trouble Tickets - {priority_filter} Priority"
        else:
            filtered_tickets = self.active_tickets
            title = "All Active Trouble Tickets"

        listing = f"""{title}
Query Time: {current_time}

{'ID':<10} {'PRIORITY':<8} {'AGE':<6} {'LOCATION':<15} {'CUSTOMERS':<9} {'STATUS':<12} {'DESCRIPTION':<30}
{'=' * 100}"""

        # Sort by priority (Critical first) then by age
        priority_order = {'CRITICAL': 0, 'MAJOR': 1, 'MINOR': 2}
        sorted_tickets = sorted(filtered_tickets,
                              key=lambda x: (priority_order[x['priority']], x['created_time']))

        for ticket in sorted_tickets:
            age = self.clock.now() - ticket['created_time']
            age_str = f"{int(age.total_seconds() // 3600)}h{int((age.total_seconds() % 3600) // 60)}m"

            location = f"{ticket['affected_office']['city']}, {ticket['affected_office']['state']}"
            customers = f"{ticket['customer_impact']:,}"
            description = ticket['title'][:28] + ".." if len(ticket['title']) > 30 else ticket['title']

            listing += f"\n{ticket['id']:<10} {ticket['priority']:<8} {age_str:<6} {location:<15} {customers:<9} {ticket['status']:<12} {description}"

        if not filtered_tickets:
            listing += f"\n{'No tickets found matching criteria' if priority_filter else 'No active tickets'}"

        listing += f"\n\nTotal: {len(filtered_tickets)} tickets"
        return listing
    def _show_trouble_ticket_detail(self, ticket_id: str) -> str:
        """Show comprehensive details for a specific trouble ticket."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found\nUse 'trouble list' to see active tickets"

        age = self.clock.now() - ticket['created_time']
        age_str = f"{int(age.total_seconds() // 3600)}h {int((age.total_seconds() % 3600) // 60)}m"

        detail = f"""Trouble Ticket Detail: {ticket['id']}
{'=' * 50}

TICKET IDENTIFICATION
{'=' * 30}
Ticket ID:                {ticket['id']}
Category:                 {ticket['category']}
Priority:                 {ticket['priority']}
Status:                   {ticket['status']}
Escalation Level:         {ticket['escalation_level']}
Created:                  {ticket['created_time'].strftime('%B %d, %Y %H:%M EST')}
Age:                      {age_str}

PROBLEM DESCRIPTION
{'=' * 30}
Title:                    {ticket['title']}

Description:
{ticket['description']}

AFFECTED INFRASTRUCTURE
{'=' * 30}
Central Office:           {ticket['affected_office']['city']}, {ticket['affected_office']['state']}
Area Code:                {ticket['affected_office']['npa']}
Exchange:                 {ticket['affected_office']['nxx']}
Switch Type:              {ticket['affected_office']['switch_type']}
Office Capacity:          {ticket['affected_office']['capacity']:,} lines
Current Utilization:      {ticket['affected_office']['utilization']}%

IMPACT ASSESSMENT
{'=' * 30}
Customers Affected:       {ticket['customer_impact']:,}
Geographic Scope:         {ticket['geographic_scope']}
Revenue Impact (hourly):  ${ticket['business_impact']['revenue_loss_hour']:,}
Service Level Impact:     {ticket['business_impact']['service_level_impact']}
Regulatory Exposure:      {'YES' if ticket['business_impact']['regulatory_exposure'] else 'NO'}

TECHNICAL DETAILS
{'=' * 30}
{ticket['technical_details']}

Equipment Involved:       {', '.join(ticket['equipment_involved'])}

ASSIGNMENT AND RESPONSE
{'=' * 30}
Assigned Team:            {ticket['assigned_team']}
Estimated Duration:       {ticket['estimated_duration']} minutes
Response Time Target:     {15 if ticket['priority'] == 'CRITICAL' else 30 if ticket['priority'] == 'MAJOR' else 60} minutes

REQUIRED ACTIONS
{'=' * 30}"""

        for i, action in enumerate(ticket['required_actions'], 1):
            detail += f"\n{i}. {action}"

        if ticket['resolution_steps']:
            detail += f"""

RESOLUTION PROGRESS
{'=' * 30}"""
            for i, step in enumerate(ticket['resolution_steps'], 1):
                detail += f"\n{i}. {step}"

        detail += f"""

ESCALATION CONTACTS
{'=' * 30}
Level 1:                  Field Maintenance Team ext 4350
Level 2:                  Engineering Support ext 4370
Level 3:                  Network Operations Center ext 4911
Emergency:                Bell System Emergency Line ext 911

Commands:
  trouble assign {ticket_id} <team>     Assign to team
  trouble update {ticket_id} <status>   Update status
  trouble escalate {ticket_id}          Escalate priority
  trouble resolve {ticket_id}           Mark as resolved"""

        return detail
    def _assign_trouble_ticket(self, ticket_id: str, team: str) -> str:
        """Assign trouble ticket to a specific team."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found"

        old_team = ticket['assigned_team']
        ticket['assigned_team'] = team
        # The switching control centre hands out unassigned tickets as the
        # shift runs. A ticket the operator has just dispatched is not
        # unassigned, so record it here or the SCC takes it straight back
        # and the dispatch you made silently disappears.
        self._assigned_tickets.add(ticket_id)
        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Add resolution step
        ticket['resolution_steps'].append(f"[{current_time}] Reassigned from '{old_team}' to '{team}' by {self.username}")

        return f"""Ticket Assignment Updated
{'=' * 30}
Ticket ID:        {ticket_id}
Previous Team:    {old_team}
New Team:         {team}
Updated By:       {self.username}
Time:             {current_time}

Assignment notification sent to {team}.
Ticket status updated in Bell System Trouble Management Database."""
    def _update_trouble_ticket(self, ticket_id: str, status: str) -> str:
        """Update trouble ticket status."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found"

        valid_statuses = ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'PENDING', 'TESTING', 'RESOLVED', 'CLOSED']
        if status not in valid_statuses:
            return f"trouble: Invalid status '{status}'\nValid statuses: {', '.join(valid_statuses)}"

        old_status = ticket['status']
        ticket['status'] = status
        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Add resolution step
        ticket['resolution_steps'].append(f"[{current_time}] Status changed from '{old_status}' to '{status}' by {self.username}")

        return f"""Ticket Status Updated
{'=' * 25}
Ticket ID:        {ticket_id}
Previous Status:  {old_status}
New Status:       {status}
Updated By:       {self.username}
Time:             {current_time}

Status change recorded in Bell System Operations Log."""
    def _escalate_trouble_ticket(self, ticket_id: str) -> str:
        """Escalate trouble ticket to higher priority or management level."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found"

        # Increase escalation level
        old_level = ticket['escalation_level']
        ticket['escalation_level'] = min(old_level + 1, 4)  # Max escalation level 4

        # Escalate priority if appropriate
        priority_escalation = {
            'MINOR': 'MAJOR',
            'MAJOR': 'CRITICAL',
            'CRITICAL': 'CRITICAL'  # Already at highest
        }

        old_priority = ticket['priority']
        if old_level == 1 and ticket['priority'] != 'CRITICAL':
            ticket['priority'] = priority_escalation[ticket['priority']]

        current_time = self.clock.now().strftime("%H:%M:%S EST")

        # Add resolution step
        escalation_note = f"[{current_time}] Escalated to level {ticket['escalation_level']} by {self.username}"
        if ticket['priority'] != old_priority:
            escalation_note += f" - Priority raised from {old_priority} to {ticket['priority']}"

        ticket['resolution_steps'].append(escalation_note)

        # Determine escalation contacts
        escalation_contacts = {
            2: "Engineering Support ext 4370",
            3: "Network Operations Manager ext 4950",
            4: "Director of Operations ext 4980"
        }

        return f"""Ticket Escalation Completed
{'=' * 35}
Ticket ID:            {ticket_id}
Previous Level:       {old_level}
New Escalation Level: {ticket['escalation_level']}
Priority:             {old_priority} → {ticket['priority']}
Escalated By:         {self.username}
Time:                 {current_time}

Escalation Contact:   {escalation_contacts.get(ticket['escalation_level'], 'Executive Team')}

Automatic notifications sent to management chain.
Escalation logged in Bell System Operations Database."""
    def _resolve_trouble_ticket(self, ticket_id: str) -> str:
        """Mark trouble ticket as resolved and move to completed tickets."""
        ticket = next((t for t in self.active_tickets if t['id'] == ticket_id), None)
        if not ticket:
            return f"trouble: Ticket {ticket_id} not found"

        # Calculate resolution time
        resolution_time = self.clock.now()
        total_time = resolution_time - ticket['created_time']
        resolution_minutes = int(total_time.total_seconds() / 60)

        # Update ticket
        ticket['status'] = 'RESOLVED'
        ticket['resolution_time'] = resolution_time
        ticket['actual_duration'] = resolution_minutes

        current_time = resolution_time.strftime("%H:%M:%S EST")
        ticket['resolution_steps'].append(f"[{current_time}] Ticket resolved by {self.username}")

        # Move to completed tickets
        self.active_tickets.remove(ticket)
        self.completed_tickets.append(ticket)

        # Calculate metrics
        target_time = 15 if ticket['priority'] == 'CRITICAL' else 30 if ticket['priority'] == 'MAJOR' else 60
        on_time = resolution_minutes <= target_time

        return f"""Trouble Ticket Resolved
{'=' * 30}
Ticket ID:            {ticket_id}
Resolution Time:      {current_time}
Total Duration:       {resolution_minutes} minutes
Target Time:          {target_time} minutes
Performance:          {'ON TIME' if on_time else 'EXCEEDED TARGET'}

Customer Impact:      {ticket['customer_impact']:,} customers restored
Revenue Recovered:    ${ticket['business_impact']['revenue_loss_hour'] * (resolution_minutes / 60):,.0f}

Resolution Details:
{ticket['technical_details']}

Ticket closed and archived in Bell System Trouble Management Database.
Service restoration confirmed for affected customers."""
    def _create_manual_ticket(self, args: List[str]) -> str:
        """Create a trouble ticket manually from craft-entered parameters."""
        valid_categories = list(self.ticket_categories.keys())
        valid_priorities = ['CRITICAL', 'MAJOR', 'MINOR']

        if not args:
            return f"""Trouble Ticket - Manual Entry
{'=' * 50}

Usage: trouble create <category> <priority> <description>

Valid categories:  {', '.join(valid_categories)}
Valid priorities:  {', '.join(valid_priorities)}

Example:
  trouble create {valid_categories[0]} MAJOR Water in cable at Elm St manhole"""

        category = args[0].upper()
        if category not in self.ticket_categories:
            return (f"trouble create: Unknown category '{args[0]}'\n"
                    f"Valid categories: {', '.join(valid_categories)}")

        priority = args[1].upper() if len(args) > 1 else 'MINOR'
        if priority not in valid_priorities:
            return (f"trouble create: Unknown priority '{args[1]}'\n"
                    f"Valid priorities: {', '.join(valid_priorities)}")

        description = " ".join(args[2:]) if len(args) > 2 else "Craft-reported trouble, details pending"

        category_data = self.ticket_categories[category]
        self.ticket_counter += random.randint(1, 5)
        ticket_id = f"TK-{self.ticket_counter}"

        # The same shape the generated tickets carry. This used to be a bare
        # office code, which every display that reached into the office
        # record then crashed on.
        affected_office = self._select_affected_infrastructure()
        customer_impact = random.randint(*category_data['customer_impact'][priority])
        estimated_duration = random.randint(*category_data['typical_duration'][priority])

        ticket: TroubleTicket = {
            'id': ticket_id,
            'category': category,
            'priority': priority,
            'title': description[:60],
            'description': description,
            'affected_office': affected_office,
            'customer_impact': customer_impact,
            'estimated_duration': estimated_duration,
            'status': 'OPEN',
            'assigned_team': 'UNASSIGNED',
            'created_time': self.clock.now(),
            'escalation_level': 1,
            'technical_details': 'Manually entered by craft; awaiting test board verification',
            'required_actions': ['Dispatch test board', 'Verify trouble condition', 'Assign repair force'],
            'equipment_involved': [],
            'geographic_scope': 'LOCAL',
            'business_impact': self._calculate_business_impact(priority, customer_impact),
            'resolution_steps': []
        }
        self.active_tickets.append(ticket)

        return f"""Trouble Ticket Created
{'=' * 50}
Ticket ID:                {ticket_id}
Created:                  {ticket['created_time'].strftime('%B %d, %Y %H:%M EST')}
Entered By:               {self.username}

TICKET DETAILS
{'=' * 40}
Category:                 {category}
Priority:                 {priority}
Description:              {description}
Affected Office:          {self._office_label(affected_office)}
Customers Affected:       {customer_impact:,}
Estimated Duration:       {estimated_duration} minutes
Status:                   OPEN (unassigned)

NEXT STEPS
{'=' * 40}
  trouble detail {ticket_id}          Review full ticket record
  trouble assign {ticket_id} <team>   Assign to a repair team
  trouble escalate {ticket_id}        Escalate priority

Total Active Tickets: {len(self.active_tickets)}"""
    def _show_geographic_trouble_overview(self) -> str:
        """Show geographic distribution and analysis of trouble tickets."""
        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        # Analyze geographic distribution
        state_analysis = {}
        metro_analysis = {}

        for ticket in self.active_tickets:
            state = ticket['affected_office']['state']
            city = ticket['affected_office']['city']

            # State-level analysis
            if state not in state_analysis:
                state_analysis[state] = {
                    'total': 0, 'critical': 0, 'major': 0, 'minor': 0,
                    'customers': 0, 'revenue_impact': 0
                }

            state_analysis[state]['total'] += 1
            state_analysis[state][ticket['priority'].lower()] += 1
            state_analysis[state]['customers'] += ticket['customer_impact']
            state_analysis[state]['revenue_impact'] += ticket['business_impact']['revenue_loss_hour']

            # Metro area analysis
            if city not in metro_analysis:
                metro_analysis[city] = {'count': 0, 'customers': 0}
            metro_analysis[city]['count'] += 1
            metro_analysis[city]['customers'] += ticket['customer_impact']

        overview = f"""Geographic Trouble Analysis
Report Generated: {current_time}

STATE-LEVEL IMPACT ANALYSIS
{'=' * 40}
{'STATE':<6} {'TOTAL':<5} {'CRIT':<4} {'MAJ':<4} {'MIN':<4} {'CUSTOMERS':<10} {'REV/HR':<8}"""

        for state, data in sorted(state_analysis.items(), key=lambda x: x[1]['total'], reverse=True):
            overview += f"\n{state:<6} {data['total']:<5} {data['critical']:<4} {data['major']:<4} {data['minor']:<4} {data['customers']:<10,} ${data['revenue_impact']:<7,.0f}"

        overview += f"""

METROPOLITAN AREA IMPACT
{'=' * 40}
{'CITY':<15} {'TICKETS':<7} {'CUSTOMERS':<10} {'SEVERITY':<8}"""

        for city, data in sorted(metro_analysis.items(), key=lambda x: x[1]['customers'], reverse=True)[:12]:
            severity = 'HIGH' if data['customers'] > 5000 else 'MEDIUM' if data['customers'] > 1000 else 'LOW'
            overview += f"\n{city:<15} {data['count']:<7} {data['customers']:<10,} {severity:<8}"

        # Network topology impact
        overview += f"""

NETWORK TOPOLOGY ANALYSIS
{'=' * 40}
Interstate Routes:        {len([t for t in self.active_tickets if t['geographic_scope'] == 'INTERSTATE'])} tickets
Regional Networks:        {len([t for t in self.active_tickets if t['geographic_scope'] == 'REGIONAL'])} tickets
Local Exchanges:          {len([t for t in self.active_tickets if t['geographic_scope'] == 'LOCAL'])} tickets

INFRASTRUCTURE TYPE IMPACT
{'=' * 40}"""

        # Analyze by switch type
        switch_impact = {}
        for ticket in self.active_tickets:
            switch_type = ticket['affected_office']['switch_type']
            if switch_type not in switch_impact:
                switch_impact[switch_type] = 0
            switch_impact[switch_type] += 1

        for switch_type, count in sorted(switch_impact.items(), key=lambda x: x[1], reverse=True):
            overview += f"\n{switch_type:<12} {count} tickets affecting this equipment type"

        # Risk assessment
        high_risk_areas = [state for state, data in state_analysis.items() if data['critical'] > 0 or data['customers'] > 10000]

        overview += f"""

RISK ASSESSMENT
{'=' * 40}
High Risk Areas:          {len(high_risk_areas)} states/territories
Critical Situations:      {len([t for t in self.active_tickets if t['priority'] == 'CRITICAL'])} active
Network Vulnerability:    {'ELEVATED' if len(high_risk_areas) > 3 else 'NORMAL'}

Recommended Actions:
• Monitor high-impact areas closely
• Prepare additional resources for critical regions
• Review network redundancy in affected areas
• Coordinate with regional operations centers"""

        return overview
    def _show_priority_analysis(self) -> str:
        """Show priority analysis and trends for trouble tickets."""
        current_time = self.clock.now().strftime("%B %d, %Y %H:%M EST")

        # Analyze current priorities
        priority_stats = {'CRITICAL': 0, 'MAJOR': 0, 'MINOR': 0}
        for ticket in self.active_tickets:
            priority_stats[ticket['priority']] += 1

        total_tickets = len(self.active_tickets)

        analysis = f"""Trouble Ticket Priority Analysis
Report Generated: {current_time}

CURRENT PRIORITY DISTRIBUTION
{'=' * 40}
Critical Priority:        {priority_stats['CRITICAL']} tickets ({priority_stats['CRITICAL']/max(total_tickets,1)*100:.1f}%)
Major Priority:           {priority_stats['MAJOR']} tickets ({priority_stats['MAJOR']/max(total_tickets,1)*100:.1f}%)
Minor Priority:           {priority_stats['MINOR']} tickets ({priority_stats['MINOR']/max(total_tickets,1)*100:.1f}%)

PRIORITY THRESHOLDS
{'=' * 40}
Critical Threshold:       Service affecting >1000 customers
Major Threshold:          Service affecting >100 customers
Minor Threshold:          Service affecting <100 customers

ESCALATION ANALYSIS
{'=' * 40}"""

        escalated_tickets = [t for t in self.active_tickets if t['escalation_level'] > 1]
        analysis += f"\nEscalated Tickets:        {len(escalated_tickets)} tickets"
        analysis += f"\nEscalation Rate:          {len(escalated_tickets)/max(total_tickets,1)*100:.1f}%"

        # Show escalated tickets
        if escalated_tickets:
            analysis += "\n\nEscalated Ticket Details:"
            for ticket in escalated_tickets:
                age = self.clock.now() - ticket['created_time']
                age_str = f"{int(age.total_seconds() // 3600)}h{int((age.total_seconds() % 3600) // 60)}m"
                analysis += f"\n{ticket['id']:<10} Level {ticket['escalation_level']} {ticket['priority']:<8} {age_str:<6} {ticket['affected_office']['city']}"

        # Performance metrics
        if self.completed_tickets:
            recent_completed = self.completed_tickets[-20:]  # Last 20 completed tickets
            avg_resolution = sum(t.get('actual_duration', 180) for t in recent_completed) / len(recent_completed)

            analysis += f"""

RESOLUTION PERFORMANCE
{'=' * 40}
Average Resolution Time:  {avg_resolution:.0f} minutes
Target Performance:
  Critical (15 min):      {len([t for t in recent_completed if t['priority'] == 'CRITICAL' and t.get('actual_duration', 999) <= 15])}/{len([t for t in recent_completed if t['priority'] == 'CRITICAL'])if recent_completed else 1} on time
  Major (30 min):         {len([t for t in recent_completed if t['priority'] == 'MAJOR' and t.get('actual_duration', 999) <= 30])}/{len([t for t in recent_completed if t['priority'] == 'MAJOR']) if recent_completed else 1} on time
  Minor (60 min):         {len([t for t in recent_completed if t['priority'] == 'MINOR' and t.get('actual_duration', 999) <= 60])}/{len([t for t in recent_completed if t['priority'] == 'MINOR']) if recent_completed else 1} on time"""

        # Trending analysis
        analysis += f"""

TRENDING ANALYSIS
{'=' * 40}
Current Workload:         {'HIGH' if total_tickets > 15 else 'NORMAL' if total_tickets > 8 else 'LOW'}
Critical Trend:           {'INCREASING' if priority_stats['CRITICAL'] > 2 else 'STABLE'}
Network Health:           {'DEGRADED' if priority_stats['CRITICAL'] > 0 else 'GOOD'}

RECOMMENDATIONS
{'=' * 40}"""

        if priority_stats['CRITICAL'] > 2:
            analysis += "\n• IMMEDIATE: Activate emergency response procedures"
            analysis += "\n• Deploy additional technical resources"
            analysis += "\n• Implement network protection measures"
        elif priority_stats['MAJOR'] > 8:
            analysis += "\n• Increase maintenance staffing levels"
            analysis += "\n• Review preventive maintenance schedules"
            analysis += "\n• Monitor for pattern development"
        else:
            analysis += "\n• Continue normal operations monitoring"
            analysis += "\n• Maintain current staffing levels"
            analysis += "\n• Focus on preventive maintenance"

        return analysis
