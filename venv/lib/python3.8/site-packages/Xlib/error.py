# Xlib.error -- basic error classes
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

# Xlib modules
from Xlib import X

# Xlib.protocol modules
from Xlib.protocol import rq


class DisplayError(Exception):
    def __init__(self, display):
        self.display = display

    def __str__(self):
        return 'Display error "%s"' % self.display

class DisplayNameError(DisplayError):
    def __str__(self):
        return 'Bad display name "%s"' % self.display

class DisplayConnectionError(DisplayError):
    def __init__(self, display, msg):
        self.display = display
        self.msg = msg

    def __str__(self):
        return 'Can\'t connect to display "%s": %s' % (self.display, self.msg)

class ConnectionClosedError(Exception):
    def __init__(self, whom):
        self.whom = whom

    def __str__(self):
        return 'Display connection closed by %s' % self.whom


class XauthError(Exception): pass
class XNoAuthError(Exception): pass

class ResourceIDError(Exception): pass


class XError(rq.GetAttrData, Exception):
    _fields = rq.Struct( rq.Card8('type'),  # Always 0
                         rq.Card8('code'),
                         rq.Card16('sequence_number'),
                         rq.Card32('resource_id'),
                         rq.Card16('minor_opcode'),
                         rq.Card8('major_opcode'),
                         rq.Pad(21)
                         )

    def __init__(self, display, data):
        self._data, data = self._fields.parse_binary(data, display, rawdict = 1)

    def __str__(self):
        s = []
        for f in ('code', 'resource_id', 'sequence_number',
                  'major_opcode', 'minor_opcode'):
            s.append('%s = %s' % (f, self._data[f]))

        return '%s: %s' % (self.__class__, ', '.join(s))

class XResourceError(XError):
    _fields = rq.Struct( rq.Card8('type'),  # Always 0
                         rq.Card8('code'),
                         rq.Card16('sequence_number'),
                         rq.Resource('resource_id'),
                         rq.Card16('minor_opcode'),
                         rq.Card8('major_opcode'),
                         rq.Pad(21)
                         )

class BadRequest(XError): pass
class BadValue(XError): pass
class BadWindow(XResourceError): pass
class BadPixmap(XResourceError): pass
class BadAtom(XError): pass
class BadCursor(XResourceError): pass
class BadFont(XResourceError): pass
class BadMatch(XError): pass
class BadDrawable(XResourceError): pass
class BadAccess(XError): pass
class BadAlloc(XError): pass
class BadColor(XResourceError): pass
class BadGC(XResourceError): pass
class BadIDChoice(XResourceError): pass
class BadName(XError): pass
class BadLength(XError): pass
class BadImplementation(XError): pass

xerror_class = {
    X.BadRequest: BadRequest,
    X.BadValue: BadValue,
    X.BadWindow: BadWindow,
    X.BadPixmap: BadPixmap,
    X.BadAtom: BadAtom,
    X.BadCursor: BadCursor,
    X.BadFont: BadFont,
    X.BadMatch: BadMatch,
    X.BadDrawable: BadDrawable,
    X.BadAccess: BadAccess,
    X.BadAlloc: BadAlloc,
    X.BadColor: BadColor,
    X.BadGC: BadGC,
    X.BadIDChoice: BadIDChoice,
    X.BadName: BadName,
    X.BadLength: BadLength,
    X.BadImplementation: BadImplementation,
    }


class CatchError:
    def __init__(self, *errors):
        self.error_types = errors
        self.error = None
        self.request = None

    def __call__(self, error, request):
        if self.error_types:
            for etype in self.error_types:
                if isinstance(error, etype):
                    self.error = error
                    self.request = request
                    return 1

            return 0
        else:
            self.error = error
            self.request = request
            return 1

    def get_error(self):
        return self.error

    def get_request(self):
        return self.request

    def reset(self):
        self.error = None
        self.request = None
