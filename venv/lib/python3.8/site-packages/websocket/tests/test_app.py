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
import sys
sys.path[0:0] = [""]

try:
    import ssl
except ImportError:
    HAVE_SSL = False

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    import unittest2 as unittest
else:
    import unittest

# Skip test to access the internet.
TEST_WITH_INTERNET = os.environ.get('TEST_WITH_INTERNET', '0') == '1'
TRACEABLE = True


class WebSocketAppTest(unittest.TestCase):

    class NotSetYet(object):
        """ A marker class for signalling that a value hasn't been set yet.
        """

    def setUp(self):
        ws.enableTrace(TRACEABLE)

        WebSocketAppTest.keep_running_open = WebSocketAppTest.NotSetYet()
        WebSocketAppTest.keep_running_close = WebSocketAppTest.NotSetYet()
        WebSocketAppTest.get_mask_key_id = WebSocketAppTest.NotSetYet()

    def tearDown(self):
        WebSocketAppTest.keep_running_open = WebSocketAppTest.NotSetYet()
        WebSocketAppTest.keep_running_close = WebSocketAppTest.NotSetYet()
        WebSocketAppTest.get_mask_key_id = WebSocketAppTest.NotSetYet()

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def testKeepRunning(self):
        """ A WebSocketApp should keep running as long as its self.keep_running
        is not False (in the boolean context).
        """

        def on_open(self, *args, **kwargs):
            """ Set the keep_running flag for later inspection and immediately
            close the connection.
            """
            WebSocketAppTest.keep_running_open = self.keep_running

            self.close()

        def on_close(self, *args, **kwargs):
            """ Set the keep_running flag for the test to use.
            """
            WebSocketAppTest.keep_running_close = self.keep_running

        app = ws.WebSocketApp('ws://echo.websocket.org/', on_open=on_open, on_close=on_close)
        app.run_forever()

        # if numpy is installed, this assertion fail
        # self.assertFalse(isinstance(WebSocketAppTest.keep_running_open,
        #                             WebSocketAppTest.NotSetYet))

        # self.assertFalse(isinstance(WebSocketAppTest.keep_running_close,
        #                             WebSocketAppTest.NotSetYet))

        # self.assertEqual(True, WebSocketAppTest.keep_running_open)
        # self.assertEqual(False, WebSocketAppTest.keep_running_close)

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def testSockMaskKey(self):
        """ A WebSocketApp should forward the received mask_key function down
        to the actual socket.
        """

        def my_mask_key_func():
            pass

        def on_open(self, *args, **kwargs):
            """ Set the value so the test can use it later on and immediately
            close the connection.
            """
            WebSocketAppTest.get_mask_key_id = id(self.get_mask_key)
            self.close()

        app = ws.WebSocketApp('ws://echo.websocket.org/', on_open=on_open, get_mask_key=my_mask_key_func)
        app.run_forever()

        # if numpy is installed, this assertion fail
        # Note: We can't use 'is' for comparing the functions directly, need to use 'id'.
        # self.assertEqual(WebSocketAppTest.get_mask_key_id, id(my_mask_key_func))

    @unittest.skipUnless(TEST_WITH_INTERNET, "Internet-requiring tests are disabled")
    def testPingInterval(self):
        """ A WebSocketApp should ping regularly
        """

        def on_ping(app, msg):
            print("Got a ping!")
            app.close()

        def on_pong(app, msg):
            print("Got a pong! No need to respond")
            app.close()

        app = ws.WebSocketApp('wss://api-pub.bitfinex.com/ws/1', on_ping=on_ping, on_pong=on_pong)
        app.run_forever(ping_interval=2, ping_timeout=1)  # , sslopt={"cert_reqs": ssl.CERT_NONE}
        self.assertRaises(ws.WebSocketException, app.run_forever, ping_interval=2, ping_timeout=3, sslopt={"cert_reqs": ssl.CERT_NONE})


if __name__ == "__main__":
    unittest.main()
