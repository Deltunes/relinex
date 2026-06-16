"""
Collection of QGC helper methods which can be used
outside the QGCMessage or QGCReader classes.

Created on 6 Oct 2025

:author: semuadmin (Steve Smith)
:copyright: semuadmin © 2020
:license: BSD 3-Clause
"""

import struct
from typing import Any

import pyqgc.exceptions as qge
from pyqgc.qgctypes_core import ATTTYPE, GET, POLL, QGC_MSGIDS, SCALROUND, SET, U2
from pyqgc.qgctypes_get import QGC_PAYLOADS_GET
from pyqgc.qgctypes_poll import QGC_PAYLOADS_POLL
from pyqgc.qgctypes_set import QGC_PAYLOADS_SET


def att2idx(att: str) -> object:
    """
    Get integer indices corresponding to grouped attribute.

    e.g. svid_06 -> 6; gnssId_103 -> 103, gsid_03_04 -> (3,4), tow -> 0

    :param str att: grouped attribute name e.g. svid_01
    :return: indices as integer(s), or 0 if not grouped
    :rtype: int or tuple for nested group
    """

    try:
        att = att.split("_")
        ln = len(att)
        if ln == 2:  # one group level
            return int(att[1])
        if ln > 2:  # nested group level(s)
            return tuple(int(att[i]) for i in range(1, ln))
        return 0  # not grouped
    except ValueError:
        return 0


def att2name(att: str) -> str:
    """
    Get name of grouped attribute.

    e.g. svid_06 -> svid; gnssId_103 -> gnssId, tow -> tow

    :param str att: grouped attribute name e.g. svid_01
    :return: name without index e.g. svid
    :rtype: str
    """

    return att.split("_")[0]


def attsiz(att: str) -> int:
    """
    Helper function to return attribute size in bytes.

    :param str: attribute type e.g. 'U002'
    :return: size of attribute in bytes, or -1 if variable length
    :rtype: int

    """

    try:
        return int(att[1:4])
    except ValueError:
        return -1


def atttyp(att: str) -> str:
    """
    Helper function to return attribute type as string.

    :param str: attribute type e.g. 'U002'
    :return: type of attribute as string e.g. 'U'
    :rtype: str

    """

    return att[0:1]


def bytes2val(valb: bytes, adef: str) -> Any:
    """
    Convert bytes to value for given UNI attribute type.

    :param bytes valb: attribute value in byte format e.g. b'\\\\x19\\\\x00\\\\x00\\\\x00'
    :param str adef: attribute definition e.g. 'U004'
    :return: attribute value as int, float, str or bytes
    :rtype: Any
    :raises: UNITypeError

    """

    if "*" in adef:
        adef, scaling = adef.split("*", 1)
        scaling = float(scaling)
    else:
        scaling = 1

    if atttyp(adef) == "X":  # bytes
        val = valb
    elif atttyp(adef) == "C":  # string
        val = valb.replace(b"\x00", b" ").decode("utf-8", errors="backslashreplace")
    elif atttyp(adef) in ("S", "U"):  # integer
        val = int.from_bytes(valb, byteorder="little", signed=atttyp(adef) == "S")
        if scaling != 1:
            val = round(val / scaling, SCALROUND)
    elif atttyp(adef) == "R":  # floating point
        val = struct.unpack("<f" if attsiz(adef) == 4 else "<d", valb)[0]
        if scaling != 1:
            val = round(val / scaling, SCALROUND)
    else:
        raise qge.QGCTypeError(f"Unknown attribute type {adef}")
    return val


def calc_checksum(content: bytes) -> int:
    """
    Calculate checksum.

    :param bytes content: message content, excluding header and checksum bytes
    :return: return code
    :rtype: int
    """

    check_a = 0
    check_b = 0

    for char in content:
        check_a += char
        check_a &= 0xFF
        check_b += check_a
        check_b &= 0xFF

    return bytes((check_a, check_b))


def escapeall(val: bytes) -> str:
    """
    Escape all byte characters e.g. b'\\\\x73' rather than b`s`

    :param bytes val: bytes
    :return: string of escaped bytes
    :rtype: str
    """

    return "b'{}'".format("".join(f"\\x{b:02x}" for b in val))


def get_bits(bitfield: bytes, bitmask: int) -> int:
    """
    Get integer value of specified (masked) bit(s) in a QGC bitfield (attribute type 'X')

    e.g. to get value of bits 6,7 in bitfield b'\\\\x89' (binary 0b10001001)::

        get_bits(b'\\x89', 0b11000000) = get_bits(b'\\x89', 192) = 2

    :param bytes bitfield: bitfield byte(s)
    :param int bitmask: bitmask as integer (= Σ(2**n), where n is the number of the bit)
    :return: value of masked bit(s)
    :rtype: int
    """

    i = 0
    val = int(bitfield.hex(), 16)
    while bitmask & 1 == 0:
        bitmask = bitmask >> 1
        i += 1
    return val >> i & bitmask


def getinputmode(msggrp: bytes, msgid: bytes, length: bytes) -> int:
    """
    Return input message mode (SET or POLL).

    :param bytes data: raw QGC input message
    :return: message mode (1 = SET, 2 = POLL)
    :rtype: int
    """

    try:
        mid = QGC_MSGIDS[msggrp + msgid]
        leni = bytes2val(length, U2)
        if leni == getpaylen(mid, SET):
            return SET
        if leni == getpaylen(mid, POLL):
            return POLL
    except (KeyError, ValueError):
        pass
    return SET


def getpaylen(identity: str, mode: int = GET) -> int:
    """
    Get length of payload dictionary in bytes.

    :param str identity: identity of message
    :param int mode: message mode (GET/SET/POLL)
    :return: length in bytes or -1 if variable length
    :rtype: int
    """

    try:
        dic = [QGC_PAYLOADS_GET, QGC_PAYLOADS_SET, QGC_PAYLOADS_POLL][mode]
        leni = 0
        for _, typ in dic[identity].items():
            siz = attsiz(typ)
            if siz > 0:
                leni += siz
            else:
                return -1
        return leni
    except (IndexError, ValueError):
        return -1


def hextable(raw: bytes, cols: int = 8) -> str:
    """
    Formats raw (binary) message in tabular hexadecimal format e.g.

    000: 2447 4e47 5341 2c41 2c33 2c33 342c 3233 | b'$GNGSA,A,3,34,23' |

    :param bytes raw: raw (binary) data
    :param int cols: number of columns in hex table (8)
    :return: table of hex data
    :rtype: str
    """

    hextbl = ""
    colw = cols * 4
    rawh = raw.hex()
    for i in range(0, len(rawh), colw):
        rawl = rawh[i : i + colw].ljust(colw, " ")
        hextbl += f"{int(i/2):03}: "
        for col in range(0, colw, 4):
            hextbl += f"{rawl[col : col + 4]} "
        bfh = str(bytes.fromhex(rawl))
        hextbl += f" | {bfh:<67} |\n"

    return hextbl


def isvalid_checksum(message: bytes) -> bool:
    """
    Validate message checksum.

    :param bytes message: message including header and checksum bytes
    :return: checksum valid flag
    :rtype: bool

    """

    lenm = len(message)
    ckm = message[lenm - 2 : lenm]
    return ckm == calc_checksum(message[2 : lenm - 2])


def key_from_val(dictionary: dict, value) -> str:
    """
    Helper method - get dictionary key corresponding to (unique) value.

    :param dict dictionary: dictionary
    :param object value: unique dictionary value
    :return: dictionary key
    :rtype: str
    :raises: KeyError: if no key found for value

    """

    val = None
    for key, val in dictionary.items():
        if val == value:
            return key
    raise KeyError(f"No key found for value {value}")


def nomval(att: str) -> object:
    """
    Get nominal value for given QGC attribute type.

    :param str att: attribute type e.g. 'U004'
    :return: attribute value as int, float, str or bytes
    :rtype: object
    :raises: QGCTypeError

    """

    if atttyp(att) == "X":
        val = b"\x00" * attsiz(att)
    elif atttyp(att) == "C":
        val = " " * attsiz(att)
    elif atttyp(att) == "R":
        val = 0.0
    elif atttyp(att) in ("S", "U"):
        val = 0
    else:
        raise qge.QGCTypeError(f"Unknown attribute type {att}")
    return val


def val2bytes(val: Any, adef: str) -> bytes:
    """
    Convert value to bytes for given UNI attribute type.

    :param Any val: attribute value e.g. 25
    :param str adef: attribute definition e.g. 'U004'
    :return: attribute value as bytes
    :rtype: bytes
    :raises: UNITypeError

    """

    if "*" in adef:
        adef, scaling = adef.split("*", 1)
        scaling = float(scaling)
    else:
        scaling = 1

    try:
        if not isinstance(val, ATTTYPE[atttyp(adef)]):
            raise TypeError(
                f"Attribute type {adef} value {val} must be "
                f"{ATTTYPE[atttyp(adef)]}, not {type(val)}"
            )
    except KeyError as err:
        raise qge.QGCTypeError(f"Unknown attribute type {adef}") from err

    valb = val
    if atttyp(adef) == "X":  # byte
        valb = val
    elif atttyp(adef) == "C":  # string
        valb = f"{val:<{attsiz(adef)}}".encode("utf-8", errors="backslashreplace")
    elif atttyp(adef) in ("S", "U"):  # integer
        if scaling != 1:
            val = int(val * scaling)
        valb = val.to_bytes(
            attsiz(adef), byteorder="little", signed=atttyp(adef) == "S"
        )
    elif atttyp(adef) == "R":  # floating point
        if scaling != 1:
            val = float(val * scaling)
        valb = struct.pack("<f" if attsiz(adef) == 4 else "<d", val)
    return valb
