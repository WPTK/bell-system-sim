"""
Generating trouble tickets and the infrastructure they hit.
"""

import random
from datetime import timedelta
from typing import (
    Any,
    Dict,
    List,
)
from ..types import (
    TroubleTicket,
)


from .session import SessionState


class TicketGeneration(SessionState):
    """
    Generating trouble tickets and the infrastructure they hit.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _initialize_ticket_system(self) -> None:
        """Initialize the Bell System trouble ticket management system."""
        self.ticket_system = {
            "open": {},
            "pending": {},
            "closed": {},
            "escalated": {},
            "priorities": {
                "CRITICAL": {"response_time": 15, "escalation": 30},
                "HIGH": {"response_time": 60, "escalation": 120},
                "MEDIUM": {"response_time": 240, "escalation": 480},
                "LOW": {"response_time": 1440, "escalation": 2880}
            },
            "customer_classes": {
                "GOVERNMENT-PRIORITY": {
                    "escalation_multiplier": 0.5,
                    "priority_boost": 1
                },
                "EMERGENCY-SERVICES": {
                    "escalation_multiplier": 0.25,
                    "priority_boost": 2
                },
                "BUSINESS-CRITICAL": {
                    "escalation_multiplier": 0.75,
                    "priority_boost": 1
                },
                "RESIDENTIAL": {
                    "escalation_multiplier": 1.0,
                    "priority_boost": 0
                }
            }
        }
    def _initialize_enhanced_ticket_system(self) -> None:
        """Initialize comprehensive ticket management system with realistic scenarios."""

        # Enhanced ticket categories with Bell System authenticity
        self.ticket_categories = {
            'NETWORK_OUTAGE': {
                'priority_weights': {'CRITICAL': 0.15, 'MAJOR': 0.35, 'MINOR': 0.50},
                'typical_duration': {'CRITICAL': (30, 240), 'MAJOR': (60, 480), 'MINOR': (120, 720)},
                'customer_impact': {'CRITICAL': (1000, 50000), 'MAJOR': (100, 5000), 'MINOR': (10, 500)}
            },
            'EQUIPMENT_FAILURE': {
                'priority_weights': {'CRITICAL': 0.20, 'MAJOR': 0.45, 'MINOR': 0.35},
                'typical_duration': {'CRITICAL': (45, 180), 'MAJOR': (90, 360), 'MINOR': (180, 600)},
                'customer_impact': {'CRITICAL': (500, 25000), 'MAJOR': (50, 2500), 'MINOR': (5, 250)}
            },
            'SERVICE_INTERRUPTION': {
                'priority_weights': {'CRITICAL': 0.10, 'MAJOR': 0.30, 'MINOR': 0.60},
                'typical_duration': {'CRITICAL': (15, 120), 'MAJOR': (30, 240), 'MINOR': (60, 480)},
                'customer_impact': {'CRITICAL': (100, 10000), 'MAJOR': (25, 1000), 'MINOR': (1, 100)}
            },
            'MAINTENANCE': {
                'priority_weights': {'CRITICAL': 0.05, 'MAJOR': 0.25, 'MINOR': 0.70},
                'typical_duration': {'CRITICAL': (60, 300), 'MAJOR': (120, 480), 'MINOR': (240, 720)},
                'customer_impact': {'CRITICAL': (0, 5000), 'MAJOR': (0, 500), 'MINOR': (0, 50)}
            },
            'TRAFFIC_ANOMALY': {
                'priority_weights': {'CRITICAL': 0.08, 'MAJOR': 0.32, 'MINOR': 0.60},
                'typical_duration': {'CRITICAL': (20, 90), 'MAJOR': (45, 180), 'MINOR': (90, 360)},
                'customer_impact': {'CRITICAL': (1000, 100000), 'MAJOR': (100, 10000), 'MINOR': (10, 1000)}
            }
        }

        # Initialize dynamic ticket generation
        self.active_tickets: List[TroubleTicket] = []
        self.ticket_counter = 4500  # Start from realistic Bell System ticket numbers
        self.completed_tickets = []

        # Generate initial realistic ticket scenarios
        self._generate_initial_tickets()
    def _generate_initial_tickets(self) -> None:
        """Generate initial realistic trouble tickets for the simulation session."""

        # Generate 8-15 initial tickets for authentic operational load
        initial_ticket_count = random.randint(8, 15)

        for _ in range(initial_ticket_count):
            self._create_realistic_ticket()
    def _create_realistic_ticket(self) -> TroubleTicket:
        """Create a realistic trouble ticket with authentic Bell System characteristics."""
        import random

        # Select ticket category and priority
        category = random.choice(list(self.ticket_categories.keys()))
        category_data = self.ticket_categories[category]

        # Determine priority based on realistic weights
        priority_choices = list(category_data['priority_weights'].keys())
        priority_weights = list(category_data['priority_weights'].values())
        priority = random.choices(priority_choices, weights=priority_weights)[0]

        # Generate ticket ID
        self.ticket_counter += random.randint(1, 5)
        ticket_id = f"TK-{self.ticket_counter}"

        # Select affected infrastructure from NANPA data
        affected_office = self._select_affected_infrastructure()

        # Generate realistic scenario based on category
        scenario = self._generate_ticket_scenario(category, priority, affected_office)

        # Calculate realistic duration and impact
        duration_range = category_data['typical_duration'][priority]
        estimated_duration = random.randint(*duration_range)

        impact_range = category_data['customer_impact'][priority]
        customer_impact = random.randint(*impact_range)

        # Create comprehensive ticket
        ticket: TroubleTicket = {
            'id': ticket_id,
            'category': category,
            'priority': priority,
            'title': scenario['title'],
            'description': scenario['description'],
            'affected_office': affected_office,
            'customer_impact': customer_impact,
            'estimated_duration': estimated_duration,
            'status': 'OPEN',
            'assigned_team': scenario['assigned_team'],
            'created_time': self.clock.now() - timedelta(minutes=random.randint(10, 480)),
            'escalation_level': 1,
            'technical_details': scenario['technical_details'],
            'required_actions': scenario['actions'],
            'equipment_involved': scenario.get('equipment', []),
            'geographic_scope': scenario.get('scope', 'LOCAL'),
            'business_impact': self._calculate_business_impact(priority, customer_impact),
            'resolution_steps': []
        }

        self.active_tickets.append(ticket)
        return ticket
    def _select_affected_infrastructure(self) -> Dict[str, Any]:
        """Select realistic affected infrastructure from Bell System network."""

        if self.central_offices:
            office_code = random.choice(list(self.central_offices.keys()))
            return dict(self.central_offices[office_code])
        else:
            # Fallback to major metropolitan areas
            return {
                'npa': '212',
                'nxx': '555',
                'city': 'New York',
                'state': 'NY',
                'switch_type': '4ESS',
                'capacity': 35000,
                'utilization': 78
            }
    def _generate_ticket_scenario(self, category: str, priority: str, office: dict) -> dict:
        """Generate realistic ticket scenario based on category and Bell System operations."""
        import random

        city = office['city']
        state = office['state']
        switch_type = office['switch_type']
        npa = office['npa']

        scenarios = {
            'NETWORK_OUTAGE': {
                'CRITICAL': [
                    {
                        'title': f"Total service outage - {city} central office",
                        'description': f"Complete loss of dial tone affecting {npa} area code in {city}, {state}",
                        'assigned_team': 'Emergency Response Team Alpha',
                        'technical_details': f"Primary {switch_type} switching system failure. All trunk groups down. Backup power systems operational.",
                        'actions': ['Dispatch emergency technicians', 'Activate backup switching', 'Notify major customers', 'Coordinate with NOC'],
                        'equipment': [f'{switch_type}-MAIN', 'POWER-PRIMARY', 'TRUNK-GROUPS'],
                        'scope': 'REGIONAL'
                    },
                    {
                        'title': f"Inter-office trunk failure - {city} to major hubs",
                        'description': f"Loss of all long-distance connectivity from {city} affecting interstate traffic",
                        'assigned_team': 'Network Operations Emergency',
                        'technical_details': "Fiber optic cable cut on Route 80 corridor. Microwave backup circuits at capacity.",
                        'actions': ['Locate cable fault', 'Deploy emergency repair crew', 'Reroute traffic via alternate paths', 'Customer notifications'],
                        'equipment': ['FIBER-MAIN', 'MICROWAVE-BACKUP', 'ROUTING-SYSTEMS'],
                        'scope': 'INTERSTATE'
                    }
                ],
                'MAJOR': [
                    {
                        'title': f"Partial service degradation - {city} {switch_type} switch",
                        'description': f"50% capacity loss on {switch_type} switch affecting {city} area",
                        'assigned_team': 'Switching Maintenance Team',
                        'technical_details': f"Memory module failure in {switch_type} central processing unit. System running on backup processors.",
                        'actions': ['Replace faulty memory modules', 'Run comprehensive diagnostics', 'Monitor system performance', 'Prepare for cutover if needed'],
                        'equipment': [f'{switch_type}-CPU', 'MEMORY-MODULES', 'BACKUP-SYSTEMS'],
                        'scope': 'LOCAL'
                    }
                ],
                'MINOR': [
                    {
                        'title': f"Intermittent service issues - {city} area",
                        'description': f"Sporadic call setup failures reported in {npa} area code",
                        'assigned_team': 'Local Maintenance',
                        'technical_details': "Line interface circuit experiencing intermittent failures. Error rate: 0.3%",
                        'actions': ['Test line interface circuits', 'Monitor error patterns', 'Schedule preventive maintenance'],
                        'equipment': ['LINE-INTERFACE', 'DIAGNOSTIC-SYSTEMS'],
                        'scope': 'LOCAL'
                    }
                ]
            },
            'EQUIPMENT_FAILURE': {
                'CRITICAL': [
                    {
                        'title': f"Primary power system failure - {city} CO",
                        'description': f"Main power feed lost at {city} central office, running on battery backup",
                        'assigned_team': 'Power Systems Emergency',
                        'technical_details': f"Utility power failure affecting {city} CO. Battery backup operational for 8 hours. Generator startup failed.",
                        'actions': ['Repair generator system', 'Monitor battery levels', 'Coordinate with utility company', 'Prepare for emergency shutdown'],
                        'equipment': ['POWER-MAIN', 'GENERATOR', 'BATTERY-BACKUP'],
                        'scope': 'LOCAL'
                    }
                ],
                'MAJOR': [
                    {
                        'title': f"Crossbar switch mechanical failure - {city}",
                        'description': f"Crossbar switching matrix experiencing mechanical binding in {city} office",
                        'assigned_team': 'Electromechanical Repair',
                        'technical_details': "Contact spring tension loss causing call setup failures. Estimated 25% capacity reduction.",
                        'actions': ['Spring tension adjustment', 'Contact cleaning', 'Lubrication service', 'Performance testing'],
                        'equipment': ['CROSSBAR-MATRIX', 'CONTACT-SPRINGS', 'MECHANICAL-SYSTEMS'],
                        'scope': 'LOCAL'
                    }
                ],
                'MINOR': [
                    {
                        'title': f"Trunk interface card failure - {city}",
                        'description': "Single trunk interface card malfunction affecting 24 circuits",
                        'assigned_team': 'Circuit Maintenance',
                        'technical_details': "T1 interface card showing signal level degradation. BER: 10^-4",
                        'actions': ['Replace interface card', 'Test circuit performance', 'Update maintenance records'],
                        'equipment': ['T1-INTERFACE', 'TRUNK-CIRCUITS'],
                        'scope': 'LOCAL'
                    }
                ]
            },
            'SERVICE_INTERRUPTION': {
                'CRITICAL': [
                    {
                        'title': f"Emergency services circuit down - {city}",
                        'description': f"911 emergency services losing connectivity in {city} area",
                        'assigned_team': 'Emergency Services Team',
                        'technical_details': "Dedicated emergency trunk group failure. Backup circuits activated but limited capacity.",
                        'actions': ['Immediate circuit repair', 'Verify backup operations', 'Notify emergency dispatch', 'Monitor call overflow'],
                        'equipment': ['EMERGENCY-TRUNKS', 'BACKUP-CIRCUITS', 'DISPATCH-SYSTEMS'],
                        'scope': 'REGIONAL'
                    }
                ],
                'MAJOR': [
                    {
                        'title': f"Business customer group outage - {city}",
                        'description': f"Major business district losing phone service in {city}",
                        'assigned_team': 'Business Services',
                        'technical_details': "Serving area interface failure affecting 500+ business lines. PBX connections down.",
                        'actions': ['Repair serving area interface', 'Test PBX connections', 'Customer notifications', 'Service verification'],
                        'equipment': ['SAI-EQUIPMENT', 'PBX-INTERFACES', 'BUSINESS-LINES'],
                        'scope': 'LOCAL'
                    }
                ],
                'MINOR': [
                    {
                        'title': f"Residential area intermittent service - {city}",
                        'description': f"Sporadic dial tone issues in residential area of {city}",
                        'assigned_team': 'Residential Services',
                        'technical_details': "Line concentrator showing intermittent failures. Affects approximately 50 customers.",
                        'actions': ['Test line concentrator', 'Check subscriber loops', 'Monitor service quality'],
                        'equipment': ['LINE-CONCENTRATOR', 'SUBSCRIBER-LOOPS'],
                        'scope': 'LOCAL'
                    }
                ]
            }
        }

        if category in scenarios and priority in scenarios[category]:
            return random.choice(scenarios[category][priority])
        else:
            # Generic fallback scenario
            return {
                'title': f"System issue - {city} area",
                'description': f"Technical issue affecting service in {city}, {state}",
                'assigned_team': 'General Maintenance',
                'technical_details': "System requiring investigation and repair",
                'actions': ['Investigate issue', 'Implement repair', 'Test service'],
                'equipment': ['SYSTEM-COMPONENTS'],
                'scope': 'LOCAL'
            }
    def _calculate_business_impact(self, priority: str, customer_count: int) -> dict:
        """Calculate business impact metrics for trouble tickets."""

        # Revenue impact calculations based on 1983 Bell System rates
        avg_revenue_per_customer_hour = random.uniform(0.85, 2.45)  # 1983 rates

        impact = {
            'revenue_loss_hour': int(customer_count * avg_revenue_per_customer_hour),
            'customer_calls_affected': customer_count * random.randint(2, 8),
            'business_severity': priority,
            'regulatory_exposure': priority == 'CRITICAL',
            'media_attention_risk': customer_count > 10000,
            'service_level_impact': {
                'CRITICAL': 'Severe degradation',
                'MAJOR': 'Moderate impact',
                'MINOR': 'Minimal impact'
            }[priority]
        }

        return impact
