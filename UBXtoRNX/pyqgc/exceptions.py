"""
QGC Custom Exception Types.

Created on 6 Oct 2025

:author: semuadmin (Steve Smith)
:copyright: semuadmin © 2020
:license: BSD 3-Clause
"""


class ParameterError(Exception):
    """Parameter Error Class."""


class GNSSStreamError(Exception):
    """Generic Stream Error Class."""


class QGCParseError(Exception):
    """
    QGC Parsing error.
    """


class QGCStreamError(Exception):
    """
    QGC Streaming error.
    """


class QGCMessageError(Exception):
    """
    QGC Undefined message class/id.
    Essentially a prompt to add missing payload types to QGC_PAYLOADS.
    """


class QGCTypeError(Exception):
    """
    QGC Undefined payload attribute type.
    Essentially a prompt to fix incorrect payload definitions to QGC_PAYLOADS.
    """
