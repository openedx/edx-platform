# Xlib.xauth -- ~/.Xauthority access
#
#    Copyright (C) 2000 Peter Liljenberg <petli@ctrl-c.liu.se>
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

import os
import struct

from Xlib import X, error

FamilyInternet = X.FamilyInternet
FamilyDECnet = X.FamilyDECnet
FamilyChaos = X.FamilyChaos
FamilyLocal = 256

class Xauthority:
    def __init__(self, filename = None):
        if filename is None:
            filename = os.environ.get('XAUTHORITY')

        if filename is None:
            try:
                filename = os.path.join(os.environ['HOME'], '.Xauthority')
            except KeyError:
                raise error.XauthError(
                    '$HOME not set, cannot find ~/.Xauthority')

        try:
            raw = open(filename, 'rb').read()
        except OSError as err:
            raise error.XauthError('~/.Xauthority: %s' % err)

        self.entries = []

        # entry format (all shorts in big-endian)
        #   short family;
        #   short addrlen;
        #   char addr[addrlen];
        #   short numlen;
        #   char num[numlen];
        #   short namelen;
        #   char name[namelen];
        #   short datalen;
        #   char data[datalen];

        n = 0
        try:
            while n < len(raw):
                family, = struct.unpack('>H', raw[n:n+2])
                n = n + 2

                length, = struct.unpack('>H', raw[n:n+2])
                n = n + length + 2
                addr = raw[n - length : n]

                length, = struct.unpack('>H', raw[n:n+2])
                n = n + length + 2
                num = raw[n - length : n]

                length, = struct.unpack('>H', raw[n:n+2])
                n = n + length + 2
                name = raw[n - length : n]

                length, = struct.unpack('>H', raw[n:n+2])
                n = n + length + 2
                data = raw[n - length : n]

                if len(data) != length:
                    break

                self.entries.append((family, addr, num, name, data, ))
        except struct.error as e:
            print("Xlib.xauth: warning, failed to parse part of xauthority file (%s), aborting all further parsing" % filename)

        if len(self.entries) == 0:
            print("Xlib.xauth: warning, no xauthority details available")
            # raise an error?  this should get partially caught by the XNoAuthError in get_best_auth..

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, i):
        return self.entries[i]

    def get_best_auth(self, family, address, dispno,
                      types = ( b"MIT-MAGIC-COOKIE-1", )):

        """Find an authentication entry matching FAMILY, ADDRESS and
        DISPNO.

        The name of the auth scheme must match one of the names in
        TYPES.  If several entries match, the first scheme in TYPES
        will be choosen.

        If an entry is found, the tuple (name, data) is returned,
        otherwise XNoAuthError is raised.
        """

        num = str(dispno).encode()
        address = address.encode()

        matches = {}

        for efam, eaddr, enum, ename, edata in self.entries:
            if efam == family and eaddr == address and num == enum:
                matches[ename] = edata

        for t in types:
            try:
                return (t, matches[t])
            except KeyError:
                pass

        raise error.XNoAuthError((family, address, dispno))
