# coding: utf-8
"""zmq device functions"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

from ._cffi import C, ffi
from .socket import Socket
from .utils import _retry_sys_call


def device(device_type, frontend, backend):
    return proxy(frontend, backend)

def proxy(frontend, backend, capture=None):
    if isinstance(capture, Socket):
        capture = capture._zmq_socket
    else:
        capture = ffi.NULL

    _retry_sys_call(C.zmq_proxy, frontend._zmq_socket, backend._zmq_socket, capture)

__all__ = ['device', 'proxy']
