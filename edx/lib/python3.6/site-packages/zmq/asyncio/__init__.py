"""AsyncIO support for zmq

Requires asyncio and Python 3.
"""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.

import zmq as _zmq
from zmq import _future

# TODO: support trollius for Legacy Python? (probably not)

import asyncio
from asyncio import SelectorEventLoop, Future
try:
    import selectors
except ImportError:
    from asyncio import selectors # py33


class _AsyncIO(object):
    _Future = Future
    _WRITE = selectors.EVENT_WRITE
    _READ = selectors.EVENT_READ

    def _default_loop(self):
        return asyncio.get_event_loop()

class Poller(_AsyncIO, _future._AsyncPoller):
    """Poller returning asyncio.Future for poll results."""
    def _watch_raw_socket(self, loop, socket, evt, f):
        """Schedule callback for a raw socket"""
        if evt & self._READ:
            loop.add_reader(socket, lambda *args: f())
        if evt & self._WRITE:
            loop.add_writer(socket, lambda *args: f())

    def _unwatch_raw_sockets(self, loop, *sockets):
        """Unschedule callback for a raw socket"""
        for socket in sockets:
            loop.remove_reader(socket)
            loop.remove_writer(socket)


class Socket(_AsyncIO, _future._AsyncSocket):
    """Socket returning asyncio Futures for send/recv/poll methods."""

    _poller_class = Poller

    def _init_io_state(self):
        """initialize the ioloop event handler"""
        self.io_loop.add_reader(self._fd, lambda : self._handle_events(0, 0))

    def _clear_io_state(self):
        """clear any ioloop event handler

        called once at close
        """
        self.io_loop.remove_reader(self._fd)

Poller._socket_class = Socket

class Context(_zmq.Context):
    """Context for creating asyncio-compatible Sockets"""
    _socket_class = Socket


class ZMQEventLoop(SelectorEventLoop):
    """DEPRECATED: AsyncIO eventloop using zmq_poll.

    pyzmq sockets should work with any asyncio event loop as of pyzmq 17.
    """
    def __init__(self, selector=None):
        _deprecated()
        return super(ZMQEventLoop, self).__init__(selector)


_loop = None


def _deprecated():
    if _deprecated.called:
        return
    _deprecated.called = True
    import warnings
    warnings.warn("ZMQEventLoop and zmq.asyncio.install are deprecated in pyzmq 17. Special eventloop integration is no longer needed.", DeprecationWarning, stacklevel=3)
_deprecated.called = False


def install():
    """DEPRECATED: No longer needed in pyzmq 17"""
    _deprecated()


__all__ = [
    'Context',
    'Socket',
    'Poller',
    'ZMQEventLoop',
    'install',
]
