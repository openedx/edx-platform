# Xlib.xobject.fontable -- fontable objects (GC, font)
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
from Xlib.xobject import resource, cursor

class Fontable(resource.Resource):
    __fontable__ = resource.Resource.__resource__

    def query(self):
        return request.QueryFont(display = self.display,
                                 font = self.id)

    def query_text_extents(self, string):
        return request.QueryTextExtents(display = self.display,
                                        font = self.id,
                                        string = string)


class GC(Fontable):
    __gc__ = resource.Resource.__resource__

    def change(self, onerror = None, **keys):
        request.ChangeGC(display = self.display,
                         onerror = onerror,
                         gc = self.id,
                         attrs = keys)


    def copy(self, src_gc, mask, onerror = None):
        request.CopyGC(display = self.display,
                       onerror = onerror,
                       src_gc = src_gc,
                       dst_gc = self.id,
                       mask = mask)

    def set_dashes(self, offset, dashes, onerror = None):
        request.SetDashes(display = self.display,
                          onerror = onerror,
                          gc = self.id,
                          dash_offset = offset,
                          dashes = dashes)

    def set_clip_rectangles(self, x_origin, y_origin, rectangles, ordering, onerror = None):
        request.SetClipRectangles(display = self.display,
                                  onerror = onerror,
                                  ordering = ordering,
                                  gc = self.id,
                                  x_origin = x_origin,
                                  y_origin = y_origin,
                                  rectangles = rectangles)
    def free(self, onerror = None):
        request.FreeGC(display = self.display,
                       onerror = onerror,
                       gc = self.id)

        self.display.free_resource_id(self.id)



class Font(Fontable):
    __font__ = resource.Resource.__resource__

    def close(self, onerror = None):
        request.CloseFont(display = self.display,
                          onerror = onerror,
                          font = self.id)
        self.display.free_resource_id(self.id)

    def create_glyph_cursor(self, mask, source_char, mask_char,
                            f_rgb, b_rgb):
        fore_red, fore_green, fore_blue = f_rgb
        back_red, back_green, back_blue = b_rgb

        cid = self.display.allocate_resource_id()
        request.CreateGlyphCursor(display = self.display,
                                  cid = cid,
                                  source = self.id,
                                  mask = mask,
                                  source_char = source_char,
                                  mask_char = mask_char,
                                  fore_red = fore_red,
                                  fore_green = fore_green,
                                  fore_blue = fore_blue,
                                  back_red = back_red,
                                  back_green = back_green,
                                  back_blue = back_blue)

        cls = self.display.get_resource_class('cursor', cursor.Cursor)
        return cls(self.display, cid, owner = 1)
