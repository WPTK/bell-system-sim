"""
Transmission carrier systems: T-carrier, L-carrier, multiplex, radio.
"""

from typing import (
    List,
)
from ..data.carrier import (
    L3_LINE_ASSEMBLY,
    L_CARRIER_SYSTEMS,
    MULTIPLEX_HIERARCHY,
    MULTIPLEX_PILOTS_KHZ,
)


from .session import SessionState


class CarrierCommands(SessionState):
    """
    Transmission carrier systems: T-carrier, L-carrier, multiplex, radio.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _format_carrier_bands(self) -> str:
        """
        Render the L-carrier line bands and the multiplex hierarchy.

        The two are distinct and were previously conflated: 564-3084 kHz is
        the basic mastergroup, an assembly band, not the L4 line spectrum.
        """
        lines = ["  LINE SPECTRUM TRANSMITTED ON COAXIAL"]
        for code, system in L_CARRIER_SYSTEMS.items():
            lines.append(
                f"    {code:<4} {system.line_band():<26}"
                f"{system.channels:>6,} channels  "
                f"{system.repeater_spacing_miles:g} mi repeaters"
            )
        lines.append("")
        lines.append("  MULTIPLEX ASSEMBLY HIERARCHY")
        for level in MULTIPLEX_HIERARCHY:
            pilot = MULTIPLEX_PILOTS_KHZ.get(level.name)
            pilot_text = f"pilot {pilot:,.2f} kHz" if pilot else ""
            lines.append(
                f"    {level.name:<26}{level.band():<22}"
                f"{level.channels:>5,} ch  {pilot_text}"
            )
        lines.append("")
        lines.append("  L3 LINE SIGNAL ASSEMBLY (3 mastergroups + 1 supergroup = 1,860)")
        for name, low, high in L3_LINE_ASSEMBLY:
            lines.append(f"    {name:<20}{low:>7,.0f} - {high:>7,.0f} kHz")
        return "\n".join(lines)
    def cmd_t1carrier(self, args: List[str]) -> str:
        """T1 Digital Carrier System Operations"""
        if not args:
            return """T1 Digital Carrier System Management
Bell System Digital Transmission Hierarchy

Available Commands:
  t1carrier status         - System overview and DS-1 circuits
  t1carrier test <ds1>     - Digital circuit testing procedures
  t1carrier multiplex     - Digital multiplexing hierarchy
  t1carrier regenerator   - Regenerator status and maintenance
  t1carrier sync          - Timing and synchronization
  t1carrier performance   - Performance monitoring and analysis
  t1carrier alarm         - Alarm status and error analysis
  t1carrier provision     - Circuit provisioning procedures

Current Digital Hierarchy Status:
  DS-1 Circuits (1.544 Mbps):     2,347 active
  DS-2 Circuits (6.312 Mbps):     156 active
  DS-3 Circuits (44.736 Mbps):    23 active

Performance Summary:
  Bit Error Rate:              < 10^-9 (all circuits)
  Slip Rate:                   < 1 per day
  Availability:                99.95% (monthly average)

Reference: Western Electric T1 Carrier System Technical Manual"""

        elif args[0] == "status":
            return """T1 Digital Carrier System Status
November 14, 1983 07:45:30

DS-1 Circuit Status (1.544 Mbps):
  DS1-NYC-WAS-001:            ACTIVE    BER: < 10^-9    No alarms
  DS1-NYC-BOS-002:            ACTIVE    BER: 2.3x10^-8  Minor alarm (B8ZS)
  DS1-WAS-ATL-003:            ACTIVE    BER: < 10^-9    No alarms
  DS1-CHI-DET-004:            TESTING   Loop-back test in progress
  DS1-LAX-SFO-005:            ACTIVE    BER: < 10^-9    No alarms

Digital Signal Hierarchy:
  DS-0 (64 kbps):             Voice channel fundamental rate
  DS-1 (1.544 Mbps):          24 DS-0 channels + framing
  DS-2 (6.312 Mbps):          4 DS-1 signals multiplexed
  DS-3 (44.736 Mbps):         7 DS-2 signals multiplexed

M12 Multiplexer Status:
  M12-NYC-001:                OPERATIONAL (4 DS-1 → 1 DS-2)
  M12-BOS-002:                OPERATIONAL (4 DS-1 → 1 DS-2)
  M12-WAS-003:                MAINTENANCE (Scheduled 14:30)

M23 Multiplexer Status:
  M23-NYC-001:                OPERATIONAL (7 DS-2 → 1 DS-3)
  M23-CHI-001:                OPERATIONAL (7 DS-2 → 1 DS-3)

Regenerator Status:
  Line Regenerators:          1,247 units operational
  Terminal Equipment:         156 units operational
  Timing Sources:             All synchronized to LORAN-C

Performance Monitoring:
  Error Seconds (ES):         < 0.01% (excellent)
  Severely Errored Seconds:   0 events (24-hour period)
  Unavailable Seconds:        < 10 seconds total"""

        elif args[0] == "test" and len(args) > 1:
            circuit = args[1].upper()
            return f"""T1 Digital Circuit Test: {circuit}
Test Sequence Initiated: November 14, 1983 07:46:00

Circuit Configuration:
  Circuit Type:               DS-1 (1.544 Mbps)
  Line Code:                  B8ZS (Bipolar 8-Zero Substitution)
  Framing Format:             Extended Superframe (ESF)
  Interface:                  DSX-1 cross-connect

Test Procedures:
  1. Loop-back Test:          [████████████████████] COMPLETE
     Near-end loop:           PASS - No errors detected
     Far-end loop:            PASS - Pattern integrity verified

  2. Bit Error Rate Test:     [████████████████████] COMPLETE
     Test Pattern:            2^15-1 PRBS (Pseudo Random)
     Duration:                15 minutes
     BER Result:              < 10^-9 (Excellent)

  3. Jitter Measurement:      [████████████████████] COMPLETE
     Peak-to-peak jitter:     0.05 UI (within spec < 0.28 UI)
     RMS jitter:              0.02 UI (excellent)

  4. Signal Level Test:       [████████████████████] COMPLETE
     Transmit level:          +12.0 dBm (nominal +13 dBm)
     Receive level:           -8.5 dBm (nominal -7.5 dBm)

  5. Alarm Generation Test:   [██████████████░░░░░] IN PROGRESS
     AIS insertion:           Testing alarm propagation
     Yellow alarm:            Verifying upstream notification

Test Results Summary:
  Overall Performance:        EXCELLENT
  Circuit Quality:            Meets all specifications
  Recommended Action:         Return to service

Next Test Scheduled:         November 21, 1983 02:00"""

        elif args[0] == "multiplex":
            return """Digital Multiplexing Hierarchy
Bell System Digital Signal Standards

Digital Signal Levels:
  DS-0:    64 kbps     (Voice channel - 8-bit PCM, 8 kHz sampling)
  DS-1:    1.544 Mbps  (24 DS-0 + 8 kbps framing)
  DS-2:    6.312 Mbps  (4 DS-1 + stuffing bits)
  DS-3:    44.736 Mbps (7 DS-2 + overhead)
  DS-4:    274.176 Mbps (6 DS-3 + overhead) [Future implementation]

M12 Multiplexer Operations:
  Function:                   Combine 4 DS-1 signals into 1 DS-2
  Bit Stuffing:               Asynchronous multiplexing
  Stuff Ratio:                Average 1.2% overhead

  Active M12 Units:
    M12-NYC-001:              Input: 4 DS-1, Output: DS-2 #47
    M12-BOS-002:              Input: 4 DS-1, Output: DS-2 #48
    M12-WAS-003:              Input: 4 DS-1, Output: DS-2 #49

M23 Multiplexer Operations:
  Function:                   Combine 7 DS-2 signals into 1 DS-3
  Bit Stuffing:               Positive/negative stuffing
  Stuff Ratio:                Average 2.1% overhead

  Active M23 Units:
    M23-NYC-001:              Input: 7 DS-2, Output: DS-3 #12
    M23-CHI-001:              Input: 7 DS-2, Output: DS-3 #13

Multiplexing Performance:
  Stuff Jitter:               < 0.1 UI (all multiplexers)
  Pattern Jitter:             < 0.05 UI (excellent)
  Frequency Accuracy:         ±32 ppm (within ±50 ppm spec)

Synchronization:
  Master Clock:               LORAN-C referenced
  Clock Accuracy:             ±1 x 10^-11 (cesium standard)
  Distribution:               Stratum 1 → Stratum 2 → Stratum 3

Use 't1carrier sync' for detailed timing information"""

        elif args[0] == "regenerator":
            return """T1 Digital Regenerator System
Line and Terminal Equipment Status

Regenerator Functions:
  Signal Detection:           Extract timing and data
  Retiming:                   Eliminate accumulated jitter
  Reshaping:                  Restore pulse amplitude
  Regeneration:               Output clean digital signal

Line Regenerator Status:
  REG-NYC-WAS-001-R47:       OPERATIONAL - Signal: -18.2 dBm
  REG-NYC-WAS-001-R48:       OPERATIONAL - Signal: -19.1 dBm
  REG-NYC-BOS-002-R23:       OPERATIONAL - Signal: -17.8 dBm
  REG-WAS-ATL-003-R56:       MAINTENANCE - Scheduled PM

Performance Parameters:
  Input Sensitivity:          -36 dBm (minimum detectable)
  Output Level:               +13 dBm (nominal DS-1 level)
  Jitter Accumulation:        < 0.01 UI per regenerator
  Bit Error Rate:             < 10^-12 (regenerator contribution)

Terminal Equipment:
  Channel Service Unit (CSU): 156 units operational
  Data Service Unit (DSU):    89 units operational
  Office Channel Unit (OCU):  234 units operational

Regenerator Spacing:
  T1 Cable (22 AWG):          6,000 feet maximum
  T1 Cable (19 AWG):          9,000 feet maximum
  Environmental Limits:       -40°F to +140°F operating

Maintenance Status:
  Last PM Cycle:              47 regenerators completed
  Performance Degradation:    0 units flagged
  Spare Units Available:      23 units (central stock)

Power Systems:
  -130V DC Distribution:      NORMAL (all regenerators)
  Current Consumption:        Average 47 mA per unit
  Alarm Monitoring:           Remote monitoring active

Testing Procedures:
  Monthly:                    Signal level verification
  Quarterly:                  BER performance testing
  Annually:                   Environmental stress testing"""

        elif args[0] == "sync":
            return """T1 Network Synchronization
Digital Timing Hierarchy and Distribution

Network Timing Standards:
  Stratum 1:                  ±1 x 10^-11 accuracy (cesium)
  Stratum 2:                  ±1.6 x 10^-8 accuracy
  Stratum 3:                  ±4.6 x 10^-6 accuracy
  Stratum 4:                  ±32 x 10^-6 accuracy

Current Synchronization Status:
  Primary Reference:          LORAN-C Navigation System
  Secondary Reference:        Cesium beam standard (backup)
  Distribution Method:        Through digital hierarchy

Timing Distribution:
  Master Clock (Stratum 1):   AT&T Network Operations Center
    Location:                 Hillsboro, New Jersey
    Accuracy:                 ±1 x 10^-11
    Distribution:             Via DS-1 timing signals

  Regional Clocks (Stratum 2):
    NYC Regional Center:      Synchronized, tracking normal
    CHI Regional Center:      Synchronized, tracking normal
    LAX Regional Center:      Synchronized, tracking normal

  Local Office Clocks (Stratum 3):
    NYC Central Office:       Synchronized, ±2.1 x 10^-6 drift
    BOS Central Office:       Synchronized, ±1.8 x 10^-6 drift
    WAS Central Office:       Synchronized, ±3.2 x 10^-6 drift

Synchronization Methods:
  Through-Timing:             DS-1 signals carry timing
  External Timing:            Separate timing distribution
  Loop Timing:                Terminal derives from line

Performance Monitoring:
  Slip Events (24-hour):      0 controlled slips
  Timing Errors:              No events detected
  Clock Drift:                All within specifications

Slip Control:
  Controlled Slip Rate:       < 1 slip per 72 days (target)
  Slip Buffer Depth:          ±2 frame positions
  Slip Indication:            Yellow alarm generation

LORAN-C Reception:
  Signal Strength:            40 dB above noise floor
  Time Difference:            Tracking within 0.1 microsecond
  Chain Selection:            Northeast U.S. Chain (9960)

Backup Timing:
  Cesium Standard:            Available (automatic switchover)
  GPS Timing:                 Under evaluation [Future]
  Rubidium Standards:         Local office backup"""

        else:
            return f"t1carrier: unknown option '{args[0]}'\nUse 't1carrier' for available commands"
    def cmd_lcarrier(self, args: List[str]) -> str:
        """L-Carrier Coaxial Cable System Operations"""
        if not args:
            return """L-Carrier Coaxial Cable System Management
Bell System Analog Long-Haul Transmission

Available Commands:
  lcarrier status          - System overview and route status
  lcarrier test <route>    - Coaxial cable testing procedures
  lcarrier repeater        - Repeater status and maintenance
  lcarrier equalizer       - Equalization and frequency response
  lcarrier pilot           - Pilot tone monitoring and control
  lcarrier temperature     - Cable temperature monitoring
  lcarrier fault           - Fault location and analysis

Current L-Carrier Routes:
  L3 Systems (1860 circuits):     23 routes operational
  L4 Systems (3600 circuits):     47 routes operational
  L5 Systems (10800 circuits):    12 routes operational

Performance Summary:
  Noise Level:                43 dBrnC (excellent)
  Frequency Response:         ±0.5 dB (within spec)
  Cross-talk:                 < -65 dB (all systems)

Reference: Western Electric L-Carrier Technical Manual"""

        elif args[0] == "status":
            return """L-Carrier Coaxial Cable System Status
November 14, 1983 07:45:30

L3 Coaxial Systems (1860 voice circuits):
  L3-NYC-PHL-001:             OPERATIONAL - 1847 circuits active
    Pilot Level:              -20.0 dBm0 (nominal -20 dBm0)
    Noise Level:              42.8 dBrnC (excellent)
    Temperature:              68°F (normal range)

  L3-BOS-NYC-002:             OPERATIONAL - 1854 circuits active
    Pilot Level:              -19.8 dBm0 (nominal -20 dBm0)
    Noise Level:              43.2 dBrnC (good)
    Temperature:              71°F (normal range)

L4 Coaxial Systems (3600 voice circuits):
  L4-NYC-WAS-001:             OPERATIONAL - 3587 circuits active
    Pilot Level:              -20.1 dBm0 (nominal -20 dBm0)
    Noise Level:              41.5 dBrnC (excellent)
    Repeater Status:          47 repeaters operational

  L4-CHI-STL-002:             OPERATIONAL - 3594 circuits active
    Pilot Level:              -19.9 dBm0 (nominal -20 dBm0)
    Noise Level:              42.1 dBrnC (excellent)
    Repeater Status:          39 repeaters operational

L5 Coaxial Systems (10800 voice circuits):
  L5-NYC-CHI-001:             OPERATIONAL - 10,756 circuits active
    Pilot Level:              -20.0 dBm0 (nominal -20 dBm0)
    Noise Level:              40.2 dBrnC (superior)
    Repeater Status:          156 repeaters operational
    Cable Length:             789.3 miles total

System Performance:
  Overall Availability:       99.98% (monthly average)
  Mean Time to Repair:        3.7 hours (system outages)
  Preventive Maintenance:     Schedule compliance 97%

Cable Plant Status:
  Cable Pressure:             All sections pressurized (8.5 psi)
  Moisture Detection:         No moisture alarms
  Sheath Current:             Normal (< 10 mA all cables)

Frequency Allocation:
""" + self._format_carrier_bands()

        elif args[0] == "repeater":
            return """L-Carrier Repeater Status and Operations
Analog Amplification and Equalization

Repeater Functions:
  Amplification:              Restore signal level
  Equalization:               Compensate cable loss
  Regulation:                 Maintain constant output
  Monitoring:                 Performance surveillance

L4 Repeater Status (NYC-WAS Route):
  REP-L4-001 (Mile 23.4):    OPERATIONAL
    Input Level:              -43.2 dBm (pilot tone)
    Output Level:             +7.8 dBm (pilot tone)
    Gain:                     51.0 dB (nominal 51 dB)
    Temperature:              73°F (normal)

  REP-L4-002 (Mile 46.8):    OPERATIONAL
    Input Level:              -42.8 dBm (pilot tone)
    Output Level:             +8.1 dBm (pilot tone)
    Gain:                     50.9 dB (nominal 51 dB)
    Temperature:              69°F (normal)

L5 Repeater Status (NYC-CHI Route):
  REP-L5-001 (Mile 12.1):    OPERATIONAL
    Input Level:              -41.5 dBm (pilot tone)
    Output Level:             +8.5 dBm (pilot tone)
    Gain:                     50.0 dB (nominal 50 dB)
    Temperature:              71°F (normal)
    AGC Range:                ±3 dB (automatic gain control)

Repeater Spacing:
  L3 Systems:                 4 miles (approximate)
  L4 Systems:                 2 miles (approximate)
  L5 Systems:                 1 mile (approximate)

Automatic Gain Control:
  Pilot Tone Frequency:
    L3: 552 kHz               Reference level -20 dBm0
    L4: 1116 kHz              Reference level -20 dBm0
    L5: 564 kHz               Reference level -20 dBm0

  AGC Response Time:          < 100 milliseconds
  Gain Tracking:              ±0.1 dB (temperature compensated)

Maintenance Procedures:
  Monthly Gain Checks:        Scheduled via pilot tone
  Quarterly Alignments:       Frequency response verification
  Annual Overhaul:            Component replacement cycle

Power Systems:
  Remote Powering:            -130V DC via cable center
  Current Consumption:        Average 2.3 A per repeater
  Power Feeding:              From terminal equipment

Environmental Monitoring:
  Temperature Range:          -40°F to +140°F operating
  Humidity:                   0-95% non-condensing
  Vibration:                  MIL-STD-810 compliance"""

        elif args[0] == "test" and len(args) > 1:
            route = args[1].upper()
            return f"""L-Carrier System Test: {route}
Test Sequence Initiated: November 14, 1983 07:46:15

System Configuration:
  Route Type:                 L4 Coaxial Cable System
  Circuit Capacity:           3600 voice channels
  Frequency Range:            564 kHz - 3084 kHz
  Cable Type:                 0.375" coax, foam dielectric

Test Procedures:
  1. Pilot Tone Check:        [████████████████████] COMPLETE
     564 kHz Pilot:           -19.8 dBm0 (nominal -20.0 dBm0)
     1116 kHz Pilot:          -20.2 dBm0 (nominal -20.0 dBm0)
     Result:                  PASS - Levels within ±0.5 dB

  2. Noise Measurement:       [████████████████████] COMPLETE
     C-Message Weighted:      42.1 dBrnC (excellent)
     3 kHz Flat:              47.3 dBrn (good)
     Impulse Noise:           2 counts/15 min (acceptable)

  3. Frequency Response:      [████████████████████] COMPLETE
     300 Hz - 3400 Hz:        ±0.3 dB variation
     Group Delay:             < 1.5 ms (excellent)
     Envelope Delay:          Within specifications

  4. Cross-talk Test:         [████████████████████] COMPLETE
     Near-end cross-talk:     -67.2 dB (excellent)
     Far-end cross-talk:      -71.5 dB (superior)
     Echo return loss:        -28.4 dB (good)

  5. Repeater Gain Test:      [██████████████░░░░░] IN PROGRESS
     Testing 39 repeaters:    Gain stability ±0.1 dB
     Temperature compensation: Active

Test Results Summary:
  Overall Performance:        EXCELLENT
  All Parameters:             Within specifications
  Recommended Action:         Continue normal service

Next Scheduled Test:         November 28, 1983 02:00"""

        elif args[0] == "pilot":
            return """L-Carrier Pilot Tone System
Automatic Level Control and System Monitoring

Pilot Tone Functions:
  Level Control:              Automatic gain regulation
  System Monitoring:          Performance surveillance
  Fault Detection:            Rapid alarm generation
  Temperature Compensation:   Thermal stability

L3 System Pilot Tones:
  552 kHz Pilot:
    Current Level:            -19.9 dBm0 (nominal -20.0 dBm0)
    Regulation Range:         ±3.0 dB
    Response Time:            < 2 seconds

L4 System Pilot Tones:
  564 kHz Pilot (Group 1):    -20.1 dBm0 (nominal -20.0 dBm0)
  1116 kHz Pilot (Group 2):   -19.8 dBm0 (nominal -20.0 dBm0)
  1620 kHz Pilot (Group 3):   -20.2 dBm0 (nominal -20.0 dBm0)

L5 System Pilot Tones:
  564 kHz Master Pilot:       -20.0 dBm0 (nominal -20.0 dBm0)
  8284 kHz Regulation Pilot:  -20.1 dBm0 (nominal -20.0 dBm0)

Automatic Level Regulation:
  Regulation Accuracy:        ±0.1 dB (short term)
  Temperature Stability:      ±0.3 dB (-40°F to +140°F)
  Frequency Stability:        ±1 Hz (crystal controlled)

Alarm Thresholds:
  Minor Alarm:                ±1.0 dB deviation
  Major Alarm:                ±2.0 dB deviation
  Critical Alarm:             ±3.0 dB deviation (system failure)

Current Alarm Status:
  All Systems:                NO ALARMS
  Regulation Status:          NORMAL
  Pilot Continuity:           VERIFIED

Pilot Tone Monitoring:
  Measurement Interval:       Every 6 seconds
  Data Recording:             15-minute averages
  Trend Analysis:             24-hour performance graphs
  Historical Data:            30-day retention"""

        elif args[0] == "fault":
            return """L-Carrier Fault Location System
Cable Fault Detection and Analysis

Fault Location Methods:
  Time Domain Reflectometry:  Cable impedance analysis
  Pilot Tone Interruption:    Service affecting faults
  Sheath Current Monitoring:  Moisture detection
  Temperature Monitoring:     Thermal anomalies

Recent Fault History:
  No active faults detected   (Last 30 days)

Fault Location Equipment:
  TDR Test Set:               Model WE-810A
    Range:                    0-50 miles
    Resolution:               ±25 feet
    Impedance:                75 ohms (coaxial standard)

  Bridge Measurements:
    Cable Resistance:         0.31 ohms/mile (center conductor)
    Cable Capacitance:        21.5 nF/mile (normal)
    Insulation Resistance:    >1000 megohms/mile

Preventive Monitoring:
  Cable Pressure:             8.5 psi (all sections)
  Moisture Indicators:        Dry gas flow normal
  Temperature Sensors:        47 locations monitored
  Sheath Current:             < 5 mA (all cables)

Historical Fault Analysis:
  Cable Cuts (6 months):      2 events (external damage)
  Moisture Intrusion:         0 events
  Equipment Failures:         3 repeater replacements
  Mean Time to Locate:        1.2 hours (cable faults)
  Mean Time to Repair:        4.7 hours (including splicing)

Fault Response Procedures:
  1. Alarm Reception:         Immediate NOC notification
  2. Remote Testing:          TDR and pilot tone analysis
  3. Dispatch Authorization:  Field crew deployment
  4. Fault Location:          Precise distance measurement
  5. Repair Coordination:     Service restoration priority

Emergency Procedures:
  Service Protection:         Automatic rerouting available
  Backup Facilities:          Microwave protection routes
  Repair Priority:            Based on circuit criticality
  Customer Notification:      Automated for major outages"""

        else:
            return f"lcarrier: unknown option '{args[0]}'\nUse 'lcarrier' for available commands"
    def cmd_multiplex(self, args: List[str]) -> str:
        """Digital Multiplexing Operations and Hierarchy Management"""
        if not args:
            return """Digital Multiplexing Operations
Bell System Digital Signal Hierarchy

Available Commands:
  multiplex status         - Overall multiplexing system status
  multiplex m12            - M12 multiplexer operations (DS-1 to DS-2)
  multiplex m23            - M23 multiplexer operations (DS-2 to DS-3)
  multiplex stuff          - Bit stuffing analysis and control
  multiplex alarm          - Multiplexer alarm status
  multiplex test <unit>    - Multiplexer testing procedures
  multiplex sync           - Synchronization and timing

Digital Signal Hierarchy:
  DS-0:    64 kbps         Voice channel (8-bit PCM)
  DS-1:    1.544 Mbps      24 DS-0 + framing (193 bits/frame)
  DS-2:    6.312 Mbps      4 DS-1 + bit stuffing
  DS-3:    44.736 Mbps     7 DS-2 + overhead

Current Multiplexer Status:
  M12 Units:               23 operational
  M23 Units:               8 operational
  Performance:             All within specifications"""

        elif args[0] == "m12":
            return """M12 Multiplexer Operations
DS-1 to DS-2 Digital Multiplexing

M12 Multiplexer Function:
  Input:                      4 independent DS-1 signals (1.544 Mbps each)
  Output:                     1 DS-2 signal (6.312 Mbps)
  Multiplexing:               Asynchronous (bit stuffing)
  Stuff Ratio:                Nominal 1.15% overhead

Active M12 Units:
  M12-NYC-001:
    Input DS-1 #1:            ACTIVE - 1.5440 Mbps, sync normal
    Input DS-1 #2:            ACTIVE - 1.5441 Mbps, sync normal
    Input DS-1 #3:            ACTIVE - 1.5439 Mbps, sync normal
    Input DS-1 #4:            ACTIVE - 1.5440 Mbps, sync normal
    Output DS-2:              ACTIVE - 6.3120 Mbps
    Stuff Rate:               1.12% (normal)

  M12-BOS-002:
    Input DS-1 #1:            ACTIVE - 1.5441 Mbps, sync normal
    Input DS-1 #2:            ACTIVE - 1.5440 Mbps, sync normal
    Input DS-1 #3:            ACTIVE - 1.5442 Mbps, sync normal
    Input DS-1 #4:            ACTIVE - 1.5439 Mbps, sync normal
    Output DS-2:              ACTIVE - 6.3121 Mbps
    Stuff Rate:               1.14% (normal)

Bit Stuffing Operation:
  Justification:              Positive stuffing only
  Stuff Decision:             Made every 4 input bits
  Stuff Indication:           C-bits indicate stuffing
  Buffer Depth:               ±2 bits (elastic store)

Performance Parameters:
  Jitter Accumulation:        < 0.05 UI (output)
  Frequency Accuracy:         ±20 ppm (all inputs accepted)
  Phase Hits:                 < 1 per hour (excellent)
  Bit Error Rate:             < 10^-9 (multiplexer contribution)

Frame Structure:
  Frame Length:               1176 bits (186.3 μs)
  Overhead Bits:              48 bits per frame (4.08%)
  Payload Capacity:           1128 bits per frame
  Framing Pattern:            F0F1F2F3 sequence

Alarm Conditions:
  Loss of Signal (LOS):       Input DS-1 signal failure
  Out of Frame (OOF):         Frame synchronization lost
  AIS Detection:              All-ones pattern received
  Equipment Failure:          Internal multiplexer fault"""

        elif args[0] == "m23":
            return """M23 Multiplexer Operations
DS-2 to DS-3 Digital Multiplexing

M23 Multiplexer Function:
  Input:                      7 independent DS-2 signals (6.312 Mbps each)
  Output:                     1 DS-3 signal (44.736 Mbps)
  Multiplexing:               Asynchronous (positive/negative stuffing)
  Stuff Ratio:                Nominal 2.05% overhead

Active M23 Units:
  M23-NYC-001:
    Input DS-2 #1:            ACTIVE - 6.3120 Mbps, sync normal
    Input DS-2 #2:            ACTIVE - 6.3121 Mbps, sync normal
    Input DS-2 #3:            ACTIVE - 6.3119 Mbps, sync normal
    Input DS-2 #4:            ACTIVE - 6.3122 Mbps, sync normal
    Input DS-2 #5:            ACTIVE - 6.3120 Mbps, sync normal
    Input DS-2 #6:            ACTIVE - 6.3118 Mbps, sync normal
    Input DS-2 #7:            ACTIVE - 6.3121 Mbps, sync normal
    Output DS-3:              ACTIVE - 44.7360 Mbps
    Stuff Rate:               2.03% (normal)

Bit Stuffing Operation:
  Justification:              Positive and negative stuffing
  Stuff Decision:             Made every 8 input bits
  Stuff Indication:           C-bits and S-bits
  Buffer Management:          ±4 bits elastic store

Advanced Features:
  Stuff Threshold:            Adaptive based on input frequency
  Jitter Reduction:           Phase-locked loop filtering
  Alarm Integration:          Upstream/downstream coordination
  Performance Monitoring:     Real-time BER estimation

Frame Structure:
  Frame Length:               4760 bits (106.4 μs)
  M-Frame Length:             (4 × 4760) = 19,040 bits
  Overhead Allocation:        Framing, stuffing, maintenance
  Payload Efficiency:         97.95% (nominal)

Performance Monitoring:
  Input Frequency Tracking:   ±50 ppm range
  Output Jitter:              < 0.1 UI peak-to-peak
  Stuff Jitter:               < 0.2 UI (filtered)
  Error Detection:            CRC-based monitoring"""

        else:
            return f"multiplex: unknown option '{args[0]}'\nUse 'multiplex' for available commands"
    def cmd_regenerator(self, args: List[str]) -> str:
        """Digital Signal Regenerator Management"""
        if not args:
            return """Digital Regenerator System Management
T1 Line and Terminal Equipment

Available Commands:
  regenerator status       - System overview and regenerator status
  regenerator test <id>    - Individual regenerator testing
  regenerator power        - Power system monitoring
  regenerator alarm        - Alarm status and fault analysis
  regenerator maintenance  - Preventive maintenance schedules
  regenerator performance  - Performance monitoring and trends

Current Regenerator Status:
  Line Regenerators:           1,247 units operational
  Terminal Equipment:          156 CSU/DSU units
  Performance:                 All within specifications
  Power Consumption:           Normal (58.7 kW total)"""

        elif args[0] == "status":
            return """Digital Regenerator System Status
November 14, 1983 07:45:30

Line Regenerator Status:
  REG-NYC-WAS-001-R47:
    Location:                 Mile 23.4 (manhhole MH-2347)
    Input Signal:             -18.2 dBm (nominal -22.5 dBm)
    Output Signal:            +13.0 dBm (nominal +13.0 dBm)
    Bit Error Rate:           < 10^-12
    Jitter:                   0.02 UI (excellent)
    Temperature:              68°F (normal)

  REG-NYC-WAS-001-R48:
    Location:                 Mile 46.8 (repeater hut RH-4680)
    Input Signal:             -19.1 dBm (nominal -22.5 dBm)
    Output Signal:            +12.8 dBm (nominal +13.0 dBm)
    Bit Error Rate:           < 10^-12
    Jitter:                   0.03 UI (excellent)
    Temperature:              71°F (normal)

Terminal Equipment Status:
  CSU-NYC-001 (Channel Service Unit):
    Circuit:                  DS1-NYC-WAS-001
    Input Level:              +13.2 dBm
    Output Level:             +13.0 dBm
    Loop-back:                Available (remote/local)

  DSU-NYC-002 (Data Service Unit):
    Circuit:                  DS1-NYC-BOS-002
    Data Rate:                56 kbps (subrate)
    Clock Source:             Network derived
    Interface:                V.35 to customer

Performance Summary:
  Signal Quality:             Excellent (all regenerators)
  Power Efficiency:           47 mA average consumption
  Environmental:              All within operating range
  Maintenance Status:         Current with PM schedule

Regenerator Spacing:
  Cable Type:                 T1 (22 AWG, PIC)
  Span Length:                6,000 feet (nominal)
  Signal Loss:                22.5 dB per span
  Safety Margin:              10.5 dB (adequate)"""

        else:
            return f"regenerator: unknown option '{args[0]}'\nUse 'regenerator' for available commands"
