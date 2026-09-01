"""
The catalogue of things that happen on a shift.

Two hundred lines of event records that used to sit inside
``generate_shift_events`` in screens/shift.py, which is behaviour and had
grown past the thousand-line guard carrying them. These are reference data:
what the building has scheduled, what it is testing, and what the season
does to it, keyed by the hour and the month they belong to.

The events themselves came with the original codebase. They are the
simulation's own: no source consulted by this project fixes what was on a
wire centre's schedule on any particular day, and the ticket numbers,
times and percentages in them are invented. What is grounded is the shape -
that a shift began with a briefing of scheduled work, tests and known
conditions - and that is documented in Engineering and Operations where the
rest of the shift model is.
"""

import random
from typing import Any, Dict, List

Event = Dict[str, Any]


def build(hour: int, month: int) -> List[Event]:
    """
    Return the events on the board for a shift starting at a given hour.

    Base events happen on any shift. The rest are chosen by the hour of the
    tour and the month of the year, two or three equipment events are drawn
    at random, and the whole is sorted by time and capped at eight - which
    is about what a briefing sheet held.

    Args:
        hour: Hour the shift starts, 0-23
        month: Calendar month, 1-12

    Returns:
        Up to eight events, in time order
    """
    current_hour = hour
    current_month = month
    # Base events that occur during any shift with ticket numbers
    base_events = [
        {
            "id": "EV-8001",
            "time": "08:15",
            "type": "SYSTEM",
            "title": "Routine trunk group monitoring TG-023 to TG-067",
            "priority": "LOW",
            "status": "MONITORING",
            "description": "Daily trunk group performance monitoring cycle initiated",
            "details": "All 45 trunk groups showing normal utilization. TG-023 at 67%, TG-045 at 73%, TG-067 at 58%. No blocking events detected.",
            "actions": ["Review hourly reports", "Monitor for threshold violations", "Document performance metrics"]
        },
        {
            "id": "EV-8002",
            "time": "08:30",
            "type": "SYSTEM",
            "title": "UUCP queue processing - 47 files transferred",
            "priority": "LOW",
            "status": "COMPLETE",
            "description": "UNIX-to-UNIX Copy network file transfer cycle",
            "details": "Overnight UUCP queue processed successfully. 47 files transferred between Bell Labs sites. Queue depth now at normal levels.",
            "actions": ["Verify transfer logs", "Check for failed transfers", "Archive completed jobs"]
        },
        {
            "id": "EV-8003",
            "time": "08:45",
            "type": "TEST",
            "title": "Emergency services test call verification completed",
            "priority": "MEDIUM",
            "status": "COMPLETE",
            "description": "Daily test of emergency service routing",
            "details": "All 911 emergency routing paths tested successfully. Average setup time 1.8 seconds, all within specifications.",
            "actions": ["Document test results", "Report to emergency services coordinator", "Schedule next test cycle"]
        }
    ]

    # Time-specific events
    time_events = []
    if 6 <= current_hour < 14:  # Day shift
        time_events = [
            {
                "id": "EV-8010",
                "time": "09:15",
                "type": "MAINTENANCE",
                "title": "5ESS system cutover preparation scheduled 14:30",
                "priority": "HIGH",
                "status": "PENDING",
                "description": "Electronic switching system cutover coordination",
                "details": "5ESS-NYC-002 cutover from test to production. Requires coordination with traffic engineering and field operations.",
                "actions": ["Verify test results", "Coordinate with NOC", "Prepare rollback procedures", "Brief field technicians"]
            },
            {
                "id": "EV-8011",
                "time": "10:00",
                "type": "MEETING",
                "title": "Network planning meeting NP-8301 at 10:00",
                "priority": "MEDIUM",
                "status": "SCHEDULED",
                "description": "Northeast Corridor Expansion Project review",
                "details": "Quarterly review of NP-8301 project milestones. Discussion of capacity requirements and timeline adjustments.",
                "actions": ["Prepare traffic analysis reports", "Review budget status", "Present capacity forecasts"]
            }
        ]
    elif 14 <= current_hour < 22:  # Evening shift
        time_events = [
            {
                "id": "EV-8020",
                "time": "15:30",
                "type": "TRAFFIC",
                "title": "Peak traffic period - all trunk groups monitored",
                "priority": "HIGH",
                "status": "ACTIVE",
                "description": "Daily peak traffic management",
                "details": "Evening calling peak approaching. All trunk groups under enhanced monitoring. TG-023 approaching 85% capacity.",
                "actions": ["Monitor trunk utilization", "Prepare overflow routing", "Coordinate with traffic engineering"]
            },
            {
                "id": "EV-8021",
                "time": "16:00",
                "type": "TRAINING",
                "title": "TSPS operator training session 16:00-17:30",
                "priority": "MEDIUM",
                "status": "SCHEDULED",
                "description": "Traffic Service Position System operator certification",
                "details": "Monthly TSPS operator training on new procedures and emergency protocols.",
                "actions": ["Prepare training materials", "Coordinate with training department", "Document attendance"]
            }
        ]
    else:  # Night shift
        time_events = [
            {
                "id": "EV-8030",
                "time": "02:30",
                "type": "MAINTENANCE",
                "title": "Preventive maintenance window 02:00-05:00",
                "priority": "MEDIUM",
                "status": "ACTIVE",
                "description": "Scheduled overnight maintenance procedures",
                "details": "Crossbar system maintenance at three central offices. Estimated completion 04:30.",
                "actions": ["Monitor maintenance progress", "Coordinate with field teams", "Verify service restoration"]
            }
        ]

    # Equipment-specific events with authentic Bell System issues
    equipment_events = [
        {
            "id": "EV-8040",
            "time": "09:47",
            "type": "ALARM",
            "title": "TH-3 microwave path NYC-WAS fade event detected",
            "priority": "HIGH",
            "status": "MONITORING",
            "description": "Radio path fade margin below threshold",
            "details": "TH-3 path NYC-WAS-001 experiencing atmospheric fade. Current RSL -65 dBm, fade margin reduced to 12 dB. Space diversity activated.",
            "actions": ["Monitor signal levels", "Check weather conditions", "Verify diversity operation", "Prepare backup routing"]
        },
        {
            "id": "EV-8041",
            "time": "11:23",
            "type": "EQUIPMENT",
            "title": "3A Central Control Unit D diagnostic alert",
            "priority": "HIGH",
            "status": "INVESTIGATING",
            "description": "Central control processor requires attention",
            "details": "3A Central Control Unit D reporting memory parity errors. Unit switched to standby. Diagnostic testing in progress.",
            "actions": ["Run comprehensive diagnostics", "Check memory modules", "Coordinate with maintenance", "Monitor standby unit"]
        },
        {
            "id": "EV-8042",
            "time": "13:15",
            "type": "CUSTOMER",
            "title": "Government priority circuit outage - Pentagon line",
            "priority": "CRITICAL",
            "status": "URGENT",
            "description": "High-priority government customer service interruption",
            "details": "Dedicated Pentagon communication line experiencing total outage. Customer class: GOVERNMENT-PRIORITY. Immediate response required.",
            "actions": ["Dispatch emergency team", "Activate backup circuits", "Notify government liaison", "Escalate to Level 3"]
        }
    ]

    # Seasonal events
    seasonal_events = []
    if current_month in [12, 1, 2]:  # Winter
        seasonal_events = [
            {
                "id": "EV-8050",
                "time": "07:30",
                "type": "WEATHER",
                "title": "Ice storm impact on microwave paths",
                "priority": "HIGH",
                "status": "MONITORING",
                "description": "Weather affecting radio propagation",
                "details": "Ice accumulation on microwave antennas in northeast corridor. Multiple paths showing degraded performance.",
                "actions": ["Monitor all radio paths", "Coordinate ice removal crews", "Implement backup routing", "Track weather conditions"]
            }
        ]
    elif current_month in [6, 7, 8]:  # Summer
        seasonal_events = [
            {
                "id": "EV-8060",
                "time": "14:20",
                "type": "WEATHER",
                "title": "Thunderstorm fade analysis for radio paths",
                "priority": "MEDIUM",
                "status": "MONITORING",
                "description": "Summer storm impact assessment",
                "details": "Thunderstorm activity affecting multiple TH-3 paths. Increased fade events expected through evening hours.",
                "actions": ["Monitor fade events", "Verify diversity switching", "Prepare traffic rerouting", "Document performance"]
            }
        ]


    selected_events = base_events.copy()
    selected_events.extend(time_events)
    if equipment_events:
        selected_events.extend(
            random.sample(equipment_events, min(2, len(equipment_events))))
    selected_events.extend(seasonal_events)
    selected_events.sort(key=lambda event: str(event["time"]))
    return selected_events[:8]
