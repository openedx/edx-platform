# Xlib.ext.xinerama -- Xinerama extension module
#
#    Copyright (C) 2006 Mike Meyer <mwm@mired.org>
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



"""Xinerama - provide access to the Xinerama extension information.

There are at least there different - and mutually incomparable -
Xinerama extensions available. This uses the one bundled with XFree86
4.6 and/or Xorg 6.9 in the ati/radeon driver. It uses the include
files from that X distribution, so should work with it as well.  I
provide code for the lone Sun 1.0 request that isn't part of 1.1, but
this is untested because I don't have a server that implements it.

The functions loosely follow the libXineram functions. Mostly, they
return an rq.Struct in lieue of passing in pointers that get data from
the rq.Struct crammed into them. The exception is isActive, which
returns the state information - because that's what libXinerama does."""


from Xlib import X
from Xlib.protocol import rq, structs

extname = 'XINERAMA'


class QueryVersion(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(0),
        rq.RequestLength(),
        rq.Card8('major_version'),
        rq.Card8('minor_version'),
        rq.Pad(2),
        )

    _reply = rq.Struct(
            rq.ReplyCode(),
            rq.Pad(1),
            rq.Card16('sequence_number'),
            rq.ReplyLength(),
            rq.Card16('major_version'),
            rq.Card16('minor_version'),
            rq.Pad(20),
            )

def query_version(self):
    return QueryVersion(display=self.display,
                        opcode=self.display.get_extension_major(extname),
                        major_version=1,
                        minor_version=1)


class GetState(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(1),
        rq.RequestLength(),
        rq.Window('window'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Bool('state'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('window'),
        rq.Pad(20),
        )

def get_state(self):
    return GetState(display=self.display,
                    opcode=self.display.get_extension_major(extname),
                    window=self.id,
                    )


class GetScreenCount(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(2),
        rq.RequestLength(),
        rq.Window('window'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('screen_count'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('window'),
        rq.Pad(20),
        )

def get_screen_count(self):
    return GetScreenCount(display=self.display,
                          opcode=self.display.get_extension_major(extname),
                          window=self.id,
                          )


class GetScreenSize(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(3),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Card32('screen'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.Card32('length'),
        rq.Card32('width'),
        rq.Card32('height'),
        rq.Window('window'),
        rq.Card32('screen'),
        rq.Pad(8),
        )

def get_screen_size(self, screen_no):
    """Returns the size of the given screen number"""
    return GetScreenSize(display=self.display,
                         opcode=self.display.get_extension_major(extname),
                         window=self.id,
                         screen=screen_no,
                         )


# IsActive is only available from Xinerama 1.1 and later.
# It should be used in preference to GetState.
class IsActive(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(4),
        rq.RequestLength(),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('state'),
        rq.Pad(20),
        )

def is_active(self):
    r = IsActive(display=self.display,
                 opcode=self.display.get_extension_major(extname),
                 )
    return r.state


# QueryScreens is only available from Xinerama 1.1 and later
class QueryScreens(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(5),
        rq.RequestLength(),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('number'),
        rq.Pad(20),
        rq.List('screens', structs.Rectangle),
        )

def query_screens(self):
    # Hmm. This one needs to read the screen data from the socket. Ooops...
    return QueryScreens(display=self.display,
                        opcode=self.display.get_extension_major(extname),
                        )


# GetInfo is only available from some Xinerama 1.0, and *NOT* later! Untested
class GetInfo(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(4),
        rq.RequestLength(),
        rq.Card32('visual'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('window'),
        # An array of subwindow slots goes here. Bah.
        )

def get_info(self, visual):
    r = GetInfo(display=self.display,
             opcode=self.display.get_extension_major(extname),
             visual=visual)

def init(disp, info):
    disp.extension_add_method('display', 'xinerama_query_version', query_version)
    disp.extension_add_method('window', 'xinerama_get_state', get_state)
    disp.extension_add_method('window', 'xinerama_get_screen_count', get_screen_count)
    disp.extension_add_method('window', 'xinerama_get_screen_size', get_screen_size)
    disp.extension_add_method('display', 'xinerama_is_active', is_active)
    disp.extension_add_method('display', 'xinerama_query_screens', query_screens)
    disp.extension_add_method('display', 'xinerama_get_info', get_info)
