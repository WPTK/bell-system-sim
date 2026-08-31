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

    "5ess": """
NAME
     5ess - 5ESS Electronic Switching System operations

SYNOPSIS
     5ess [status|diagnostics|traffic|translations|maintenance] [switch-id]

DESCRIPTION
     Monitor and manage 5ESS Electronic Switching Systems. The 5ESS provides
     digital switching capabilities with stored program control, featuring
     dual processor architecture and distributed switching modules.

OPTIONS
     status          Display 5ESS system configuration and status
     diagnostics     Execute comprehensive diagnostic routines
     traffic         Analyze call processing load and capacity
     translations    Translation table management and updates
     maintenance     Scheduled maintenance procedures

TECHNICAL SPECIFICATIONS
     Administrative Module (AM):     Dual processor control
     Switching Modules (SM):         Up to 192 remote/local modules
     Communications Module (CM):     Message switching interface
     Call Processing Capacity:       750,000 BHCA per system

EXAMPLES
     5ess status                     Display all 5ESS systems
     5ess diagnostics NYC-5ESS-01    Run diagnostics on specific switch
     5ess traffic CHI-5ESS-02        Monitor traffic load

SEE ALSO
     3a(1), switch(1), western(1), crossbar(1)

BELL SYSTEM PRACTICES
     BSP 200-100-001 - 5ESS System Description
     BSP 200-100-100 - 5ESS Operations and Maintenance
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

    "microwave": """
NAME
     microwave - Microwave transmission system analysis

SYNOPSIS
     microwave [path|fade|interference|performance] [route-id]

DESCRIPTION
     Analyze microwave transmission paths including path loss calculations,
     fade margin analysis, interference assessment, and performance
     monitoring for Bell System microwave radio systems.

OPTIONS
     path            Radio path analysis and calculations
     fade            Fade margin and reliability analysis
     interference    Interference analysis and mitigation
     performance     System performance monitoring

PATH ANALYSIS
     Free Space Loss:        Basic transmission loss calculation
     Obstruction Analysis:   Fresnel zone clearance verification
     Refractivity:          Atmospheric propagation effects
     Multipath:             Signal reflection and fading

EXAMPLES
     microwave path NYC-BOS          Analyze radio path
     microwave fade TH3-ROUTE-14     Check fade margins
     microwave performance all       Monitor all routes

SEE ALSO
     radio(1), antenna(1), satellite(1)

BELL SYSTEM PRACTICES
     BSP 365-300-001 - Microwave Path Engineering
""",

    "satellite": """
NAME
     satellite - Satellite communication link monitoring

SYNOPSIS
     satellite [status|earth-station|orbit|performance] [station-id]

DESCRIPTION
     Monitor Bell System satellite communication facilities including
     earth stations, satellite tracking, and communication link
     performance for long-distance and international services.

OPTIONS
     status          Satellite system operational status
     earth-station   Earth station equipment monitoring
     orbit           Satellite tracking and positioning
     performance     Link performance and quality monitoring

SATELLITE SYSTEMS
     COMSTAR:        Domestic satellite communication system
     INTELSAT:       International satellite services
     Earth Stations: Large aperture antenna facilities
     Transponders:   Satellite repeater channels

EXAMPLES
     satellite status                Show all satellite links
     satellite earth-station ES-NY   Monitor earth station
     satellite orbit COMSTAR-D1      Track satellite position

SEE ALSO
     radio(1), microwave(1), antenna(1)

BELL SYSTEM PRACTICES
     BSP 365-400-001 - Satellite Communications
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

    "collect": """
NAME
     collect - Collect call services and billing verification

SYNOPSIS
     collect [process|verify|statistics] [call-record]

DESCRIPTION
     Process collect call requests including call setup, billing party
     verification, and charge collection for operator-assisted collect
     calls through the Traffic Service Position System.

OPTIONS
     process         Process incoming collect call requests
     verify          Verify billing party acceptance
     statistics      Collect call volume and revenue statistics

CALL PROCESSING
     Setup:              Establish connection to called party
     Verification:       Confirm billing party acceptance
     Billing:           Apply collect call charges
     Completion:        Complete call or return deposit

EXAMPLES
     collect process CCR-19830315-001    Process collect call
     collect verify 212-555-1234         Verify billing party
     collect statistics monthly          Monthly statistics

SEE ALSO
     operator(1), tsps(1), billing(1)

BELL SYSTEM PRACTICES
     BSP 100-270-001 - Collect Call Procedures
""",


        "capacity": """
NAME
     capacity - Network capacity planning and utilization

SYNOPSIS
     capacity [utilization|forecast|planning|analysis] [network-element]

DESCRIPTION
     Monitor network capacity utilization and perform capacity planning
     for Bell System facilities including trunks, switches, and transmission
     systems to ensure adequate service levels and growth accommodation.

OPTIONS
     utilization     Current capacity utilization monitoring
     forecast        Capacity demand forecasting and projections
     planning        Long-term capacity planning analysis
     analysis        Detailed capacity analysis and recommendations

CAPACITY METRICS
     BUSY HOUR:              Peak traffic measurement period
     ERLANG B:              Blocking probability calculations
     GRADE OF SERVICE:       Acceptable blocking probability
     GROWTH FACTORS:        Traffic growth projections

EXAMPLES
     capacity utilization            Current network utilization
     capacity forecast annual        Annual growth projections
     capacity planning NYC-REGION    Regional capacity planning

SEE ALSO
     traffic(1), routing(1), tnds(1), netplan(1)

BELL SYSTEM PRACTICES
     BSP 100-800-001 - Capacity Planning Procedures
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

    "dbquery": """
NAME
     dbquery - Database query and management operations

SYNOPSIS
     dbquery [select|update|report|maintenance] [table|query]

DESCRIPTION
     Access and manage Bell System databases including customer records,
     equipment inventories, billing data, and operational information
     through structured query interfaces and reporting systems.

OPTIONS
     select          Execute database queries and data retrieval
     update          Update database records and information
     report          Generate standard and custom reports
     maintenance     Database maintenance and optimization

DATABASE SYSTEMS
     CUSTOMER RECORDS:       Customer information and service data
     EQUIPMENT INVENTORY:    Hardware and facility databases
     BILLING DATA:          Call records and billing information
     OPERATIONAL DATA:      Traffic, performance, and status data

EXAMPLES
     dbquery select customer 2125551234  Query customer record
     dbquery report monthly-traffic      Generate traffic report
     dbquery maintenance optimize        Database optimization

SEE ALSO
     custdb(1), billing(1), service(1)

BELL SYSTEM PRACTICES
     BSP 230-100-001 - Database Management Procedures
""",

    "custdb": """
NAME
     custdb - Customer database operations and analytics

SYNOPSIS
     custdb [lookup|update|service|billing] [customer-number]

DESCRIPTION
     Manage customer database operations including account information,
     service records, billing history, and customer service interactions
     for Bell System residential and business customers.

OPTIONS
     lookup          Search and retrieve customer information
     update          Update customer records and service data
     service         Customer service history and interactions
     billing         Customer billing and payment information

CUSTOMER DATA
     ACCOUNT INFORMATION:    Name, address, service location
     SERVICE RECORDS:        Telephone numbers, service types
     BILLING HISTORY:        Payment records, service charges
     SERVICE HISTORY:        Installation, repairs, modifications

EXAMPLES
     custdb lookup 2125551234            Search customer record
     custdb update service-address       Update service location
     custdb billing payment-history      Review billing history

SEE ALSO
     dbquery(1), billing(1), service(1), directory(1)

BELL SYSTEM PRACTICES
     BSP 230-200-001 - Customer Records Management
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

    "provision": """
NAME
     provision - Service provisioning and installation management

SYNOPSIS
     provision [circuit|equipment|testing|activation] [order-id]

DESCRIPTION
     Coordinate service provisioning activities including circuit assignment,
     equipment installation, testing procedures, and service activation
     for Bell System customer services and special circuits.

OPTIONS
     circuit         Circuit assignment and path provisioning
     equipment       Equipment installation and configuration
     testing         Pre-service testing and verification
     activation      Service activation and customer notification

PROVISIONING PHASES
     DESIGN:                 Circuit design and facility assignment
     INSTALLATION:           Physical installation and connection
     TESTING:               Pre-service testing and verification
     ACTIVATION:            Service turn-up and customer notification

EXAMPLES
     provision circuit DS-NYC-001        Provision data circuit
     provision equipment PBX-INSTALL     Equipment installation
     provision testing verify-service    Pre-service testing

SEE ALSO
     service(1), sarts(1), testboard(1), custdb(1)

BELL SYSTEM PRACTICES
     BSP 100-650-001 - Service Provisioning Procedures
""",

    "analysis": """
NAME
     analysis - Advanced network analysis and modeling

SYNOPSIS
     analysis [performance|traffic|economic|reliability] [scope]

DESCRIPTION
     Perform advanced analysis of Bell System network performance including
     traffic modeling, economic analysis, reliability studies, and
     optimization recommendations for network operations and planning.

OPTIONS
     performance     Network performance analysis and optimization
     traffic         Traffic pattern analysis and modeling
     economic        Economic analysis and cost optimization
     reliability     Reliability analysis and improvement studies

ANALYSIS TYPES
     QUEUING THEORY:         Traffic flow and blocking analysis
     ECONOMIC MODELING:      Cost-benefit and investment analysis
     RELIABILITY STUDIES:    System availability and redundancy
     OPTIMIZATION:          Performance and efficiency improvement

EXAMPLES
     analysis performance NYC-REGION     Regional performance study
     analysis traffic busy-hour          Peak hour analysis
     analysis economic cost-benefit      Investment analysis

SEE ALSO
     tnds(1), capacity(1), netplan(1), traffic(1)

BELL SYSTEM PRACTICES
     BSP 100-950-001 - Network Analysis Procedures
""",

    "netdata": """
NAME
     netdata - Network data collection and processing

SYNOPSIS
     netdata [collect|process|archive|export] [data-type]

DESCRIPTION
     Collect and process network operational data including traffic
     measurements, performance statistics, equipment status, and
     billing records for analysis, reporting, and archive purposes.

OPTIONS
     collect         Initiate data collection from network elements
     process         Process and validate collected data
     archive         Archive data for long-term storage
     export          Export data for external analysis

DATA TYPES
     TRAFFIC DATA:           Call volume and usage measurements
     PERFORMANCE DATA:       System performance and quality metrics
     BILLING DATA:          Call records and revenue information
     STATUS DATA:           Equipment and facility status information

EXAMPLES
     netdata collect traffic-daily       Collect daily traffic data
     netdata process billing-records     Process billing information
     netdata export performance-monthly  Export performance data

SEE ALSO
     tnds(1), analysis(1), dbquery(1)

BELL SYSTEM PRACTICES
     BSP 100-905-200 - Data Collection and Processing
""",

    "ls": """
NAME
     ls - list directory contents

SYNOPSIS
     ls [-acdilrstu] [name...]

DESCRIPTION
     List contents of directories on the Bell System UNIX workstation.
     For each directory argument, ls lists the contents; for each file
     argument, ls repeats its name and any other information requested.

OPTIONS
     -a              List all entries including those beginning with '.'
     -c              Use time of last modification of the inode
     -d              List directories themselves, not their contents
     -i              Print inode number for each file
     -l              List in long format with permissions and details
     -r              Reverse the order of sort
     -s              Give size in blocks for each entry
     -t              Sort by time modified instead of name
     -u              Use time of last access instead of modification

EXAMPLES
     ls                              List current directory
     ls -la /usr/bell                List Bell System directory with details
     ls -t *.log                     List log files by modification time

SEE ALSO
     pwd(1), cd(1), file(1)

UNIX V7 PROGRAMMER'S MANUAL
     ls(1) - January 1979
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

    "western": """
NAME
     western - Western Electric equipment specifications

SYNOPSIS
     western [equipment|specs|manual] [model-number]

DESCRIPTION
     Access Western Electric equipment specifications, installation manuals,
     and technical documentation for Bell System equipment manufactured
     by Western Electric Company, the manufacturing arm of Bell System.

OPTIONS
     equipment       List available Western Electric equipment
     specs           Display technical specifications
     manual          Access installation and maintenance manuals

EQUIPMENT CATEGORIES
     SWITCHING:              Electronic and electromechanical switches
     TRANSMISSION:           Carrier systems and transmission equipment
     STATION APPARATUS:      Telephone sets and customer equipment
     PROTECTION:            Power and environmental protection systems

EXAMPLES
     western equipment switching     List switching equipment
     western specs 5ESS              5ESS switch specifications
     western manual T1-CARRIER       T1 carrier manual

SEE ALSO
     5ess(1), 3a(1), t1carrier(1), equipment(1)

BELL SYSTEM PRACTICES
     BSP 000-100-001 - Western Electric Equipment Catalog
""",

    "coer": """
NAME
     coer - Central Office Equipment Reports

SYNOPSIS
     coer [inventory|status|maintenance|reports] [equipment-type]

DESCRIPTION
     Generate and manage Central Office Equipment Reports (COER) for
     tracking Bell System equipment inventory, status, maintenance
     schedules, and operational reports for central office facilities.

OPTIONS
     inventory       Equipment inventory reports
     status          Current equipment status reports
     maintenance     Maintenance scheduling and tracking
     reports         Generate standard COER reports

REPORT TYPES
     EQUIPMENT INVENTORY:    Complete equipment lists and specifications
     STATUS REPORTS:         Operational status and performance
     MAINTENANCE LOGS:       Scheduled and emergency maintenance records
     UTILIZATION REPORTS:    Equipment usage and capacity analysis

EXAMPLES
     coer inventory switching        Switching equipment inventory
     coer status NYC-CO-14           Central office status report
     coer maintenance weekly         Weekly maintenance schedule

SEE ALSO
     western(1), lmos(1), alarm(1)

BELL SYSTEM PRACTICES
     BSP 069-200-001 - Central Office Equipment Reporting
""",


        "trace": """
NAME
     trace - Call tracing and routing analysis

SYNOPSIS
     trace [call|route|path|billing] [call-identifier]

DESCRIPTION
     Trace call routing paths through the Bell System network for
     billing verification, network analysis, and trouble resolution.
     Provides detailed call path information and routing decisions.

OPTIONS
     call            Trace specific call routing and path
     route           Analyze routing decisions and alternatives
     path            Display complete network path information
     billing         Verify billing accuracy for traced calls

TRACE INFORMATION
     ORIGINATING OFFICE:     Call origination point and equipment
     ROUTING DECISIONS:      Switching and routing choices made
     TRANSMISSION PATH:      Facilities used for call completion
     TERMINATING OFFICE:     Call destination and completion details

EXAMPLES
     trace call CALL-19830315-001    Trace specific call
     trace route NYC-LAX             Analyze routing path
     trace billing disputed-call     Verify billing accuracy

SEE ALSO
     routing(1), billing(1), toll(1)

BELL SYSTEM PRACTICES
     BSP 100-500-001 - Call Tracing Procedures
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
     handoff - Authentic Bell System shift handoff procedures

SYNOPSIS
     handoff [briefing|status|issues|turnover] [shift]

DESCRIPTION
     Manage Bell System shift handoff procedures including status
     briefings, outstanding issues, equipment conditions, and
     operational continuity between shifts for 24/7 operations.

OPTIONS
     briefing        Generate shift briefing information
     status          Current operational status summary
     issues          Outstanding issues and problem reports
     turnover        Complete shift turnover documentation

HANDOFF ELEMENTS
     EQUIPMENT STATUS:       All systems operational status
     OUTSTANDING ISSUES:     Active tickets and problem reports
     MAINTENANCE ACTIVITIES: Scheduled and ongoing maintenance
     SERVICE IMPACTS:        Customer affecting conditions

EXAMPLES
     handoff briefing incoming       Generate incoming shift briefing
     handoff status all-systems      Complete operational status
     handoff issues priority         Priority issue summary

SEE ALSO
     events(1), status(1), ticket(1)

BELL SYSTEM PRACTICES
     BSP 100-025-001 - Shift Handoff Procedures
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

    "training": """
NAME
     training - Bell System training programs and procedures

SYNOPSIS
     training [programs|schedule|progress|certification] [employee-id]

DESCRIPTION
     Manage Bell System training programs including technical training,
     operational procedures, safety programs, and certification
     requirements for Bell System operations personnel.

OPTIONS
     programs        List available training programs
     schedule        Training schedules and availability
     progress        Individual training progress tracking
     certification   Certification requirements and status

TRAINING CATEGORIES
     TECHNICAL TRAINING:     Equipment and system operation
     OPERATIONAL PROCEDURES: Bell System Practices and procedures
     SAFETY TRAINING:        Workplace safety and emergency procedures
     MANAGEMENT TRAINING:    Supervisory and management development

EXAMPLES
     training programs switching     Switching system training
     training schedule quarterly     Quarterly training schedule
     training progress EMP-1234      Employee training status

SEE ALSO
     bsp(1), operator(1), procedures(1)

BELL SYSTEM PRACTICES
     BSP 000-200-001 - Training Program Administration
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

    "nroff": """
NAME
     nroff - Text formatting and document preparation

SYNOPSIS
     nroff [-options] [files...]

DESCRIPTION
     Format text documents for Bell System documentation including
     technical manuals, operational procedures, and administrative
     reports. Part of the Bell System document preparation system.

OPTIONS
     -ms             Use manuscript macro package
     -mm             Use memorandum macro package
     -man            Use manual page macro package

DOCUMENT TYPES
     TECHNICAL MANUALS:      Equipment specifications and procedures
     OPERATIONAL PROCEDURES: Bell System Practices documentation
     ADMINISTRATIVE REPORTS: Management and statistical reports
     CORRESPONDENCE:         Business letters and memoranda

EXAMPLES
     nroff -ms technical_spec.ms     Format technical specification
     nroff -man command.1            Format manual page
     nroff procedure.txt             Format procedure document

SEE ALSO
     troff(1), tbl(1), eqn(1), pic(1)

UNIX V7 PROGRAMMER'S MANUAL
     nroff(1) - January 1979
""",

    "troff": """
NAME
     troff - Typesetting and document formatting

SYNOPSIS
     troff [-options] [files...]

DESCRIPTION
     Typeset high-quality documents for Bell System publications
     including technical documentation, engineering reports, and
     formal correspondence requiring professional presentation.

OPTIONS
     -ms             Use manuscript macro package
     -mm             Use memorandum macro package
     -Tdevice        Specify output device type

TYPESETTING FEATURES
     PROPORTIONAL FONTS:     Multiple typefaces and sizes
     MATHEMATICAL NOTATION:  Equations and technical symbols
     GRAPHICS INTEGRATION:   Diagrams and illustrations
     PAGE LAYOUT:           Professional document formatting

EXAMPLES
     troff -ms -Tcat report.ms       Typeset technical report
     troff -mm memo.mm               Format memorandum
     troff engineering_spec.tr       Typeset specification

SEE ALSO
     nroff(1), tbl(1), eqn(1), pic(1)

UNIX V7 PROGRAMMER'S MANUAL
     troff(1) - January 1979
""",

    "tbl": """
NAME
     tbl - Table formatting preprocessor

SYNOPSIS
     tbl [files...] | nroff
     tbl [files...] | troff

DESCRIPTION
     Format tables for Bell System documentation including technical
     specifications, performance data, equipment lists, and statistical
     reports requiring structured tabular presentation.

TABLE FEATURES
     COLUMN ALIGNMENT:       Left, right, center, numeric alignment
     SPANNING:              Column and row spanning capabilities
     BOXING:                Table borders and grid lines
     FORMATTING:            Text formatting within table cells

EXAMPLES
     tbl equipment_list.tbl | nroff  Format equipment table
     tbl performance.tbl | troff     Typeset performance data
     tbl specifications.tbl          Process specification table

SEE ALSO
     nroff(1), troff(1), eqn(1), pic(1)

UNIX V7 PROGRAMMER'S MANUAL
     tbl(1) - January 1979
""",

    "eqn": """
NAME
     eqn - Mathematical equation formatting

SYNOPSIS
     eqn [files...] | nroff
     eqn [files...] | troff

DESCRIPTION
     Format mathematical equations and technical formulas for Bell System
     engineering documentation including transmission calculations,
     traffic engineering formulas, and technical specifications.

EQUATION FEATURES
     MATHEMATICAL NOTATION:  Fractions, exponents, subscripts
     SPECIAL SYMBOLS:       Greek letters, mathematical operators
     ALIGNMENT:             Multi-line equation alignment
     SIZING:               Automatic size adjustment

EXAMPLES
     eqn formulas.eqn | troff        Format engineering formulas
     eqn calculations.eqn | nroff    Process traffic calculations
     eqn specifications.eqn          Format technical equations

SEE ALSO
     nroff(1), troff(1), tbl(1), pic(1)

UNIX V7 PROGRAMMER'S MANUAL
     eqn(1) - January 1979
""",

    "pic": """
NAME
     pic - Picture drawing language and graphics

SYNOPSIS
     pic [files...] | nroff
     pic [files...] | troff

DESCRIPTION
     Create technical diagrams and illustrations for Bell System
     documentation including network diagrams, equipment layouts,
     circuit schematics, and organizational charts.

GRAPHICS FEATURES
     GEOMETRIC SHAPES:       Boxes, circles, lines, arrows
     NETWORK DIAGRAMS:       Switching and transmission layouts
     FLOWCHARTS:            Process and procedure diagrams
     SCALING:              Automatic sizing and positioning

EXAMPLES
     pic network_diagram.pic | troff    Create network diagram
     pic circuit_layout.pic | nroff     Format circuit diagram
     pic organizational.pic             Process org chart

SEE ALSO
     nroff(1), troff(1), tbl(1), eqn(1)

UNIX V7 PROGRAMMER'S MANUAL
     pic(1) - January 1979
""",

    "refer": """
NAME
     refer - Bibliography and reference management

SYNOPSIS
     refer [files...] | nroff
     refer [files...] | troff

DESCRIPTION
     Manage bibliographic references and citations for Bell System
     technical documentation including references to Bell System
     Practices, technical journals, and engineering specifications.

REFERENCE FEATURES
     CITATION FORMATTING:    Automatic citation numbering
     BIBLIOGRAPHY:          Reference list generation
     DATABASE:              Reference database management
     CROSS-REFERENCING:     Internal document references

EXAMPLES
     refer technical_paper.ref | troff  Process technical paper
     refer manual.ref | nroff           Format reference manual
     refer bibliography.ref             Process bibliography

SEE ALSO
     nroff(1), troff(1), lookbib(1)

UNIX V7 PROGRAMMER'S MANUAL
     refer(1) - January 1979
""",

    "pwb": """
NAME
     pwb - Programmer's Workbench operations

SYNOPSIS
     pwb [command] [options]

DESCRIPTION
     Access Programmer's Workbench (PWB) system for Bell System
     software development and maintenance including system programming,
     application development, and software version control.

PWB FEATURES
     VERSION CONTROL:        Source code management and tracking
     DEVELOPMENT TOOLS:      Compilers, debuggers, utilities
     PROJECT MANAGEMENT:     Software project coordination
     DOCUMENTATION:         Technical documentation tools

EXAMPLES
     pwb checkout source.c           Check out source file
     pwb delta modifications         Record code changes
     pwb make project               Build software project

SEE ALSO
     cc(1), make(1), sccs(1)

PROGRAMMER'S WORKBENCH
     PWB/UNIX - Bell Laboratories
""",

    "rje": """
NAME
     rje - Remote Job Entry system

SYNOPSIS
     rje [submit|status|output] [job-parameters]

DESCRIPTION
     Submit and manage batch processing jobs through the Remote Job Entry
     system for Bell System data processing including billing calculations,
     traffic analysis, and network planning computations.

RJE FEATURES
     JOB SUBMISSION:         Batch job scheduling and execution
     STATUS MONITORING:      Job progress and completion tracking
     OUTPUT RETRIEVAL:       Job results and report generation
     PRIORITY SCHEDULING:    Job priority and resource allocation

EXAMPLES
     rje submit billing_run.jcl      Submit billing job
     rje status JOB-19830315-001     Check job status
     rje output traffic_analysis     Retrieve job output

SEE ALSO
     batch(1), at(1), cron(1)

BELL SYSTEM DATA PROCESSING
     RJE System - Bell System Computing
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
}
