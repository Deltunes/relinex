"""
QGC Protocol poll payload definitions.

Created on 6 Oct 2025

Information sourced from public domain Quectel Interface Specifications © 2025, Quectel
https://www.quectel.com/download/quectel_lg290p03lgx80p03_gnss_protocol_specification_v1-1/

:author: semuadmin (Steve Smith)
"""

from pyqgc.qgctypes_core import U1

QGC_PAYLOADS_POLL = {
    # ********************************************************************
    # https://quectel.com/content/uploads/2024/02/Quectel_LUA600A_IMU_Protocol_Specification_V1.0.pdf
    # ********************************************************************
    "CFG-UART": {
        "intfid": U1,
    },
    "CFG-CAN": {
        "intfid": U1,
    },
    "CFG-MSG": {
        "setmsggrp": U1,
        "setmsgid": U1,
        "msgver": U1,
    },
    "CFG-MSG-INTF": {
        "intftype": U1,
        "intfid": U1,
        "setmsggrp": U1,
        "setmsgid": U1,
        "msgver": U1,
    },
    "CFG-IMULPF": {},
    "INF-SN": {
        "snid": U1,
    },
    "INF-VER": {},
}
