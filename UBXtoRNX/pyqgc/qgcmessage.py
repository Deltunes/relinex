"""
QGCmessage.py

Main QGC Message Protocol Class.

Created on 26 Sep 2020

:author: semuadmin (Steve Smith)
:copyright: semuadmin © 2020
:license: BSD 3-Clause
"""

# pylint: disable=too-many-positional-arguments, too-many-locals, too-many-arguments

from types import NoneType

from pyqgc.exceptions import QGCMessageError
from pyqgc.qgchelpers import (
    attsiz,
    bytes2val,
    calc_checksum,
    escapeall,
    nomval,
    val2bytes,
)
from pyqgc.qgctypes_core import (
    GET,
    PAGE53,
    POLL,
    QGC_HDR,
    QGC_MSGIDS,
    SCALROUND,
    SET,
    SNSTR,
    U2,
    VERSTR,
)
from pyqgc.qgctypes_get import QGC_PAYLOADS_GET
from pyqgc.qgctypes_poll import QGC_PAYLOADS_POLL
from pyqgc.qgctypes_set import QGC_PAYLOADS_SET


class QGCMessage:
    """QGC Message Class."""

    def __init__(
        self,
        msggrp: bytes,
        msgid: bytes,
        checksum: bytes | NoneType = None,
        length: bytes | NoneType = None,
        msgmode: int = GET,
        parsebitfield: bool = True,
        **kwargs,
    ):
        """Constructor.

        If no keyword parms are passed, the payload is taken to be empty.

        If 'payload' is passed as a keyword parm, this is taken to contain the complete
        payload as a sequence of bytes; any other keyword parms are ignored.

        Otherwise, any named attributes will be assigned the value given, all others will
        be assigned a nominal value according to type.

        :param object msggrp: message group
        :param object msgID: message ID
        :param bytes checksum: checksum (will be derived if None)
        :param bytes length: payload length (will be derived if None)
        :param int msgmode: message mode (0=GET, 1=SET, 2=POLL)
        :param bool parsebitfield: parse bitfields ('X' type attributes) Y/N
        :param kwargs: optional payload keyword arguments
        :raises: QGCMessageError
        """

        if msgmode not in (GET, SET, POLL):
            raise QGCMessageError(f"Invalid msgmode {msgmode} - must be 0, 1 or 2")

        # object is mutable during initialisation only
        super().__setattr__("_immutable", False)
        self._mode = msgmode
        self._length = length  # bytes
        if length is None:
            self._lengthint = 0
        else:
            self._lengthint = bytes2val(length, U2)  # integer
        self._checksum = checksum  # bytes
        self._msggrp = msggrp
        self._msgid = msgid
        self._parsebf = parsebitfield  # parsing bitfields Y/N?
        self._payload = kwargs.get("payload", b"")
        self._offset = 0  # payload offset in bytes
        self._index = []  # array of (nested) group indices
        self._suffix = ""  # attribute index suffix ("_01", "_02", etc.)

        pdict = self._get_dict(**kwargs)  # get appropriate payload dict
        for anam in pdict:  # process each attribute in dict
            self._set_attribute(anam, pdict, **kwargs)
        self._do_len_checksum()

        self._immutable = True  # once initialised, object is immutable

    def _set_attribute(self, anam: str, pdict: dict, **kwargs):  #  -> tuple:
        """
        Recursive routine to set individual or grouped payload attributes.

        :param str anam: attribute name
        :param dict pdict: dict representing payload definition
        :param int offset: payload offset in bytes
        :param list index: repeating group index array
        :param kwargs: optional payload key/value pairs
        :return: (offset, index[])
        :rtype: tuple

        """
        adef = pdict[anam]  # get attribute definition
        if isinstance(
            adef, tuple
        ):  # repeating group of attributes or subdefined bitfield
            numr, _ = adef
            if numr[0] == "X":  # bitfield
                if self._parsebf:  # if we're parsing bitfields
                    self._set_attribute_bitfield(adef, **kwargs)
                else:  # treat bitfield as a single byte array
                    self._set_attribute_single(anam, numr, **kwargs)
            else:  # repeating group of attributes
                self._set_attribute_group(adef, **kwargs)
        else:  # single attribute
            self._set_attribute_single(anam, adef, **kwargs)

    def _set_attribute_group(self, adef: tuple, **kwargs):
        """
        Process (nested) group of attributes.

        :param tuple adef: attribute definition - tuple of (num repeats, attribute dict)
        :param int offset: payload offset in bytes
        :param list index: repeating group index array
        :param kwargs: optional payload key/value pairs
        :return: (offset, index[])
        :rtype: tuple

        """

        self._index.append(0)  # add a (nested) group index
        anam, gdict = adef  # attribute signifying group size, group dictionary
        # derive or retrieve number of items in group
        if isinstance(anam, int):  # fixed number of repeats
            gsiz = anam
        elif anam == "None":  # number of repeats 'variable by size'
            gsiz = self._calc_num_repeats(gdict, self._payload, self._offset, 0)
        else:  # number of repeats is defined in named attribute
            gsiz = getattr(self, anam)
        # recursively process each group attribute,
        # incrementing the payload offset and index as we go
        for i in range(gsiz):
            self._index[-1] = i + 1
            for key1 in gdict:
                self._set_attribute(key1, gdict, **kwargs)

        self._index.pop()  # remove this (nested) group index

    def _set_attribute_single(self, anam: str, adef: str, **kwargs):
        """
        Set individual attribute value, applying scaling where appropriate.

        :param str anam: attribute keyword
        :param str adef: attribute definition string e.g. 'U002', 'R004*100'
        :param int offset: payload offset in bytes
        :param list index: repeating group index array
        :param kwargs: optional payload key/value pairs
        :return: offset
        :rtype: int

        """
        # pylint: disable=no-member

        # if attribute is part of a (nested) repeating group, suffix name with index
        anami = anam
        for i in self._index:  # one index for each nested level
            if i > 0:
                anami += f"_{i:02d}"

        # determine attribute size (bytes) - some attributes have
        # variable length, depending on
        # - multiple of value of preceding attribute
        # - payload length - offset
        if adef in (PAGE53, VERSTR, SNSTR):
            an, at, ml = adef.split("_", 2)
            if adef in (PAGE53,):
                vl = getattr(self, an) * int(ml)
            else:
                vl = bytes2val(self._length, U2) - int(ml)
            adef = f"{at}{vl:03d}"
        asiz = attsiz(adef)

        # if payload keyword has been provided,
        # use the appropriate offset of the payload
        if "payload" in kwargs:
            valb = self._payload[self._offset : self._offset + asiz]
            val = bytes2val(valb, adef)
        else:
            # if individual keyword has been provided,
            # set to provided value, else set to
            # nominal value
            val = kwargs.get(anami, nomval(adef))
            valb = val2bytes(val, adef)
            self._payload += valb

        setattr(self, anami, val)
        self._offset += asiz

    def _set_attribute_bitfield(self, adef: tuple[str, dict], **kwargs):
        """
        Parse bitfield attribute (type 'X').

        :param tuple[str, dict] adef: attribute definition and dictionary
        :param kwargs: optional payload key/value pairs
        :return: (offset, index[])
        :rtype: tuple

        """
        # pylint: disable=no-member

        btyp, bdict = adef  # type of bitfield, bitfield dictionary
        bsiz = attsiz(btyp)  # size of bitfield in bytes
        bfoffset = 0

        # if payload keyword has been provided,
        # use the appropriate offset of the payload
        if "payload" in kwargs:
            bitfield = int.from_bytes(
                self._payload[self._offset : self._offset + bsiz], "little"
            )
        else:
            bitfield = 0

        # process each flag in bitfield
        for key, keyt in bdict.items():
            bitfield, bfoffset = self._set_attribute_bits(
                bitfield, bfoffset, key, keyt, self._index, **kwargs
            )

        # update payload
        if "payload" not in kwargs:
            self._payload += bitfield.to_bytes(bsiz, "little")

        self._offset += bsiz

    def _set_attribute_bits(
        self,
        bitfield: int,
        bfoffset: int,
        anam: str,
        adef: str,
        index: list,
        **kwargs,
    ) -> tuple[int, int]:
        """
        Set individual bit flag from bitfield.

        :param int bitfield: bitfield
        :param int bfoffset: bitfield offset in bits
        :param str anam: attribute name
        :param str adef: attribute definition e.g. 'U001'
        :param list index: repeating group index array
        :param kwargs: optional payload key/value pairs
        :return: (bitfield, bfoffset)
        :rtype: tuple[int,int]

        """
        # pylint: disable=no-member

        # if attribute is part of a (nested) repeating group, suffix name with index
        anami = anam
        for i in index:  # one index for each nested level
            if i > 0:
                anami += f"_{i:02d}"

        # if attribute is scaled
        if "*" in adef:
            adef, scaling = adef.split("*", 1)
            scaling = float(scaling)
        else:
            scaling = 1

        asiz = attsiz(adef)  # determine flag size in bits

        if "payload" in kwargs:
            val = (bitfield >> bfoffset) & ((1 << asiz) - 1)
            if scaling != 1:
                val = round(val / scaling, SCALROUND)
        else:
            if scaling == 1:
                val = kwargs.get(anami, 0)
            else:
                val = int(kwargs.get(anami, 0) * scaling)
            bitfield = bitfield | (val << bfoffset)

        if anam[0:8] != "reserved":  # don't bother to set reserved bits
            setattr(self, anami, val)
        return (bitfield, bfoffset + asiz)

    def _do_len_checksum(self):
        """
        Calculate and format payload length and checksum as bytes,
        if not passed as input arguments.
        """

        payload = b"" if self._payload is None else self._payload
        if self._length is None:
            self._lengthint = len(payload)
            self._length = val2bytes(len(payload), U2)
        if self._checksum is None:
            self._checksum = calc_checksum(
                self._msggrp + self._msgid + self._length + payload
            )

    def _get_dict(self, **kwargs) -> dict:  # pylint: disable=unused-argument
        """
        Get payload dictionary corresponding to message mode (GET/SET/POLL)

        :param kwargs: optional payload key/value pairs
        :return: dictionary representing payload definition
        :rtype: dict

        """

        try:
            if self._mode == POLL:
                pdict = QGC_PAYLOADS_POLL[self.identity]
                # alternate definitions
                if self.identity == "CFG-MSG" and self._lengthint == 5:
                    pdict = QGC_PAYLOADS_POLL[f"{self.identity}-INTF"]
            elif self._mode == SET:
                pdict = QGC_PAYLOADS_SET[self.identity]
                # alternate definitions
                if self.identity == "CFG-MSG" and self._lengthint == 7:
                    pdict = QGC_PAYLOADS_SET[f"{self.identity}-INTF"]
                elif self.identity == "CFG-UART" and self._lengthint == 2:
                    pdict = QGC_PAYLOADS_SET[f"{self.identity}-DIS"]
            else:
                # Unknown GET message, parsed to nominal definition
                if self.identity[-7:] == "NOMINAL":
                    pdict = {}
                else:
                    pdict = QGC_PAYLOADS_GET[self.identity]
                    # alternate definitions
                    if self.identity == "CFG-MSG" and self._lengthint == 7:
                        pdict = QGC_PAYLOADS_GET[f"{self.identity}-INTF"]
            return pdict
        except KeyError as err:
            mode = ["GET", "SET", "POLL"][self._mode]
            raise QGCMessageError(
                f"Unknown message type {escapeall(self._msggrp + self._msgid)}, mode {mode}. "
                "Check 'msgmode' setting is appropriate for data stream"
            ) from err

    def _calc_num_repeats(
        self, attd: dict, payload: bytes, offset: int, offsetend: int = 0
    ) -> int:
        """
        Deduce number of items in 'variable by size' repeating group by
        dividing length of remaining payload by length of group.

        This is predicated on there being only one such repeating group
        per message payload, which is true for all currently supported types.

        :param dict attd: grouped attribute dictionary
        :param bytes payload : raw payload
        :param int offset: number of bytes in payload before repeating group
        :param int offsetend: number of bytes in payload after repeating group
        :return: number of repeats
        :rtype: int

        """

        lenpayload = len(payload) - offset - offsetend
        lengroup = 0
        for _, val in attd.items():
            if isinstance(val, tuple):
                val, _ = val
            lengroup += attsiz(val)
        return int(lenpayload / lengroup)

    def __str__(self) -> str:
        """
        Human readable representation.

        :return: human readable representation
        :rtype: str

        """

        umsg_name = self.identity
        if self.payload is None:
            return f"<QGC({umsg_name})>"
        if self.identity[-7:] == "NOMINAL":
            return f"<QGC({umsg_name}, payload={escapeall(self._payload)})>"

        stg = f"<QGC({umsg_name}, "
        for i, att in enumerate(self.__dict__):
            if att[0] != "_":  # only show public attributes
                val = self.__dict__[att]
                # escape all byte chars unless they're
                # intended to be character strings
                if isinstance(val, bytes):
                    val = escapeall(val)
                stg += att + "=" + str(val).rstrip()
                if i < len(self.__dict__) - 1:
                    stg += ", "
        stg += ")>"

        return stg

    def __repr__(self) -> str:
        """
        Machine readable representation.

        eval(repr(obj)) = obj

        :return: machine readable representation
        :rtype: str

        """

        if self._payload is None:
            return f"QGCMessage({self._msggrp}, {self._msgid}, {self._mode}"
        return f"QGCMessage({self._msggrp}, {self._msgid}, {self._mode}, payload={self._payload})"

    def __setattr__(self, name, value):
        """
        Override setattr to make object immutable after instantiation.

        :param str name: attribute name
        :param object value: attribute value
        :raises: QGCMessageError

        """

        if self._immutable:
            raise QGCMessageError(
                f"Object is immutable. Updates to {name} not permitted after initialisation."
            )

        super().__setattr__(name, value)

    def serialize(self) -> bytes:
        """
        Serialize message.

        :return: serialized output
        :rtype: bytes

        """

        return (
            QGC_HDR
            + self._msggrp
            + self._msgid
            + self._length
            + (b"" if self._payload is None else self._payload)
            + self._checksum
        )

    @property
    def identity(self) -> str:
        """
        Returns message identity in plain text form.

        If the message is unrecognised, the message is parsed
        to a nominal payload definition QGC-NOMINAL and
        the term 'NOMINAL' is appended to the identity.

        :return: message identity e.g. 'RAW-HASE6'
        :rtype: str

        """

        try:
            umsg_name = QGC_MSGIDS[self._msggrp + self._msgid]
        except KeyError:
            # unrecognised Quectel message, parsed to QGC-NOMINAL definition
            cls = "UNKNOWN"
            umsg_name = (
                f"{cls}-{int.from_bytes(self._msggrp, 'little'):02x}"
                + f"{int.from_bytes(self._msgid, 'little'):02x}-NOMINAL"
            )
        return umsg_name

    @property
    def msg_grp(self) -> bytes:
        """
        Message group getter.

        :return: message class as bytes
        :rtype: bytes

        """
        return self._msggrp

    @property
    def msg_id(self) -> bytes:
        """
        Message id getter.

        :return: message id as bytes
        :rtype: bytes

        """

        return self._msgid

    @property
    def length(self) -> int:
        """
        Payload length getter.

        :return: payload length as integer
        :rtype: int

        """

        return bytes2val(self._length, U2)

    @property
    def payload(self) -> bytes:
        """
        Payload getter - returns the raw payload bytes.

        :return: raw payload as bytes
        :rtype: bytes

        """

        return self._payload

    @property
    def msgmode(self) -> int:
        """
        Message mode getter.

        :return: msgmode as integer
        :rtype: int

        """

        return self._mode
