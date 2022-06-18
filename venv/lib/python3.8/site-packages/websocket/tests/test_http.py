# -*- coding: utf-8 -*-
#
"""
websocket - WebSocket client library for Python

Copyright (C) 2010 Hiroki Ohtani(liris)

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

"""

import os
import os.path
import websocket as ws
from websocket._http import proxy_info, read_headers, _open_proxied_socket, _tunnel
import sys
sys.path[0:0] = [""]

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    import unittest2 as unittest
else:
    import unittest


class SockMock(object):
    def __init__(self):
        self.data = []
        self.sent = []

    def add_packet(self, data):
        self.data.append(data)

    def gettimeout(self):
        return None

    def recv(self, bufsize):
        if self.data:
            e = self.data.pop(0)
            if isinstance(e, Exception):
                raise e
            if len(e) > bufsize:
                self.data.insert(0, e[bufsize:])
            return e[:bufsize]

    def send(self, data):
        self.sent.append(data)
        return len(data)

    def close(self):
        pass


class HeaderSockMock(SockMock):

    def __init__(self, fname):
        SockMock.__init__(self)
        path = os.path.join(os.path.dirname(__file__), fname)
        with open(path, "rb") as f:
            self.add_packet(f.read())


class OptsList():

    def __init__(self):
        self.timeout = 0
        self.sockopt = []


class HttpTest(unittest.TestCase):

    def testReadHeader(self):
        status, header, status_message = read_headers(HeaderSockMock("data/header01.txt"))
        self.assertEqual(status, 101)
        self.assertEqual(header["connection"], "Upgrade")
        # header02.txt is intentionally malformed
        self.assertRaises(ws.WebSocketException, read_headers, HeaderSockMock("data/header02.txt"))

    def testTunnel(self):
        self.assertRaises(ws.WebSocketProxyException, _tunnel, HeaderSockMock("data/header01.txt"), "example.com", 80, ("username", "password"))
        self.assertRaises(ws.WebSocketProxyException, _tunnel, HeaderSockMock("data/header02.txt"), "example.com", 80, ("username", "password"))

    def testConnect(self):
        # Not currently testing an actual proxy connection, so just check whether TypeError is raised
        self.assertRaises(TypeError, _open_proxied_socket, "wss://example.com", OptsList(), proxy_info(http_proxy_host="example.com", http_proxy_port="8080", proxy_type="http"))
        self.assertRaises(TypeError, _open_proxied_socket, "wss://example.com", OptsList(), proxy_info(http_proxy_host="example.com", http_proxy_port="8080", proxy_type="socks4"))
        self.assertRaises(TypeError, _open_proxied_socket, "wss://example.com", OptsList(), proxy_info(http_proxy_host="example.com", http_proxy_port="8080", proxy_type="socks5h"))

    def testProxyInfo(self):
        self.assertEqual(proxy_info(http_proxy_host="127.0.0.1", http_proxy_port="8080", proxy_type="http").type, "http")
        self.assertRaises(ValueError, proxy_info, http_proxy_host="127.0.0.1", http_proxy_port="8080", proxy_type="badval")
        self.assertEqual(proxy_info(http_proxy_host="example.com", http_proxy_port="8080", proxy_type="http").host, "example.com")
        self.assertEqual(proxy_info(http_proxy_host="127.0.0.1", http_proxy_port="8080", proxy_type="http").port, "8080")
        self.assertEqual(proxy_info(http_proxy_host="127.0.0.1", http_proxy_port="8080", proxy_type="http").auth, None)


if __name__ == "__main__":
    unittest.main()
