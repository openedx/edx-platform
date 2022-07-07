# Xlib.support.vms_connect -- VMS-type display connection functions
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

import re
import socket

from Xlib import error

display_re = re.compile(r'^([-a-zA-Z0-9._]*):([0-9]+)(\.([0-9]+))?$')

def get_display(display):

    # Use dummy display if none is set.  We really should
    # check DECW$DISPLAY instead, but that has to wait

    if display is None:
        return ':0.0', 'localhost', 0, 0

    m = display_re.match(display)
    if not m:
        raise error.DisplayNameError(display)

    name = display

    # Always return a host, since we don't have AF_UNIX sockets
    host = m.group(1)
    if not host:
        host = 'localhost'

    dno = int(m.group(2))
    screen = m.group(4)
    if screen:
        screen = int(screen)
    else:
        screen = 0

    return name, host, dno, screen


def get_socket(dname, host, dno):
    try:
        # Always use TCP/IP sockets.  Later it would be nice to
        # be able to use DECNET och LOCAL connections.

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, 6000 + dno))

    except OSError as val:
        raise error.DisplayConnectionError(dname, str(val))

    return s


def get_auth(sock, dname, host, dno):
    # VMS doesn't have xauth
    return '', ''
