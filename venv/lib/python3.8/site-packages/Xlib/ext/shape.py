# Xlib.ext.shape -- SHAPE extension module
#
#    Copyright (C) 2002 Jeffrey Boser <verin@lvcm.com>
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


# Constants to use
#
# Regions of a window
ShapeBounding = 0       # the 'edge' of a shaped window
ShapeClip = 1           # the clipping region
# Shape Operations
ShapeSet = 0            # Set the region unmodified (dest=src)
ShapeUnion = 1          # Add the new region to the old (dest=src|dest)
ShapeIntersect = 2      # Use the intersection (dest=src&dest)
ShapeSubtract = 3       # remove region (dest = dest - intersect)
ShapeInvert = 4         # opposite of subtract (dest = src - intersect)
# Events
ShapeNotifyMask = (1<<0)        #a keypress mask?
ShapeNotify = 0                 #still unsure of these values

# How to Use
# The basic functions that change the shapes of things are:
#   shape_rectangles (uses a set of rectangles as the source)
#       operation, region, ordering, rects
#   shape_mask (uses a bitmap as the source)
#       operation, region, x_offset, y_offset, bitmap
#   shape_combine (uses a window as the source)
#       operation, src_region, dest_region, x_offset, y_offset, src_window
#   shape_offset (moves the region)
#       region, x_offset, y_offset
# The functions to find stuff out (these three return mappings of field/values):
#   shape_query_version (shape extension version)
#       major_version, minor_version
#   shape_query_extents (rectangle boundaries of a window's regions)
#       clip_shaped, clip_x, clip_y, clip_width, clip_height,
#       bounding_shaped, bounding_x, bounding_y, bounding_width, bounding_height
#   shape_input_selected (if the window products shapenotify events)
#       enabled
#   shape_get_rectangles (the rectangles set by shape_rectangles)
#       ordering, rects
# And to turn on shape notify events:
#   shape_select_input
#       enable



from Xlib import X
from Xlib.protocol import rq, structs

extname = 'SHAPE'

class QueryVersion(rq.ReplyRequest):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(0),
            rq.RequestLength(),
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
    return QueryVersion(
        display = self.display,
        opcode = self.display.get_extension_major(extname),
        )



class Rectangles(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(1),
            rq.RequestLength(),
            rq.Card8('operation'),
            rq.Set('region', 1, (ShapeBounding, ShapeClip)),
            rq.Card8('ordering'),
            rq.Pad(1),
            rq.Window('window'),
            rq.Int16('x'),
            rq.Int16('y'),
            rq.List('rectangles', structs.Rectangle),
            )

def rectangles(self, region, operation, ordering, x, y, rectangles):
    Rectangles(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            operation = operation,
            region = region,
            ordering = ordering,
            window = self.id,
            x = x,
            y = y,
            rectangles = rectangles,
            )



class Mask(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(2),
            rq.RequestLength(),
            rq.Card8('operation'),
            rq.Set('region', 1, (ShapeBounding, ShapeClip)),
            rq.Pad(2),
            rq.Window('window'),
            rq.Int16('x'),
            rq.Int16('y'),
            rq.Pixmap('source', (X.NONE, )),
            )

def mask(self, operation, region, x, y, source):
    Mask(display = self.display,
         opcode = self.display.get_extension_major(extname),
         window = self.id,
         operation = operation,
         region = region,
         x = x,
         y = y,
         source = source,
         )


class Combine(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(3),
            rq.RequestLength(),
            rq.Card8('operation'),
            rq.Set('dest_region', 1, (ShapeBounding, ShapeClip)),
            rq.Set('source_region', 1, (ShapeBounding, ShapeClip)),
            rq.Pad(1),
            rq.Window('dest'),
            rq.Int16('x'),
            rq.Int16('y'),
            rq.Window('source'),
            )

def combine(self, operation, region, source, source_region, x, y):
    Combine(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            operation = operation,
            dest_region = region,
            source_region = source_region,
            dest = self.id,
            x = x,
            y = y,
            source = source,
            )



class Offset(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(4),
            rq.RequestLength(),
            rq.Set('region', 1, (ShapeBounding, ShapeClip)),
            rq.Pad(3),
            rq.Window('window'),
            rq.Int16('x'),
            rq.Int16('y'),
            )

def offset(self, region, x, y):
    Offset(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            region = region,
            window = self.id,
            x = x,
            y = y,
            )



class QueryExtents(rq.ReplyRequest):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(5),
            rq.RequestLength(),
            rq.Window('window'),
            )

    _reply = rq.Struct(
            rq.ReplyCode(),
            rq.Pad(1),
            rq.Card16('sequence_number'),
            rq.ReplyLength(),
            rq.Bool('bounding_shaped'),
            rq.Bool('clip_shaped'),
            rq.Pad(2),
            rq.Int16('bounding_x'),
            rq.Int16('bounding_y'),
            rq.Card16('bounding_width'),
            rq.Card16('bounding_height'),
            rq.Int16('clip_x'),
            rq.Int16('clip_y'),
            rq.Card16('clip_width'),
            rq.Card16('clip_height'),
            rq.Pad(4),
            )

def query_extents(self):
    return QueryExtents(
        display = self.display,
        opcode = self.display.get_extension_major(extname),
        window = self.id,
        )


class SelectInput(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(6),
            rq.RequestLength(),
            rq.Window('window'),
            rq.Bool('enable'),
            rq.Pad(3),
            )

def select_input(self, enable = 1):
    SelectInput(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            window = self.id,
            enable = enable,
            )


class InputSelected(rq.ReplyRequest):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(7),
            rq.RequestLength(),
            rq.Window('window'),
            )

    _reply = rq.Struct(
            rq.ReplyCode(),
            rq.Bool('enabled'),
            rq.Card16('sequence_number'),
            rq.ReplyLength(),
            rq.Pad(24),
            )

def input_selected(self):
    reply = InputSelected(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            window = self.id,
            )
    return reply.enabled


class GetRectangles(rq.ReplyRequest):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(8),
            rq.RequestLength(),
            rq.Window('window'),
            rq.Set('region', 1, (ShapeBounding, ShapeClip)),
            rq.Pad(3),
            )

    _reply = rq.Struct(
            rq.ReplyCode(),
            rq.Card8('ordering'),
            rq.Card16('sequence_number'),
            rq.ReplyLength(),
            rq.LengthOf('rectangles', 4),
            rq.Pad(20),
            rq.List('rectangles', structs.Rectangle),
            )

def get_rectangles(self, region):
    return GetRectangles(
        display = self.display,
        opcode = self.display.get_extension_major(extname),
        window = self.id,
        region = region,
        )


class ShapeNotify(rq.Event):
    _code = None
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Set('region', 1, (ShapeBounding, ShapeClip)),
                         rq.Card16('sequence_number'),
                         rq.Window('window'),
                         rq.Int16('x'),
                         rq.Int16('y'),
                         rq.Card16('width'),
                         rq.Card16('height'),
                         rq.Card32('time'),
                         rq.Bool('shaped'),
                         rq.Pad(11),
                         )

def init(disp, info):
    disp.extension_add_method('display', 'shape_query_version', query_version )
    disp.extension_add_method('window', 'shape_rectangles',     rectangles )
    disp.extension_add_method('window', 'shape_mask',           mask )
    disp.extension_add_method('window', 'shape_combine',        combine )
    disp.extension_add_method('window', 'shape_offset',         offset )
    disp.extension_add_method('window', 'shape_query_extents',  query_extents )
    disp.extension_add_method('window', 'shape_select_input',   select_input )
    disp.extension_add_method('window', 'shape_input_selected', input_selected )
    disp.extension_add_method('window', 'shape_get_rectangles', get_rectangles )

    disp.extension_add_event(info.first_event, ShapeNotify)
