# Xlib.ext.record -- RECORD extension module
#
#    Copyright (C) 2006 Alex Badea <vamposdecampos@gmail.com>
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

from Xlib import X
from Xlib.protocol import rq

extname = 'RECORD'

FromServerTime          = 0x01
FromClientTime          = 0x02
FromClientSequence      = 0x04

CurrentClients          = 1
FutureClients           = 2
AllClients              = 3

FromServer              = 0
FromClient              = 1
ClientStarted           = 2
ClientDied              = 3
StartOfData             = 4
EndOfData               = 5

Record_Range8 = rq.Struct(
        rq.Card8('first'),
        rq.Card8('last'))
Record_Range16 = rq.Struct(
        rq.Card16('first'),
        rq.Card16('last'))
Record_ExtRange = rq.Struct(
        rq.Object('major_range', Record_Range8),
        rq.Object('minor_range', Record_Range16))
Record_Range = rq.Struct(
        rq.Object('core_requests', Record_Range8),
        rq.Object('core_replies', Record_Range8),
        rq.Object('ext_requests', Record_ExtRange),
        rq.Object('ext_replies', Record_ExtRange),
        rq.Object('delivered_events', Record_Range8),
        rq.Object('device_events', Record_Range8),
        rq.Object('errors', Record_Range8),
        rq.Bool('client_started'),
        rq.Bool('client_died'))

Record_ClientInfo = rq.Struct(
        rq.Card32('client_resource'),
        rq.LengthOf('ranges', 4),
        rq.List('ranges', Record_Range))


class RawField(rq.ValueField):
    """A field with raw data, stored as a string"""

    structcode = None

    def pack_value(self, val):
        return val, len(val), None

    def parse_binary_value(self, data, display, length, format):
        return data, ''


class GetVersion(rq.ReplyRequest):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(0),
            rq.RequestLength(),
            rq.Card16('major_version'),
            rq.Card16('minor_version'))
    _reply = rq.Struct(
            rq.Pad(2),
            rq.Card16('sequence_number'),
            rq.ReplyLength(),
            rq.Card16('major_version'),
            rq.Card16('minor_version'),
            rq.Pad(20))

def get_version(self, major, minor):
    return GetVersion(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            major_version = major,
            minor_version = minor)


class CreateContext(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(1),
            rq.RequestLength(),
            rq.Card32('context'),           # Record_RC
            rq.Card8('element_header'),     # Record_Element_Header
            rq.Pad(3),
            rq.LengthOf('clients', 4),
            rq.LengthOf('ranges', 4),
            rq.List('clients', rq.Card32Obj),
            rq.List('ranges', Record_Range))

def create_context(self, datum_flags, clients, ranges):
    context = self.display.allocate_resource_id()
    CreateContext(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            context = context,
            element_header = datum_flags,
            clients = clients,
            ranges = ranges)
    return context


class RegisterClients(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(2),
            rq.RequestLength(),
            rq.Card32('context'),           # Record_RC
            rq.Card8('element_header'),     # Record_Element_Header
            rq.Pad(3),
            rq.LengthOf('clients', 4),
            rq.LengthOf('ranges', 4),
            rq.List('clients', rq.Card32Obj),
            rq.List('ranges', Record_Range))

def register_clients(self, context, element_header, clients, ranges):
    RegisterClients(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            context = context,
            element_header = element_header,
            clients = clients,
            ranges = ranges)


class UnregisterClients(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(3),
            rq.RequestLength(),
            rq.Card32('context'),           # Record_RC
            rq.LengthOf('clients', 4),
            rq.List('clients', rq.Card32Obj))

def unregister_clients(self, context, clients):
    UnregisterClients(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            context = context,
            clients = clients)


class GetContext(rq.ReplyRequest):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(4),
            rq.RequestLength(),
            rq.Card32('context'))           # Record_RC
    _reply = rq.Struct(
            rq.Pad(2),
            rq.Card16('sequence_number'),
            rq.ReplyLength(),
            rq.Card8('element_header'),     # Record_Element_Header
            rq.Pad(3),
            rq.LengthOf('client_info', 4),
            rq.Pad(16),
            rq.List('client_info', Record_ClientInfo))

def get_context(self, context):
    return GetContext(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            context = context)


class EnableContext(rq.ReplyRequest):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(5),
            rq.RequestLength(),
            rq.Card32('context'))           # Record_RC
    _reply = rq.Struct(
            rq.Pad(1),
            rq.Card8('category'),
            rq.Card16('sequence_number'),
            rq.ReplyLength(),
            rq.Card8('element_header'),     # Record_Element_Header
            rq.Bool('client_swapped'),
            rq.Pad(2),
            rq.Card32('id_base'),           # Record_XIDBase
            rq.Card32('server_time'),
            rq.Card32('recorded_sequence_number'),
            rq.Pad(8),
            RawField('data'))

    # This request receives multiple responses, so we need to keep
    # ourselves in the 'sent_requests' list in order to receive them all.

    # See the discussion on ListFonstsWithInfo in request.py

    def __init__(self, callback, *args, **keys):
        self._callback = callback
        rq.ReplyRequest.__init__(self, *args, **keys)

    def _parse_response(self, data):
        r, d = self._reply.parse_binary(data, self._display)
        self._callback(r)

        if r.category == StartOfData:
            # Hack ourselves a sequence number, used by the code in
            # Xlib.protocol.display.Display.parse_request_response()
            self.sequence_number = r.sequence_number

        if r.category == EndOfData:
            self._response_lock.acquire()
            self._data = r
            self._response_lock.release()
        else:
            self._display.sent_requests.insert(0, self)

def enable_context(self, context, callback):
    EnableContext(
            callback = callback,
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            context = context)


class DisableContext(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(6),
            rq.RequestLength(),
            rq.Card32('context'))           # Record_RC

def disable_context(self, context):
    DisableContext(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            context = context)


class FreeContext(rq.Request):
    _request = rq.Struct(
            rq.Card8('opcode'),
            rq.Opcode(7),
            rq.RequestLength(),
            rq.Card32('context'))           # Record_RC

def free_context(self, context):
    FreeContext(
            display = self.display,
            opcode = self.display.get_extension_major(extname),
            context = context)
    self.display.free_resource_id(context)


def init(disp, info):
    disp.extension_add_method('display', 'record_get_version', get_version)
    disp.extension_add_method('display', 'record_create_context', create_context)
    disp.extension_add_method('display', 'record_register_clients', register_clients)
    disp.extension_add_method('display', 'record_unregister_clients', unregister_clients)
    disp.extension_add_method('display', 'record_get_context', get_context)
    disp.extension_add_method('display', 'record_enable_context', enable_context)
    disp.extension_add_method('display', 'record_disable_context', disable_context)
    disp.extension_add_method('display', 'record_free_context', free_context)
