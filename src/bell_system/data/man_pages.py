"""
Manual pages for Bell System and UNIX V7 commands.

Held as data rather than embedded in the terminal class, where the literal
made up roughly a fifth of the module. Keyed by command name; each value is
the full man page text as it is rendered by ``man <command>``.
"""

MAN_PAGES = {
    "trunk": """
NAME
     trunk - Bell System trunk group monitoring and management

SYNOPSIS
     trunk [status|detail|test|traffic|maintenance] [trunk-group]

DESCRIPTION
     Monitor and manage Bell System inter-office trunk groups including
     traffic analysis, capacity utilization, and billing coordination.

     Trunk groups connect switching centers and carry inter-office traffic.
     Each trunk group (TG-xxx) has specific capacity and routing characteristics.

OPTIONS
     status          Display summary of all trunk groups (the default)
     detail TG-xxx   Detailed analysis of specific trunk group
     test TG-xxx     Run transmission tests against a trunk group
     traffic TG-xxx  Real-time traffic monitoring
     maintenance     Trunk maintenance schedule

EXAMPLES
     trunk                           Show all trunk groups
     trunk status                    Same as above
     trunk detail TG-001-NYC        Analyze trunk group TG-001-NYC
     trunk traffic TG-023-BOS       Monitor TG-023-BOS traffic

SEE ALSO
     switch(1), traffic(1), routing(1), capacity(1)

BELL SYSTEM PRACTICES
     BSP 400-200-001 - Trunk Group Administration
     BSP 400-200-100 - Traffic Analysis Procedures
""",


    "alarm": """
NAME
     alarm - Central office alarm monitoring and management

SYNOPSIS
     alarm [status|history|acknowledge|test] [alarm-id]

DESCRIPTION
     Monitor and manage central office alarm systems including major, minor,
     and critical alarms. Provides real-time status monitoring and alarm
     acknowledgment capabilities for Bell System equipment.

OPTIONS
     status          Display current active alarms
     history         Show alarm history log
     acknowledge     Acknowledge specific alarm condition
     test            Test alarm system functionality

ALARM CATEGORIES
     CRITICAL        Power failure, system down conditions
     MAJOR           Equipment failure affecting service
     MINOR           Warning conditions, maintenance required

EXAMPLES
     alarm status                    Show all active alarms
     alarm acknowledge ALM-1247      Acknowledge alarm ALM-1247
     alarm history 24                Show 24-hour alarm history

SEE ALSO
     emergency(1), switch(1), testboard(1)

BELL SYSTEM PRACTICES
     BSP 069-100-001 - Central Office Alarm Systems
""",

    "billing": """
NAME
     billing - Customer billing and toll charge management

SYNOPSIS
     billing [summary|customer|dispute|tariff] [parameters]

DESCRIPTION
     Manage customer billing operations including toll charge calculation,
     billing dispute resolution, and tariff rate application. Interfaces
     with Automatic Message Accounting (AMA) and Customer Records Information
     System (CRIS).

OPTIONS
     summary         Daily billing operations summary
     customer NUM    Customer account billing details
     dispute ID      Billing dispute investigation
     tariff          Current tariff rate structures

EXAMPLES
     billing summary                 Daily operations report
     billing customer 2125551234     Account details for customer
     billing dispute BD-4789         Investigate billing dispute

SEE ALSO
     toll(1), collect(1), custdb(1), tariff(1)

BELL SYSTEM PRACTICES
     BSP 230-190-001 - Billing System Operations
     BSP 230-190-100 - AMA Tape Processing
""",

    "crossbar": """
NAME
     crossbar - Crossbar switching system controls

SYNOPSIS
     crossbar [status|test|maintenance|config] [office-code]

DESCRIPTION
     Monitor and control electromechanical crossbar switching systems.
     Crossbar switches use coordinate switching with horizontal and vertical
     bars to establish talking paths through crosspoint contacts.

OPTIONS
     status          Display crossbar office status
     test            Execute crossbar test routines
     maintenance     Crossbar maintenance procedures
     config          System configuration display

TECHNICAL SPECIFICATIONS
     Switching Matrix:       10x20 crosspoint array
     Holding Time:          Average 180 seconds per call
     Traffic Capacity:      36 CCS per crossbar switch
     Seizure Rate:          1200 attempts per hour maximum

EXAMPLES
     crossbar status                 Show all crossbar offices
     crossbar test NYC-XB-01         Test specific crossbar office
     crossbar maintenance            Schedule maintenance window

SEE ALSO
     switch(1), 3a(1), 5ess(1), testboard(1)

BELL SYSTEM PRACTICES
     BSP 200-210-001 - Crossbar System Description
     BSP 200-210-100 - Crossbar Maintenance Procedures
""",

    "emergency": """
NAME
     emergency - Emergency dispatch and escalation system

SYNOPSIS
     emergency [dispatch|escalate|status] [priority] [description]

DESCRIPTION
     Handle emergency situations affecting Bell System operations including
     service outages, equipment failures, and priority restoration procedures.
     Coordinates with field forces and management escalation.

OPTIONS
     dispatch        Create emergency dispatch ticket
     escalate        Escalate existing emergency to management
     status          Show current emergency status

PRIORITY LEVELS
     P1-CRITICAL     Complete service outage affecting >10,000 customers
     P2-MAJOR        Significant service degradation, equipment failure
     P3-MINOR        Localized issues, preventive maintenance

EXAMPLES
     emergency dispatch P1 "Power failure CO-Manhattan-14th"
     emergency escalate EMG-4721 "Escalating trunk failure"
     emergency status                Show all active emergencies

SEE ALSO
     alarm(1), ticket(1), switch(1)

BELL SYSTEM PRACTICES
     BSP 024-100-001 - Emergency Procedures
     BSP 024-100-100 - Service Restoration Priorities
""",

    "tsps": """
NAME
     tsps - Traffic Service Position System operations

SYNOPSIS
     tsps [status|operator|traffic|billing] [position]

DESCRIPTION
     Monitor and manage Traffic Service Position System (TSPS) for operator
     services including person-to-person, collect calls, third-party billing,
     and directory assistance. TSPS provides centralized operator services.

OPTIONS
     status          TSPS system operational status
     operator        Individual operator position monitoring
     traffic         Operator traffic load analysis
     billing         Operator-assisted call billing

PERFORMANCE METRICS
     Answer Time:            95% within 20 seconds
     Average Handle Time:    45 seconds per call
     Positions Active:       Variable based on traffic load
     Peak Traffic:           Mother's Day, Christmas Eve

EXAMPLES
     tsps status                     System operational overview
     tsps operator POS-12            Monitor position 12
     tsps traffic                    Current traffic load

SEE ALSO
     operator(1), directory(1), collect(1), billing(1)

BELL SYSTEM PRACTICES
     BSP 100-255-001 - TSPS System Description
     BSP 100-255-100 - Operator Performance Standards
""",


    "tnds": """
NAME
     tnds - Total Network Data System operations

SYNOPSIS
     tnds [collect|analyze|report] [network-element]

DESCRIPTION
     Total Network Data System (TNDS) provides comprehensive network
     performance monitoring and analysis. Collects traffic data from
     switching systems and transmission facilities for network planning.

OPTIONS
     collect         Initiate data collection from network elements
     analyze         Perform network performance analysis
     report          Generate network utilization reports

DATA SOURCES
     Switching Systems:      Traffic measurements from ESS and crossbar
     Transmission:          Facility utilization and performance data
     Trunking:              Inter-office traffic patterns
     Customer:              Service usage patterns

EXAMPLES
     tnds collect all                Collect from all elements
     tnds analyze NYC-REGION         Analyze regional performance
     tnds report monthly             Generate monthly report

SEE ALSO
     netplan(1), traffic(1), analysis(1), capacity(1)

BELL SYSTEM PRACTICES
     BSP 100-905-001 - TNDS System Description
     BSP 100-905-100 - Data Collection Procedures
""",

    "radio": """
NAME
     radio - TH-3 microwave radio system monitoring

SYNOPSIS
     radio [status|alignment|test|maintenance] [radio-route]

DESCRIPTION
     Monitor and maintain TH-3 microwave radio systems for long-haul
     transmission. TH-3 systems provide 1800 voice channels over microwave
     frequencies in the 4 and 6 GHz bands with digital multiplexing.

OPTIONS
     status          Display radio route operational status
     alignment       Antenna alignment and optimization procedures
     test            RF performance testing and measurements
     maintenance     Scheduled maintenance and inspections

TECHNICAL SPECIFICATIONS
     Frequency Bands:        4 GHz (3700-4200 MHz), 6 GHz (5925-6425 MHz)
     Channel Capacity:       1800 voice channels per radio bearer
     Hop Distance:           25-30 miles typical
     Modulation:            8-PSK digital modulation

EXAMPLES
     radio status                    Show all radio routes
     radio alignment NYC-BOS-R1      Align antennas on route
     radio test CHI-DET-R2           Test RF performance

SEE ALSO
     microwave(1), antenna(1), satellite(1), t1carrier(1)

BELL SYSTEM PRACTICES
     BSP 365-100-001 - TH-3 Radio System Description
     BSP 365-100-100 - Microwave Alignment Procedures
""",

    "t1carrier": """
NAME
     t1carrier - T1 Digital Carrier System operations

SYNOPSIS
     t1carrier [status|test|provision|alarm] [t1-facility]

DESCRIPTION
     Monitor and manage T1 digital carrier systems providing 1.544 Mbps
     digital transmission. T1 systems multiplex 24 voice channels using
     pulse code modulation (PCM) with 8-bit encoding at 8 kHz sampling.

OPTIONS
     status          Display T1 facility operational status
     test            Execute T1 performance testing
     provision       Provision new T1 circuits
     alarm           Monitor T1 alarm conditions

TECHNICAL SPECIFICATIONS
     Bit Rate:               1.544 Mbps (DS1 rate)
     Channel Capacity:       24 voice channels
     Frame Structure:        193 bits per frame (24 channels + framing)
     Encoding:              Bipolar AMI (Alternate Mark Inversion)
     Regenerator Spacing:    6000 feet maximum

EXAMPLES
     t1carrier status                Show all T1 facilities
     t1carrier test T1-NYC-BOS-01    Test specific T1 span
     t1carrier provision CKT-12345   Provision new circuit

SEE ALSO
     multiplex(1), regenerator(1), lcarrier(1), radio(1)

BELL SYSTEM PRACTICES
     BSP 362-100-001 - T1 Carrier System Description
     BSP 362-100-100 - T1 Testing and Maintenance
""",

    "lcarrier": """
NAME
     lcarrier - L-Carrier coaxial cable system operations

SYNOPSIS
     lcarrier [status|test|maintenance|amplifier] [l-system]

DESCRIPTION
     Monitor and manage L-Carrier coaxial cable transmission systems.
     L1, L3, L4, and L5 systems provide high-capacity analog transmission
     over coaxial cable with intermediate amplifiers.

OPTIONS
     status          Display L-Carrier system operational status
     test            Execute system performance testing
     maintenance     Amplifier and repeater maintenance
     amplifier       Individual amplifier monitoring

SYSTEM TYPES
     L1 System:             600 voice channels, 3 MHz bandwidth
     L3 System:             1860 voice channels, 8 MHz bandwidth
     L4 System:             3600 voice channels, 17 MHz bandwidth
     L5 System:             10,800 voice channels, 57 MHz bandwidth

EXAMPLES
     lcarrier status                 Show all L-Carrier systems
     lcarrier test L4-NYC-CHI        Test L4 system performance
     lcarrier amplifier AMP-147      Monitor specific amplifier

SEE ALSO
     t1carrier(1), multiplex(1), radio(1)

BELL SYSTEM PRACTICES
     BSP 361-100-001 - L-Carrier System Description
     BSP 361-100-100 - Coaxial Cable Maintenance
""",

    "ps": """
NAME
     ps - display process status

SYNOPSIS
     ps [options]

DESCRIPTION
     Display information about currently running processes on the Bell System
     UNIX workstation including system daemons, switching processes, and
     user sessions.

OPTIONS
     (no options)    Display processes for current terminal
     -a              Display processes for all terminals
     -u              Display user-oriented format
     -x              Display processes without controlling terminal

EXAMPLES
     ps                              Show current terminal processes
     ps -aux                         Show all processes with details

PROCESS TYPES
     System Daemons:                 init, cron, switching monitors
     Bell System Processes:          TSPS, AMA, billing systems
     User Sessions:                  Terminal sessions and applications

SEE ALSO
     who(1), jobs(1), kill(1)

UNIX V7 PROGRAMMER'S MANUAL
     ps(1) - January 1979
""",

    "who": """
NAME
     who - display logged-in users

SYNOPSIS
     who [options] [file]

DESCRIPTION
     Display information about users currently logged into the Bell System
     UNIX workstation including login time, terminal, and location.

OPTIONS
     (no options)    Display current users
     am i            Display information about current user only

EXAMPLES
     who                             Show all logged-in users
     who am i                        Show current user information

OUTPUT FORMAT
     username    terminal    login-time    location

SEE ALSO
     ps(1), users(1), last(1)

UNIX V7 PROGRAMMER'S MANUAL
     who(1) - January 1979
""",

    "man": """
NAME
     man - display manual pages

SYNOPSIS
     man [section] command
     man -k keyword

DESCRIPTION
     Display manual pages for Bell System commands and UNIX utilities.
     Manual pages provide comprehensive documentation including syntax,
     options, examples, and cross-references.

OPTIONS
     command         Display manual page for specified command
     -k keyword      Search manual pages for keyword
     section command Display page from specific manual section

MANUAL SECTIONS
     1               User commands and Bell System operations
     2               System calls and kernel interfaces
     3               Library functions and subroutines

EXAMPLES
     man trunk                       Display trunk command manual
     man 1 ps                        Display ps command from section 1
     man -k traffic                  Search for traffic-related commands

SEE ALSO
     help(1), bsp(1), apropos(1)

UNIX V7 PROGRAMMER'S MANUAL
     man(1) - January 1979
""",

    "ticket": """
NAME
     ticket - Bell System trouble ticket management

SYNOPSIS
     ticket [create|status|update|close] [ticket-id] [description]

DESCRIPTION
     Manage Bell System trouble tickets for customer complaints, equipment
     failures, and service issues. Provides complete ticket lifecycle
     management with priority assignment and resolution tracking.

OPTIONS
     create          Create new trouble ticket
     status          Display ticket status and details
     update          Update existing ticket with progress notes
     close           Close resolved ticket with resolution code

PRIORITY CODES
     P1-EMERGENCY    Service affecting, immediate response required
     P2-URGENT       Service degraded, respond within 4 hours
     P3-ROUTINE      Non-service affecting, respond within 24 hours

EXAMPLES
     ticket create P1 "No dial tone 212-555-1234"
     ticket status TKT-19830315-001
     ticket update TKT-19830315-001 "Dispatched technician"
     ticket close TKT-19830315-001 "Cable pair replaced"

SEE ALSO
     emergency(1), testboard(1), sarts(1)

BELL SYSTEM PRACTICES
     BSP 100-105-001 - Trouble Ticket Procedures
""",

    "traffic": """
NAME
     traffic - Network traffic analysis and monitoring

SYNOPSIS
     traffic [current|forecast|report] [region|timeframe]

DESCRIPTION
     Analyze and monitor Bell System network traffic patterns including
     call volumes, busy hour traffic, and capacity utilization. Provides
     data for network planning and capacity management.

OPTIONS
     current         Display real-time traffic status
     forecast        Traffic projections and growth analysis
     report          Generate traffic utilization reports

TRAFFIC MEASUREMENTS
     CCS (Centi-Call-Seconds):      Traffic intensity measurement
     BHCA (Busy Hour Call Attempts): Peak hour call volume
     Peg Count:                     Call attempt measurements
     Overflow:                      Blocked call statistics

EXAMPLES
     traffic current                 Real-time network status
     traffic forecast monthly        Monthly growth projections
     traffic report NYC-REGION       Regional traffic analysis

SEE ALSO
     capacity(1), routing(1), tnds(1), netplan(1)

BELL SYSTEM PRACTICES
     BSP 100-701-001 - Traffic Engineering Procedures
""",

    "status": """
NAME
     status - Bell System operational status overview

SYNOPSIS
     status [system|network|alarms|performance]

DESCRIPTION
     Display comprehensive operational status of Bell System equipment,
     network facilities, and service performance. Provides real-time
     monitoring dashboard for operations personnel.

OPTIONS
     system          System-wide equipment status
     network         Network facility status
     alarms          Active alarm summary
     performance     Service performance metrics

STATUS INDICATORS
     NORMAL          All systems operational
     WARNING         Minor issues, monitoring required
     CRITICAL        Service affecting conditions

EXAMPLES
     status                          Full operational overview
     status alarms                   Active alarm summary
     status performance              Service quality metrics

SEE ALSO
     alarm(1), test(1), emergency(1)

BELL SYSTEM PRACTICES
     BSP 100-000-001 - Operations Procedures
""",

    "test": """
NAME
     test - Bell System equipment testing interface

SYNOPSIS
     test [equipment-type] [test-type] [parameters]

DESCRIPTION
     Execute comprehensive testing procedures for Bell System equipment
     including switching systems, transmission facilities, and customer
     services. Provides automated and manual testing capabilities.

OPTIONS
     switching       Test switching equipment and call processing
     transmission    Test transmission facilities and circuits
     customer        Test customer services and line conditions

TEST CATEGORIES
     ROUTINE         Scheduled preventive testing
     DIAGNOSTIC      Fault isolation and troubleshooting
     ACCEPTANCE      New equipment acceptance testing
     PERFORMANCE     Service quality verification

EXAMPLES
     test switching NYC-5ESS-01      Test 5ESS switch
     test transmission T1-NYC-BOS    Test T1 facility
     test customer 212-555-1234      Test customer line

SEE ALSO
     testboard(1), sarts(1), alarm(1)

BELL SYSTEM PRACTICES
     BSP 100-200-001 - Testing Procedures
""",

    "bsp": """
NAME
     bsp - Bell System Practices reference system

SYNOPSIS
     bsp [search|view|index] [topic|bsp-number]

DESCRIPTION
     Access Bell System Practices (BSP) documentation providing standard
     operating procedures, technical specifications, and maintenance
     instructions for all Bell System equipment and operations.

OPTIONS
     search          Search BSP database by keyword
     view            Display specific BSP document
     index           Browse BSP index by category

BSP CATEGORIES
     000-099         General Information and Procedures
     100-199         Switching Systems and Operations
     200-299         Electronic Switching Systems
     300-399         Transmission Systems
     400-499         Outside Plant and Cable Systems

EXAMPLES
     bsp search "trunk testing"      Search for trunk procedures
     bsp view BSP-200-100-001        View specific BSP document
     bsp index switching             Browse switching procedures

SEE ALSO
     man(1), help(1), training(1)

BELL SYSTEM DOCUMENTATION
     BSP Master Index - Updated Quarterly
""",


    "antenna": """
NAME
     antenna - Microwave antenna and tower equipment management

SYNOPSIS
     antenna [alignment|status|maintenance|weather] [tower-id]

DESCRIPTION
     Monitor and maintain microwave antenna systems and tower equipment
     for Bell System radio transmission facilities. Includes antenna
     alignment, weather monitoring, and obstruction analysis.

OPTIONS
     alignment       Execute antenna alignment procedures
     status          Display antenna and tower status
     maintenance     Tower and antenna maintenance scheduling
     weather         Weather impact monitoring and alerts

TECHNICAL SPECIFICATIONS
     Antenna Types:          Parabolic reflectors, horn antennas
     Frequency Bands:        4 GHz, 6 GHz, 11 GHz, 18 GHz
     Beam Width:            1-3 degrees typical
     Gain:                  35-45 dB typical

EXAMPLES
     antenna status TWR-NYC-001      Check tower status
     antenna alignment NYC-BOS-R1    Align radio path antennas
     antenna weather                 Check weather conditions

SEE ALSO
     radio(1), microwave(1), satellite(1)

BELL SYSTEM PRACTICES
     BSP 365-200-001 - Antenna Systems Maintenance
""",



    "multiplex": """
NAME
     multiplex - Digital multiplexing operations and hierarchy

SYNOPSIS
     multiplex [hierarchy|combine|separate|monitor] [level|signal]

DESCRIPTION
     Manage digital multiplexing hierarchy for combining multiple voice
     and data channels into higher-capacity transmission facilities.
     Supports Bell System digital hierarchy from DS0 to DS4 levels.

OPTIONS
     hierarchy       Display digital signal hierarchy
     combine         Multiplex lower-level signals
     separate        Demultiplex higher-level signals
     monitor         Monitor multiplexer performance

DIGITAL HIERARCHY
     DS0:            64 kbps - Single voice channel
     DS1:            1.544 Mbps - 24 voice channels (T1)
     DS2:            6.312 Mbps - 96 voice channels
     DS3:            44.736 Mbps - 672 voice channels (T3)
     DS4:            274.176 Mbps - 4032 voice channels

EXAMPLES
     multiplex hierarchy             Show signal levels
     multiplex combine DS1-TO-DS2    Combine T1 signals
     multiplex monitor MUX-NYC-001   Monitor multiplexer

SEE ALSO
     t1carrier(1), regenerator(1), lcarrier(1)

BELL SYSTEM PRACTICES
     BSP 362-200-001 - Digital Multiplexing Systems
""",

    "regenerator": """
NAME
     regenerator - Digital signal regenerator management

SYNOPSIS
     regenerator [status|test|alignment|performance] [regen-id]

DESCRIPTION
     Monitor and maintain digital signal regenerators for T1 carrier
     systems. Regenerators restore digital pulse timing and amplitude
     at regular intervals along transmission facilities.

OPTIONS
     status          Display regenerator operational status
     test            Execute regenerator performance tests
     alignment       Timing and threshold adjustments
     performance     Monitor regenerator performance metrics

TECHNICAL PARAMETERS
     Span Length:            6000 feet maximum (T1)
     Input Sensitivity:      -36 dBm minimum
     Jitter Tolerance:       ±132 nanoseconds
     Bit Error Rate:         <10^-6 operational limit

EXAMPLES
     regenerator status              Show all regenerators
     regenerator test REG-001        Test specific regenerator
     regenerator alignment T1-SPAN-5 Align regenerator timing

SEE ALSO
     t1carrier(1), multiplex(1), testboard(1)

BELL SYSTEM PRACTICES
     BSP 362-150-001 - T1 Regenerator Maintenance
""",

    "operator": """
NAME
     operator - TSPS operator services and performance monitoring

SYNOPSIS
     operator [performance|training|assistance|billing] [position-id]

DESCRIPTION
     Monitor Traffic Service Position System (TSPS) operator performance
     including call handling statistics, training programs, and service
     quality metrics for person-to-person and operator-assisted calls.

OPTIONS
     performance     Operator performance statistics and metrics
     training        Training program status and schedules
     assistance      Directory assistance call monitoring
     billing         Operator-assisted billing verification

PERFORMANCE STANDARDS
     Answer Time:            95% answered within 20 seconds
     Average Work Time:      45 seconds per call maximum
     Abandonment Rate:       <5% target
     Service Observing:      Regular quality monitoring

EXAMPLES
     operator performance            Show performance summary
     operator training POS-012       Check training status
     operator assistance             Directory assistance stats

SEE ALSO
     tsps(1), directory(1), collect(1), billing(1)

BELL SYSTEM PRACTICES
     BSP 100-255-200 - Operator Performance Standards
""",

    "directory": """
NAME
     directory - Directory assistance services and number lookup

SYNOPSIS
     directory [lookup|statistics|database] [name|number|city]

DESCRIPTION
     Provide directory assistance services including telephone number
     lookup, customer information verification, and directory database
     maintenance for Bell System customer records.

OPTIONS
     lookup          Search directory for customer information
     statistics      Directory assistance call statistics
     database        Directory database maintenance operations

DIRECTORY TYPES
     LOCAL           Local telephone directory information
     NATIONAL        National directory assistance network
     BUSINESS        Business and commercial listings
     GOVERNMENT      Government and emergency services

EXAMPLES
     directory lookup "John Smith" NYC    Find customer number
     directory statistics                 Call volume statistics
     directory database update            Update directory records

SEE ALSO
     operator(1), tsps(1), custdb(1)

BELL SYSTEM PRACTICES
     BSP 100-260-001 - Directory Assistance Procedures
""",




    "netplan": """
NAME
     netplan - Network planning and infrastructure development

SYNOPSIS
     netplan [design|analysis|forecast|implementation] [project-id]

DESCRIPTION
     Comprehensive network planning for Bell System infrastructure including
     switching center placement, transmission facility routing, and capacity
     expansion to meet projected demand and service requirements.

OPTIONS
     design          Network design and topology planning
     analysis        Network performance and efficiency analysis
     forecast        Long-term demand and growth forecasting
     implementation  Implementation planning and scheduling

PLANNING PHASES
     DEMAND FORECASTING:     Traffic growth and service projections
     NETWORK DESIGN:         Topology and facility planning
     ECONOMIC ANALYSIS:      Cost-benefit and investment analysis
     IMPLEMENTATION:         Deployment planning and scheduling

EXAMPLES
     netplan design NYC-EXPANSION       Design network expansion
     netplan analysis NORTHEAST         Analyze regional network
     netplan forecast 5-year            Long-term planning

SEE ALSO
     capacity(1), traffic(1), tnds(1), routing(1)

BELL SYSTEM PRACTICES
     BSP 100-900-001 - Network Planning Procedures
""",



    "service": """
NAME
     service - Service order management and provisioning

SYNOPSIS
     service [order|install|repair|disconnect] [service-order]

DESCRIPTION
     Manage Bell System service orders including new service installation,
     service changes, repair coordination, and service disconnection
     through centralized service order processing systems.

OPTIONS
     order           Create and process new service orders
     install         Coordinate service installation activities
     repair          Schedule and track repair activities
     disconnect      Process service disconnection orders

SERVICE TYPES
     NEW SERVICE:            Initial telephone service installation
     SERVICE CHANGES:        Moves, additions, modifications
     REPAIR SERVICES:        Trouble resolution and maintenance
     DISCONNECTION:          Service termination processing

EXAMPLES
     service order new 212-555-1234      Create new service order
     service install SO-19830315-001     Track installation
     service repair TKT-4789             Coordinate repair

SEE ALSO
     provision(1), custdb(1), ticket(1), billing(1)

BELL SYSTEM PRACTICES
     BSP 100-600-001 - Service Order Procedures
""",





    "date": """
NAME
     date - display or set system date

SYNOPSIS
     date [yymmddhhmm[.ss]]

DESCRIPTION
     Display current date and time on the Bell System UNIX workstation.
     With argument, set system date and time (requires superuser privileges).
     Used for timestamping Bell System operational logs and records.

FORMAT
     Day Mon dd hh:mm:ss TimeZone yyyy

EXAMPLES
     date                            Display current date and time
     date 8303151430                 Set date to Mar 15, 1983 2:30 PM

BELL SYSTEM USAGE
     System time synchronization across Bell System facilities is critical
     for accurate billing records, traffic measurements, and operational logs.

SEE ALSO
     who(1), ps(1)

UNIX V7 PROGRAMMER'S MANUAL
     date(1) - January 1979
""",

    "pwd": """
NAME
     pwd - print working directory

SYNOPSIS
     pwd

DESCRIPTION
     Print the pathname of the current working directory on the Bell System
     UNIX workstation. Essential for navigation within Bell System file
     structures and operational directories.

EXAMPLES
     pwd                             Show current directory path

BELL SYSTEM DIRECTORIES
     /usr/bell                       Bell System operations files
     /usr/bell/logs                  Operational logs and records
     /usr/bell/data                  Network data and statistics

SEE ALSO
     ls(1), cd(1)

UNIX V7 PROGRAMMER'S MANUAL
     pwd(1) - January 1979
""",

    "df": """
NAME
     df - display filesystem disk space usage

SYNOPSIS
     df [filesystem...]

DESCRIPTION
     Display disk space usage for Bell System UNIX filesystems including
     available space, used space, and capacity information critical for
     maintaining operational logs and data storage.

OUTPUT FORMAT
     Filesystem      Blocks    Used    Available   Capacity   Mounted on

EXAMPLES
     df                              Show all filesystem usage
     df /usr                         Show /usr filesystem usage

BELL SYSTEM USAGE
     Monitor disk usage for operational logs, billing records, traffic data,
     and customer databases to ensure adequate storage for operations.

SEE ALSO
     du(1), ls(1)

UNIX V7 PROGRAMMER'S MANUAL
     df(1) - January 1979
""",

    "clear": """
NAME
     clear - clear terminal screen

SYNOPSIS
     clear

DESCRIPTION
     Clear the terminal screen on Bell System UNIX workstation, providing
     a clean display for operational activities. Commonly used during
     shift changes and when switching between different operational tasks.

EXAMPLES
     clear                           Clear the terminal screen

BELL SYSTEM USAGE
     Used frequently during Bell System operations to maintain clean
     terminal displays for monitoring activities and operational procedures.

SEE ALSO
     reset(1), tput(1)

TERMINAL CONTROL
     Sends clear screen escape sequence to terminal
""",

    "quit": """
NAME
     quit - exit Bell System terminal session

SYNOPSIS
     quit

DESCRIPTION
     Properly terminate Bell System UNIX terminal session with session
     cleanup, command history saving, and operational log finalization.
     Ensures proper logout procedures for Bell System operations.

EXAMPLES
     quit                            Exit terminal session
     exit                            Alternative exit command

BELL SYSTEM PROCEDURES
     Session termination includes:
     - Command history preservation
     - Operational log finalization
     - Session activity recording
     - Proper logout authentication

SEE ALSO
     login(1), logout(1)

BELL SYSTEM OPERATIONS
     Always use proper logout procedures for security and audit compliance
""",





    "events": """
NAME
     events - Bell System operational events and shift activity

SYNOPSIS
     events [current|history|generate|summary] [timeframe]

DESCRIPTION
     Monitor and manage Bell System operational events including
     equipment status changes, maintenance activities, service
     impacts, and shift handoff information for operational awareness.

OPTIONS
     current         Display current active events
     history         Show historical events and activities
     generate        Generate shift briefing events
     summary         Provide event summary and statistics

EVENT CATEGORIES
     EQUIPMENT EVENTS:       Status changes and equipment alerts
     MAINTENANCE EVENTS:     Scheduled and emergency maintenance
     SERVICE EVENTS:         Service impacts and customer issues
     OPERATIONAL EVENTS:     Shift activities and procedures

EXAMPLES
     events current                  Show current events
     events history 24               Show 24-hour event history
     events summary shift            Shift event summary

SEE ALSO
     handoff(1), alarm(1), status(1)

BELL SYSTEM PRACTICES
     BSP 100-050-001 - Event Management Procedures
""",

    "handoff": """
NAME
     handoff - shift turnover record, and signing off a tour

SYNOPSIS
     handoff
     handoff relieve

DESCRIPTION
     An office worked around the clock, so a tour ended by handing the
     board to whoever was relieving you and telling them what was on it.
     With no argument this prints that record: what came in from the
     previous shift, what is pending now, what is past commitment, what
     has not been measured, and which alarms are still unacknowledged.

     'handoff relieve' signs off. Anything still pending is carried
     forward, because it was: a report past its commitment at midnight is
     still past its commitment in the morning.

SIGNING OFF
     Relieving prints three sentences on the tour before it prints the
     tally - what went well, what did not, and the one thing worth doing
     differently. They are written from the tour's own numbers rather than
     scored, and only ever one thing is named, because a list of four
     things to improve is a list nobody acts on.

     Then the index for the tour is banked, the shift count advances, and
     a fresh board opens with the carried reports still on it. Banked
     figures accumulate on the craft record, which draws them as a trend
     once there are three tours behind you.

THE LAST TOUR
     A career walks the calendar four days at a time, so the thirteenth
     tour falls on 31 December 1983 and there is no fourteenth. Signing
     off that one closes the career rather than opening a board: the whole
     record, every tour of the index drawn as a trend, and the wire chief.
     It happens once. The board stays on the machine afterwards, because
     the machine did not stop on the first of January either.

SEE ALSO
     report(1), qual(1), events(1)

BELL SYSTEM PRACTICES
     BSP 010-100-000 - Shift Turnover Procedures, cited by the turnover
     checklist this command prints. The practice number is the one the
     simulation shows on that checklist; it is not independently verified
     against a bundled document.
""",

    "tariff": """
NAME
     tariff - Bell System tariff and rate structure information

SYNOPSIS
     tariff [rates|schedule|calculate|verify] [service-type]

DESCRIPTION
     Access Bell System tariff information including rate schedules,
     service charges, billing calculations, and regulatory rate
     structures for various telecommunications services.

OPTIONS
     rates           Display current rate schedules
     schedule        Show tariff filing schedules
     calculate       Calculate service charges
     verify          Verify billing rate applications

TARIFF CATEGORIES
     LOCAL SERVICE:          Basic exchange service rates
     TOLL SERVICE:           Long distance service charges
     SPECIAL SERVICES:       Private line and data service rates
     EQUIPMENT RENTAL:       Terminal equipment charges

EXAMPLES
     tariff rates local              Local service rate schedule
     tariff calculate toll-call      Calculate toll charges
     tariff verify billing-dispute   Verify rate application

SEE ALSO
     billing(1), toll(1), service(1)

BELL SYSTEM PRACTICES
     BSP 230-300-001 - Tariff Administration
""",


    "errors": """
NAME
     errors - Display recent error summary and troubleshooting

SYNOPSIS
     errors [summary|detail|clear] [count]

DESCRIPTION
     Display recent command errors with troubleshooting suggestions
     and resolution guidance. Part of the enhanced Bell System
     terminal user experience for improved operational efficiency.

OPTIONS
     summary         Show error summary with counts
     detail          Display detailed error information
     clear           Clear error history

ERROR CATEGORIES
     COMMAND ERRORS:         Invalid commands or syntax
     SYSTEM ERRORS:          System or equipment failures
     ACCESS ERRORS:          Permission or authentication issues
     DATA ERRORS:           Data format or validation problems

EXAMPLES
     errors                          Show recent error summary
     errors detail 10                Show last 10 errors in detail
     errors clear                    Clear error history

SEE ALSO
     help(1), verbosity(1), history(1)

ENHANCED TERMINAL FEATURES
     Part of Bell System UX enhancement package
""",

    "verbosity": """
NAME
     verbosity - Control logging detail level

SYNOPSIS
     verbosity [DEBUG|INFO|WARNING|ERROR|CRITICAL]

DESCRIPTION
     Dynamically control the logging verbosity level for Bell System
     terminal operations. Higher levels provide more detailed
     information for troubleshooting and system analysis.

LOGGING LEVELS
     DEBUG:                  Detailed diagnostic information
     INFO:                   General operational information
     WARNING:               Warning conditions and alerts
     ERROR:                 Error conditions requiring attention
     CRITICAL:              Critical system conditions

EXAMPLES
     verbosity                       Show current logging level
     verbosity DEBUG                 Enable debug logging
     verbosity ERROR                 Show only errors and critical

SEE ALSO
     errors(1), help(1), history(1)

ENHANCED TERMINAL FEATURES
     Part of Bell System UX enhancement package
""",

    "history": """
NAME
     history - Display command history with filtering

SYNOPSIS
     history [count] [pattern]

DESCRIPTION
     Display Bell System terminal command history with optional
     filtering and count limits. Provides command usage statistics
     and session activity tracking for operational review.

OPTIONS
     count           Number of recent commands to display
     pattern         Filter commands matching pattern

HISTORY FEATURES
     COMMAND TRACKING:       Complete command execution history
     USAGE STATISTICS:       Command frequency and patterns
     SESSION ANALYSIS:       Activity tracking and review
     NAVIGATION:            Up/down arrow command recall

EXAMPLES
     history                         Show recent command history
     history 50                      Show last 50 commands
     history trunk                   Show commands containing 'trunk'

SEE ALSO
     errors(1), verbosity(1), help(1)

ENHANCED TERMINAL FEATURES
     Part of Bell System UX enhancement package with readline support
""",









    "uucp": """
NAME
     uucp - UNIX to UNIX copy and communication

SYNOPSIS
     uucp [options] source destination

DESCRIPTION
     Transfer files and execute commands between Bell System UNIX
     workstations over dial-up or dedicated communication lines.
     Essential for Bell System inter-office data exchange.

COMMUNICATION FEATURES
     FILE TRANSFER:          Reliable file copying between systems
     REMOTE EXECUTION:       Execute commands on remote systems
     MAIL DELIVERY:          Electronic mail between Bell offices
     NEWS DISTRIBUTION:      Technical bulletins and announcements

EXAMPLES
     uucp report.txt chicago!~/reports/  Copy file to Chicago office
     uucp chicago!status.log local_file  Copy from remote system
     uumail user@boston "Meeting tomorrow" Send mail to Boston

SEE ALSO
     mail(1), cu(1), tip(1)

UNIX V7 PROGRAMMER'S MANUAL
     uucp(1) - January 1979
""",

    "switch": """
NAME
     switch - Bell System central office switching system control

SYNOPSIS
     switch [status|detail|test|traffic|maintenance] [office-code]

DESCRIPTION
     Monitor and control central office switching equipment across the
     Bell System network, covering electromechanical and electronic
     switching systems.

     Each central office is identified by its NPA-NXX office code and
     carries a switch type indicating its generation of equipment.

OPTIONS
     status          Display switching system summary
     detail CODE     Detailed status for a specific office
     test CODE       Run switching diagnostics on an office
     traffic CODE    Current call processing load
     maintenance     Offices with maintenance activity in progress

EXAMPLES
     switch status                   Show all switching systems
     switch detail 212-555          Analyze office 212-555
     switch test 212-555            Run diagnostics on 212-555

SEE ALSO
     trunk(1), crossbar(1), 5ess(1), testboard(1)

BELL SYSTEM PRACTICES
     BSP 231-090-000 - Central Office Maintenance
     BSP 231-318-000 - Switching System Administration
""",

    "trouble": """
NAME
     trouble - Bell System trouble ticket administration

SYNOPSIS
     trouble [list|detail|assign|update|escalate|resolve|create|
              geographic|priority] [arguments]

DESCRIPTION
     Administer trouble tickets covering network outages, equipment
     failures, service interruptions, maintenance activity and traffic
     anomalies.

     Each ticket carries a priority of CRITICAL, MAJOR or MINOR, an
     affected office, an estimated repair duration and a running record
     of every action taken against it.

     Invoked with no arguments, trouble displays the dashboard summarising
     open tickets, customers affected and revenue impact.

OPTIONS
     list [priority]      List tickets, optionally filtered by priority
     detail ID            Full ticket record including action history
     assign ID TEAM       Assign a ticket to a repair team
     update ID STATUS     Change ticket status
     escalate ID          Raise escalation level and notify management
     resolve ID           Close a ticket and record resolution
     create CAT PRI DESC  Open a ticket from craft-reported trouble
     geographic           Ticket distribution by region
     priority             Priority breakdown and trend analysis

EXAMPLES
     trouble                              Show the dashboard
     trouble list CRITICAL                List critical tickets only
     trouble detail TK-4021               Inspect ticket TK-4021
     trouble assign TK-4021 Cable Repair  Assign to the cable team
     trouble create CABLE_TROUBLE MAJOR Water in Elm St manhole

SEE ALSO
     ticket(1), testboard(1), lmos(1), alarm(1)

BELL SYSTEM PRACTICES
     BSP 660-100-000 - Trouble Reporting and Analysis
     BSP 660-210-000 - Repair Service Administration
""",

    "3a": """
NAME
     3a - 3A Central Control processor status and diagnostics

SYNOPSIS
     3a [status|diagnostics|memory|peripherals]

DESCRIPTION
     Report on the 3A Central Control processor used in Bell System
     electronic switching and operations support equipment.

     The 3A processor provides duplex operation with automatic fault
     detection and switchover between active and standby units.

OPTIONS
     status          Processor state, duplex configuration and uptime
     diagnostics     Fault detection and diagnostic history
     memory          Store utilisation and parity status
     peripherals     Attached peripheral equipment status

EXAMPLES
     3a status                       Current processor state
     3a diagnostics                  Review diagnostic history

SEE ALSO
     5ess(1), switch(1), alarm(1)

BELL SYSTEM PRACTICES
     BSP 254-280-000 - 3A Processor Maintenance
""",

    "help": """
NAME
     help - list available Bell System terminal commands

SYNOPSIS
     help

DESCRIPTION
     Display the commands available in the current session, grouped by
     operational area. Commands relevant to the selected role are listed
     first.

     For detailed documentation on any individual command, use man(1).

EXAMPLES
     help                            List available commands
     man trunk                       Detailed help for trunk

SEE ALSO
     man(1), status(1)
""",

    "set": """
NAME
     set - display and change simulation settings

SYNOPSIS
     set
     set <setting>
     set <setting> <value>
     set reset [<setting>]

DESCRIPTION
     Display the simulation settings screen, or change one setting.

     The simulation runs period-accurate by default. Where a historically
     accurate behaviour is less playable on a modern terminal, that choice
     is offered here rather than decided for you. Settings whose value
     departs from 1978-1983 behaviour are marked on the settings screen.

     Settings persist between sessions in the state directory named by
     BELL_SYSTEM_HOME.

SETTINGS
     date.source         simulated | real
                         simulated runs the 1983 shift clock, which advances
                         in real time from the configured epoch. real reports
                         the host system clock.

     date.epoch          YYYY-MM-DD
                         Date on which the simulated shift begins. The shift
                         starts at 08:00. Default 1983-11-14, a Monday.

     date.format         v7 | iso | us
                         v7 is UNIX date(1) order, as a Seventh Edition
                         system printed it. iso is YYYY-MM-DD. us is
                         MM-DD-YYYY.

     date.clock          24 | 12
                         24-hour was standard in Bell System operational
                         records.

     date.seconds        on | off
                         Whether timestamps carry seconds.

     display.charset     ascii | unicode
                         ascii restricts output to printable 7-bit ASCII, as
                         period terminals required. unicode permits block and
                         box-drawing glyphs on a modern terminal.

     display.prompt      v7 | verbose
                         v7 is the bare Bourne shell prompt. verbose adds
                         user, host and working directory.

     display.log_console off | on
                         Whether diagnostic log records print to the terminal.
                         They always reach the log file.

EXAMPLES
     set                          Show the settings screen
     set date.format              Explain one setting
     set date.format iso          Display dates as YYYY-MM-DD
     set date.clock 12            Use a 12-hour clock
     set date.source real         Show the real date instead of 1983
     set display.charset unicode  Permit block glyphs on a modern terminal
     set reset                    Restore period-accurate defaults

     display.pacing  Print output at a terminal speed: 110 for a Model 33,
                     300 for the Model 43 this position has, 1200 for a
                     later CRT, or off. A teleprinter printed one character
                     at a time and you watched it happen. Ctrl-C stops a
                     listing, as it did then. A pipe is never paced.

SEE ALSO
     date(1), status(1), verbosity(1)
""",

    "dialtone": """
NAME
     dialtone - call progress tones and dial tone speed testing

SYNOPSIS
     dialtone
     dialtone test [office]
     dialtone tone <name>
     dialtone mf <digits>

DESCRIPTION
     Display the Bell System call progress tones, run a dial tone speed
     test, or show the multifrequency train an office outpulses for a
     called number.

     Tone frequencies follow the Precise Tone Plan, which standardised
     call progress tones on exact frequency pairs. Before it, tones were
     derived from ringing generator harmonics and varied between offices.

TONES
     dial        350 + 440 Hz, continuous
     busy        480 + 620 Hz, 60 interruptions per minute
     reorder     480 + 620 Hz, 120 IPM - all trunks busy, or fast busy
     ringback    440 + 480 Hz, 2 seconds on, 4 seconds off
     congestion  480 + 620 Hz, 120 IPM under network management control
     howler      1400 + 2060 + 2450 + 2600 Hz, receiver left off hook
     highandwet  200 + 400 Hz, vacant code intercept

SIGNALING
     Multifrequency pulsing carries called digits between offices on six
     frequencies - 700, 900, 1100, 1300, 1500 and 1700 Hz - two sounded
     at a time. A train opens with KP and closes with ST. This is not the
     same as Touch-Tone, which a subscriber set produces on a different
     set of frequencies entirely.

     Single frequency supervision uses 2600 Hz on analogue toll trunks.
     Tone present means the trunk is idle.

EXAMPLES
     dialtone                     Show all call progress tones
     dialtone tone busy           Detail for the busy tone
     dialtone test 212-555        Dial tone speed test on an office
     dialtone mf 2125551212       MF train for a called number

SEE ALSO
     testboard(1), trunk(1), switch(1)

BELL SYSTEM PRACTICES
     BSP 660-100-000 - Transmission Maintenance
""",

    "routing": """
NAME
     routing - hierarchical alternate routing analysis

SYNOPSIS
     routing [status]
     routing trace <from-office> <to-office>
     routing chain <office>

DESCRIPTION
     Examine how the toll network routes a call, and follow one through.

     The rule is to complete each connection at the lowest level of the
     hierarchy that can carry it, using the fewest trunks in tandem. A
     call is offered first to a high-usage group - a direct route
     engineered to overflow - and only when every trunk there is busy
     does it climb its homing chain on final groups.

     Final groups are the last route available. When every trunk in one
     is busy the call is blocked and the caller receives reorder.

     Note the distinction between topology and use: a direct trunk group
     is not necessarily a high-usage group. Direct and tandem describe how
     groups are connected; high-usage and final describe how traffic is
     offered to them, and the two are engineered differently.

GRADE OF SERVICE
     Final groups        P.01 - one call in a hundred finds all trunks
                         busy in the busy hour
     High-usage groups   P.10 - overflow is their purpose

     Grade of service is engineered per group, not end to end, so a
     connection crossing several groups blocks more often than any one
     of them does.

CONNECTION LENGTH
     A minimum toll connection is three trunks: up a toll connecting
     trunk from the originating end office, across one intertoll group,
     and back down at the far end. The average was slightly over three.
     No connection could use more than nine trunks in tandem.

     Some end offices had end office toll trunks that bypassed the toll
     centre entirely, and those are tried first where they exist.

EXAMPLES
     routing                            Show the routing table
     routing trace EO-BOS-01 EO-CHI-01  Follow a Boston to Chicago call
     routing chain EO-CHI-01            Show an office's homing chain

SEE ALSO
     trunk(1), tnds(1), switch(1), dialtone(1)
""",

    "clli": """
NAME
     clli - COMMON LANGUAGE location identification codes

SYNOPSIS
     clli
     clli decode <code>
     clli office <npanxx>
     clli examples

DESCRIPTION
     Decode and look up COMMON LANGUAGE location identifiers. Every
     location in the Bell System carries one, and every record that
     refers to a place refers to it by that code.

STRUCTURE
     A code is eleven characters in four segments:

       1-4    Geographical    place, town or locality    alphabetic
       5-6    Geopolitical    state, province, country   alphabetic
       7-8    Network site    building within the place  alphanumeric
       9-11   Network entity  equipment or work centre   alphanumeric

     The first eight characters identify a building; all eleven identify
     a particular machine or entity within it. Records that need only the
     building carry the eight character form.

ENTITY CODES
     MG0-MG9   Marker group, crossbar
     SG0-SG9   Step group, step-by-step
     CG0-CG9   Control group, stored program electronic switching
     DS0       Digital switch, 1982 and later
     nnT       Toll or tandem switching entity
     nnB       Board - operator and switchboard positions

     The letters I, O, U, W and Y are not used in entity codes.

ADMINISTRATION
     COMMON LANGUAGE is AT&T Co Standard, published in the Bell System
     Practices Division 795. The governing practice is BSP 795-100-100,
     Common Language Location Identification (CLLI) Code Description,
     Issue 5, October 1982.

EXAMPLES
     clli decode CHCGILCL57T    Break down the first No. 4 ESS code
     clli office 212555         Show an office's record by code
     clli examples              Codes of offices known to have existed

SEE ALSO
     switch(1), trunk(1), routing(1), cosmos(1)

BELL SYSTEM PRACTICES
     BSP 795-100-100 - CLLI Code Description
""",

    "cosmos": """
NAME
     cosmos - wire centre administration and main frame operations

SYNOPSIS
     cosmos [status]
     cosmos assign <number>
     cosmos jumper <number>
     cosmos balance
     cosmos pending

DESCRIPTION
     Computer System for Main Frame Operations. The main frame is the
     main distributing frame - the manually operated field of
     terminations where outside plant cable meets central office
     equipment - and not a mainframe computer.

     COSMOS exists to minimise congestion and long cross-connects on the
     frame while keeping load balanced across the switching equipment in
     the wire centre. It holds the line and number inventory, assigns
     office equipment and frame appearances, and prints the frame work
     orders a frame technician works from.

THE FRAME
     The vertical side carries outside plant cable terminations through
     protector units; the horizontal side carries office equipment
     terminations. A jumper run between them cross-connects a customer's
     pair to their line equipment. Preferential assignment places that
     jumper as short as possible, because a frame full of long jumpers
     becomes congested and hard to work.

     Setting a protector unit to its inactive position disconnects a
     customer temporarily without disturbing the cross-connection.

OPTIONS
     status            Frame occupancy, jumper administration, balance
     assign <number>   Assign office equipment and a frame appearance
     jumper <number>   Show the cross-connect record for a line
     balance           Load balance across the line link groups
     pending           Frame work orders awaiting the frame technician

NOTES
     COSMOS transaction syntax is not reproduced from any source
     available to this simulation. The commands here are its own.

SEE ALSO
     clli(1), switch(1), trouble(1)
""",
    "report": """
NAME
     report - work the repair service bureau's board of customer trouble
     reports

SYNOPSIS
     report [board]
     report next
     report show <number>
     report callback <number>
     report dispatch <number> <force>
     report close <number> <5|8> [fault]
     report closed | faults | forces

DESCRIPTION
     A customer trouble report arrives with nothing but the customer's own
     words. What is actually on the pair is not known until it is measured,
     and locating the trouble is described in Engineering and Operations in
     the Bell System as the most difficult and time consuming step of
     corrective maintenance. That is the work this command is for.

     The sequence is detect, notify, verify, locate, repair, verify. The
     bureau has done the first two by the time a report reaches your board.
     The rest is yours.

OPTIONS
     board             The pending list, nearest commitment first
     next              The one report that most wants working, and what it
                       wants. The same decision the standing prompt makes
     show <n>          The line record, the symptom and everything done so far
     callback <n>      Telephone the customer for more than the card carries
     dispatch <n> <f>  Send a repair force. The wrong force costs time
     close <n> 5 <c>   Trouble found. Name the condition you found
     close <n> 8       No trouble found
     closed            What has been closed this session, and how it was judged
     faults            The trouble conditions and what each measures like
     forces            The repair forces a report may be dispatched to

DISPOSITION CODES
     Two codes are used, and both are published Bell System dispositions
     counted separately in the network switching performance measurement
     plan:

     5    Trouble found. A fault was located and corrected.
     8    No trouble found. The report is closed without a repair.

     Closing a faulty line as code 8 does not fail loudly. It closes, and
     then the customer calls back. That repeat is what the measurement plan
     was counting.

REFERRING TO A REPORT
     A report answers to its number (TR-04471), to the telephone number on
     it, or to its position on the board (1, 2, 3).

AS FILES
     The board is also a directory. /usr/lmos holds one file per report
     with the whole record on it, alongside three that are always there:

     board       The pending list, one line to a report
     closed      What has been closed this session, and how it was judged
     cable       The wet sections, the pairs they have taken, and the
                 weather that is making them worse

     So the second way to work is the shell:

          grep WRONG /usr/lmos/closed
          cat /usr/lmos/TR-04471
          ls /usr/lmos | wc -l

     Your mail is a file too, under /usr/spool/mail, and the practices are
     under /usr/bsp.

TIME
     Every action is charged against the report's commitment: a measurement
     costs four minutes, a call back eight, a repair as long as that repair
     takes, and a trip by the wrong force forty-five. The commitment
     intervals and these costs are the simulation's own; no bundled source
     states the Bell System's actual commitment policy.

SEE ALSO
     mlt(1), testboard(1), testline(1), qual(1), trouble(1)
""",
    "mlt": """
NAME
     mlt - mechanised loop testing

SYNOPSIS
     mlt <report number | telephone number>

DESCRIPTION
     Measure a subscriber loop from the test desk and report the readings.
     Two different measurements are reported and they must not be confused.

     Insulation resistance is taken with the loop open and the office
     battery removed. It is high on a healthy pair - hundreds of thousands
     of ohms or more - and low wherever a fault is bridging something. Tip
     to ring, tip to ground and ring to ground are each read separately,
     because which one is low is what tells you what the fault is.

     Loop resistance is the resistance of the pair itself with the loop
     closed. It is the number the 1300-ohm design limit applies to, and an
     open pair has none to read.

     Capacitance is the third reading and the most useful one. Local
     exchange cable runs 0.083 microfarads to the mile, so a capacitance
     measurement on an open pair is a distance to the break.

READING THE RESULT
     Infinite tip to ring, no station termination      open
     Near zero tip to ring                             short
     One conductor low to ground, tip to ring normal   ground
     Foreign potential with no battery applied         foreign EMF
     Several pairs low in one cable                    wet cable
     Everything within limits, loop closed, current    receiver off hook
     Loop clean to the frame, customer still cut off   office equipment

DESIGN LIMITS
     Loops of 18 kft or less were designed to 1300 ohms maximum and
     nonloaded. Loops between 18 and 24 kft were designed to 1500 ohms with
     H88 loading. Anything longer went on digital loop carrier. A coin
     station needs 23 milliamperes to operate, which puts its own range
     limit at the same 1300 ohms, about three miles.

DIFFICULTY
     On the forgiving setting the system names the condition it reads. On
     the other one it prints the numbers and nothing else, because reading
     them is the job.

NOTES
     The abbreviation table in Engineering and Operations expands MLT as
     "mechanical loop testing". The system was more widely called Mechanized
     Loop Testing. The conflict is recorded here rather than resolved.

SEE ALSO
     report(1), testboard(1), testline(1)
""",
    "testline": """
NAME
     testline - reach a test line or responder and read the result

SYNOPSIS
     testline
     testline <code>
     testline <code> <circuit>

DESCRIPTION
     Transmission testing is done against equipment at the far end of the
     circuit that answers automatically. The Bell System Technical Journal
     for April 1982 names the series:

     102-type   Far-end test line for a one-way loss measurement
     100-type   Far-end test line for one-way loss and noise
     105-type   Responder giving two-way loss, noise, noise with tone and
                gain slope
     Balance    Connects the balance termination so office balance can be
                measured
     ROTL       Remote office test line. Seizes a trunk from the far office
                under command and connects it to a 52A responder

     Every loss reading is taken at 1004 Hz, because that is the frequency
     the Bell System stated its loss objectives at. A reading at any other
     frequency is not measuring what the objective is written against.

CAROT
     Centralized Automatic Reporting On Trunks drives the remote office test
     line with multifrequency signalling and routines trunk groups without
     anybody asking it to. Its exceptions print to the maintenance teletype.
     The processor controlled interrogator works the same equipment from the
     local office or a switching control centre when CAROT is not involved.

NOTES
     The access codes shown are the simulation's own. Real test line access
     codes were local to each office and carried in office records, not in
     any national list.

SEE ALSO
     testboard(1), trunk(1), mlt(1)
""",
    "shift": """
NAME
     shift - where you are in the tour

SYNOPSIS
     shift

DESCRIPTION
     The four numbers you want in the middle of a tour, on one screen:
     how far in you are and how much is left, what is on the board and how
     much of it is past commitment or has never been measured, what you
     have closed so far and how it went, and which crews are out and when
     they are due back.

     handoff(1) is the full turnover record and it is a page and a half,
     because it is for handing the board to the person relieving you.
     This is for the middle of the shift.

     The date and the days remaining are on it because a career walks the
     calendar: tours are four days apart, from the fourteenth of November
     to the last working day of the Bell System.

RESUMING
     A tour survives the session being closed. The board, the weather, the
     cable, where every crew is standing and how much of every commitment
     has been spent are written down after every command and picked back
     up next time. Signing off with 'handoff relieve' ends the tour and
     throws the saved one away, because it is finished.

SEE ALSO
     handoff(1), report(1), qual(1)
""",

    "hint": """
NAME
     hint - ask somebody, and ask again if that was not enough

SYNOPSIS
     hint

DESCRIPTION
     Somewhere between the board and the manual there is a gap a manual
     cannot close, which is not knowing what to do next. This is for
     that. It looks at what is actually in front of you and puts somebody
     on write(1) about it.

     Ask again and you get more. There are three levels to any situation
     and they come out one at a time: Vasquez on the testboard gives you
     a nudge, then you are sent to read something that exists on this
     machine, then Halloran tells you outright and is short about it,
     because by then you have asked three times.

     The level starts over whenever the situation changes, so moving on
     to a different problem starts you at the beginning of that one
     rather than at the end of the last.

COST
     One minute of the shift, on top of the minute any command at this
     terminal costs. Nothing else. Asking does not count against the
     service index and it is not kept on the craft record: being stuck is
     already the penalty, and a hint that costs more than that is a hint
     nobody uses.

SEE ALSO
     help(1), report(1), qual(1), man(1)
""",

    "qual": """
NAME
     qual - craft record, qualifications and service index

SYNOPSIS
     qual
     qual index

DESCRIPTION
     What a craftsperson was allowed to work on was governed by
     qualification, not by seniority or by asking nicely. This command shows
     which sign-offs you hold, which you are working toward, and how the
     work you have done is scoring.

     The position you were assigned to carries its own sign-off. Everything
     beyond that desk is earned a correctly closed report at a time.

QUALIFICATIONS
     Loop and Station              report, mlt, trouble, testboard, testline
     Main Distributing Frame       cosmos, lmos
     Central Office Switching      switch, alarm, crossbar, 3a
     Switching Control Center      sarts, orderwire
     Interoffice Trunks            trunk, routing, dialtone
     Toll Network                  toll, tnds, traffic

SERVICE INDEX
     Scored against the weights published in the network switching
     performance measurement plan for No. 1 and No. 1A ESS offices. Those
     weights sum to 100 and customer reports carry ten of them, which is the
     component scored here. 'qual index' prints the whole weighting.

     A report closed as no trouble found on a line that really was faulty
     counts twice against you: once as a wrong disposition and again when
     the customer calls back.

     Once there are three tours behind you the record draws the last five
     index figures as a bar, because a column of decimals does not show a
     trend and getting better is the point.

DIFFICULTY
     set game.difficulty fun      Fun Simulation. Close without measuring,
                                  advance quickly, a wrong call costs little
     set game.difficulty craft    I Hate Myself. Measure before you close,
                                  repeats come back on your index,
                                  commitments count, qualification is slow

SEE ALSO
     report(1), set(1), handoff(1)
""",
    "write": """
NAME
     write - write to another user

SYNOPSIS
     write <user> [message]

DESCRIPTION
     Write copies lines from your terminal to that of another user. The
     Seventh Edition form is followed: the recipient sees a banner naming
     the sender and the terminal it came from, and EOT ends the message.

     The other craft on this system are working too, and they answer.

USERS
     rjohnson    Switching Equipment Technician, central office
     mreyes      Repair Service Attendant, repair service bureau
     dpetrak     SCC Maintenance Administrator, switching control centre
     lokafor     Cable Splicer, in the field
     gvasquez    Testboard Technician, test centre
     ehalloran   Wire Chief, central office
     tnakamura   Transmission Engineer, transmission centre
     carot       Not a person. Prints to you; does not read

SEE ALSO
     who(1), mail(1), orderwire(1)
""",
    "mail": """
NAME
     mail - read mail left by the other craft

SYNOPSIS
     mail

DESCRIPTION
     Mail reaches you whether you are at the terminal or not, which is what
     it is for. Reading it empties the mailbox, as mail(1) does.

     Qualification sign-offs from the wire chief arrive here, along with
     whatever the transmission engineer and the switching control centre
     want on the record rather than shouted across the room.

     This terminal takes mail; it does not originate it. Use write(1) to
     reach somebody now.

SEE ALSO
     write(1), who(1), qual(1)
""",
    "orderwire": """
NAME
     orderwire - the maintenance order wire

SYNOPSIS
     orderwire
     orderwire scc
     orderwire report <text>

DESCRIPTION
     The order wire is the maintenance circuit between an office, the field
     and the switching control centre. In the plant it was voice; here it is
     the words that went over it.

     Field forces call in on it, the control centre raises the office on it,
     and transmission announces its routines on it so a craftsperson does
     not chase a trunk that is only being tested.

OPTIONS
     (none)            The last traffic on the wire
     scc               Raise the switching control centre
     report <text>     Call something in and have it logged against the
                       office

QUALIFICATION
     Working the order wire requires the Switching Control Center sign-off.
     Traffic on the wire reaches you before then; speaking on it does not.

SEE ALSO
     write(1), qual(1), sarts(1)
""",
    "testboard": """
NAME
     testboard - central office test board

SYNOPSIS
     testboard
     testboard loop <report>
     testboard supervision <circuit>
     testboard results

DESCRIPTION
     The board is where the three testing systems meet. Loop measurement
     goes through mechanised loop testing, transmission goes through the
     test line series, and supervision is what single frequency signalling
     shows about a trunk.

OPTIONS
     loop <report>          Measure a subscriber loop. Same as mlt(1)
     supervision <circuit>  Single frequency supervision state of a trunk
     results                Every measurement taken this session
     status                 Board status and what is on it

SUPERVISION
     Single frequency signalling puts 2600 Hz on a trunk while it is idle
     and removes it when the trunk is seized. That makes the tone a
     supervisory signal a craftsperson reads directly:

     Tone on, trunk idle                normal
     Tone off, trunk seized             normal
     Tone on far end only               far end released, near end has not
     Tone present during a connection   irregularity. Report it and hold the
                                        circuit out of service

     Routine testing of these groups is run by CAROT, which reports its
     exceptions to the maintenance teletype whether anybody is reading or
     not.

SEE ALSO
     mlt(1), testline(1), report(1), trunk(1)
""",
    "testcall": """
NAME
     testcall - place a test call through the network

SYNOPSIS
     testcall
     testcall <from> <to>
     testcall <from> <to> <test line>

DESCRIPTION
     A test call is how a trunk is proved. The originating office seizes it,
     outpulses the address, the network advances the call through the
     hierarchy, and something at the far end answers so the connection can
     be measured. Every stage leaves a signal a craftsperson can read.

STAGES
     Seizure          Single frequency signalling puts 2600 Hz on an idle
                      trunk. Seizing it removes the tone toward the far end,
                      which is what the far end is watching for.

     Start signal     The far end says when its register is ready. Wink
                      start winks off-hook and back; delay dial holds
                      off-hook until the register frees; immediate start
                      does neither and relies on a fixed interval.

     Address          Outpulsed in multifrequency, bracketed by KP to open
                      the register and ST to release it. The talking path is
                      muted while an office outpulses, which is why MF needs
                      no protection against the human voice and Touch-Tone
                      does.

     Route advance    Each group is offered in turn. A call goes to a
                      high-usage group first and overflows up its homing
                      chain to a final group. When every trunk in a final
                      group is busy the call is blocked and the caller gets
                      reorder.

     Answer           Answer supervision comes back and the tone is off in
                      both directions.

     Release          The tone is restored and the trunk returns to idle.

MEASUREMENT
     Name a test line as the third argument and the call terminates on it,
     so the connection itself is measured rather than merely completed. Loss
     accumulates on every trunk in tandem, so a call that took five is
     measurably worse than one that took three.

     A circuit outside its working limits should not go back in service.

NOTES
     Test numbers and test line access codes here are the simulation's own.
     Real ones were carried in office records, office by office, not in any
     national list. Which start arrangement a trunk group used was an office
     record too; the choice here is deterministic on the office code so a
     group answers the same way every time it is tested.

QUALIFICATION
     Requires the Interoffice Trunks sign-off.

SEE ALSO
     testline(1), testboard(1), routing(1), dialtone(1), trunk(1)
""",
    "lmos": """
NAME
     lmos - Loop Maintenance Operations System

SYNOPSIS
     lmos [status]
     lmos line <telephone number>
     lmos reports | chronic | utilisation
     lmos treat [coin|force]

DESCRIPTION
     LMOS is a component of an Automated Repair Service Bureau. It
     mechanises the bureau's customer line card records by holding them in
     computer memory, and produces management reports from them. Its
     functions are customer trouble report processing, control of mechanised
     testing, analysis of past trouble reports through TREAT, and equipment
     utilisation reporting. One installation held up to five million
     customer line records.

     The bureau it belongs to has three stated objectives: improve efficiency
     and reduce the cost of repair operations, reduce the time required to
     detect, locate and repair troubles, and improve the handling of customer
     contacts by repair service attendants.

OPTIONS
     status            Line records held, reports in process, testing
     line <number>     One customer line card record and its trouble history
     reports           Trouble reports the bureau has in process
     chronic           Lines carrying three or more reports
     treat             Trouble report evaluation and analysis
     treat coin        Coin telephone operation
     treat force       Repair force administration
     utilisation       Equipment utilisation report

TESTING
     Three test systems worked with the bureau. The line status verifier and
     automated line verification equipment both had limited capability.
     Mechanised loop testing "provides mechanization of essentially all ARSB
     test functions", which is why mlt(1) is the command you will actually
     spend the shift in.

NOTES
     The chronic-line threshold of three reports is this simulation's own. No
     source available to it states the Bell System's own figure.

QUALIFICATION
     Requires the Main Distributing Frame sign-off.

     lmos cable      Group the pending board by cable and binder group.
                     Water is a sheath fault: several reports in one
                     twenty-five-pair binder group is what it looks like,
                     and one splicer trip repairs all of them.

SEE ALSO
     report(1), mlt(1), cosmos(1), qual(1)
""",
    "sarts": """
NAME
     sarts - Switched Access Remote Test System

SYNOPSIS
     sarts [status]
     sarts list | trouble | access | categories
     sarts circuit <circuit id>
     sarts test <circuit id>

DESCRIPTION
     Special services are everything that is not ordinary service. Ordinary
     service is residence, public telephone, mobile and basic
     individual-line business service; all the rest require special
     treatment as to transmission, signalling, switching, billing or
     customer use, and are used mostly by business customers. There were
     about twenty-five major categories.

     SARTS reaches those circuits without anybody driving anywhere. The
     Switched Maintenance Access System, through the use of relays, provides
     concentrated metallic access to individual circuits to permit that
     remote access and testing. In the digital environment, digital access
     and cross-connect test access serves the same purpose as jack or SMAS
     arrangements.

     A circuit on manual jack access cannot be reached from this position.
     That is the whole point of the distinction, and the command will say so
     rather than pretending otherwise.

OPTIONS
     status            Inventory, troubles, and what is reachable
     list              Every circuit on this position
     trouble           Circuits reported in trouble
     circuit <id>      One circuit's record
     test <id>         Reach a circuit and measure it
     access            The access arrangements and what each means
     categories        What counts as a special service

MEASUREMENT
     A four-wire circuit is measured on a 105-type responder, which returns
     two-way loss, noise, noise with tone and gain slope. A two-wire circuit
     gets the 100-type far-end test line: one-way loss and noise. Both are
     read at 1004 Hz.

     A circuit that measures clean is returned to service. One outside its
     working limits is held, because a special service out of limits should
     not go back to the customer.

NOTES
     Circuit identifiers here follow a plausible shape rather than the
     COMMON LANGUAGE circuit identification format, which no document
     available to this project sets out in full. Per-category circuit counts
     and trouble rates are this simulation's own. Seven of the nine service
     categories are attested by name in the bundled documents; 'sarts
     categories' marks which.

QUALIFICATION
     Requires the Switching Control Center sign-off.

SEE ALSO
     testline(1), testboard(1), testcall(1), trunk(1)
""",
    "toll": """
NAME
     toll - the toll network

SYNOPSIS
     toll
     toll hierarchy
     toll load

DESCRIPTION
     The toll network consists of the class 4 and higher offices. Class 5 is
     the end office, where subscriber loops terminate, and is not part of
     it. This command shows the network as the routing engine holds it: how
     many offices sit at each class, what homes on what, and how the trunk
     groups between them are loaded.

     Each office is joined to one of higher class by a final group and is
     said to home on it. A call is completed at the lowest level of the
     hierarchy that can carry it, using the fewest trunks in tandem, which
     is why a typical toll connection takes three: up a toll connecting
     trunk, across one intertoll group, and back down.

OPTIONS
     (none)            Offices by class, and trunking summary
     hierarchy         The homing chain, class by class
     load              Trunk group occupancy

GRADE OF SERVICE
     Final trunk groups are engineered to P.01 - one call in a hundred finds
     all trunks busy. High-usage groups are engineered to P.10, because
     overflowing is what they are for.

QUALIFICATION
     Requires the Toll Network sign-off.

SEE ALSO
     routing(1), testcall(1), trunk(1), traffic(1), tnds(1)
""",
    "cd": """
NAME
     cd - change working directory

SYNOPSIS
     cd [directory]

DESCRIPTION
     Change the working directory. With no argument, change to the home
     directory of the position you are logged in as.

     Relative paths, "." and ".." all work, and "~" means your home
     directory.

SEE ALSO
     ls(1), pwd(1)
""",
    "ls": """
NAME
     ls - list contents of directory

SYNOPSIS
     ls [-la] [name ...]

DESCRIPTION
     List the contents of each directory named. With no argument, list the
     working directory.

OPTIONS
     -l   Long form: mode, links, owner, group, size, date and name
     -a   Include entries beginning with a dot

SEE ALSO
     cd(1), cat(1), file(1)
""",
    "cat": """
NAME
     cat - concatenate and print

SYNOPSIS
     cat file ...

DESCRIPTION
     Read each file in turn and write it out. With no file, read standard
     input, so cat is useful at the head of a pipeline.

     Worth reading on this machine:

     /etc/motd                 What the company wants you to know
     /usr/doc/divestiture      What happens on 1 January 1984
     /usr/doc/bulletin         This week's operations bulletin
     /usr/users/sysop/notes    Left by whoever had the position before you
     /usr/lmos/board           The trouble reports, one to a line
     /usr/adm/shiftlog         What you have closed this shift
     /usr/adm/messages         What the machine has been doing

SEE ALSO
     more(1), head(1), tail(1), grep(1)
""",
    "more": """
NAME
     more - print a file a screenful at a time

SYNOPSIS
     more file ...

DESCRIPTION
     Print a file, stopping after a screenful. The terminal this runs in
     scrolls on its own, so more(1) here prints one screen and says how much
     is left rather than waiting for a keystroke.

SEE ALSO
     cat(1), head(1)
""",
    "head": """
NAME
     head - print the first few lines

SYNOPSIS
     head [-count] [file ...]

DESCRIPTION
     Print the first lines of each file, ten by default. With no file, read
     standard input.

SEE ALSO
     tail(1), cat(1)
""",
    "tail": """
NAME
     tail - print the last few lines

SYNOPSIS
     tail [-count] [file ...]

DESCRIPTION
     Print the last lines of each file, ten by default. With no file, read
     standard input.

     Useful on /usr/adm/messages and /usr/adm/shiftlog, which both grow.

SEE ALSO
     head(1), cat(1)
""",
    "grep": """
NAME
     grep - search a file for a pattern

SYNOPSIS
     grep [-cinv] pattern [file ...]

DESCRIPTION
     Print the lines of each file that contain the pattern. With no file,
     read standard input, which is how grep is most often used.

OPTIONS
     -i   Ignore case
     -n   Number the lines
     -v   Print the lines that do NOT match
     -c   Print a count instead of the lines

EXAMPLES
     grep 1FR /usr/lmos/board            Residence lines on the board
     cat /usr/lmos/board | grep PEND     Reports not yet worked
     grep -c . /usr/lmos/board           How many lines that is
     who | grep -v carot                 Everybody who is a person

SEE ALSO
     cat(1), wc(1), sort(1)
""",
    "wc": """
NAME
     wc - count lines, words and characters

SYNOPSIS
     wc [-lwc] [file ...]

DESCRIPTION
     Count lines, words and characters in each file, printing them in that
     order. With no file, read standard input.

OPTIONS
     -l   Lines only
     -w   Words only
     -c   Characters only

EXAMPLES
     who | wc -l                     How many people are logged on
     cat /usr/lmos/board | wc -l     How deep the board is

SEE ALSO
     grep(1), sort(1)
""",
    "sort": """
NAME
     sort - sort lines

SYNOPSIS
     sort [-ru] [file ...]

DESCRIPTION
     Sort the lines of each file. With no file, read standard input.

OPTIONS
     -r   Reverse the order
     -u   Discard duplicate lines

SEE ALSO
     uniq(1), grep(1), wc(1)
""",
    "uniq": """
NAME
     uniq - report repeated lines

SYNOPSIS
     uniq [-c] [file ...]

DESCRIPTION
     Drop adjacent repeated lines. Usually used after sort(1), because it
     only looks at neighbours.

OPTIONS
     -c   Prefix each line with the number of times it occurred

SEE ALSO
     sort(1)
""",
    "echo": """
NAME
     echo - write its arguments

SYNOPSIS
     echo [argument ...]

DESCRIPTION
     Write the arguments, separated by blanks. Chiefly useful at the head of
     a pipeline or for seeing what the shell did with a line.

SEE ALSO
     cat(1)
""",
    "file": """
NAME
     file - determine file type

SYNOPSIS
     file name ...

DESCRIPTION
     Say what kind of thing each argument is: a directory, ascii text, C
     program text, or a special file.

SEE ALSO
     ls(1), cat(1)
""",
    "cal": """
NAME
     cal - print a calendar

SYNOPSIS
     cal [month [year]]

DESCRIPTION
     Print a calendar for the month, defaulting to the month the shift is
     in. With a year as well, print that month of that year.

     cal 12 1983 is worth a look.

SEE ALSO
     date(1)
""",
    "cp": """
NAME
     cp - copy a file

SYNOPSIS
     cp source target

DESCRIPTION
     Copy the source file to the target. If the target is a directory,
     the copy is made inside it under the same name.

SEE ALSO
     mv(1), rm(1)
""",
    "mv": """
NAME
     mv - move or rename a file

SYNOPSIS
     mv source target

DESCRIPTION
     Rename the source, or move it into the target directory.

SEE ALSO
     cp(1), rm(1)
""",
    "rm": """
NAME
     rm - remove files

SYNOPSIS
     rm [-r] file ...

DESCRIPTION
     Remove each file. A directory needs -r, which removes everything
     under it as well and does not ask twice.

SEE ALSO
     rmdir(1), cp(1)
""",
    "mkdir": """
NAME
     mkdir - make directories

SYNOPSIS
     mkdir directory ...

DESCRIPTION
     Create each directory. The parent must already exist.

SEE ALSO
     rmdir(1), ls(1)
""",
    "rmdir": """
NAME
     rmdir - remove empty directories

SYNOPSIS
     rmdir directory ...

DESCRIPTION
     Remove each directory, which must be empty. Use rm -r otherwise.

SEE ALSO
     mkdir(1), rm(1)
""",
    "touch": """
NAME
     touch - create a file

SYNOPSIS
     touch file ...

DESCRIPTION
     Create each file if it does not already exist. An existing file is
     left alone.

SEE ALSO
     cp(1), ed(1)
""",
    "chmod": """
NAME
     chmod - change mode

SYNOPSIS
     chmod mode file ...

DESCRIPTION
     Change the permission bits, given in octal. The mode is shown by
     ls -l and read by file(1).

     Nothing in this simulation enforces permission, which is stated here
     rather than implied by the command existing.

SEE ALSO
     ls(1)
""",
    "du": """
NAME
     du - summarise space used

SYNOPSIS
     du [name ...]

DESCRIPTION
     Report the space used, in 512-byte blocks, the unit V7 counted in.

SEE ALSO
     df(1), ls(1)
""",
    "find": """
NAME
     find - walk a file tree

SYNOPSIS
     find path [-name pattern] [-type f|d]

DESCRIPTION
     Walk the tree under the path, printing what it finds. Supports
     -name and -type, which is most of what find gets used for.

SEE ALSO
     ls(1), grep(1)
""",
    "tty": """
NAME
     tty - print the terminal name

SYNOPSIS
     tty

DESCRIPTION
     Print the name of the terminal you are on.

SEE ALSO
     who(1)
""",
    "sync": """
NAME
     sync - flush the buffer cache

SYNOPSIS
     sync

DESCRIPTION
     Write out any buffered blocks. Prints nothing, which is correct.

SEE ALSO
     df(1)
""",
    "tr": """
NAME
     tr - translate characters

SYNOPSIS
     tr [-d] set1 [set2]

DESCRIPTION
     Read standard input and translate characters in set1 to the
     corresponding character in set2. Ranges are written a-z.

     -d deletes the characters in set1 instead.

EXAMPLES
     cat notes | tr a-z A-Z
     cat file | tr -d 0123456789

SEE ALSO
     sed(1), cut(1)
""",
    "cut": """
NAME
     cut - cut out columns

SYNOPSIS
     cut -f list [-d char] [file]
     cut -c list [file]

DESCRIPTION
     Take fields or character positions out of every line. A list is
     written 1,3-5. Fields are separated by tabs unless -d says otherwise.

EXAMPLES
     cat /etc/passwd | cut -d: -f1

SEE ALSO
     tr(1), sed(1), sort(1)
""",
    "sed": """
NAME
     sed - stream editor

SYNOPSIS
     sed 's/old/new/[g]' [file]
     sed '/pattern/d' [file]

DESCRIPTION
     Edit a stream. This sed does substitution and deletion, not the
     whole language, and says so rather than failing quietly on the rest.

SEE ALSO
     ed(1), grep(1), tr(1)
""",
    "tee": """
NAME
     tee - copy input to a file and on

SYNOPSIS
     tee [-a] file ...

DESCRIPTION
     Copy standard input to each named file and to the output, so a
     pipeline can be tapped part way along. -a appends.

SEE ALSO
     cat(1)
""",
    "rev": """
NAME
     rev - reverse lines

SYNOPSIS
     rev [file]

DESCRIPTION
     Reverse the characters of every line.

SEE ALSO
     tr(1)
""",
    "cmp": """
NAME
     cmp - compare two files

SYNOPSIS
     cmp file1 file2

DESCRIPTION
     Say where two files first differ, by character and line. Silent if
     they are the same, which is the point.

SEE ALSO
     diff(1)
""",
    "diff": """
NAME
     diff - report differing lines

SYNOPSIS
     diff file1 file2

DESCRIPTION
     Report the lines that differ, in ed(1) command form: the output was
     meant to be fed back into the editor to turn one file into the other.

SEE ALSO
     cmp(1), ed(1)
""",
    "od": """
NAME
     od - octal dump

SYNOPSIS
     od [file]

DESCRIPTION
     Dump a file in octal, which is what the o stands for.

SEE ALSO
     cat(1)
""",
    "spell": """
NAME
     spell - find spelling errors

SYNOPSIS
     spell [file]

DESCRIPTION
     Print the words not in the dictionary.

     The dictionary on this machine is small and Bell-flavoured, so spell
     is a toy here. It will call most ordinary English wrong.

SEE ALSO
     grep(1)
""",
    "banner": """
NAME
     banner - print in large letters

SYNOPSIS
     banner text

DESCRIPTION
     Print its argument in letters five rows high, for the top of a
     listing or the front of a printout.

SEE ALSO
     echo(1)
""",
    "factor": """
NAME
     factor - factor a number

SYNOPSIS
     factor number

DESCRIPTION
     Print the prime factors. factor: ouch means it did not like the
     number, which is what it said in 1979 too.

SEE ALSO
     primes(1), bc(1)
""",
    "primes": """
NAME
     primes - print primes

SYNOPSIS
     primes [start [stop]]

DESCRIPTION
     Print the primes in the range.

SEE ALSO
     factor(1)
""",
    "bc": """
NAME
     bc - calculator

SYNOPSIS
     bc expression

DESCRIPTION
     Evaluate an arithmetic expression. Takes it on the command line
     rather than reading a session, because this terminal cannot feed it
     one a line at a time.

     ^ is exponentiation.

SEE ALSO
     factor(1), units(1)
""",
    "units": """
NAME
     units - convert units

SYNOPSIS
     units number from to

DESCRIPTION
     Convert between units, including the ones the outside plant is
     measured in: miles, kilofeet, feet, kilometres, inches, centimetres,
     pounds and kilogrammes.

EXAMPLES
     units 3 mile kft

SEE ALSO
     bc(1)
""",
    "sleep": """
NAME
     sleep - suspend execution

SYNOPSIS
     sleep seconds

DESCRIPTION
     Wait. Nothing blocks this terminal, so sleep charges the shift
     clock instead, which is what time means here.

SEE ALSO
     date(1)
""",
    "mesg": """
NAME
     mesg - permit or deny messages

SYNOPSIS
     mesg [y|n]

DESCRIPTION
     Allow or refuse messages from write(1) and the rest of the craft.
     With no argument, report the current state.

     This is the same switch as set game.ambience.

SEE ALSO
     write(1), set(1)
""",
    "wall": """
NAME
     wall - write to all users

SYNOPSIS
     wall message

DESCRIPTION
     Send a message to everybody logged on. They will have opinions
     about whether it needed to be a wall.

SEE ALSO
     write(1), mesg(1)
""",
    "passwd": """
NAME
     passwd - change login password

SYNOPSIS
     passwd

DESCRIPTION
     Change your password. This terminal cannot read one without
     echoing it, so nothing is changed; and every account in /etc/passwd
     has an empty password field anyway. It was 1983.

SEE ALSO
     who(1)
""",
    "stty": """
NAME
     stty - set terminal options

SYNOPSIS
     stty [everything]

DESCRIPTION
     Report or set the terminal modes. This is a 300 baud line.

SEE ALSO
     tty(1)
""",
    "fortune": """
NAME
     fortune - print a random adage

SYNOPSIS
     fortune

DESCRIPTION
     Print a saying from /usr/games/fortunes.

SEE ALSO
     cat(1)
""",
    "bcd": """
NAME
     bcd - convert to punched card

SYNOPSIS
     bcd text

DESCRIPTION
     Print its argument as an 80-column punched card. Letters take a
     zone punch and a digit punch, the way an 026 keypunch encoded them:
     A to I on the 12 zone, J to R on the 11 zone, S to Z on the 0 zone.

SEE ALSO
     ppt(6)
""",
    "ppt": """
NAME
     ppt - convert to paper tape

SYNOPSIS
     ppt text

DESCRIPTION
     Print its argument as punched paper tape, sprocket holes and all.

SEE ALSO
     bcd(6)
""",
    "arithmetic": """
NAME
     arithmetic - provide drill in arithmetic

SYNOPSIS
     arithmetic

DESCRIPTION
     Pose a problem. This terminal takes one line at a time, so it gives
     the answer rather than waiting for yours.

SEE ALSO
     bc(1)
""",
    "moo": """
NAME
     moo - guess the number

SYNOPSIS
     moo
     moo nnnn

DESCRIPTION
     Bulls and cows. The number has four digits, all different. A bull
     is a right digit in the right place, a cow a right digit in the wrong
     place.

     moo starts a game; moo 1234 guesses.

     There is a scoreboard in /usr/games/lib/moo.scores that somebody has
     been keeping.

SEE ALSO
     arithmetic(6)
""",
    "readnews": """
NAME
     readnews - read netnews

SYNOPSIS
     readnews [n]
     readnews -n group

DESCRIPTION
     Read the news. This machine takes a feed nightly over uucp.

     With no argument, list what is waiting. With a number, read that
     article. With -n, pick a newsgroup.

     Articles are files under /usr/spool/news, so cat(1) and grep(1) work
     on them as well.

SEE ALSO
     uucp(1), mail(1)
""",
    "ed": """
NAME
     ed - text editor

SYNOPSIS
     ed [file]

DESCRIPTION
     The editor. Every line you type goes to ed until you type q.

COMMANDS
     a         append lines after the current one; a lone . ends it
     i         insert before the current line
     c         change lines
     d         delete lines
     p         print lines
     n         print lines with numbers
     s/old/new/[g]   substitute on the addressed lines
     w [file]  write out; prints the byte count
     r file    read a file in
     =         print a line number
     q         quit; refuses once if the buffer is modified
     Q         quit without writing
     h         explain the last ?
     H         leave explanations on

ADDRESSES
     A number, . for the current line, $ for the last, /pattern/ to search,
     a,b for a range, and 1,$ or % for the whole buffer.

DIAGNOSTICS
     ?

     That is the entire diagnostic. It is not a fault in this simulation.
     h will explain the last one, and after three in a row ed relents and
     says how to get out - which the real editor never did.

SEE ALSO
     sed(1), cat(1)
""",
    "cc": """
NAME
     cc - C compiler

SYNOPSIS
     cc [-o name] file.c

DESCRIPTION
     Compile a C program and leave the result in a.out, or in the name
     given after -o. Run it by typing its name.

     This compiler understands printf and nothing else. It reads the calls
     out of your program and builds something that prints them. That is
     enough for /usr/src/cmd/hello.c and it is not a C compiler; saying so
     plainly is better than letting you find out.

SEE ALSO
     ed(1)
""",
    "nroff": """
NAME
     nroff - format text

SYNOPSIS
     nroff [-ms|-man] [file]

DESCRIPTION
     Format a document for a terminal or a line printer, filling and
     breaking lines to the measure.

REQUESTS
     .TH .SH .PP .LP .IP .TP .B .I .br .sp .nf .fi

     Reads standard input when given no file, so tbl table | nroff works
     the way it always did.

SEE ALSO
     troff(1), tbl(1), man(1)
""",
    "troff": """
NAME
     troff - typeset text

SYNOPSIS
     troff [-ms|-man] [file]

DESCRIPTION
     Format a document for a phototypesetter. There is no typesetter on
     this machine, so troff sets to a wider measure and says so rather
     than emitting codes nothing can read.

SEE ALSO
     nroff(1), tbl(1)
""",
    "tbl": """
NAME
     tbl - format tables

SYNOPSIS
     tbl [file]

DESCRIPTION
     Lay out the tables between .TS and .TE and pass everything on.
     The line after .TS gives the column formats: l, r or c.

EXAMPLES
     tbl report | nroff

SEE ALSO
     nroff(1), troff(1)
""",
    "eqn": """
NAME
     eqn - typeset mathematics

SYNOPSIS
     eqn [file]

DESCRIPTION
     Set mathematics for troff. There is no typesetter here, so eqn
     passes its input through and says why.

SEE ALSO
     troff(1), tbl(1)
""",
    "pr": """
NAME
     pr - paginate a file for printing

SYNOPSIS
     pr [-t] [-h header] [-ln] [-n] [file ...]

DESCRIPTION
     Print a file in pages of 66 lines, five of heading and five of foot,
     which is a letter sheet at six lines to the inch.

OPTIONS
     -t          No heading and no foot: just the text
     -h header   Put this in the heading instead of the file name
     -ln         Set the page length to n lines
     -n          Lay the text out in n columns

EXAMPLES
     pr /usr/lmos/board          The board, with a heading and page numbers
     pr -t -2 /usr/dict/words    The dictionary in two columns, no heading

SEE ALSO
     cat(1), more(1), nroff(1)
""",
    "comm": """
NAME
     comm - select or reject lines common to two sorted files

SYNOPSIS
     comm [-123] file1 file2

DESCRIPTION
     Read two sorted files and print three columns: the lines only in the
     first, the lines only in the second, and the lines in both.

     Both files must be sorted or the answer is nonsense. sort(1) first.

OPTIONS
     -1  Leave out the lines only in file1
     -2  Leave out the lines only in file2
     -3  Leave out the lines in both

EXAMPLES
     comm -12 yesterday today    Only what is in both
     comm -23 yesterday today    Only what has gone away

SEE ALSO
     sort(1), uniq(1), join(1), diff(1)
""",
    "join": """
NAME
     join - join two sorted files on a common field

SYNOPSIS
     join file1 file2

DESCRIPTION
     For every line in file1 whose first field matches the first field of a
     line in file2, print the field followed by the rest of both lines.
     Both files must be sorted on that field.

     This is how two lists were put beside each other before there was a
     database on anybody's desk.

SEE ALSO
     sort(1), comm(1), awk(1)
""",
    "look": """
NAME
     look - find lines in a sorted list

SYNOPSIS
     look prefix [file]

DESCRIPTION
     Print the words in /usr/dict/words that begin with the given prefix,
     or the lines of another file if one is named.

     The dictionary here is a few hundred words against the real one's
     twenty-five thousand. It is an ordinary file, so cat(1) and wc(1)
     will tell you exactly what is in it.

EXAMPLES
     look tel        telephone, tell
     look sw         switch, switches, switching

SEE ALSO
     spell(1), grep(1), sort(1)
""",
    "split": """
NAME
     split - split a file into pieces

SYNOPSIS
     split [-n] file [name]

DESCRIPTION
     Break a file into pieces of 1000 lines, or n lines with -n. The pieces
     are called xaa, xab and so on, which is where the x in the name comes
     from; give a name to use something else.

EXAMPLES
     split -50 /usr/dict/words part    part-aa, part-ab, ...

SEE ALSO
     cat(1), wc(1), head(1), tail(1)
""",
    "sum": """
NAME
     sum - print a checksum and block count

SYNOPSIS
     sum file ...

DESCRIPTION
     Add the bytes of a file into a sixteen-bit total, rotating the
     accumulator right one bit before each addition so that two bytes
     swapped over do not go unnoticed, and print the total with the number
     of 512-byte blocks.

     This is how you checked a file had crossed a phone line intact: run
     sum at both ends and compare the two numbers.

SEE ALSO
     wc(1), cmp(1), uucp(1)
""",
    "dd": """
NAME
     dd - convert and copy a file

SYNOPSIS
     dd if=file [of=file] [bs=n] [count=n] [skip=n] [conv=ucase|lcase]

DESCRIPTION
     Copy a file, converting it on the way. Arguments are keyword=value
     rather than flags, which is dd's own convention and nobody else's.

OPTIONS
     if=     Input file
     of=     Output file; standard output if left off
     bs=     Block size in bytes, 512 by default
     count=  Copy only this many blocks
     skip=   Skip this many blocks of input first
     conv=   ucase or lcase

EXAMPLES
     dd if=/etc/motd conv=ucase
     dd if=/usr/dict/words of=/tmp/part count=1

SEE ALSO
     cp(1), tr(1), sum(1)
""",
    "expr": """
NAME
     expr - evaluate an expression

SYNOPSIS
     expr arg operator arg

DESCRIPTION
     Evaluate an expression and print the result. The shell has no
     arithmetic of its own, so this is how a shell loop counted:

          i=`expr $i + 1`

     Handles + - \\* / % and the comparisons = != < <= > >=, which prints
     1 for true and 0 for false.

EXAMPLES
     expr 6 + 7
     expr 100 / 7
     expr 5 '>' 3

SEE ALSO
     bc(1), sh(1), test(1)
""",
    "basename": """
NAME
     basename - strip directories from a path

SYNOPSIS
     basename string [suffix]

DESCRIPTION
     Print the last part of a path, with an optional suffix removed as
     well. Used inside shell scripts to turn a file name into the name of
     the thing it builds.

EXAMPLES
     basename /usr/src/cmd/hello.c .c        hello

SEE ALSO
     sh(1), make(1)
""",
    "true": """
NAME
     true - do nothing, successfully

SYNOPSIS
     true

DESCRIPTION
     Return a successful exit status and print nothing. Half of every
     shell loop ever written begins "while true".

SEE ALSO
     false(1), sh(1)
""",
    "false": """
NAME
     false - do nothing, unsuccessfully

SYNOPSIS
     false

DESCRIPTION
     Return an unsuccessful exit status and print nothing.

SEE ALSO
     true(1), sh(1)
""",
    "at": """
NAME
     at - run a command at a given time

SYNOPSIS
     at hhmm command
     at -l
     at -r job ...

DESCRIPTION
     Queue a command to run later in the shift. The time is four digits on
     the twenty-four hour clock. The job fires when the shift clock reaches
     it and its output arrives on the terminal, the same way a message from
     anyone else in the building does.

     Queued jobs are files under /usr/spool/at, so ls(1) finds them.

OPTIONS
     -l          List the queue
     -r job      Take a job back out of it

EXAMPLES
     at 1030 report board       Look at the board at half past ten
     at 1145 lmos reports       Pull the reports before the tour ends
     at -l                      What is queued

     A job may not queue another job.

SEE ALSO
     sleep(1), date(1), ps(1)
""",
    "make": """
NAME
     make - maintain programs

SYNOPSIS
     make [-f makefile] [target ...]

DESCRIPTION
     Read a makefile and bring a target up to date. A rule is a target, a
     colon, what it depends on, and then the commands to build it, each
     indented with a tab.

     Anything already built is left alone. That is the whole point of the
     program: it does the least work that leaves you with a current
     program.

     There is a makefile under /usr/src/cmd for the two programs there.

EXAMPLES
     cd /usr/src/cmd
     make                  Build whatever is out of date
     make hello            Build just that one

SEE ALSO
     cc(1), sh(1)
""",
    "su": """
NAME
     su - become another user

SYNOPSIS
     su [user]

DESCRIPTION
     Ask for another user's password and become them if you have it. Root
     if no user is named.

     Every attempt is written to /usr/adm/sulog whether it succeeds or not.
     Nobody at a craft position has the root password, and the log is how
     the wire chief knows who tried.

SEE ALSO
     passwd(1), who(1), logname(1)
""",
    "logname": """
NAME
     logname - print your login name

SYNOPSIS
     logname

DESCRIPTION
     Print the name you logged in under. A script uses this to find out
     who is running it, which is not always who owns it.

SEE ALSO
     who(1), su(1), passwd(1)
""",
    "uuname": """
NAME
     uuname - list the machines this one can call

SYNOPSIS
     uuname [-l]

DESCRIPTION
     Print the names of the systems this machine has a uucp connection to.
     With -l, print the name of this machine instead.

     The netnews under /usr/spool/news arrives over these links, one call
     a night.

SEE ALSO
     uucp(1), uulog(1), uux(1), readnews(1)
""",
    "uulog": """
NAME
     uulog - print the uucp log

SYNOPSIS
     uulog [-ssite]

DESCRIPTION
     Print /usr/adm/uucplog, the record of what this machine has called and
     what it sent. With -s, only the traffic with one site.

     A call that FAILED is worth reading. It usually means the far end did
     not answer, and it means whatever was queued for them is still queued.

EXAMPLES
     uulog -sihnp4

SEE ALSO
     uucp(1), uuname(1), uux(1)
""",
    "uux": """
NAME
     uux - run a command on another machine

SYNOPSIS
     uux site!command

DESCRIPTION
     Queue a command to be run on another system and the answer sent back.
     Nothing comes back inside a shift: the job waits until the two
     machines are next talking, which on this one is four in the morning.

EXAMPLES
     uux research!date

SEE ALSO
     uucp(1), uuname(1), uulog(1)
""",
    "kill": """
NAME
     kill - send a signal to a process

SYNOPSIS
     kill [-signal] pid ...

DESCRIPTION
     Send a signal to a running process, by default a terminate. Only the
     owner of a process, or root, may signal it.

     Everything in the process table on this machine belongs to root. You
     will be told you are not the owner, which is the correct answer and
     not a fault.

SEE ALSO
     ps(1), who(1)
""",
    "nice": """
NAME
     nice - run a command at low priority

SYNOPSIS
     nice [-number] command

DESCRIPTION
     Run a command at lower priority so that it gives way to everything
     else. On a machine with this much work on it the courtesy is real; on
     this one the command runs at once regardless.

SEE ALSO
     ps(1), time(1), nohup(1)
""",
    "time": """
NAME
     time - time a command

SYNOPSIS
     time command

DESCRIPTION
     Run a command and print how long it took: elapsed, then the time spent
     in the program, then the time spent in the system on its behalf.

EXAMPLES
     time wc /usr/dict/words

SEE ALSO
     date(1), nice(1), ps(1)
""",
    "nohup": """
NAME
     nohup - run a command immune to hangups

SYNOPSIS
     nohup command

DESCRIPTION
     Run a command so that it survives the line dropping, with its output
     going to nohup.out in the working directory rather than to the
     terminal.

     This is what you ran before going home when the dial-up would not
     stay up all night.

SEE ALSO
     at(1), nice(1), sh(1)
""",
    "pic": """
NAME
     pic - set diagrams for troff

SYNOPSIS
     pic [file]

DESCRIPTION
     Read the .PS/.PE blocks in a file and draw what they describe.
     Everything outside a block passes through unchanged, which is how pic
     sat in front of troff in a pipeline.

     Statements are box, circle, ellipse, arrow, line and move, each with
     an optional quoted label, chained left to right. A "down" statement
     turns the chain vertical and "right" turns it back.

     The real pic is a language with variables, named positions and
     splines, described in Kernighan's paper. This one draws in characters
     because a terminal is what is here.

EXAMPLES
     pic /usr/doc/loop.pic
     pic diagram | nroff

SEE ALSO
     troff(1), nroff(1), tbl(1), refer(1)
""",
    "refer": """
NAME
     refer - fill in citations from a bibliography

SYNOPSIS
     refer [file]

DESCRIPTION
     Text between .[ and .] names a paper. refer finds it in
     /usr/dict/papers, puts a bracketed number in its place, and prints a
     numbered reference list at the end.

     A citation is just words that appear in the record, so

          .[
          ritchie thompson 1974
          .]

     finds the CACM paper. The real refer searched an index built by
     indxbib; this one reads the file, which on a bibliography this size
     is the same answer.

SEE ALSO
     troff(1), nroff(1), pic(1), look(1)
""",
    "send": """
NAME
     send - submit a batch job to the host

SYNOPSIS
     send [-h host] file

DESCRIPTION
     Submit a file to the revenue accounting office over the remote job
     entry link. This machine does not do its own billing: message detail
     goes up the line to a mainframe and the listing comes back on the
     overnight run.

     There is one host from this position, RAO1.

SEE ALSO
     rjestat(1), uux(1), billing(1)
""",
    "rjestat": """
NAME
     rjestat - report on the remote job entry link

SYNOPSIS
     rjestat

DESCRIPTION
     Print the state of the link to the revenue accounting office and the
     jobs queued on it from this position.

     Worth running before you spend a morning building a job: if the line
     is down, nothing you submit goes anywhere.

SEE ALSO
     send(1), uucp(1)
""",
    "trace": """
NAME
     trace - follow a call through the toll network

SYNOPSIS
     trace
     trace office
     trace origin destination

DESCRIPTION
     With no arguments, list the offices in the routing table by class.

     With one office, print its homing chain: the route a call from it
     climbs until it reaches an office the far end also homes on.

     With two, offer a call between them and print every trunk group it
     takes in order, with what each was carrying and how many trunks ended
     up in tandem. A blocked call says which route was refused and why.

EXAMPLES
     trace EO-NYC-01                homing chain
     trace EO-NYC-01 EO-CHI-01      route a call New York to Chicago

SEE ALSO
     routing(1), toll(1), trunk(1), capacity(1)
""",
    "western": """
NAME
     western - Western Electric equipment reference

SYNOPSIS
     western [name]

DESCRIPTION
     Western Electric was the Bell System's manufacturing arm and made
     nearly everything in the plant. With no argument, list what is in the
     reference by kind: station apparatus, switching systems, transmission
     equipment. With a name, print the entry.

     Dates are the year the type entered service. Anything the sources
     consulted did not settle is absent rather than guessed at, which is
     why the table is short.

EXAMPLES
     western 500        the set most reports are about
     western no5xbar    the crossbar office behind most of them
     western 5ess       what replaces it

SEE ALSO
     crossbar(1), switch(1), 5ess(1)
""",
    "capacity": """
NAME
     capacity - what the trunk groups carry against what they hold

SYNOPSIS
     capacity

DESCRIPTION
     Print every trunk group with its size, how much of it is busy, and
     whether that is inside its objective.

     A final group is engineered to P.01: one call in a hundred finds every
     trunk busy. A high usage group is engineered to P.10, because
     overflowing is what it is for, and a high usage group running quiet is
     not good news - it means traffic is not being offered to it.

     Traffic engineering wants a count before it will add trunks.

SEE ALSO
     trunk(1), traffic(1), trace(1), tnds(1)
""",
    "coer": """
NAME
     coer - central office equipment report

SYNOPSIS
     coer [office]

DESCRIPTION
     What is in each office, how it homes, and what is in trouble. The
     report a wire chief signed at the end of a tour and sent up.

     With an office code, report on that one: its class, what it homes on,
     its whole chain to a regional centre, and what that class of office
     does.

EXAMPLES
     coer               the whole report
     coer TC-NYC        one office

SEE ALSO
     switch(1), alarm(1), trace(1), report(1)
""",
    "5ess": """
NAME
     5ess - the No. 5 ESS, and what it means for this building

SYNOPSIS
     5ess

DESCRIPTION
     The newest switching system in the plant, in service since 1982.
     There is not one in this office and there will not be one this year.

     The command is here so that you can find out what is coming and what
     it replaces: half of what is on a repair board is metal contacts, and
     that half of the work does not exist in a digital office. The other
     half is the loop, and that is copper in the ground either way.

SEE ALSO
     western(1), crossbar(1), switch(1)
""",
    "microwave": """
NAME
     microwave - long-haul microwave radio

SYNOPSIS
     microwave

DESCRIPTION
     The summary a shift starts with: what the system is, what band it
     works in, and what the routes on this position are doing.

     The routes here are TH-3 at six gigahertz. Rain absorbs at six
     gigahertz and heavy rain on a long hop takes the fade margin with it.
     A path that fades is not a fault and there is nothing on the ground to
     go and fix.

     radio(1) has the path-by-path detail.

SEE ALSO
     radio(1), antenna(1), satellite(1)
""",
    "satellite": """
NAME
     satellite - satellite circuits, and why the network mostly avoids them

SYNOPSIS
     satellite

DESCRIPTION
     Nothing this office switches goes by satellite, and that is a decision
     rather than an omission.

     A geostationary satellite sits about 22,300 miles up. Up and down
     again is roughly a quarter of a second, so a round trip costs half a
     second before the switching at either end has done anything. On a
     telephone call that is two people talking over each other.

     It is also why an echo suppressor is on every circuit that has been
     near one.

SEE ALSO
     microwave(1), radio(1), trace(1)
""",
    "custdb": """
NAME
     custdb - look a customer line record up

SYNOPSIS
     custdb [number]

DESCRIPTION
     Given a telephone number or a report number, print what the records
     say about that line: who it serves, where it is, what cable and pair
     it comes in on, where it lands on the frame, and how often it has been
     in trouble.

     A line marked CHRONIC has reported often enough that the fix is
     probably not where the last one was.

     With no argument, list the lines that have a record on this position.

     This is the same line card LMOS holds. It is here under its own name
     because it is the lookup you do twenty times a tour.

SEE ALSO
     lmos(1), cosmos(1), dbquery(1), report(1)
""",
    "dbquery": """
NAME
     dbquery - find which records system holds what you are after

SYNOPSIS
     dbquery
     dbquery system thing

DESCRIPTION
     With no arguments, list the mechanised records systems, what each one
     holds, and how to ask it.

     With a system and a thing, put the question to that system. This is
     the same as typing that system's own command, and is here so that you
     do not have to know which one it is.

     A telephone number is in lmos and cosmos. A circuit identifier is in
     tirks. A bare number with no system named is taken as a line lookup,
     because that is what people mean.

EXAMPLES
     dbquery lmos 201-200-1577
     dbquery cosmos 201-200-1577

SEE ALSO
     custdb(1), lmos(1), cosmos(1), sarts(1), tnds(1)
""",
    "provision": """
NAME
     provision - raise a service order against a line

SYNOPSIS
     provision [type number]

DESCRIPTION
     A service order is what makes the outside plant change: it tells the
     frame what to cross-connect, the assignment records what to update,
     and an installer where to go. Nothing moves without one.

     With no arguments, list the order types. With a type and a number,
     raise the order.

     The due date is the next working day. The frame works to a list, and
     today's list was made up last night.

SEE ALSO
     cosmos(1), custdb(1), service(1), frame(1)
""",
    "collect": """
NAME
     collect - operator-handled calls, and why they need an operator

SYNOPSIS
     collect [queue]

DESCRIPTION
     Collect, third number, person to person, credit card and coin calls
     all need a person, because every one of them is a promise to pay made
     by somebody who is not the caller, and nothing in the switching
     equipment can take a promise.

     The operator asks, hears the answer, and keys the acceptance. Only
     then does the equipment cut the call through and start timing.

     That is the whole reason there is a traffic service position system.

     This is a repair position and does not take calls. collect queue shows
     the operator position's own status.

SEE ALSO
     tsps(1), operator(1), billing(1)
""",
    "training": """
NAME
     training - what you are signed off for, and how to get the rest

SYNOPSIS
     training [qualification]

DESCRIPTION
     Qualification in the Bell System followed the work: you were signed
     off for what you had done, on the say-so of somebody who had watched
     you do it.

     With no argument, print where you are in that and what the next step
     wants. With a qualification named, print what it covers and which
     commands it opens.

     Nothing here is a course you sit. The reports on your board are the
     course, and closing them correctly is how it is passed.

EXAMPLES
     training            where you are
     training trunk      what interoffice trunks covers

SEE ALSO
     qual(1), report(1), trouble(1), man(1)
""",
    "weather": """
NAME
     weather - what it is doing outside, and what that does to the plant

SYNOPSIS
     weather

DESCRIPTION
     The conditions over the wire centre, how they got there through the
     tour, and what they are doing to the cable.

     This is not scenery. Wet cable is water in a sheath, and rain is what
     makes it worse: an unrepaired binder group takes another pair faster
     the harder it is raining, and each pair that goes is another report on
     your board. A splicer trip while it is dry costs one dispatch. The
     same water after an afternoon of rain costs several.

     A sheath whose pressure has fallen far enough is shown as alarming.
     Cable is pressurised with dry air to keep water out, so the pressure
     goes first and the water comes after - the contactor is the thing that
     could have told you before the customer did.

SEE ALSO
     lmos(1), report(1), radio(1)
""",
    "force": """
NAME
     force - who is available to go out

SYNOPSIS
     force

DESCRIPTION
     The field force this wire centre has, where each of them is, and who
     is already on a job.

     Dispatching used to go to a category, and a category is never busy.
     There are five people here. A report dispatched when they are all out
     does not vanish - it stays on the board and the queue runs on the
     customer's commitment, which is the cost of a finite force and is
     worth knowing before you promise anybody a time.

     A crew's travel time depends on where they are standing when the call
     goes out, and it is charged against the commitment like everything
     else.

SEE ALSO
     report(1), lmos(1), trouble(1), weather(1)
""",
    "connect": """
NAME
     connect - work another office from this console

SYNOPSIS
     connect
     connect clli
     connect home

DESCRIPTION
     A switching control centre watches a group of offices from one
     console. This is that: reach another building by its CLLI code, by the
     start of its city name, or by its number in the listing.

     With no argument, list the offices this console watches and mark the
     one you are on. connect home comes back.

     While connected, alarm(1) reads the office you are connected to, which
     has its own alarms and its own health. Acknowledging one office's
     alarm does not touch another's.

     The trouble board does NOT travel. A customer loop lands on exactly
     one frame in one building, so its report stays there. What travels is
     everything above the loop: the switching machine, its alarms and its
     records. That division is not a simplification - it is why a control
     centre could watch eleven offices and a repair service bureau could
     not.

EXAMPLES
     connect                       what is on the console
     connect NWRKNJCOCG0          by code
     connect Newark               by place
     connect home                 back to the building you can walk to

SEE ALSO
     alarm(1), switch(1), coer(1), company(1), sarts(1)
""",
    "company": """
NAME
     company - whose office this is, and where it goes in January

SYNOPSIS
     company
     company state
     company all

DESCRIPTION
     AT&T was sole stockholder in twenty-one operating companies and a
     minority stockholder in two. On 1 January 1984 the twenty-one pass to
     seven regional holding companies.

     With no argument, the company running the office this console is on.
     With a two-letter state code, that state's. With all, the whole table.

     This is the one thing everybody in every one of these buildings
     actually knew about their own company in the autumn of 1983.

     Connecticut and Cincinnati are absent from the table because AT&T held
     only a minority stake in Southern New England Telephone and Cincinnati
     Bell. They do not divest.

     An entry marked ? has its regional assignment from outside the bundled
     documents. Engineering and Operations gives three of the seven
     groupings in full - Pacific Telesis, Ameritech and Bell Atlantic - and
     the rest are externally sourced.

EXAMPLES
     company all
     company IL
     company CT

SEE ALSO
     connect(1), coer(1)
""",
    "tone": """
NAME
     tone - write a signalling tone to a file you can listen to

SYNOPSIS
     tone
     tone name [-n]
     tone mf digits
     tone dtmf digits

DESCRIPTION
     Every frequency, level and cadence in the tone plan has been in this
     simulation's data since it was written, described in words and never
     heard. A craftsperson told a busy from a reorder by ear - they are the
     same two frequencies, 480 and 620 Hz, and differ only in how fast they
     are interrupted, sixty a minute against a hundred and twenty. That is
     not a distinction you can read off a table.

     With no argument, list what can be made.

OPTIONS
     -n    Normalise for listening. The levels in the tables are relative
           to each other and honest, which makes a busy tone genuinely
           quiet: it is eleven dB below dial tone because it is. This
           changes the file, not the table.

EXAMPLES
     tone busy               the tone, cadence and all
     tone reorder            the same frequencies, twice the rate
     tone howler             0 dBm, and meant to be unbearable
     tone mf KP212ST         an address pulsed as a switch would
     tone dtmf 5551212       as a Touch-Tone set would
     tone sf                 2600 Hz, a seizure, and the tone returning

     A wave file is not something a 1983 machine could have made. It is
     written outside the simulation, in this session's own directory, and
     the path printed is a real one.

SEE ALSO
     dialtone(1), testline(1), testcall(1), trunk(1)
""",
    "era": """
NAME
     era - what network the date you are set to produces

SYNOPSIS
     era

DESCRIPTION
     The epoch is a setting, and moving it moves the plant. A shift set to
     1955 finds step-by-step and crossbar and no electronic switching
     anywhere, because no ESS had entered service. A shift set to 1971
     finds the first No. 1 and No. 2 ESS machines among a network still
     mostly step-by-step.

     That is not decoration. The office generator reads the first-service
     year of every switching system and will not place one that does not
     exist yet, so the network genuinely is a different network.

     What does not move is the writing. The message of the day, the
     divestiture memo and the netnews spool are November 1983. era says so
     rather than letting you discover it by reading a 1984 divestiture
     notice on a 1955 machine.

EXAMPLES
     set date.epoch 1955-06-14
     era
     set date.epoch 1983-11-14

SEE ALSO
     set(1), switch(1), crossbar(1), western(1), company(1)
""",
}
