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
import websocket as ws
from websocket._abnf import *
import sys
sys.path[0:0] = [""]

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    import unittest2 as unittest
else:
    import unittest


class ABNFTest(unittest.TestCase):

    def testInit(self):
        a = ABNF(0,0,0,0, opcode=ABNF.OPCODE_PING)
        self.assertEqual(a.fin, 0)
        self.assertEqual(a.rsv1, 0)
        self.assertEqual(a.rsv2, 0)
        self.assertEqual(a.rsv3, 0)
        self.assertEqual(a.opcode, 9)
        self.assertEqual(a.data, '')
        a_bad = ABNF(0,1,0,0, opcode=77)
        self.assertEqual(a_bad.rsv1, 1)
        self.assertEqual(a_bad.opcode, 77)

    def testValidate(self):
        a = ABNF(0,0,0,0, opcode=ABNF.OPCODE_PING)
        self.assertRaises(ws.WebSocketProtocolException, a.validate)
        a_bad = ABNF(0,1,0,0, opcode=77)
        self.assertRaises(ws.WebSocketProtocolException, a_bad.validate)
        a_close = ABNF(0,1,0,0, opcode=ABNF.OPCODE_CLOSE, data="abcdefgh1234567890abcdefgh1234567890abcdefgh1234567890abcdefgh1234567890")
        self.assertRaises(ws.WebSocketProtocolException, a_close.validate)

#    This caused an error in the Python 2.7 Github Actions build
#    Uncomment test case when Python 2 support no longer wanted
#    def testMask(self):
#        ab = ABNF(0,0,0,0, opcode=ABNF.OPCODE_PING)
#        bytes_val = bytes("aaaa", 'utf-8')
#        self.assertEqual(ab._get_masked(bytes_val), bytes_val)

    def testFrameBuffer(self):
        fb = frame_buffer(0, True)
        self.assertEqual(fb.recv, 0)
        self.assertEqual(fb.skip_utf8_validation, True)
        fb.clear
        self.assertEqual(fb.header, None)
        self.assertEqual(fb.length, None)
        self.assertEqual(fb.mask, None)
        self.assertEqual(fb.has_mask(), False)


if __name__ == "__main__":
    unittest.main()
