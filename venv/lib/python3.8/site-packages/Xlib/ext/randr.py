# Xlib.ext.randr -- RandR extension module
#
#    Copyright (C) 2006 Mike Meyer <mwm@mired.org>
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



"""RandR - provide access to the RandR extension information.

This implementation is based off version 1.3 of the XRandR protocol, and may
not be compatible with other versions.

Version 1.2 of the protocol is documented at:
http://cgit.freedesktop.org/xorg/proto/randrproto/tree/randrproto.txt

"""


from Xlib import X
from Xlib.protocol import rq, structs

extname = 'RANDR'


# Event codes #
RRScreenChangeNotify        = 0

# V1.2 additions
RRNotify                    = 1

# RRNotify Subcodes
RRNotify_CrtcChange         = 0
RRNotify_OutputChange       = 1
RRNotify_OutputProperty     = 2


# Event selection bits #
RRScreenChangeNotifyMask    = (1 << 0)

# V1.2 additions
RRCrtcChangeNotifyMask      = (1 << 1)
RROutputChangeNotifyMask    = (1 << 2)
RROutputPropertyNotifyMask  = (1 << 3)


# Constants #
SetConfigSuccess            = 0
SetConfigInvalidConfigTime  = 1
SetConfigInvalidTime        = 2
SetConfigFailed             = 3

# used in the rotation field; rotation and reflection in 0.1 proto.
Rotate_0                    = 1
Rotate_90                   = 2
Rotate_180                  = 4
Rotate_270                  = 8

# new in 1.0 protocol, to allow reflection of screen
Reflect_X                   = 16
Reflect_Y                   = 32

# new in 1.2 protocol
HSyncPositive               = 0x00000001
HSyncNegative               = 0x00000002
VSyncPositive               = 0x00000004
VSyncNegative               = 0x00000008
Interlace                   = 0x00000010
DoubleScan                  = 0x00000020
CSync                       = 0x00000040
CSyncPositive               = 0x00000080
CSyncNegative               = 0x00000100
HSkewPresent                = 0x00000200
BCast                       = 0x00000400
PixelMultiplex              = 0x00000800
DoubleClock                 = 0x00001000
ClockDivideBy2              = 0x00002000

# event types?
Connected                   = 0
Disconnected                = 1
UnknownConnection           = 2

# Conventional RandR output properties
PROPERTY_RANDR_EDID         = "EDID"
PROPERTY_SIGNAL_FORMAT      = "SignalFormat"
PROPERTY_SIGNAL_PROPERTIES  = "SignalProperties"
PROPERTY_CONNECTOR_TYPE     = "ConnectorType"
PROPERTY_CONNECTOR_NUMBER   = "ConnectorNumber"
PROPERTY_COMPATIBILITY_LIST = "CompatibilityList"
PROPERTY_CLONE_LIST         = "CloneList"

# subpixel order - TODO: These constants are part of the RENDER extension and
# should be moved there if/when that extension is added to python-xlib.
SubPixelUnknown             = 0
SubPixelHorizontalRGB       = 1
SubPixelHorizontalBGR       = 2
SubPixelVerticalRGB         = 3
SubPixelVerticalBGR         = 4
SubPixelNone                = 5


# Error Codes #
BadRROutput                 = 0
BadRRCrtc                   = 1
BadRRMode                   = 2


# Data Structures #

RandR_ScreenSizes = rq.Struct(
        rq.Card16('width_in_pixels'),
        rq.Card16('height_in_pixels'),
        rq.Card16('width_in_millimeters'),
        rq.Card16('height_in_millimeters'),
        )


RandR_ModeInfo = rq.Struct(
        rq.Card32('id'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Card32('dot_clock'),
        rq.Card16('h_sync_start'),
        rq.Card16('h_sync_end'),
        rq.Card16('h_total'),
        rq.Card16('h_skew'),
        rq.Card16('v_sync_start'),
        rq.Card16('v_sync_end'),
        rq.Card16('v_total'),
        rq.Card16('name_length'),
        rq.Card32('flags'),
        )

RandR_Rates = rq.Struct(
        rq.LengthOf('rates', 2),
        rq.List('rates', rq.Card16Obj)
        )

# TODO: This struct is part of the RENDER extension and should be moved there
# if/when that extension is added to python-xlib.
Render_Transform = rq.Struct(
        rq.Card32('matrix11'), #FIXME: All of these are listed as FIXED in the protocol header.
        rq.Card32('matrix12'),
        rq.Card32('matrix13'),
        rq.Card32('matrix21'),
        rq.Card32('matrix22'),
        rq.Card32('matrix23'),
        rq.Card32('matrix31'),
        rq.Card32('matrix32'),
        rq.Card32('matrix33'),
        )


# Requests #

class QueryVersion(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(0),
        rq.RequestLength(),
        rq.Card32('major_version'),
        rq.Card32('minor_version'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('major_version'),
        rq.Card32('minor_version'),
        rq.Pad(16),
        )

def query_version(self):
    """Get the current version of the RandR extension.

    """
    return QueryVersion(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        major_version=1,
        minor_version=3,
        )


class _1_0SetScreenConfig(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(2),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.Card32('timestamp'),
        rq.Card32('config_timestamp'),
        rq.Card16('size_id'),
        rq.Card16('rotation'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('new_timestamp'),
        rq.Card32('new_config_timestamp'),
        rq.Window('root'),
        rq.Card16('subpixel_order'),
        rq.Pad(10),
        )

def _1_0set_screen_config(self, size_id, rotation, config_timestamp, timestamp=X.CurrentTime):
    """Sets the screen to the specified size and rotation.

    """
    return _1_0SetScreenConfig(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        drawable=self,
        timestamp=timestamp,
        config_timestamp=config_timestamp,
        size_id=size_id,
        rotation=rotation,
        )


class SetScreenConfig(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(2),
        rq.RequestLength(),
        rq.Drawable('drawable'),
        rq.Card32('timestamp'),
        rq.Card32('config_timestamp'),
        rq.Card16('size_id'),
        rq.Card16('rotation'),
        rq.Card16('rate'), # added in version 1.1
        rq.Pad(2),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('new_timestamp'),
        rq.Card32('new_config_timestamp'),
        rq.Window('root'),
        rq.Card16('subpixel_order'),
        rq.Pad(10),
        )

def set_screen_config(self, size_id, rotation, config_timestamp, rate=0, timestamp=X.CurrentTime):
    """Sets the screen to the specified size, rate, rotation and reflection.

    rate can be 0 to have the server select an appropriate rate.

    """
    return SetScreenConfig(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        drawable=self,
        timestamp=timestamp,
        config_timestamp=config_timestamp,
        size_id=size_id,
        rotation=rotation,
        rate=rate,
        )


class SelectInput(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(4),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Card16('mask'),
        rq.Pad(2),
        )

def select_input(self, mask):
    return SelectInput(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        window=self,
        mask=mask,
        )


class GetScreenInfo(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(5),
        rq.RequestLength(),
        rq.Window('window'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('set_of_rotations'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Window('root'),
        rq.Card32('timestamp'),
        rq.Card32('config_timestamp'),
        rq.LengthOf('sizes', 2),
        rq.Card16('size_id'),
        rq.Card16('rotation'),
        rq.Card16('rate'), # added in version 1.1
        rq.Card16('n_rate_ents'), # XCB's protocol description disagrees with the X headers on this; ignoring.
        rq.Pad(2),
        rq.List('sizes', RandR_ScreenSizes),
        #rq.List('rates', RandR_Rates) #FIXME: Why does uncommenting this cause an error?
        )

def get_screen_info(self):
    """Retrieve information about the current and available configurations for
    the screen associated with this window.

    """
    return GetScreenInfo(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        window=self,
        )


# version 1.2

class GetScreenSizeRange(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(6),
        rq.RequestLength(),
        rq.Window('window'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card16('min_width'),
        rq.Card16('min_height'),
        rq.Card16('max_width'),
        rq.Card16('max_height'),
        rq.Pad(16),
        )

def get_screen_size_range(self):
    """Retrieve the range of possible screen sizes. The screen may be set to
	any size within this range.

    """
    return GetScreenSizeRange(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        window=self,
        )


class SetScreenSize(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(7),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Card32('width_in_millimeters'),
        rq.Card32('height_in_millimeters'),
        )

def set_screen_size(self, width, height, width_in_millimeters=None, height_in_millimeters=None):
    return SetScreenSize(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        window=self,
        width=width,
        height=height,
        width_in_millimeters=width_in_millimeters,
        height_in_millimeters=height_in_millimeters,
        )


class GetScreenResources(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(8),
        rq.RequestLength(),
        rq.Window('window'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('timestamp'),
        rq.Card32('config_timestamp'),
        rq.LengthOf('crtcs', 2),
        rq.LengthOf('outputs', 2),
        rq.LengthOf('modes', 2),
        rq.LengthOf('mode_names', 2),
        rq.Pad(8),
        rq.List('crtcs', rq.Card32Obj),
        rq.List('outputs', rq.Card32Obj),
        rq.List('modes', RandR_ModeInfo),
        rq.String8('mode_names'),
        )

def get_screen_resources(self):
    return GetScreenResources(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        window=self,
        )


class GetOutputInfo(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(9),
        rq.RequestLength(),
        rq.Card32('output'),
        rq.Card32('config_timestamp'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('timestamp'),
        rq.Card32('crtc'),
        rq.Card32('mm_width'),
        rq.Card32('mm_height'),
        rq.Card8('connection'),
        rq.Card8('subpixel_order'),
        rq.LengthOf('crtcs', 2),
        rq.LengthOf('modes', 2),
        rq.LengthOf('preferred', 2),
        rq.LengthOf('clones', 2),
        rq.LengthOf('name', 2),
        rq.List('crtcs', rq.Card32Obj),
        rq.List('modes', rq.Card32Obj),
        rq.List('preferred', rq.Card32Obj),
        rq.List('clones', rq.Card32Obj),
        rq.String8('name'),
        )

def get_output_info(self, output, config_timestamp):
    return GetOutputInfo(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        output=output,
        config_timestamp=config_timestamp,
        )


class ListOutputProperties(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(10),
        rq.RequestLength(),
        rq.Card32('output'),
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

def list_output_properties(self, output):
    return ListOutputProperties (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        output=output,
        )


class QueryOutputProperty(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(11),
        rq.RequestLength(),
        rq.Card32('output'),
        rq.Card32('property'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Bool('pending'),
        rq.Bool('range'),
        rq.Bool('immutable'),
        rq.Pad(21),
        rq.List('valid_values', rq.Card32Obj),
        )

def query_output_property(self, output, property):
    return QueryOutputProperty (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        output=output,
        property=property,
        )


class ConfigureOutputProperty (rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(12),
        rq.RequestLength(),
        rq.Card32('output'),
        rq.Card32('property'),
        rq.Bool('pending'),
        rq.Bool('range'),
        rq.Pad(2),
        rq.List('valid_values', rq.Card32Obj),
        )

def configure_output_property (self, output, property):
    return ConfigureOutputProperty (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        output=output,
        property=property,
        )


class ChangeOutputProperty(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(13),
        rq.RequestLength(),
        rq.Card32('output'),
        rq.Card32('property'),
        rq.Card32('type'),
        rq.Format('value', 1),
        rq.Card8('mode'),
        rq.Pad(2),
        rq.LengthOf('value', 4),
        rq.List('value', rq.Card8Obj),
        )

def change_output_property(self, output, property, type, format, mode, nUnits):
    return ChangeOutputProperty(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        output=output,
        property=property,
        type=type,
        format=format,
        mode=mode,
        nUnits=nUnits,
        )


class DeleteOutputProperty(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(14),
        rq.RequestLength(),
        rq.Card32('output'),
        rq.Card32('property'),
        )

def delete_output_property(self, output, property):
    return DeleteOutputProperty(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        output=output,
        property=property,
        )


class GetOutputProperty(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(15),
        rq.RequestLength(),
        rq.Card32('output'),
        rq.Card32('property'),
        rq.Card32('type'),
        rq.Card32('long_offset'),
        rq.Card32('long_length'),
        rq.Bool('delete'),
        rq.Bool('pending'),
        rq.Pad(2),
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
        rq.List('value', rq.Card8Obj),
        )

def get_output_property(self, output, property, type, longOffset, longLength):
    return GetOutputProperty(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        output=output,
        property=property,
        type=type,
        longOffset=longOffset,
        longLength=longLength,
        )


class CreateMode(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(16),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Object('mode', RandR_ModeInfo),
        rq.String8('name'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('mode'),
        rq.Pad(20),
        )

def create_mode(self):
    return CreateMode (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        window=self,
        )


class DestroyMode(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(17),
        rq.RequestLength(),
        rq.Card32('mode'),
        )

def destroy_mode(self, mode):
    return DestroyMode(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        mode=mode,
        )


class AddOutputMode(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(18),
        rq.RequestLength(),
        rq.Card32('output'),
        rq.Card32('mode'),
        )

def add_output_mode(self):
    return AddOutputMode(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        output=output,
        mode=mode,
        )


class DeleteOutputMode(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(19),
        rq.RequestLength(),
        rq.Card32('output'),
        rq.Card32('mode'),
        )

def delete_output_mode(self):
    return DeleteOutputMode(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        output=output,
        mode=mode,
        )


class GetCrtcInfo(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(20),
        rq.RequestLength(),
        rq.Card32('crtc'),
        rq.Card32('config_timestamp'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('timestamp'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Card32('mode'),
        rq.Card16('rotation'),
        rq.Card16('possible_rotations'),
        rq.LengthOf('outputs', 2),
        rq.LengthOf('possible_outputs', 2),
        rq.List('outputs', rq.Card32Obj),
        rq.List('possible_outputs', rq.Card32Obj),
        )

def get_crtc_info(self, crtc, config_timestamp):
    return GetCrtcInfo (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        crtc=crtc,
        config_timestamp=config_timestamp,
        )


class SetCrtcConfig(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(21),
        rq.RequestLength(),
        rq.Card32('crtc'),
        rq.Card32('timestamp'),
        rq.Card32('config_timestamp'),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.Card32('mode'),
        rq.Card16('rotation'),
        rq.Pad(2),
        rq.List('outputs', rq.Card32Obj),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('new_timestamp'),
        rq.Pad(20),
        )

def set_crtc_config(self, crtc, config_timestamp, mode, rotation, timestamp=X.CurrentTime):
    return SetCrtcConfig (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        crtc=crtc,
        config_timestamp=config_timestamp,
        mode=mode,
        rotation=rotation,
        timestamp=timestamp,
        )


class GetCrtcGammaSize(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(22),
        rq.RequestLength(),
        rq.Card32('crtc'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card16('size'),
        rq.Pad(22),
        )

def get_crtc_gamma_size(self, crtc):
    return GetCrtcGammaSize (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        crtc=crtc,
        )


class GetCrtcGamma(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(23),
        rq.RequestLength(),
        rq.Card32('crtc'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card16('size'),
        rq.Pad(22),
        rq.List('red', rq.Card16Obj),
        rq.List('green', rq.Card16Obj),
        rq.List('blue', rq.Card16Obj),
        )

def get_crtc_gamma(self, crtc):
    return GetCrtcGamma (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        crtc=crtc,
        )


class SetCrtcGamma(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(24),
        rq.RequestLength(),
        rq.Card32('crtc'),
        rq.Card16('size'),
        rq.Pad(2),
        rq.List('red', rq.Card16Obj),
        rq.List('green', rq.Card16Obj),
        rq.List('blue', rq.Card16Obj),
        )

def set_crtc_gamma(self, crtc, size):
    return SetCrtcGamma(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        crtc=crtc,
        size=size,
        )


# version 1.3

class GetScreenResourcesCurrent(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(25),
        rq.RequestLength(),
        rq.Window('window'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('timestamp'),
        rq.Card32('config_timestamp'),
        rq.LengthOf('crtcs', 2),
        rq.LengthOf('outputs', 2),
        rq.LengthOf('modes', 2),
        rq.LengthOf('names', 2),
        rq.Pad(8),
        rq.List('crtcs', rq.Card32Obj),
        rq.List('outputs', rq.Card32Obj),
        rq.List('modes', RandR_ModeInfo),
        rq.String8('names'),
        )

def get_screen_resources_current(self):
    return GetScreenResourcesCurrent(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        window=self,
        )


class SetCrtcTransform(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(26),
        rq.RequestLength(),
        rq.Card32('crtc'),
        rq.Object('transform', Render_Transform),
        rq.LengthOf('filter_name', 2),
        rq.Pad(2),
        rq.String8('filter_name'),
        rq.List('filter_params', rq.Card32Obj), #FIXME: The protocol says FIXED? http://cgit.freedesktop.org/xorg/proto/randrproto/tree/randrproto.txt#n2161
        )

def set_crtc_transform(self, crtc, n_bytes_filter):
    return SetCrtcTransform(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        crtc=crtc,
        n_bytes_filter=n_bytes_filter,
        )


class GetCrtcTransform(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(27),
        rq.RequestLength(),
        rq.Card32('crtc'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Object('pending_transform', Render_Transform),
        rq.Bool('has_transforms'),
        rq.Pad(3),
        rq.Object('current_transform', Render_Transform),
        rq.Pad(4),
        rq.LengthOf('pending_filter_name', 2),
        rq.LengthOf('pending_filter_params', 2),
        rq.LengthOf('current_filter_name', 2),
        rq.LengthOf('current_filter_params', 2),
        rq.String8('pending_filter_name'),
        rq.List('pending_filter_params', rq.Card32Obj), #FIXME: The protocol says FIXED? http://cgit.freedesktop.org/xorg/proto/randrproto/tree/randrproto.txt#n2161
        rq.String8('current_filter_name'),
        rq.List('current_filter_params', rq.Card32Obj), #FIXME: The protocol says FIXED? http://cgit.freedesktop.org/xorg/proto/randrproto/tree/randrproto.txt#n2161
        )

def get_crtc_transform(self, crtc):
    return GetCrtcTransform(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        crtc=crtc,
        )


class GetPanning(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(28),
        rq.RequestLength(),
        rq.Card32('crtc'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('timestamp'),
        rq.Card16('left'),
        rq.Card16('top'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Card16('track_left'),
        rq.Card16('track_top'),
        rq.Card16('track_width'),
        rq.Card16('track_height'),
        rq.Int16('border_left'),
        rq.Int16('border_top'),
        rq.Int16('border_right'),
        rq.Int16('border_bottom'),
        )

def get_panning(self, crtc):
    return GetPanning (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        crtc=crtc,
        )


class SetPanning(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(29),
        rq.RequestLength(),
        rq.Card32('crtc'),
        rq.Card32('timestamp'),
        rq.Card16('left'),
        rq.Card16('top'),
        rq.Card16('width'),
        rq.Card16('height'),
        rq.Card16('track_left'),
        rq.Card16('track_top'),
        rq.Card16('track_width'),
        rq.Card16('track_height'),
        rq.Int16('border_left'),
        rq.Int16('border_top'),
        rq.Int16('border_right'),
        rq.Int16('border_bottom'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Card8('status'),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('new_timestamp'),
        rq.Pad(20),
        )

def set_panning(self, crtc, left, top, width, height, track_left, track_top, track_width, track_height, border_left, border_top, border_width, border_height, timestamp=X.CurrentTime):
    return SetPanning (
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        crtc=crtc,
        left=left,
        top=top,
        width=width,
        height=height,
        track_left=track_left,
        track_top=track_top,
        track_width=track_width,
        track_height=track_height,
        border_left=border_left,
        border_top=border_top,
        border_width=border_width,
        border_height=border_height,
        timestamp=timestamp,
        )


class SetOutputPrimary(rq.Request):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(30),
        rq.RequestLength(),
        rq.Window('window'),
        rq.Card32('output'),
        )

def set_output_primary(self, output):
    return SetOutputPrimary(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        window=self,
        output=output,
        )


class GetOutputPrimary(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(31),
        rq.RequestLength(),
        rq.Window('window'),
        )
    _reply = rq.Struct(
        rq.ReplyCode(),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.ReplyLength(),
        rq.Card32('output'),
        rq.Pad(20),
        )

def get_output_primary(self):
    return GetOutputPrimary(
        display=self.display,
        opcode=self.display.get_extension_major(extname),
        window=self,
        )


# Events #

class ScreenChangeNotify(rq.Event):
    _code = None
    _fields = rq.Struct(
        rq.Card8('type'),
        rq.Card8('rotation'),
        rq.Card16('sequence_number'),
        rq.Card32('timestamp'),
        rq.Card32('config_timestamp'),
        rq.Window('root'),
        rq.Window('window'),
        rq.Card16('size_id'),
        rq.Card16('subpixel_order'),
        rq.Card16('width_in_pixels'),
        rq.Card16('height_in_pixels'),
        rq.Card16('width_in_millimeters'),
        rq.Card16('height_in_millimeters'),
        )


class CrtcChangeNotify(rq.Event):
    _code = None
    _fields = rq.Struct(
        rq.Card8('type'),
        rq.Card8('sub_code'),
        rq.Card16('sequence_number'),
        rq.Card32('timestamp'),
        rq.Window('window'),
        rq.Card32('crtc'),
        rq.Card32('mode'),
        rq.Card16('rotation'),
        rq.Pad(2),
        rq.Int16('x'),
        rq.Int16('y'),
        rq.Card16('width'),
        rq.Card16('height'),
        )


class OutputChangeNotify(rq.Event):
    _code = None
    _fields = rq.Struct(
        rq.Card8('type'),
        rq.Card8('sub_code'),
        rq.Card16('sequence_number'),
        rq.Card32('timestamp'),
        rq.Card32('config_timestamp'),
        rq.Window('window'),
        rq.Card32('output'),
        rq.Card32('crtc'),
        rq.Card32('mode'),
        rq.Card16('rotation'),
        rq.Card8('connection'),
        rq.Card8('subpixel_order'),
        )


class OutputPropertyNotify(rq.Event):
    _code = None
    _fields = rq.Struct(
        rq.Card8('type'),
        rq.Card8('sub_code'),
        rq.Card16('sequence_number'),
        rq.Window('window'),
        rq.Card32('output'),
        rq.Card32('atom'),
        rq.Card32('timestamp'),
        rq.Card8('state'),
        rq.Pad(11),
        )


# Initialization #

def init(disp, info):
    disp.extension_add_method('display', 'xrandr_query_version', query_version)
    disp.extension_add_method('window', 'xrandr_select_input', select_input)
    disp.extension_add_method('window', 'xrandr_get_screen_info', get_screen_info)
    disp.extension_add_method('drawable', 'xrandr_1_0set_screen_config', _1_0set_screen_config)
    disp.extension_add_method('drawable', 'xrandr_set_screen_config', set_screen_config)
    disp.extension_add_method('window', 'xrandr_get_screen_size_range', get_screen_size_range)
    disp.extension_add_method('window', 'xrandr_set_screen_size', set_screen_size)
    disp.extension_add_method('window', 'xrandr_get_screen_resources', get_screen_resources)
    disp.extension_add_method('display', 'xrandr_get_output_info', get_output_info)
    disp.extension_add_method('display', 'xrandr_list_output_properties', list_output_properties)
    disp.extension_add_method('display', 'xrandr_query_output_property', query_output_property)
    disp.extension_add_method('display', 'xrandr_configure_output_property ', configure_output_property )
    disp.extension_add_method('display', 'xrandr_change_output_property', change_output_property)
    disp.extension_add_method('display', 'xrandr_delete_output_property', delete_output_property)
    disp.extension_add_method('display', 'xrandr_get_output_property', get_output_property)
    disp.extension_add_method('window', 'xrandr_create_mode', create_mode)
    disp.extension_add_method('display', 'xrandr_destroy_mode', destroy_mode)
    disp.extension_add_method('display', 'xrandr_add_output_mode', add_output_mode)
    disp.extension_add_method('display', 'xrandr_delete_output_mode', delete_output_mode)
    disp.extension_add_method('display', 'xrandr_get_crtc_info', get_crtc_info)
    disp.extension_add_method('display', 'xrandr_set_crtc_config', set_crtc_config)
    disp.extension_add_method('display', 'xrandr_get_crtc_gamma_size', get_crtc_gamma_size)
    disp.extension_add_method('display', 'xrandr_get_crtc_gamma', get_crtc_gamma)
    disp.extension_add_method('display', 'xrandr_set_crtc_gamma', set_crtc_gamma)
    disp.extension_add_method('window', 'xrandr_get_screen_resources_current', get_screen_resources_current)
    disp.extension_add_method('display', 'xrandr_set_crtc_transform', set_crtc_transform)
    disp.extension_add_method('display', 'xrandr_get_crtc_transform', get_crtc_transform)
    disp.extension_add_method('window', 'xrandr_set_output_primary', set_output_primary)
    disp.extension_add_method('window', 'xrandr_get_output_primary', get_output_primary)
    disp.extension_add_method('display', 'xrandr_get_panning', get_panning)
    disp.extension_add_method('display', 'xrandr_set_panning', set_panning)

    disp.extension_add_event(info.first_event, ScreenChangeNotify)
    disp.extension_add_event(info.first_event + 1, CrtcChangeNotify)
    disp.extension_add_event(info.first_event + 2, OutputChangeNotify)
    disp.extension_add_event(info.first_event + 3, OutputPropertyNotify)

    #disp.extension_add_error(BadRROutput, BadRROutputError)
    #disp.extension_add_error(BadRRCrtc, BadRRCrtcError)
    #disp.extension_add_error(BadRRMode, BadRRModeError)
