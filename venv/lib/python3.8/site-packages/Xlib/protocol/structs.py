# Xlib.protocol.structs -- some common request structures
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

def WindowValues(arg):
    return rq.ValueList( arg, 4, 0,
                         rq.Pixmap('background_pixmap'),
                         rq.Card32('background_pixel'),
                         rq.Pixmap('border_pixmap'),
                         rq.Card32('border_pixel'),
                         rq.Gravity('bit_gravity'),
                         rq.Gravity('win_gravity'),
                         rq.Set('backing_store', 1,
                                (X.NotUseful, X.WhenMapped, X.Always)),
                         rq.Card32('backing_planes'),
                         rq.Card32('backing_pixel'),
                         rq.Bool('override_redirect'),
                         rq.Bool('save_under'),
                         rq.Card32('event_mask'),
                         rq.Card32('do_not_propagate_mask'),
                         rq.Colormap('colormap'),
                         rq.Cursor('cursor'),
                         )

def GCValues(arg):
    return rq.ValueList( arg, 4, 0,
                         rq.Set('function', 1,
                                (X.GXclear, X.GXand, X.GXandReverse,
                                 X.GXcopy, X.GXandInverted, X.GXnoop,
                                 X.GXxor, X.GXor, X.GXnor, X.GXequiv,
                                 X.GXinvert, X.GXorReverse, X.GXcopyInverted,
                                 X.GXorInverted, X.GXnand, X.GXset)),
                         rq.Card32('plane_mask'),
                         rq.Card32('foreground'),
                         rq.Card32('background'),
                         rq.Card16('line_width'),
                         rq.Set('line_style', 1,
                                (X.LineSolid, X.LineOnOffDash, X.LineDoubleDash)),
                         rq.Set('cap_style', 1,
                                (X.CapNotLast, X.CapButt,
                                 X.CapRound, X.CapProjecting)),
                         rq.Set('join_style', 1,
                                (X.JoinMiter, X.JoinRound, X.JoinBevel)),
                         rq.Set('fill_style', 1,
                                (X.FillSolid, X.FillTiled,
                                 X.FillStippled, X.FillOpaqueStippled)),
                         rq.Set('fill_rule', 1,
                                (X.EvenOddRule, X.WindingRule)),
                         rq.Pixmap('tile'),
                         rq.Pixmap('stipple'),
                         rq.Int16('tile_stipple_x_origin'),
                         rq.Int16('tile_stipple_y_origin'),
                         rq.Font('font'),
                         rq.Set('subwindow_mode', 1,
                                (X.ClipByChildren, X.IncludeInferiors)),
                         rq.Bool('graphics_exposures'),
                         rq.Int16('clip_x_origin'),
                         rq.Int16('clip_y_origin'),
                         rq.Pixmap('clip_mask'),
                         rq.Card16('dash_offset'),
                         rq.Card8('dashes'),
                         rq.Set('arc_mode', 1, (X.ArcChord, X.ArcPieSlice))
                         )



TimeCoord = rq.Struct(
    rq.Card32('time'),
    rq.Int16('x'),
    rq.Int16('y'),
    )

Host = rq.Struct(
    rq.Set('family', 1, (X.FamilyInternet, X.FamilyDECnet, X.FamilyChaos)),
    rq.Pad(1),
    rq.LengthOf('name', 2),
    rq.List('name', rq.Card8Obj)
    )

CharInfo = rq.Struct(
    rq.Int16('left_side_bearing'),
    rq.Int16('right_side_bearing'),
    rq.Int16('character_width'),
    rq.Int16('ascent'),
    rq.Int16('descent'),
    rq.Card16('attributes'),
    )

FontProp = rq.Struct(
    rq.Card32('name'),
    rq.Card32('value'),
    )

ColorItem = rq.Struct(
    rq.Card32('pixel'),
    rq.Card16('red'),
    rq.Card16('green'),
    rq.Card16('blue'),
    rq.Card8('flags'),
    rq.Pad(1),
    )


RGB = rq.Struct(
    rq.Card16('red'),
    rq.Card16('green'),
    rq.Card16('blue'),
    rq.Pad(2),
    )


Point = rq.Struct(
    rq.Int16('x'),
    rq.Int16('y'),
    )

Segment = rq.Struct(
    rq.Int16('x1'),
    rq.Int16('y1'),
    rq.Int16('x2'),
    rq.Int16('y2'),
    )

Rectangle = rq.Struct(
    rq.Int16('x'),
    rq.Int16('y'),
    rq.Card16('width'),
    rq.Card16('height'),
   )

Arc = rq.Struct(
    rq.Int16('x'),
    rq.Int16('y'),
    rq.Card16('width'),
    rq.Card16('height'),
    rq.Int16('angle1'),
    rq.Int16('angle2'),
   )
