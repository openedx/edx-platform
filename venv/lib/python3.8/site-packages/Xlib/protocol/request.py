# Xlib.protocol.request -- definitions of core requests
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
from Xlib.protocol import rq, structs


class CreateWindow(rq.Request):
    _request = rq.Struct(
        rq.Opcode(1),
        rq.Card8('depth'),
        rq.RequestLength(),
        rq.Window('wid'),
        rq.Window('parent'),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Card16('border_width'),
        rq.Set('window_class', 2, (X.CopyFromParent, X.InputOutput, X.InputOnly)),
        rq.Card32('visual'),
        structs.WindowValues('attrs'),
        )

class ChangeWindowAttributes(rq.Request):
    _request = rq.Struct(
        rq.Opcode(2),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window'),
        structs.WindowValues('attrs'),
        )

class GetWindowAttributes(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(3),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('backing_store'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('visual'),
        rq.Card16('win_class'),
        rq.Card8('bit_gravity'),
        rq.Card8('win_gravity'),
        rq.Card32('backing_bit_planes'),
        rq.Card32('backing_pixel'),
        rq.Card8('save_under'),
        rq.Card8('map_is_installed'),
        rq.Card8('map_state'),
        rq.Card8('override_redirect'),
        rq.Colormap('colormap', (X.NONE, )),
        rq.Card32('all_event_masks'),
        rq.Card32('your_event_mask'),
        rq.Card16('do_not_propagate_mask'),
        rq.Pad(2),
        )

class DestroyWindow(rq.Request):
    _request = rq.Struct(
        rq.Opcode(4),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

class DestroySubWindows(rq.Request):
    _request = rq.Struct(
        rq.Opcode(5),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

class ChangeSaveSet(rq.Request):
    _request = rq.Struct(
        rq.Opcode(6),
        rq.Set('mode', 1, (X.SetModeInsert, X.SetModeDelete)),
        rq.RequestLength(),
        rq.Window('window'),
        )

class ReparentWindow(rq.Request):
    _request = rq.Struct(
        rq.Opcode(7),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Window('parent'),
        rq.Int16('x'),
        rq.Int16('y'),
        )

class MapWindow(rq.Request):
    _request = rq.Struct(
        rq.Opcode(8),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

class MapSubwindows(rq.Request):
    _request = rq.Struct(
        rq.Opcode(9),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

class UnmapWindow(rq.Request):
    _request = rq.Struct(
        rq.Opcode(10),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

class UnmapSubwindows(rq.Request):
    _request = rq.Struct(
        rq.Opcode(11),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

class ConfigureWindow(rq.Request):
    _request = rq.Struct(
        rq.Opcode(12),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window'),
        rq.ValueList( 'attrs', 2, 2,
                      rq.Int16('x'),
                      rq.Int16('y'),
                      rq.Card16('width'),
                      rq.Card16('height'),
                      rq.Int16('border_width'),
                      rq.Window('sibling'),
                      rq.Set('stack_mode', 1,
                             (X.Above, X.Below, X.TopIf,
                              X.BottomIf, X.Opposite))
                      )
        )

class CirculateWindow(rq.Request):
    _request = rq.Struct(
        rq.Opcode(13),
        rq.Set('direction', 1, (X.RaiseLowest, X.LowerHighest)),
        rq.RequestLength(),
        rq.Window('window'),
        )

class GetGeometry(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(14),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('drawable')
        )

    _reply = rq.Struct (
        rq.ReplyCode(),
        rq.Card8('depth'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('root'),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Card16('border_width'),
        rq.Pad(10)
        )

class QueryTree(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(15),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('root'),
        rq.Window('parent', (X.NONE, )),
        rq.LengthOf('children', 2),
        rq.Pad(14),
        rq.List('children', rq.WindowObj),
        )

class InternAtom(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(16),
        rq.Bool('only_if_exists'),
        rq.RequestLength(),
        rq.LengthOf('name', 2),
        rq.Pad(2),
        rq.String8('name'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('atom'),
        rq.Pad(20),
        )


class GetAtomName(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(17),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Card32('atom')
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('name', 2),
        rq.Pad(22),
        rq.String8('name'),
        )

class ChangeProperty(rq.Request):
    _request = rq.Struct(
        rq.Opcode(18),
        rq.Set('mode', 1, (X.PropModeReplace, X.PropModePrepend, X.PropModeAppend)),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Card32('property'),
        rq.Card32('type'),
        rq.Format('data', 1),
        rq.Pad(3),
        rq.LengthOf('data', 4),
        rq.PropertyData('data'),
        )

class DeleteProperty(rq.Request):
    _request = rq.Struct(
        rq.Opcode(19),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Card32('property'),
        )

class GetProperty(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(20),
        rq.Bool('delete'),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Card32('property'),
        rq.Card32('type'),
        rq.Card32('long_offset'),
        rq.Card32('long_length'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Format('value', 1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('property_type'),
        rq.Card32('bytes_after'),
        rq.LengthOf('value', 4),
        rq.Pad(12),
        rq.PropertyData('value'),
        )

class ListProperties(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(21),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('atoms', 2),
        rq.Pad(22),
        rq.List('atoms', rq.Card32Obj),
        )

class SetSelectionOwner(rq.Request):
    _request = rq.Struct(
        rq.Opcode(22),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Card32('selection'),
        rq.Card32('time'),
        )

class GetSelectionOwner(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(23),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Card32('selection')
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('owner', (X.NONE, )),
        rq.Pad(20),
        )

class ConvertSelection(rq.Request):
    _request = rq.Struct(
        rq.Opcode(24),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('requestor'),
        rq.Card32('selection'),
        rq.Card32('target'),
        rq.Card32('property'),
        rq.Card32('time'),
        )

class SendEvent(rq.Request):
    _request = rq.Struct(
        rq.Opcode(25),
        rq.Bool('propagate'),
        rq.RequestLength(),
        rq.Window('destination'),
        rq.Card32('event_mask'),
        rq.EventField('event'),
        )

class GrabPointer(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(26),
        rq.Bool('owner_events'),
        rq.RequestLength(),
        rq.Window('grab_window'),
        rq.Card16('event_mask'),
        rq.Set('pointer_mode', 1, (X.GrabModeSync, X.GrabModeAsync)),
        rq.Set('keyboard_mode', 1, (X.GrabModeSync, X.GrabModeAsync)),
        rq.Window('confine_to', (X.NONE, )),
        rq.Cursor('cursor', (X.NONE, )),
        rq.Card32('time'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Pad(24),
        )

class UngrabPointer(rq.Request):
    _request = rq.Struct(
        rq.Opcode(27),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Card32('time')
        )

class GrabButton(rq.Request):
    _request = rq.Struct(
        rq.Opcode(28),
        rq.Bool('owner_events'),
        rq.RequestLength(),
        rq.Window('grab_window'),
        rq.Card16('event_mask'),
        rq.Set('pointer_mode', 1, (X.GrabModeSync, X.GrabModeAsync)),
        rq.Set('keyboard_mode', 1, (X.GrabModeSync, X.GrabModeAsync)),
        rq.Window('confine_to', (X.NONE, )),
        rq.Cursor('cursor', (X.NONE, )),
        rq.Card8('button'),
        rq.Pad(1),
        rq.Card16('modifiers'),
        )

class UngrabButton(rq.Request):
    _request = rq.Struct(
        rq.Opcode(29),
        rq.Card8('button'),
        rq.RequestLength(),
        rq.Window('grab_window'),
        rq.Card16('modifiers'),
        rq.Pad(2),
        )

class ChangeActivePointerGrab(rq.Request):
    _request = rq.Struct(
        rq.Opcode(30),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Cursor('cursor'),
        rq.Card32('time'),
        rq.Card16('event_mask'),
        rq.Pad(2),
        )

class GrabKeyboard(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(31),
        rq.Bool('owner_events'),
        rq.RequestLength(),
        rq.Window('grab_window'),
        rq.Card32('time'),
        rq.Set('pointer_mode', 1, (X.GrabModeSync, X.GrabModeAsync)),
        rq.Set('keyboard_mode', 1, (X.GrabModeSync, X.GrabModeAsync)),
        rq.Pad(2),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Pad(24),
        )

class UngrabKeyboard(rq.Request):
    _request = rq.Struct(
        rq.Opcode(32),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Card32('time')
        )

class GrabKey(rq.Request):
    _request = rq.Struct(
        rq.Opcode(33),
        rq.Bool('owner_events'),
        rq.RequestLength(),
        rq.Window('grab_window'),
        rq.Card16('modifiers'),
        rq.Card8('key'),
        rq.Set('pointer_mode', 1, (X.GrabModeSync, X.GrabModeAsync)),
        rq.Set('keyboard_mode', 1, (X.GrabModeSync, X.GrabModeAsync)),
        rq.Pad(3),
        )

class UngrabKey(rq.Request):
    _request = rq.Struct(
        rq.Opcode(34),
        rq.Card8('key'),
        rq.RequestLength(),
        rq.Window('grab_window'),
        rq.Card16('modifiers'),
        rq.Pad(2),
        )

class AllowEvents(rq.Request):
    _request = rq.Struct(
        rq.Opcode(35),
        rq.Set('mode', 1, (X.AsyncPointer,
                           X.SyncPointer,
                           X.ReplayPointer,
                           X.AsyncKeyboard,
                           X.SyncKeyboard,
                           X.ReplayKeyboard,
                           X.AsyncBoth,
                           X.SyncBoth)),
        rq.RequestLength(),
        rq.Card32('time'),
        )

class GrabServer(rq.Request):
    _request = rq.Struct(
        rq.Opcode(36),
        rq.Pad(1),
        rq.RequestLength(),
        )

class UngrabServer(rq.Request):
    _request = rq.Struct(
        rq.Opcode(37),
        rq.Pad(1),
        rq.RequestLength(),
        )

class QueryPointer(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(38),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('same_screen'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('root'),
        rq.Window('child', (X.NONE, )),
        rq.Int16('root_x'),
        rq.Int16('root_y'),
        rq.Int16('win_x'),
        rq.Int16('win_y'),
        rq.Card16('mask'),
        rq.Pad(6),
        )

class GetMotionEvents(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(39),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Card32('start'),
        rq.Card32('stop'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('events', 4),
        rq.Pad(20),
        rq.List('events', structs.TimeCoord),
        )

class TranslateCoords(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(40),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('src_wid'),
        rq.Window('dst_wid'),
        rq.Int16('src_x'),
        rq.Int16('src_y'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('same_screen'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('child', (X.NONE, )),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.Pad(16),
        )

class WarpPointer(rq.Request):
    _request = rq.Struct(
        rq.Opcode(41),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('src_window'),
        rq.Window('dst_window'),
        rq.Int16('src_x'),
        rq.Int16('src_y'),
        rq.Card16('src_width'),
        rq.Card16('src_height'),
        rq.Int16('dst_x'),
        rq.Int16('dst_y'),
        )

class SetInputFocus(rq.Request):
    _request = rq.Struct(
        rq.Opcode(42),
        rq.Set('revert_to', 1, (X.RevertToNone, X.RevertToPointerRoot,
                                X.RevertToParent)),
        rq.RequestLength(),
        rq.Window('focus'),
        rq.Card32('time'),
        )

class GetInputFocus(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(43),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('revert_to'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('focus', (X.NONE, X.PointerRoot)),
        rq.Pad(20),
        )

class QueryKeymap(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(44),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.FixedList('map', 32, rq.Card8Obj),
        )


class OpenFont(rq.Request):
    _request = rq.Struct(
        rq.Opcode(45),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Font('fid'),
        rq.LengthOf('name', 2),
        rq.Pad(2),
        rq.String8('name'),
        )

class CloseFont(rq.Request):
    _request = rq.Struct(
        rq.Opcode(46),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Font('font')
        )

class QueryFont(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(47),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Fontable('font')
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Object('min_bounds', structs.CharInfo),
        rq.Pad(4),
        rq.Object('max_bounds', structs.CharInfo),
        rq.Pad(4),
        rq.Card16('min_char_or_byte2'),
        rq.Card16('max_char_or_byte2'),
        rq.Card16('default_char'),
        rq.LengthOf('properties', 2),
        rq.Card8('draw_direction'),
        rq.Card8('min_byte1'),
        rq.Card8('max_byte1'),
        rq.Card8('all_chars_exist'),
        rq.Int16('font_ascent'),
        rq.Int16('font_descent'),
        rq.LengthOf('char_infos', 4),
        rq.List('properties', structs.FontProp),
        rq.List('char_infos', structs.CharInfo),
        )

class QueryTextExtents(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(48),
        rq.OddLength('string'),
        rq.RequestLength(),
        rq.Fontable('font'),
        rq.String16('string'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('draw_direction'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Int16('font_ascent'),
        rq.Int16('font_descent'),
        rq.Int16('overall_ascent'),
        rq.Int16('overall_descent'),
        rq.Int32('overall_width'),
        rq.Int32('overall_left'),
        rq.Int32('overall_right'),
        rq.Pad(4),
        )

class ListFonts(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(49),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Card16('max_names'),
        rq.LengthOf('pattern', 2),
        rq.String8('pattern'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('fonts', 2),
        rq.Pad(22),
        rq.List('fonts', rq.Str),
        )


class ListFontsWithInfo(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(50),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Card16('max_names'),
        rq.LengthOf('pattern', 2),
        rq.String8('pattern'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.LengthOf('name', 1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Object('min_bounds', structs.CharInfo),
        rq.Pad(4),
        rq.Object('max_bounds', structs.CharInfo),
        rq.Pad(4),
        rq.Card16('min_char_or_byte2'),
        rq.Card16('max_char_or_byte2'),
        rq.Card16('default_char'),
        rq.LengthOf('properties', 2),
        rq.Card8('draw_direction'),
        rq.Card8('min_byte1'),
        rq.Card8('max_byte1'),
        rq.Card8('all_chars_exist'),
        rq.Int16('font_ascent'),
        rq.Int16('font_descent'),
        rq.Card32('replies_hint'),
        rq.List('properties', structs.FontProp),
        rq.String8('name'),
        )


    # Somebody must have smoked some really wicked weed when they
    # defined the ListFontsWithInfo request:
    # The server sends a reply for _each_ matching font...
    # It then sends a special reply (name length == 0) to indicate
    # that there are no more fonts in the reply.

    # This means that we have to do some special parsing to see if
    # we have got the end-of-reply reply.  If we haven't, we
    # have to reinsert the request in the front of the
    # display.sent_request queue to catch the next response.

    # Bastards.

    def __init__(self, *args, **keys):
        self._fonts = []
        ReplyRequest.__init__(*(self, ) + args, **keys)

    def _parse_response(self, data):

        if ord(data[1]) == 0:
            self._response_lock.acquire()
            self._data = self._fonts
            del self._fonts
            self._response_lock.release()
            return

        r, d = self._reply.parse_binary(data)
        self._fonts.append(r)

        self._display.sent_requests.insert(0, self)


    # Override the default __getattr__, since it isn't usable for
    # the list reply.  Instead provide a __getitem__ and a __len__.

    def __getattr__(self, attr):
        raise AttributeError(attr)

    def __getitem__(self, item):
        return self._data[item]

    def __len__(self):
        return len(self._data)


class SetFontPath(rq.Request):
    _request = rq.Struct(
        rq.Opcode(51),
        rq.Pad(1),
        rq.RequestLength(),
        rq.LengthOf('path', 2),
        rq.Pad(2),
        rq.List('path', rq.Str),
        )

class GetFontPath(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(52),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('paths', 2),
        rq.Pad(22),
        rq.List('paths', rq.Str),
        )

class CreatePixmap(rq.Request):
    _request = rq.Struct(
        rq.Opcode(53),
        rq.Card8('depth'),
        rq.RequestLength(),
        rq.Pixmap('pid'),
        rq.Drawable('drawable'),
        rq.Card16('width'),
        rq.Card16('height'),
        )

class FreePixmap(rq.Request):
    _request = rq.Struct(
        rq.Opcode(54),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Pixmap('pixmap')
        )

class CreateGC(rq.Request):
    _request = rq.Struct(
        rq.Opcode(55),
        rq.Pad(1),
        rq.RequestLength(),
        rq.GC('cid'),
        rq.Drawable('drawable'),
        structs.GCValues('attrs'),
        )

class ChangeGC(rq.Request):
    _request = rq.Struct(
        rq.Opcode(56),
        rq.Pad(1),
        rq.RequestLength(),
        rq.GC('gc'),
        structs.GCValues('attrs'),
        )

class CopyGC(rq.Request):
    _request = rq.Struct(
        rq.Opcode(57),
        rq.Pad(1),
        rq.RequestLength(),
        rq.GC('src_gc'),
        rq.GC('dst_gc'),
        rq.Card32('mask'),
        )

class SetDashes(rq.Request):
    _request = rq.Struct(
        rq.Opcode(58),
        rq.Pad(1),
        rq.RequestLength(),
        rq.GC('gc'),
        rq.Card16('dash_offset'),
        rq.LengthOf('dashes', 2),
        rq.List('dashes', rq.Card8Obj),
        )

class SetClipRectangles(rq.Request):
    _request = rq.Struct(
        rq.Opcode(59),
        rq.Set('ordering', 1, (X.Unsorted, X.YSorted, X.YXSorted, X.YXBanded)),
        rq.RequestLength(),
        rq.GC('gc'),
        rq.Int16('x_origin'),
        rq.Int16('y_origin'),
        rq.List('rectangles', structs.Rectangle),
        )

class FreeGC(rq.Request):
    _request = rq.Struct(
        rq.Opcode(60),
        rq.Pad(1),
        rq.RequestLength(),
        rq.GC('gc')
        )

class ClearArea(rq.Request):
    _request = rq.Struct(
        rq.Opcode(61),
        rq.Bool('exposures'),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.Card16('width'),
        rq.Card16('height'),
        )

class CopyArea(rq.Request):
    _request = rq.Struct(
        rq.Opcode(62),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('src_drawable'),
        rq.Drawable('dst_drawable'),
        rq.GC('gc'),
        rq.Int16('src_x'),
        rq.Int16('src_y'),
        rq.Int16('dst_x'),
        rq.Int16('dst_y'),
        rq.Card16('width'),
        rq.Card16('height'),
        )

class CopyPlane(rq.Request):
    _request = rq.Struct(
        rq.Opcode(63),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('src_drawable'),
        rq.Drawable('dst_drawable'),
        rq.GC('gc'),
        rq.Int16('src_x'),
        rq.Int16('src_y'),
        rq.Int16('dst_x'),
        rq.Int16('dst_y'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Card32('bit_plane'),
        )

class PolyPoint(rq.Request):
    _request = rq.Struct(
        rq.Opcode(64),
        rq.Set('coord_mode', 1, (X.CoordModeOrigin, X.CoordModePrevious)),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.List('points', structs.Point),
        )

class PolyLine(rq.Request):
    _request = rq.Struct(
        rq.Opcode(65),
        rq.Set('coord_mode', 1, (X.CoordModeOrigin, X.CoordModePrevious)),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.List('points', structs.Point),
        )


class PolySegment(rq.Request):
    _request = rq.Struct(
        rq.Opcode(66),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.List('segments', structs.Segment),
        )


class PolyRectangle(rq.Request):
    _request = rq.Struct(
        rq.Opcode(67),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.List('rectangles', structs.Rectangle),
        )

class PolyArc(rq.Request):
    _request = rq.Struct(
        rq.Opcode(68),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.List('arcs', structs.Arc),
        )

class FillPoly(rq.Request):
    _request = rq.Struct(
        rq.Opcode(69),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.Set('shape', 1, (X.Complex, X.Nonconvex, X.Convex)),
        rq.Set('coord_mode', 1, (X.CoordModeOrigin, X.CoordModePrevious)),
        rq.Pad(2),
        rq.List('points', structs.Point),
        )

class PolyFillRectangle(rq.Request):
    _request = rq.Struct(
        rq.Opcode(70),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.List('rectangles', structs.Rectangle),
        )

class PolyFillArc(rq.Request):
    _request = rq.Struct(
        rq.Opcode(71),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.List('arcs', structs.Arc),
        )

class PutImage(rq.Request):
    _request = rq.Struct(
        rq.Opcode(72),
        rq.Set('format', 1, (X.XYBitmap, X.XYPixmap, X.ZPixmap)),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Int16('dst_x'),
        rq.Int16('dst_y'),
        rq.Card8('left_pad'),
        rq.Card8('depth'),
        rq.Pad(2),
        rq.String8('data'),
        )

class GetImage(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(73),
        rq.Set('format', 1, (X.XYPixmap, X.ZPixmap)),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Card32('plane_mask'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('depth'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('visual'),
        rq.Pad(20),
        rq.String8('data'),
        )

class PolyText8(rq.Request):
    _request = rq.Struct(
        rq.Opcode(74),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.TextElements8('items'),
        )

class PolyText16(rq.Request):
    _request = rq.Struct(
        rq.Opcode(75),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.TextElements16('items'),
        )

class ImageText8(rq.Request):
    _request = rq.Struct(
        rq.Opcode(76),
        rq.LengthOf('string', 1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.String8('string'),
        )

class ImageText16(rq.Request):
    _request = rq.Struct(
        rq.Opcode(77),
        rq.LengthOf('string', 1),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.GC('gc'),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.String16('string'),
        )

class CreateColormap(rq.Request):
    _request = rq.Struct(
        rq.Opcode(78),
        rq.Set('alloc', 1, (X.AllocNone, X.AllocAll)),
        rq.RequestLength(),
        rq.Colormap('mid'),
        rq.Window('window'),
        rq.Card32('visual'),
        )

class FreeColormap(rq.Request):
    _request = rq.Struct(
        rq.Opcode(79),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('cmap')
        )

class CopyColormapAndFree(rq.Request):
    _request = rq.Struct(
        rq.Opcode(80),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('mid'),
        rq.Colormap('src_cmap'),
        )

class InstallColormap(rq.Request):
    _request = rq.Struct(
        rq.Opcode(81),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('cmap')
        )

class UninstallColormap(rq.Request):
    _request = rq.Struct(
        rq.Opcode(82),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('cmap')
        )

class ListInstalledColormaps(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(83),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window')
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('cmaps', 2),
        rq.Pad(22),
        rq.List('cmaps', rq.ColormapObj),
        )

class AllocColor(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(84),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('cmap'),
        rq.Card16('red'),
        rq.Card16('green'),
        rq.Card16('blue'),
        rq.Pad(2),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card16('red'),
        rq.Card16('green'),
        rq.Card16('blue'),
        rq.Pad(2),
        rq.Card32('pixel'),
        rq.Pad(12),
        )

class AllocNamedColor(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(85),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('cmap'),
        rq.LengthOf('name', 2),
        rq.Pad(2),
        rq.String8('name'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('pixel'),
        rq.Card16('exact_red'),
        rq.Card16('exact_green'),
        rq.Card16('exact_blue'),
        rq.Card16('screen_red'),
        rq.Card16('screen_green'),
        rq.Card16('screen_blue'),
        rq.Pad(8),
        )

class AllocColorCells(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(86),
        rq.Bool('contiguous'),
        rq.RequestLength(),
        rq.Colormap('cmap'),
        rq.Card16('colors'),
        rq.Card16('planes'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('pixels', 2),
        rq.LengthOf('masks', 2),
        rq.Pad(20),
        rq.List('pixels', rq.Card32Obj),
        rq.List('masks', rq.Card32Obj),
        )

class AllocColorPlanes(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(87),
        rq.Bool('contiguous'),
        rq.RequestLength(),
        rq.Colormap('cmap'),
        rq.Card16('colors'),
        rq.Card16('red'),
        rq.Card16('green'),
        rq.Card16('blue'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('pixels', 2),
        rq.Pad(2),
        rq.Card32('red_mask'),
        rq.Card32('green_mask'),
        rq.Card32('blue_mask'),
        rq.Pad(8),
        rq.List('pixels', rq.Card32Obj),
        )

class FreeColors(rq.Request):
    _request = rq.Struct(
        rq.Opcode(88),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('cmap'),
        rq.Card32('plane_mask'),
        rq.List('pixels', rq.Card32Obj),
        )

class StoreColors(rq.Request):
    _request = rq.Struct(
        rq.Opcode(89),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('cmap'),
        rq.List('items', structs.ColorItem),
        )

class StoreNamedColor(rq.Request):
    _request = rq.Struct(
        rq.Opcode(90),
        rq.Card8('flags'),
        rq.RequestLength(),
        rq.Colormap('cmap'),
        rq.Card32('pixel'),
        rq.LengthOf('name', 2),
        rq.Pad(2),
        rq.String8('name'),
        )

class QueryColors(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(91),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('cmap'),
        rq.List('pixels', rq.Card32Obj),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('colors', 2),
        rq.Pad(22),
        rq.List('colors', structs.RGB),
        )

class LookupColor(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(92),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Colormap('cmap'),
        rq.LengthOf('name', 2),
        rq.Pad(2),
        rq.String8('name'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card16('exact_red'),
        rq.Card16('exact_green'),
        rq.Card16('exact_blue'),
        rq.Card16('screen_red'),
        rq.Card16('screen_green'),
        rq.Card16('screen_blue'),
        rq.Pad(12),
        )


class CreateCursor(rq.Request):
    _request = rq.Struct(
        rq.Opcode(93),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Cursor('cid'),
        rq.Pixmap('source'),
        rq.Pixmap('mask'),
        rq.Card16('fore_red'),
        rq.Card16('fore_green'),
        rq.Card16('fore_blue'),
        rq.Card16('back_red'),
        rq.Card16('back_green'),
        rq.Card16('back_blue'),
        rq.Card16('x'),
        rq.Card16('y'),
        )

class CreateGlyphCursor(rq.Request):
    _request = rq.Struct(
        rq.Opcode(94),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Cursor('cid'),
        rq.Font('source'),
        rq.Font('mask'),
        rq.Card16('source_char'),
        rq.Card16('mask_char'),
        rq.Card16('fore_red'),
        rq.Card16('fore_green'),
        rq.Card16('fore_blue'),
        rq.Card16('back_red'),
        rq.Card16('back_green'),
        rq.Card16('back_blue'),
        )

class FreeCursor(rq.Request):
    _request = rq.Struct(
        rq.Opcode(95),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Cursor('cursor')
        )

class RecolorCursor(rq.Request):
    _request = rq.Struct(
        rq.Opcode(96),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Cursor('cursor'),
        rq.Card16('fore_red'),
        rq.Card16('fore_green'),
        rq.Card16('fore_blue'),
        rq.Card16('back_red'),
        rq.Card16('back_green'),
        rq.Card16('back_blue'),
        )

class QueryBestSize(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(97),
        rq.Set('item_class', 1, (X.CursorShape, X.TileShape, X.StippleShape)),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.Card16('width'),
        rq.Card16('height'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Pad(20),
        )

class QueryExtension(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(98),
        rq.Pad(1),
        rq.RequestLength(),
        rq.LengthOf('name', 2),
        rq.Pad(2),
        rq.String8('name'),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card8('present'),
        rq.Card8('major_opcode'),
        rq.Card8('first_event'),
        rq.Card8('first_error'),
        rq.Pad(20),
        )

class ListExtensions(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(99),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.LengthOf('names', 1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Pad(24),
        rq.List('names', rq.Str),
        )

class ChangeKeyboardMapping(rq.Request):
    _request = rq.Struct(
        rq.Opcode(100),
        rq.LengthOf('keysyms', 1),
        rq.RequestLength(),
        rq.Card8('first_keycode'),
        rq.Format('keysyms', 1),
        rq.Pad(2),
        rq.KeyboardMapping('keysyms'),
        )

class GetKeyboardMapping(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(101),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Card8('first_keycode'),
        rq.Card8('count'),
        rq.Pad(2),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Format('keysyms', 1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Pad(24),
        rq.KeyboardMapping('keysyms'),
        )


class ChangeKeyboardControl(rq.Request):
    _request = rq.Struct(
        rq.Opcode(102),
        rq.Pad(1),
        rq.RequestLength(),
        rq.ValueList( 'attrs', 4, 0,
                      rq.Int8('key_click_percent'),
                      rq.Int8('bell_percent'),
                      rq.Int16('bell_pitch'),
                      rq.Int16('bell_duration'),
                      rq.Card8('led'),
                      rq.Set('led_mode', 1, (X.LedModeOff, X.LedModeOn)),
                      rq.Card8('key'),
                      rq.Set('auto_repeat_mode', 1, (X.AutoRepeatModeOff,
                                                     X.AutoRepeatModeOn,
                                                     X.AutoRepeatModeDefault))
                      )
        )

class GetKeyboardControl(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(103),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('global_auto_repeat'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('led_mask'),
        rq.Card8('key_click_percent'),
        rq.Card8('bell_percent'),
        rq.Card16('bell_pitch'),
        rq.Card16('bell_duration'),
        rq.Pad(2),
        rq.FixedList('auto_repeats', 32, rq.Card8Obj),
        )

class Bell(rq.Request):
    _request = rq.Struct(
        rq.Opcode(104),
        rq.Int8('percent'),
        rq.RequestLength(),
        )

class ChangePointerControl(rq.Request):
    _request = rq.Struct(
        rq.Opcode(105),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Int16('accel_num'),
        rq.Int16('accel_denum'),
        rq.Int16('threshold'),
        rq.Bool('do_accel'),
        rq.Bool('do_thresh'),
        )

class GetPointerControl(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(106),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card16('accel_num'),
        rq.Card16('accel_denom'),
        rq.Card16('threshold'),
        rq.Pad(18),
        )

class SetScreenSaver(rq.Request):
    _request = rq.Struct(
        rq.Opcode(107),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Int16('timeout'),
        rq.Int16('interval'),
        rq.Set('prefer_blank', 1, (X.DontPreferBlanking,
                                   X.PreferBlanking,
                                   X.DefaultBlanking)),
        rq.Set('allow_exposures', 1, (X.DontAllowExposures,
                                      X.AllowExposures,
                                      X.DefaultExposures)),
        rq.Pad(2),
        )

class GetScreenSaver(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(108),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card16('timeout'),
        rq.Card16('interval'),
        rq.Card8('prefer_blanking'),
        rq.Card8('allow_exposures'),
        rq.Pad(18),
        )

class ChangeHosts(rq.Request):
    _request = rq.Struct(
        rq.Opcode(109),
        rq.Set('mode', 1, (X.HostInsert, X.HostDelete)),
        rq.RequestLength(),
        rq.Set('host_family', 1, (X.FamilyInternet, X.FamilyDECnet, X.FamilyChaos)),
        rq.Pad(1),
        rq.LengthOf('host', 2),
        rq.List('host', rq.Card8Obj)
        )

class ListHosts(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(110),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('mode'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.LengthOf('hosts', 2),
        rq.Pad(22),
        rq.List('hosts', structs.Host),
        )

class SetAccessControl(rq.Request):
    _request = rq.Struct(
        rq.Opcode(111),
        rq.Set('mode', 1, (X.DisableAccess, X.EnableAccess)),
        rq.RequestLength(),
        )

class SetCloseDownMode(rq.Request):
    _request = rq.Struct(
        rq.Opcode(112),
        rq.Set('mode', 1, (X.DestroyAll, X.RetainPermanent, X.RetainTemporary)),
        rq.RequestLength(),
        )

class KillClient(rq.Request):
    _request = rq.Struct(
        rq.Opcode(113),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Resource('resource')
        )

class RotateProperties(rq.Request):
    _request = rq.Struct(
        rq.Opcode(114),
        rq.Pad(1),
        rq.RequestLength(),
        rq.Window('window'),
        rq.LengthOf('properties', 2),
        rq.Int16('delta'),
        rq.List('properties', rq.Card32Obj),
        )

class ForceScreenSaver(rq.Request):
    _request = rq.Struct(
        rq.Opcode(115),
        rq.Set('mode', 1, (X.ScreenSaverReset, X.ScreenSaverActive)),
        rq.RequestLength(),
        )

class SetPointerMapping(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(116),
        rq.LengthOf('map', 1),
        rq.RequestLength(),
        rq.List('map', rq.Card8Obj),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Pad(24),
        )

class GetPointerMapping(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(117),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.LengthOf('map', 1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Pad(24),
        rq.List('map', rq.Card8Obj),
        )

class SetModifierMapping(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(118),
        rq.Format('keycodes', 1),
        rq.RequestLength(),
        rq.ModifierMapping('keycodes')
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Pad(24),
        )

class GetModifierMapping(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Opcode(119),
        rq.Pad(1),
        rq.RequestLength(),
        )

    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Format('keycodes', 1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Pad(24),
        rq.ModifierMapping('keycodes')
        )

class NoOperation(rq.Request):
    _request = rq.Struct(
        rq.Opcode(127),
        rq.Pad(1),
        rq.RequestLength(),
        )


major_codes = {
    1: CreateWindow,
    2: ChangeWindowAttributes,
    3: GetWindowAttributes,
    4: DestroyWindow,
    5: DestroySubWindows,
    6: ChangeSaveSet,
    7: ReparentWindow,
    8: MapWindow,
    9: MapSubwindows,
    10: UnmapWindow,
    11: UnmapSubwindows,
    12: ConfigureWindow,
    13: CirculateWindow,
    14: GetGeometry,
    15: QueryTree,
    16: InternAtom,
    17: GetAtomName,
    18: ChangeProperty,
    19: DeleteProperty,
    20: GetProperty,
    21: ListProperties,
    22: SetSelectionOwner,
    23: GetSelectionOwner,
    24: ConvertSelection,
    25: SendEvent,
    26: GrabPointer,
    27: UngrabPointer,
    28: GrabButton,
    29: UngrabButton,
    30: ChangeActivePointerGrab,
    31: GrabKeyboard,
    32: UngrabKeyboard,
    33: GrabKey,
    34: UngrabKey,
    35: AllowEvents,
    36: GrabServer,
    37: UngrabServer,
    38: QueryPointer,
    39: GetMotionEvents,
    40: TranslateCoords,
    41: WarpPointer,
    42: SetInputFocus,
    43: GetInputFocus,
    44: QueryKeymap,
    45: OpenFont,
    46: CloseFont,
    47: QueryFont,
    48: QueryTextExtents,
    49: ListFonts,
    50: ListFontsWithInfo,
    51: SetFontPath,
    52: GetFontPath,
    53: CreatePixmap,
    54: FreePixmap,
    55: CreateGC,
    56: ChangeGC,
    57: CopyGC,
    58: SetDashes,
    59: SetClipRectangles,
    60: FreeGC,
    61: ClearArea,
    62: CopyArea,
    63: CopyPlane,
    64: PolyPoint,
    65: PolyLine,
    66: PolySegment,
    67: PolyRectangle,
    68: PolyArc,
    69: FillPoly,
    70: PolyFillRectangle,
    71: PolyFillArc,
    72: PutImage,
    73: GetImage,
    74: PolyText8,
    75: PolyText16,
    76: ImageText8,
    77: ImageText16,
    78: CreateColormap,
    79: FreeColormap,
    80: CopyColormapAndFree,
    81: InstallColormap,
    82: UninstallColormap,
    83: ListInstalledColormaps,
    84: AllocColor,
    85: AllocNamedColor,
    86: AllocColorCells,
    87: AllocColorPlanes,
    88: FreeColors,
    89: StoreColors,
    90: StoreNamedColor,
    91: QueryColors,
    92: LookupColor,
    93: CreateCursor,
    94: CreateGlyphCursor,
    95: FreeCursor,
    96: RecolorCursor,
    97: QueryBestSize,
    98: QueryExtension,
    99: ListExtensions,
    100: ChangeKeyboardMapping,
    101: GetKeyboardMapping,
    102: ChangeKeyboardControl,
    103: GetKeyboardControl,
    104: Bell,
    105: ChangePointerControl,
    106: GetPointerControl,
    107: SetScreenSaver,
    108: GetScreenSaver,
    109: ChangeHosts,
    110: ListHosts,
    111: SetAccessControl,
    112: SetCloseDownMode,
    113: KillClient,
    114: RotateProperties,
    115: ForceScreenSaver,
    116: SetPointerMapping,
    117: GetPointerMapping,
    118: SetModifierMapping,
    119: GetModifierMapping,
    127: NoOperation,
    }
