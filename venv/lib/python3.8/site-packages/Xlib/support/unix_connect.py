# Xlib.support.unix_connect -- Unix-type display connection functions
#
#    Copyright (C) 2000,2002 Peter Liljenberg <petli@ctrl-c.liu.se>
#    Copyright (C) 2013 LiuLang <gsushzhsosgsu@gmail.com>
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

import fcntl
import os
import platform
import re
import socket

F_SETFD = fcntl.F_SETFD
FD_CLOEXEC = fcntl.FD_CLOEXEC

from Xlib import error, xauth

uname = platform.uname()
if (uname[0] == 'Darwin') and ([int(x) for x in uname[2].split('.')] >= [9, 0]):

    display_re = re.compile(r'^([-a-zA-Z0-9._/]*):([0-9]+)(\.([0-9]+))?$')

else:

    display_re = re.compile(r'^([-a-zA-Z0-9._]*):([0-9]+)(\.([0-9]+))?$')

def get_display(display):
    # Use $DISPLAY if display isn't provided
    if display is None:
        display = os.environ.get('DISPLAY', '')

    m = display_re.match(display)
    if not m:
        raise error.DisplayNameError(display)

    name = display
    host = m.group(1)
    dno = int(m.group(2))
    screen = m.group(4)
    if screen:
        screen = int(screen)
    else:
        screen = 0

    return name, host, dno, screen


def get_socket(dname, host, dno):
    try:
        # Darwin funky socket
        if (uname[0] == 'Darwin') and host and host.startswith('/tmp/'):
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(dname)

        # If hostname (or IP) is provided, use TCP socket
        elif host:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, 6000 + dno))

        # Else use Unix socket
        else:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect('/tmp/.X11-unix/X%d' % dno)
    except OSError as val:
        raise error.DisplayConnectionError(dname, str(val))

    # Make sure that the connection isn't inherited in child processes
    fcntl.fcntl(s.fileno(), F_SETFD, FD_CLOEXEC)

    return s


def new_get_auth(sock, dname, host, dno):
    # Translate socket address into the xauth domain
    if (uname[0] == 'Darwin') and host and host.startswith('/tmp/'):
        family = xauth.FamilyLocal
        addr = socket.gethostname()

    elif host:
        family = xauth.FamilyInternet

        # Convert the prettyprinted IP number into 4-octet string.
        # Sometimes these modules are too damn smart...
        octets = sock.getpeername()[0].split('.')
        addr = ''.join(map(lambda x: chr(int(x)), octets))
    else:
        family = xauth.FamilyLocal
        addr = socket.gethostname()

    au = xauth.Xauthority()
    while 1:
        try:
            return au.get_best_auth(family, addr, dno)
        except error.XNoAuthError:
            pass

        # We need to do this to handle ssh's X forwarding.  It sets
        # $DISPLAY to localhost:10, but stores the xauth cookie as if
        # DISPLAY was :10.  Hence, if localhost and not found, try
        # again as a Unix socket.
        if family == xauth.FamilyInternet and addr == '\x7f\x00\x00\x01':
            family = xauth.FamilyLocal
            addr = socket.gethostname()
        else:
            return '', ''


def old_get_auth(sock, dname, host, dno):
    # Find authorization cookie
    auth_name = auth_data = ''

    try:
        # We could parse .Xauthority, but xauth is simpler
        # although more inefficient
        data = os.popen('xauth list %s 2>/dev/null' % dname).read()

        # If there's a cookie, it is of the format
        #      DISPLAY SCHEME COOKIE
        # We're interested in the two last parts for the
        # connection establishment
        lines = data.split('\n')
        if len(lines) >= 1:
            parts = lines[0].split(None, 2)
            if len(parts) == 3:
                auth_name = parts[1]
                hexauth = parts[2]
                auth = ''

                # Translate hexcode into binary
                for i in range(0, len(hexauth), 2):
                    auth = auth + chr(int(hexauth[i:i+2], 16))

                auth_data = auth
    except os.error:
        pass

    return auth_name, auth_data

get_auth = new_get_auth
