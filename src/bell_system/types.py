"""
Structural types for the simulation's operational state.

These dictionaries hold mixed value types, so without declarations a type
checker infers ``object`` for every value and rejects the arithmetic and
comparisons performed on them - the single largest category of type errors
in this package. Declaring the shapes documents the state and lets the
checker verify how it is used.

``total=False`` is used where a structure gains keys after construction.
"""

from datetime import datetime
from typing import Any, Dict, List

try:  # pragma: no cover - TypedDict moved to typing in 3.8, Required in 3.11
    from typing import TypedDict
except ImportError:  # pragma: no cover
    from typing_extensions import TypedDict


class TrunkGroup(TypedDict):
    """An inter-office trunk group and its measured load."""

    capacity: int
    utilization: int
    status: str
    route: str
    quality: float


class CrossbarSystem(TypedDict):
    """An electromechanical crossbar switching system."""

    status: str
    load: int
    maintenance_due: bool


class TndsData(TypedDict):
    """Total Network Data System collection and processing state."""

    records_today: int
    processing_status: str
    storage_used: int
    storage_capacity: int
    collection_success: float
    processing_efficiency: float
    data_quality: float
    forecast_accuracy: float
    collection_points: int
    active_streams: int
    last_update: datetime


class TspsData(TypedDict, total=False):
    """
    Traffic Service Position System operator-position state.

    The functions listed are those a TSPS position actually served, per
    Engineering and Operations in the Bell System Table 10-1. Directory
    assistance is deliberately absent: it was a separate operator force
    reached on 411 and NPA-555-1212 and concentrated onto an automatic call
    distributor, never a TSPS position function.
    """

    total_positions: int
    active_positions: int
    occupancy: float
    queue_length: int
    avg_work_time: float
    answer_time: float
    coin: int
    calling_card: int
    collect_calls: int
    third_number: int
    person_to_person: int
    assistance: int
    oni: int
    hotel_motel: int
    international: int
    verification: int
    force_requirement: int
    force_adjustment: str
    service_quality: float
    productivity_rating: str
    system_availability: float
    last_update: datetime


class SystemHealth(TypedDict):
    """Aggregate alarm and availability picture for the office."""

    overall_status: str
    critical_alarms: int
    major_alarms: int
    minor_alarms: int
    uptime_days: int
    last_outage: datetime


class Alarm(TypedDict, total=False):
    """An active alarm condition raised against a monitored system."""

    id: str
    type: str
    severity: str
    system: str
    description: str
    timestamp: datetime
    acknowledged: bool


class TroubleTicket(TypedDict, total=False):
    """
    A trouble ticket and everything recorded against it.

    ``resolution_time`` and ``actual_duration`` are set only once the ticket
    is resolved, so the shape is not total.
    """

    id: str
    category: str
    priority: str
    title: str
    description: str
    # The office record itself, not a name. Anything that displays it must
    # render it; see BellSystemTerminal._office_label.
    affected_office: Dict[str, Any]
    customer_impact: int
    estimated_duration: int
    status: str
    assigned_team: str
    created_time: datetime
    escalation_level: int
    technical_details: str
    required_actions: List[str]
    equipment_involved: List[str]
    geographic_scope: str
    business_impact: Dict[str, Any]
    resolution_steps: List[str]
    resolution_time: datetime
    actual_duration: int


class CentralOffice(TypedDict):
    """A central office derived from NANPA geographic data."""

    npa: str
    nxx: str
    city: str
    state: str
    switch_type: str
    capacity: int
    utilization: int
    trunk_groups: int
    installation_date: str
    maintenance_status: str
    coordinates: Any
    # The COMMON LANGUAGE code assigned when the office is generated.
    clli: str
    switch_name: str
