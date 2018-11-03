"""Terminals served to xterm.js using Tornado websockets"""

# Copyright (c) Jupyter Development Team
# Copyright (c) 2014, Ramalingam Saravanan <sarava@sarava.net>
# Distributed under the terms of the Simplified BSD License.

from .websocket import TermSocket
from .management import (TermManagerBase, SingleTermManager,
                         UniqueTermManager, NamedTermManager)

import logging
# Prevent a warning about no attached handlers in Python 2
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = '0.8.1'
