# Xlib.support.lock -- allocate a lock
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

class _DummyLock:
    def __init__(self):

        # This might be nerdy, but by assigning methods like this
        # instead of defining them all, we create a single bound
        # method object once instead of one each time one of the
        # methods is called.

        # This gives some speed improvements which should reduce the
        # impact of the threading infrastructure in the regular code,
        # when not using threading.

        self.acquire = self.release = self.locked = self.__noop

    def __noop(self, *args):
        return


# More optimisations: we use a single lock for all lock instances
_dummy_lock = _DummyLock()

def allocate_lock():
    return _dummy_lock
