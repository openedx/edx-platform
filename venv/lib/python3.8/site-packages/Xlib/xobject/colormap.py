# Xlib.xobject.colormap -- colormap object
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
import string

from Xlib import error
from Xlib.protocol import request
from Xlib.xobject import resource

rgb_res = [
    re.compile(r'\Argb:([0-9a-fA-F]{1,4})/([0-9a-fA-F]{1,4})/([0-9a-fA-F]{1,4})\Z'),
    re.compile(r'\A#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])\Z'),
    re.compile(r'\A#([0-9a-fA-F][0-9a-fA-F])([0-9a-fA-F][0-9a-fA-F])([0-9a-fA-F][0-9a-fA-F])\Z'),
    re.compile(r'\A#([0-9a-fA-F][0-9a-fA-F][0-9a-fA-F])([0-9a-fA-F][0-9a-fA-F][0-9a-fA-F])([0-9a-fA-F][0-9a-fA-F][0-9a-fA-F])\Z'),
    re.compile(r'\A#([0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F])([0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F])([0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F])\Z'),
    ]

class Colormap(resource.Resource):
    __colormap__ = resource.Resource.__resource__

    def free(self, onerror = None):
        request.FreeColormap(display = self.display,
                             onerror = onerror,
                             cmap = self.id)

        self.display.free_resource_id(self.id)

    def copy_colormap_and_free(self, scr_cmap):
        mid = self.display.allocate_resource_id()
        request.CopyColormapAndFree(display = self.display,
                                    mid = mid,
                                    src_cmap = src_cmap)

        cls = self.display.get_resource_class('colormap', Colormap)
        return cls(self.display, mid, owner = 1)

    def install_colormap(self, onerror = None):
        request.InstallColormap(display = self.display,
                                onerror = onerror,
                                cmap = self.id)

    def uninstall_colormap(self, onerror = None):
        request.UninstallColormap(display = self.display,
                                  onerror = onerror,
                                  cmap = self.id)

    def alloc_color(self, red, green, blue):
        return request.AllocColor(display = self.display,
                                  cmap = self.id,
                                  red = red,
                                  green = green,
                                  blue = blue)

    def alloc_named_color(self, name):
        for r in rgb_res:
            m = r.match(name)
            if m:
                rs = m.group(1)
                r = string.atoi(rs + '0' * (4 - len(rs)), 16)

                gs = m.group(2)
                g = string.atoi(gs + '0' * (4 - len(gs)), 16)

                bs = m.group(3)
                b = string.atoi(bs + '0' * (4 - len(bs)), 16)

                return self.alloc_color(r, g, b)

        try:
            return request.AllocNamedColor(display = self.display,
                                           cmap = self.id,
                                           name = name)
        except error.BadName:
            return None

    def alloc_color_cells(self, contiguous, colors, planes):
        return request.AllocColorCells(display = self.display,
                                       contiguous = contiguous,
                                       cmap = self.id,
                                       colors = colors,
                                       planes = planes)

    def alloc_color_planes(self, contiguous, colors, red, green, blue):
        return request.AllocColorPlanes(display = self.display,
                                        contiguous = contiguous,
                                        cmap = self.id,
                                        colors = colors,
                                        red = red,
                                        green = green,
                                        blue = blue)

    def free_colors(self, pixels, plane_mask, onerror = None):
        request.FreeColors(display = self.display,
                           onerror = onerror,
                           cmap = self.id,
                           plane_mask = plane_mask,
                           pixels = pixels)

    def store_colors(self, items, onerror = None):
        request.StoreColors(display = self.display,
                            onerror = onerror,
                            cmap = self.id,
                            items = items)

    def store_named_color(self, name, pixel, flags, onerror = None):
        request.StoreNamedColor(display = self.display,
                                onerror = onerror,
                                flags = flags,
                                cmap = self.id,
                                pixel = pixel,
                                name = name)

    def query_colors(self, pixels):
        r = request.QueryColors(display = self.display,
                                cmap = self.id,
                                pixels = pixels)
        return r.colors

    def lookup_color(self, name):
        return request.LookupColor(display = self.display,
                                   cmap = self.id,
                                   name = name)
