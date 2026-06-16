"""
Created on 6 Oct 2025

:author: semuadmin (Steve Smith)
:copyright: semuadmin © 2020
:license: BSD 3-Clause
"""

from pynmeagps import SocketWrapper

from pyqgc._version import __version__
from pyqgc.exceptions import (
    GNSSStreamError,
    ParameterError,
    QGCMessageError,
    QGCParseError,
    QGCStreamError,
    QGCTypeError,
)
from pyqgc.qgchelpers import *
from pyqgc.qgcmessage import QGCMessage
from pyqgc.qgcreader import QGCReader
from pyqgc.qgctypes_core import *
from pyqgc.qgctypes_get import *

version = __version__  # pylint: disable=invalid-name
