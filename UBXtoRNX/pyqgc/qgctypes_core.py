"""
QGC Protocol core globals, constants, datatypes and message identifiers.

Created on 6 Oct 2025

Information sourced from public domain Quectel Interface Specifications © 2025, Quectel

:author: semuadmin (Steve Smith)
"""

QGC_HDR = b"\x51\x47"
"""QGC message header"""
GET = 0
"""GET (receive, response) message types"""
SET = 1
"""SET (command) message types"""
POLL = 2
"""POLL (query) message types"""
SETPOLL = 3
"""SETPOLL (SET or POLL) message types"""
VALNONE = 0
"""Do not validate checksum"""
VALCKSUM = 1
"""Validate checksum"""
NMEA_PROTOCOL = 1
"""NMEA Protocol"""
QGC_PROTOCOL = 2
"""QGC Protocol"""
RTCM3_PROTOCOL = 4
"""RTCM3 Protocol"""
ERR_RAISE = 2
"""Raise error and quit"""
ERR_LOG = 1
"""Log errors"""
ERR_IGNORE = 0
"""Ignore errors"""
SCALROUND = 12  # number of dp to round scaled attributes to

# **************************************************
# THESE ARE THE QGC PROTOCOL PAYLOAD ATTRIBUTE TYPES
# **************************************************
C8 = "C008"  # 8 byte haracter string
C10 = "C010"  # 10 byte character string
CV = "CXXX"  # variable length character string
R4 = "R004"  # single precision float 4 [-1*2^127,2^127]
R8 = "R008"  # double precision float 8 [-1*2^1023,2^1023]
S1 = "S001"  # signed char 1 [-128,127]
S2 = "S002"  # signed short int 2 [-32768,32767]
S4 = "S004"  # signed int 4 [-2147483648,2147483647]
S8 = "S008"  # signed long long int 8 [-2^63,2^63-1]
U1 = "U001"  # unsigned char 1 [0,255]
U2 = "U002"  # unsigned short int 2 [0,65535]
U3 = "U003"  # unsigned short int 3
U4 = "U004"  # unsigned int 4 [0,4294967295]
U5 = "U005"  # unsigned int 5
U6 = "U006"  # unsigned int 6
U8 = "U008"  # unsigned long long int 8 [0,2^64-1]
U10 = "U010"  # unsigned long long int 10
U15 = "U015"  # unsigned long long int 15
U16 = "U016"  # unsigned long long int 16
U17 = "U017"  # unsigned long long int 17
X1 = "X001"  # 8 bits field 1 Bit 7-0
X2 = "X002"  # 16 bits field 2 Bit 15-0
X4 = "X004"  # 32 bits field 4 Bit 31-0
X8 = "X008"  # 64 bits field 8 Bit 63-0
X61 = "X061"  # 61 bytes
X250 = "X250"  # 250 bytes

PAGE53 = "page_X_053"
VERSTR = "ver_C_018"
SNSTR = "sn_C_001"

ATTTYPE = {
    "S": type(-1),
    "R": type(1.1),
    "U": type(1),
    "X": type(b"0"),
    "C": type("X"),
}
"""Permissible attribute types"""

# ***************************************************************************
# THESE ARE THE QGC PROTOCOL CORE MESSAGE IDENTITIES
# Payloads for each of these identities are defined in the QGCtypes_* modules
# ***************************************************************************
QGC_MSGIDS = {
    # ********************************************************************
    # https://www.quectel.com/download/quectel_lg290p03lgx80p03_gnss_protocol_specification_v1-1/
    # ********************************************************************
    b"\x0a\xb2": "RAW-PPPB2B",  # output
    b"\x0a\xb6": "RAW-QZSSL6",  # output
    b"\x0a\xe6": "RAW-HASE6",  # output
    # ********************************************************************
    # https://quectel.com/content/uploads/2024/02/Quectel_LUA600A_IMU_Protocol_Specification_V1.0.pdf
    # ********************************************************************
    b"\x01\x01": "ACK-ACK",  # output
    b"\x02\x01": "CFG-UART",  # get/set
    b"\x02\x04": "CFG-CAN",  # get/set
    b"\x02\x10": "CFG-MSG",  # get/set
    b"\x02\x20": "CFG-IMULPF",  # get/set
    b"\x03\x01": "CTL-RST",  # command
    b"\x03\x02": "CTL-PAR",  # command
    b"\x06\x01": "INF-VER",  # Tcommand/output
    b"\x06\x02": "INF-SN",  # command/output
    b"\x10\x01": "SEN-IMU",  # output
}
