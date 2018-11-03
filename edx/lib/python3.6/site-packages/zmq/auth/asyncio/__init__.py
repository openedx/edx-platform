"""ZAP Authenticator integrated with the asyncio IO loop.

.. versionadded:: 15.2
"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import asyncio

import zmq
from zmq.asyncio import Poller
from ..base import Authenticator


class AsyncioAuthenticator(Authenticator):
    """ZAP authentication for use in the asyncio IO loop"""

    def __init__(self, context=None, loop=None):
        super().__init__(context)
        self.loop = loop or asyncio.get_event_loop()
        self.__poller = None
        self.__task = None

    @asyncio.coroutine
    def __handle_zap(self):
        while True:
            events = yield from self.__poller.poll()
            if self.zap_socket in dict(events):
                msg = yield from self.zap_socket.recv_multipart()
                self.handle_zap_message(msg)

    def start(self):
        """Start ZAP authentication"""
        super().start()
        self.__poller = Poller()
        self.__poller.register(self.zap_socket, zmq.POLLIN)
        self.__task = asyncio.ensure_future(self.__handle_zap())

    def stop(self):
        """Stop ZAP authentication"""
        if self.__task:
            self.__task.cancel()
        if self.__poller:
            self.__poller.unregister(self.zap_socket)
            self.__poller = None
        super().stop()


__all__ = ['AsyncioAuthenticator']
