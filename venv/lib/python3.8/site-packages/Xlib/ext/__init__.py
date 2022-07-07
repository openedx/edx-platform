# Xlib.ext.__init__ -- X extension modules
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

# __extensions__ is a list of tuples: (extname, extmod)
# extname is the name of the extension according to the X
# protocol.  extmod is the name of the module in this package.

__extensions__ = [
    ('XTEST', 'xtest'),
    ('SHAPE', 'shape'),
    ('XINERAMA', 'xinerama'),
    ('RECORD', 'record'),
    ('Composite', 'composite'),
    ('RANDR', 'randr'),
    ]

__all__ = [x[1] for x in __extensions__]
