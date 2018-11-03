"""Tornado websocket handler to serve a terminal interface.
"""
# Copyright (c) Jupyter Development Team
# Copyright (c) 2014, Ramalingam Saravanan <sarava@sarava.net>
# Distributed under the terms of the Simplified BSD License.

from __future__ import absolute_import, print_function

# Python3-friendly imports
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

import json
import logging

import tornado.web
import tornado.websocket

def _cast_unicode(s):
    if isinstance(s, bytes):
        return s.decode('utf-8')
    return s

class TermSocket(tornado.websocket.WebSocketHandler):
    """Handler for a terminal websocket"""
    def initialize(self, term_manager):
        self.term_manager = term_manager
        self.term_name = ""
        self.size = (None, None)
        self.terminal = None

        self._logger = logging.getLogger(__name__)

    def origin_check(self, origin=None):
        """Deprecated: backward-compat for terminado <= 0.5."""
        return self.check_origin(origin or self.request.headers.get('Origin'))

    def open(self, url_component=None):
        """Websocket connection opened.
        
        Call our terminal manager to get a terminal, and connect to it as a
        client.
        """
        # Jupyter has a mixin to ping websockets and keep connections through
        # proxies alive. Call super() to allow that to set up:
        super(TermSocket, self).open(url_component)

        self._logger.info("TermSocket.open: %s", url_component)

        url_component = _cast_unicode(url_component)
        self.term_name = url_component or 'tty'
        self.terminal = self.term_manager.get_terminal(url_component)
        for s in self.terminal.read_buffer:
            self.on_pty_read(s)
        self.terminal.clients.append(self)

        self.send_json_message(["setup", {}])
        self._logger.info("TermSocket.open: Opened %s", self.term_name)

    def on_pty_read(self, text):
        """Data read from pty; send to frontend"""
        self.send_json_message(['stdout', text])

    def send_json_message(self, content):
        json_msg = json.dumps(content)
        self.write_message(json_msg)

    def on_message(self, message):
        """Handle incoming websocket message
        
        We send JSON arrays, where the first element is a string indicating
        what kind of message this is. Data associated with the message follows.
        """
        ##logging.info("TermSocket.on_message: %s - (%s) %s", self.term_name, type(message), len(message) if isinstance(message, bytes) else message[:250])
        command = json.loads(message)
        msg_type = command[0]    

        if msg_type == "stdin":
            self.terminal.ptyproc.write(command[1])
        elif msg_type == "set_size":
            self.size = command[1:3]
            self.terminal.resize_to_smallest()

    def on_close(self):
        """Handle websocket closing.
        
        Disconnect from our terminal, and tell the terminal manager we're
        disconnecting.
        """
        self._logger.info("Websocket closed")
        if self.terminal:
            self.terminal.clients.remove(self)
            self.terminal.resize_to_smallest()
        self.term_manager.client_disconnected(self)

    def on_pty_died(self):
        """Terminal closed: tell the frontend, and close the socket.
        """
        self.send_json_message(['disconnect', 1])
        self.close()
