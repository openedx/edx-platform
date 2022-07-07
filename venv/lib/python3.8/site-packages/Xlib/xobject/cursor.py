# Xlib.xobject.cursor -- cursor object
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

from Xlib.protocol import request
from Xlib.xobject import resource

class Cursor(resource.Resource):
    __cursor__ = resource.Resource.__resource__

    def free(self, onerror = None):
        request.FreeCursor(display = self.display,
                           onerror = onerror,
                           cursor = self.id)
        self.display.free_resource_id(self.id)

    def recolor(self, f_rgb, b_rgb, onerror = None):
        back_red, back_green, back_blue = b_rgb
        fore_red, fore_green, fore_blue = f_rgb
        request.RecolorCursor(display = self.display,
                              onerror = onerror,
                              cursor = self.id,
                              fore_red = fore_red,
                              fore_green = fore_green,
                              fore_blue = fore_blue,
                              back_red = back_red,
                              back_green = back_green,
                              back_blue = back_blue)
