"""
QGC Protocol command payload definitions.

Created on 6 Oct 2025

Information sourced from public domain Quectel Interface Specifications © 2025, Quectel
https://www.quectel.com/download/quectel_lg290p03lgx80p03_gnss_protocol_specification_v1-1/

:author: semuadmin (Steve Smith)
"""

from pyqgc.qgctypes_core import (
    U1,
    U2,
)
from pyqgc.qgctypes_get import QGC_PAYLOADS_GET

QGC_PAYLOADS_SET = {
    # ********************************************************************
    # https://quectel.com/content/uploads/2024/02/Quectel_LUA600A_IMU_Protocol_Specification_V1.0.pdf
    # ********************************************************************
    "CFG-UART": QGC_PAYLOADS_GET["CFG-UART"],
    "CFG-UART-DIS": {
        "intfid": U1,
        "intfstatus": U1,
    },
    "CFG-CAN": QGC_PAYLOADS_GET["CFG-CAN"],
    "CFG-MSG": QGC_PAYLOADS_GET["CFG-MSG"],
    "CFG-MSG-INTF": QGC_PAYLOADS_GET["CFG-MSG-INTF"],
    "CFG-IMULPF": QGC_PAYLOADS_GET["CFG-IMULPF"],
    "CTL-RST": {"rstmask": U2, "rstmode": U1, "reserved1": U1},
    "CTL-PAR": {
        "parmode": U1,  # 0x01 = save, 0x02 = restore
        "reserved1": U1,
    },
    "INF-SN": {
        "snid": U1,
    },
}
