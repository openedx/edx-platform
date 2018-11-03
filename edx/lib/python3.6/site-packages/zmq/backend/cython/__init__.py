"""Python bindings for core 0MQ objects."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Lesser GNU Public License (LGPL).

from . import (constants, error, message, context,
                      socket, utils, _poll, _version, _device )

__all__ = []
for submod in (constants, error, message, context,
               socket, utils, _poll, _version, _device):
    __all__.extend(submod.__all__)

from .constants import *
from .error import *
from .message import *
from .context import *
from .socket import *
from ._poll import *
from .utils import *
from ._device import *
from ._version import *

