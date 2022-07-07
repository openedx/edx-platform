# Xlib.ext.xtest -- XTEST extension module
#
#    Copyright (C) 2000 Peter Liljenberg <petli@ctrl-c.liu.se>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from Xlib import X
from Xlib.protocol import rq

extname = 'XTEST'

CurrentCursor = 1

class GetVersion(rq.ReplyRequest):
    _request = rq.Struct(rq.Card8('opcode'),
                         rq.Opcode(0),
                         rq.RequestLength(),
                         rq.Card8('major_version'),
                         rq.Pad(1),
                         rq.Card16('minor_version')
                         )

    _reply = rq.Struct(rq.Pad(1),
                       rq.Card8('major_version'),
                       rq.Card16('sequence_number'),
                       rq.Pad(4),
                       rq.Card16('minor_version'),
                       rq.Pad(22)
                       )

def get_version(self, major, minor):
    return GetVersion(display = self.display,
                      opcode = self.display.get_extension_major(extname),
                      major_version = major,
                      minor_version = minor)


class CompareCursor(rq.ReplyRequest):
    _request = rq.Struct(rq.Card8('opcode'),
                         rq.Opcode(1),
                         rq.RequestLength(),
                         rq.Window('window'),
                         rq.Cursor('cursor', (X.NONE, CurrentCursor)),
                         )

    _reply = rq.Struct(rq.Pad(1),
                       rq.Card8('same'),
                       rq.Card16('sequence_number'),
                       rq.Pad(28),
                       )

def compare_cursor(self, cursor):
    r = CompareCursor(display = self.display,
                      opcode = self.display.get_extension_major(extname),
                      window = self.id,
                      cursor = cursor)
    return r.same

class FakeInput(rq.Request):
    _request = rq.Struct(rq.Card8('opcode'),
                         rq.Opcode(2),
                         rq.RequestLength(),
                         rq.Set('event_type', 1, (X.KeyPress,
                                                  X.KeyRelease,
                                                  X.ButtonPress,
                                                  X.ButtonRelease,
                                                  X.MotionNotify)),
                         rq.Card8('detail'),
                         rq.Pad(2),
                         rq.Card32('time'),
                         rq.Window('root', (X.NONE, )),
                         rq.Pad(8),
                         rq.Int16('x'),
                         rq.Int16('y'),
                         rq.Pad(8)
                         )

def fake_input(self, event_type, detail = 0, time = X.CurrentTime,
               root = X.NONE, x = 0, y = 0):

    FakeInput(display = self.display,
              opcode = self.display.get_extension_major(extname),
              event_type = event_type,
              detail = detail,
              time = time,
              root = root,
              x = x,
              y = y)

class GrabControl(rq.Request):
    _request = rq.Struct(rq.Card8('opcode'),
                         rq.Opcode(3),
                         rq.RequestLength(),
                         rq.Bool('impervious'),
                         rq.Pad(3)
                         )

def grab_control(self, impervious):
    GrabControl(display = self.display,
                opcode = self.display.get_extension_major(extname),
                impervious = impervious)

def init(disp, info):
    disp.extension_add_method('display', 'xtest_get_version', get_version)
    disp.extension_add_method('window', 'xtest_compare_cursor', compare_cursor)
    disp.extension_add_method('display', 'xtest_fake_input', fake_input)
    disp.extension_add_method('display', 'xtest_grab_control', grab_control)
