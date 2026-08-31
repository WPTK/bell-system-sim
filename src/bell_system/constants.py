"""
Constants shared between the terminal and its screens.

These lived in ``terminal.py``. When the screens moved into their own modules
they needed the same values, and a constant that two modules import is
clearer than one module reaching into another.
"""

from typing import Dict, FrozenSet, Tuple  # noqa: F401

# Commands that are dispatched and documented but whose operational screens
# are not built yet. Kept here so the terminal can tell the operator honestly
# what is and is not available, and so a test can hold the list accountable.
UNIMPLEMENTED_COMMANDS = frozenset({
    '5ess', 'analysis', 'capacity', 'coer', 'collect', 'custdb', 'dbquery',
    'microwave', 'netdata', 'pic', 'refer', 'provision',
    'pwb', 'rje', 'satellite', 'trace',
    'training', 'western',
})
# Bell System Constants
# A tour of duty. Eight hours is the shift the simulation's events are laid
# out across, and the point at which the wire chief expects to be relieved.
SHIFT_LENGTH_MINUTES = 480
BELL_SYSTEM_ROLES = {
    1: ("sysop", "UNIX Systems Operator"),
    2: ("switch", "Switching Station Technician"),
    3: ("field", "Field Support Liaison"),
    4: ("noc", "National NOC Analyst"),
    5: ("tsps", "Traffic Service Position System Operator"),
    6: ("dba", "Database Administrator"),
    7: ("netplan", "Network Planning Engineer"),
    8: ("custserv", "Customer Service Interface Technician"),
    9: ("radio", "Radio/Microwave Technician"),
    10: ("tnds", "Total Network Data System (TNDS) Analyst"),
    11: ("sarts", "SARTS (Switched Access Remote Test) Technician"),
    12: ("docprep", "Document Preparation Specialist")
}
# Bell System Practices (BSP) Categories
BSP_CATEGORIES = {
    "000": "General Information and Master Indexes",
    "074": "Catalogue Information - Tools",
    "100": "Test Equipment",
    "179": "Signaling and Ringing Circuits",
    "309": "Switched Services Networks",
    "311": "Switched Special Services Systems",
    "460": "Customer Equipment - General Information",
    "620": "Outside Plant - General",
    "660": "Test Center Operation",
    "743": "Supply Ordering and Computer Control",
    "760": "Building Engineering",
    "795": "Common Language",
    "800": "Equipment Design Requirements",
    "801": "Common Systems",
    "900": "Outside Plant Engineering",
}
# Practices cited elsewhere in the simulation, with their subjects.
BSP_PRACTICES = {
    "000-000-001": "Master Alphabetical Index - All Divisions",
    "000-000-005": "Master Numerical Index - All Divisions",
    "309-400-004": "Electronic Tandem Network (ETN) Trouble Reporting",
    "660-000-005": "Alphabetical Index, Divisions 660-669",
    "795-100-100": "Common Language Location Identification (CLLI) Code "
                   "Description, Issue 5, October 1982",
}
# Project Numbering Prefixes
PROJECT_PREFIXES = {
    "NP": "Network Planning",
    "TP": "Technical/Technology",
    "OP": "Operations",
    "AC": "Area Code Implementation",
    "RE": "Route Enhancement",
    "CP": "Capacity Planning"
}
