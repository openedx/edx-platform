# Xlib.protocol.event -- definitions of core events
#
#    Copyright (C) 2000-2002 Peter Liljenberg <petli@ctrl-c.liu.se>
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


class AnyEvent(rq.Event):
    _code = None
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Card8('detail'),
                         rq.Card16('sequence_number'),
                         rq.FixedString('data', 28),
                         )

class KeyButtonPointer(rq.Event):
    _code = None
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Card8('detail'),
                         rq.Card16('sequence_number'),
                         rq.Card32('time'),
                         rq.Window('root'),
                         rq.Window('window'),
                         rq.Window('child', (X.NONE, )),
                         rq.Int16('root_x'),
                         rq.Int16('root_y'),
                         rq.Int16('event_x'),
                         rq.Int16('event_y'),
                         rq.Card16('state'),
                         rq.Card8('same_screen'),
                         rq.Pad(1),
                         )

class KeyPress(KeyButtonPointer):
    _code = X.KeyPress

class KeyRelease(KeyButtonPointer):
    _code = X.KeyRelease

class ButtonPress(KeyButtonPointer):
    _code = X.ButtonPress

class ButtonRelease(KeyButtonPointer):
    _code = X.ButtonRelease

class MotionNotify(KeyButtonPointer):
    _code = X.MotionNotify

class EnterLeave(rq.Event):
    _code = None
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Card8('detail'),
                         rq.Card16('sequence_number'),
                         rq.Card32('time'),
                         rq.Window('root'),
                         rq.Window('window'),
                         rq.Window('child', (X.NONE, )),
                         rq.Int16('root_x'),
                         rq.Int16('root_y'),
                         rq.Int16('event_x'),
                         rq.Int16('event_y'),
                         rq.Card16('state'),
                         rq.Card8('mode'),
                         rq.Card8('flags'),
                         )

class EnterNotify(EnterLeave):
    _code = X.EnterNotify

class LeaveNotify(EnterLeave):
    _code = X.LeaveNotify


class Focus(rq.Event):
    _code = None
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Card8('detail'),
                         rq.Card16('sequence_number'),
                         rq.Window('window'),
                         rq.Card8('mode'),
                         rq.Pad(23),
                         )

class FocusIn(Focus):
    _code = X.FocusIn

class FocusOut(Focus):
    _code = X.FocusOut

class Expose(rq.Event):
    _code = X.Expose
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('window'),
                         rq.Card16('x'),
                         rq.Card16('y'),
                         rq.Card16('width'),
                         rq.Card16('height'),
                         rq.Card16('count'),
                         rq.Pad(14),
                         )

class GraphicsExpose(rq.Event):
    _code = X.GraphicsExpose
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Drawable('drawable'),
                         rq.Card16('x'),
                         rq.Card16('y'),
                         rq.Card16('width'),
                         rq.Card16('height'),
                         rq.Card16('minor_event'),
                         rq.Card16('count'),
                         rq.Card8('major_event'),
                         rq.Pad(11),
                         )

class NoExpose(rq.Event):
    _code = X.NoExpose
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Drawable('window'),
                         rq.Card16('minor_event'),
                         rq.Card8('major_event'),
                         rq.Pad(21),
                         )

class VisibilityNotify(rq.Event):
    _code = X.VisibilityNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('window'),
                         rq.Card8('state'),
                         rq.Pad(23),
                         )

class CreateNotify(rq.Event):
    _code = X.CreateNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('parent'),
                         rq.Window('window'),
                         rq.Int16('x'),
                         rq.Int16('y'),
                         rq.Card16('width'),
                         rq.Card16('height'),
                         rq.Card16('border_width'),
                         rq.Card8('override'),
                         rq.Pad(9),
                         )

class DestroyNotify(rq.Event):
    _code = X.DestroyNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('event'),
                         rq.Window('window'),
                         rq.Pad(20),
                         )

class UnmapNotify(rq.Event):
    _code = X.UnmapNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('event'),
                         rq.Window('window'),
                         rq.Card8('from_configure'),
                         rq.Pad(19),
                         )

class MapNotify(rq.Event):
    _code = X.MapNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('event'),
                         rq.Window('window'),
                         rq.Card8('override'),
                         rq.Pad(19),
                         )

class MapRequest(rq.Event):
    _code = X.MapRequest
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('parent'),
                         rq.Window('window'),
                         rq.Pad(20),
                         )

class ReparentNotify(rq.Event):
    _code = X.ReparentNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('event'),
                         rq.Window('window'),
                         rq.Window('parent'),
                         rq.Int16('x'),
                         rq.Int16('y'),
                         rq.Card8('override'),
                         rq.Pad(11),
                         )

class ConfigureNotify(rq.Event):
    _code = X.ConfigureNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('event'),
                         rq.Window('window'),
                         rq.Window('above_sibling', (X.NONE, )),
                         rq.Int16('x'),
                         rq.Int16('y'),
                         rq.Card16('width'),
                         rq.Card16('height'),
                         rq.Card16('border_width'),
                         rq.Card8('override'),
                         rq.Pad(5),
                         )

class ConfigureRequest(rq.Event):
    _code = X.ConfigureRequest
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Card8('stack_mode'),
                         rq.Card16('sequence_number'),
                         rq.Window('parent'),
                         rq.Window('window'),
                         rq.Window('sibling', (X.NONE, )),
                         rq.Int16('x'),
                         rq.Int16('y'),
                         rq.Card16('width'),
                         rq.Card16('height'),
                         rq.Card16('border_width'),
                         rq.Card16('value_mask'),
                         rq.Pad(4),
                         )

class GravityNotify(rq.Event):
    _code = X.GravityNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('event'),
                         rq.Window('window'),
                         rq.Int16('x'),
                         rq.Int16('y'),
                         rq.Pad(16),
                         )

class ResizeRequest(rq.Event):
    _code = X.ResizeRequest
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('window'),
                         rq.Card16('width'),
                         rq.Card16('height'),
                         rq.Pad(20),
                         )

class Circulate(rq.Event):
    _code = None
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('event'),
                         rq.Window('window'),
                         rq.Pad(4),
                         rq.Card8('place'),
                         rq.Pad(15),
                         )

class CirculateNotify(Circulate):
    _code = X.CirculateNotify

class CirculateRequest(Circulate):
    _code = X.CirculateRequest

class PropertyNotify(rq.Event):
    _code = X.PropertyNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('window'),
                         rq.Card32('atom'),
                         rq.Card32('time'),
                         rq.Card8('state'),
                         rq.Pad(15),
                         )

class SelectionClear(rq.Event):
    _code = X.SelectionClear
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Card32('time'),
                         rq.Window('window'),
                         rq.Card32('atom'),
                         rq.Pad(16),
                         )

class SelectionRequest(rq.Event):
    _code = X.SelectionRequest
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Card32('time'),
                         rq.Window('owner'),
                         rq.Window('requestor'),
                         rq.Card32('selection'),
                         rq.Card32('target'),
                         rq.Card32('property'),
                         rq.Pad(4),
                         )

class SelectionNotify(rq.Event):
    _code = X.SelectionNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Card32('time'),
                         rq.Window('requestor'),
                         rq.Card32('selection'),
                         rq.Card32('target'),
                         rq.Card32('property'),
                         rq.Pad(8),
                         )

class ColormapNotify(rq.Event):
    _code = X.ColormapNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Window('window'),
                         rq.Colormap('colormap', (X.NONE, )),
                         rq.Card8('new'),
                         rq.Card8('state'),
                         rq.Pad(18),
                         )

class MappingNotify(rq.Event):
    _code = X.MappingNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Pad(1),
                         rq.Card16('sequence_number'),
                         rq.Card8('request'),
                         rq.Card8('first_keycode'),
                         rq.Card8('count'),
                         rq.Pad(25),
                         )

class ClientMessage(rq.Event):
    _code = X.ClientMessage
    _fields = rq.Struct( rq.Card8('type'),
                         rq.Format('data', 1),
                         rq.Card16('sequence_number'),
                         rq.Window('window'),
                         rq.Card32('client_type'),
                         rq.FixedPropertyData('data', 20),
                         )

class KeymapNotify(rq.Event):
    _code = X.KeymapNotify
    _fields = rq.Struct( rq.Card8('type'),
                         rq.FixedList('data', 31, rq.Card8Obj, pad = 0)
                         )


event_class = {
    X.KeyPress:         KeyPress,
    X.KeyRelease:       KeyRelease,
    X.ButtonPress:      ButtonPress,
    X.ButtonRelease:    ButtonRelease,
    X.MotionNotify:     MotionNotify,
    X.EnterNotify:      EnterNotify,
    X.LeaveNotify:      LeaveNotify,
    X.FocusIn:          FocusIn,
    X.FocusOut:         FocusOut,
    X.KeymapNotify:     KeymapNotify,
    X.Expose:           Expose,
    X.GraphicsExpose:   GraphicsExpose,
    X.NoExpose:         NoExpose,
    X.VisibilityNotify: VisibilityNotify,
    X.CreateNotify:     CreateNotify,
    X.DestroyNotify:    DestroyNotify,
    X.UnmapNotify:      UnmapNotify,
    X.MapNotify:        MapNotify,
    X.MapRequest:       MapRequest,
    X.ReparentNotify:   ReparentNotify,
    X.ConfigureNotify:  ConfigureNotify,
    X.ConfigureRequest: ConfigureRequest,
    X.GravityNotify:    GravityNotify,
    X.ResizeRequest:    ResizeRequest,
    X.CirculateNotify:  CirculateNotify,
    X.CirculateRequest: CirculateRequest,
    X.PropertyNotify:   PropertyNotify,
    X.SelectionClear:   SelectionClear,
    X.SelectionRequest: SelectionRequest,
    X.SelectionNotify:  SelectionNotify,
    X.ColormapNotify:   ColormapNotify,
    X.ClientMessage:    ClientMessage,
    X.MappingNotify:    MappingNotify,
    }
