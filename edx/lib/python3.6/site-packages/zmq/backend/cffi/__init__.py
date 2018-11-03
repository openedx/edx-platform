"""CFFI backend (for PyPY)"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from zmq.backend.cffi import (constants, error, message, context, socket,
                           _poll, devices, utils)

__all__ = []
for submod in (constants, error, message, context, socket,
               _poll, devices, utils):
    __all__.extend(submod.__all__)

from .constants import *
from .error import *
from .message import *
from .context import *
from .socket import *
from .devices import *
from ._poll import *
from ._cffi import zmq_version_info, ffi
from .utils import *
