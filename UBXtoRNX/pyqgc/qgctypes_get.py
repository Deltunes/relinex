"""
QGC Protocol output payload definitions.

Created on 6 Oct 2025

Information sourced from public domain Quectel Interface Specifications © 2025, Quectel
https://www.quectel.com/download/quectel_lg290p03lgx80p03_gnss_protocol_specification_v1-1/

:author: semuadmin (Steve Smith)
"""

# pylint: disable=too-many-lines, line-too-long

from pyqgc.qgctypes_core import (
    C8,
    C10,
    PAGE53,
    R4,
    SNSTR,
    U1,
    U2,
    U3,
    U4,
    U5,
    U6,
    U8,
    U15,
    U16,
    U17,
    VERSTR,
    X1,
    X61,
    X250,
)

QGC_PAYLOADS_GET = {
    # ********************************************************************
    # https://www.quectel.com/download/quectel_lg290p03lgx80p03_gnss_protocol_specification_v1-1/
    # ********************************************************************
    "RAW-PPPB2B": {
        "msgver": U1,  # 1 for this version
        "reserved1": U4,
        "prn": U1,
        "flag": (
            X1,
            {
                "reserved4": U5,
                "pppstatus": U1,  # 0 normal, 1 abnormal
                "reserved3": U2,
            },
        ),
        "msgtype": U1,
        "reserved2": U16,
        "msgdata": X61,
    },
    "RAW-QZSSL6": {
        "msgver": U1,  # 1 for this version
        "reserved1": U4,
        "prn": U1,
        "flag": (
            X1,
            {
                "rsstatus": U2,  # 0 fail, 1, pass, 2 pass after correction
                "reserved": U5,
                "msgtype": U1,  # 0 L6E, 1 L6D
            },
        ),
        "reserved2": U17,
        "msgdata": X250,
    },
    "RAW-HASE6": {
        "msgver": U1,  # 1 for this version
        "reserved1": U3,
        "prn": U1,
        "status": (
            X1,
            {
                "hasmode": U2,  # 0 testing, 1 operational
                "reserved4": U6,
            },
        ),
        "msgtype": U1,  # 1 = MT1
        "reserved2": U1,
        "page": U1,
        "reserved3": U15,
        "msgdata": PAGE53,  # length = page*53
    },
    # ********************************************************************
    # https://quectel.com/content/uploads/2024/02/Quectel_LUA600A_IMU_Protocol_Specification_V1.0.pdf
    # ********************************************************************
    "ACK-ACK": {
        "ackmsggrp": U1,
        "ackmsgid": U1,
        "errcode": U1,
        "reserved1": U1,
    },
    "CFG-UART": {
        "intfid": U1,
        "intfstatus": U1,
        "reserved1": U2,
        "baudrate": U4,
        "databit": U1,
        "parity": U1,
        "stopbit": U1,
        "reserved2": U1,
    },
    "CFG-CAN": {
        "intfid": U1,
        "intfstatus": U1,
        "frameprotocol": U1,
        "frameformat": U1,
        "baudrate": U4,
        "databaudrate": U4,
    },
    "CFG-MSG": {
        "setmsggrp": U1,
        "setmsgid": U1,
        "rate": U2,
        "msgver": U1,
    },
    "CFG-MSG-INTF": {
        "intftype": U1,
        "intfid": U1,
        "setmsggrp": U1,
        "setmsgid": U1,
        "rate": U2,
        "msgver": U1,
    },
    "CFG-IMULPF": {
        "gyofilter": U2,
        "accfilter": U2,
    },
    "INF-VER": {
        "verstr": VERSTR,  # variable <32
        "builddate": C10,
        "buildtime": C8,
    },
    "INF-SN": {
        "snid": U1,
        "snstr": SNSTR,  # variable < 32
    },
    "SEN-IMU": {
        "msgver": U1,  # fixed at 0x03 for this version
        "timestamp": U8,
        "imutemp": R4,
        "gyox": R4,
        "gyoy": R4,
        "gyoz": R4,
        "accx": R4,
        "accy": R4,
        "accz": R4,
    },
    # ********************************************************************
    # QGC nominal payload definition, used as fallback where no documented
    # payload definition is available.
    # ********************************************************************
    "QGC-NOMINAL": {
        "group": (
            "None",
            {
                "data": X1,
            },
        )
    },
}
