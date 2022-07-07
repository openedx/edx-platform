# Xlib.protocol.rq -- structure primitives for request, events and errors
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

from array import array
import struct
import sys
import traceback
import types

# Xlib modules
from Xlib import X
from Xlib.support import lock


_PY3 = sys.version[0] >= '3'

# in Python 3, bytes are an actual array; in python 2, bytes are still
# string-like, so in order to get an array element we need to call ord()
if _PY3:
    def _bytes_item(x):
        return x
else:
    def _bytes_item(x):
        return ord(x)

class BadDataError(Exception): pass

# These are struct codes, we know their byte sizes

signed_codes = { 1: 'b', 2: 'h', 4: 'l' }
unsigned_codes = { 1: 'B', 2: 'H', 4: 'L' }


# Unfortunately, we don't know the array sizes of B, H and L, since
# these use the underlying architecture's size for a char, short and
# long.  Therefore we probe for their sizes, and additionally create
# a mapping that translates from struct codes to array codes.
#
# Bleah.

array_unsigned_codes = { }
struct_to_array_codes = { }

for c in 'bhil':
    size = array(c).itemsize

    array_unsigned_codes[size] = c.upper()
    try:
        struct_to_array_codes[signed_codes[size]] = c
        struct_to_array_codes[unsigned_codes[size]] = c.upper()
    except KeyError:
        pass

# print array_unsigned_codes, struct_to_array_codes


class Field:
    """Field objects represent the data fields of a Struct.

    Field objects must have the following attributes:

       name         -- the field name, or None
       structcode   -- the struct codes representing this field
       structvalues -- the number of values encodes by structcode

    Additionally, these attributes should either be None or real methods:

       check_value  -- check a value before it is converted to binary
       parse_value  -- parse a value after it has been converted from binary

    If one of these attributes are None, no check or additional
    parsings will be done one values when converting to or from binary
    form.  Otherwise, the methods should have the following behaviour:

       newval = check_value(val)
         Check that VAL is legal when converting to binary form.  The
         value can also be converted to another Python value.  In any
         case, return the possibly new value.  NEWVAL should be a
         single Python value if structvalues is 1, a tuple of
         structvalues elements otherwise.

       newval = parse_value(val, display)
         VAL is an unpacked Python value, which now can be further
         refined.  DISPLAY is the current Display object.  Return the
         new value.  VAL will be a single value if structvalues is 1,
         a tuple of structvalues elements otherwise.

    If `structcode' is None the Field must have the method
    f.parse_binary_value() instead.  See its documentation string for
    details.

    """

    name = None
    default = None

    structcode = None
    structvalues = 0

    check_value = None
    parse_value = None

    keyword_args = 0

    def __init__(self):
        pass

    def parse_binary_value(self, data, display, length, format):
        """value, remaindata = f.parse_binary_value(data, display, length, format)

        Decode a value for this field from the binary string DATA.
        If there are a LengthField and/or a FormatField connected to this
        field, their values will be LENGTH and FORMAT, respectively.  If
        there are no such fields the parameters will be None.

        DISPLAY is the display involved, which is really only used by
        the Resource fields.

        The decoded value is returned as VALUE, and the remaining part
        of DATA shold be returned as REMAINDATA.
        """

        raise RuntimeError('Neither structcode or parse_binary_value provided for %s'
                           % self)


class Pad(Field):
    def __init__(self, size):
        self.size = size
        self.value = b'\0' * size
        self.structcode = '%dx' % size
        self.structvalues = 0


class ConstantField(Field):
    def __init__(self, value):
        self.value = value


class Opcode(ConstantField):
    structcode = 'B'
    structvalues = 1

class ReplyCode(ConstantField):
    structcode = 'B'
    structvalues = 1

    def __init__(self):
        self.value = 1

class LengthField(Field):
    """A LengthField stores the length of some other Field whose size
    may vary, e.g. List and String8.

    Its name should be the same as the name of the field whose size
    it stores.

    The lf.get_binary_value() method of LengthFields is not used, instead
    a lf.get_binary_length() should be provided.

    Unless LengthField.get_binary_length() is overridden in child classes,
    there should also be a lf.calc_length().
    """

    structcode = 'L'
    structvalues = 1

    def calc_length(self, length):
        """newlen = lf.calc_length(length)

        Return a new length NEWLEN based on the provided LENGTH.
        """

        return length


class TotalLengthField(LengthField):
    pass

class RequestLength(TotalLengthField):
    structcode = 'H'
    structvalues = 1

    def calc_length(self, length):
        return length // 4

class ReplyLength(TotalLengthField):
    structcode = 'L'
    structvalues = 1

    def calc_length(self, length):
        return (length - 32) // 4


class LengthOf(LengthField):
    def __init__(self, name, size):
        self.name = name
        self.structcode = unsigned_codes[size]


class OddLength(LengthField):
    structcode = 'B'
    structvalues = 1

    def __init__(self, name):
        self.name = name

    def calc_length(self, length):
        return length % 2

    def parse_value(self, value, display):
        if value == 0:
            return 'even'
        else:
            return 'odd'


class FormatField(Field):
    """A FormatField encodes the format of some other field, in a manner
    similar to LengthFields.

    The ff.get_binary_value() method is not used, replaced by
    ff.get_binary_format().
    """

    structvalues = 1

    def __init__(self, name, size):
        self.name = name
        self.structcode = unsigned_codes[size]

Format = FormatField


class ValueField(Field):
    def __init__(self, name, default = None):
        self.name = name
        self.default = default


class Int8(ValueField):
    structcode = 'b'
    structvalues = 1

class Int16(ValueField):
    structcode = 'h'
    structvalues = 1

class Int32(ValueField):
    structcode = 'l'
    structvalues = 1

class Card8(ValueField):
    structcode = 'B'
    structvalues = 1

class Card16(ValueField):
    structcode = 'H'
    structvalues = 1

class Card32(ValueField):
    structcode = 'L'
    structvalues = 1


class Resource(Card32):
    cast_function = '__resource__'
    class_name = 'resource'

    def __init__(self, name, codes = (), default = None):
        Card32.__init__(self, name, default)
        self.codes = codes

    def check_value(self, value):
        try:
            return getattr(value, self.cast_function)()
        except AttributeError:
            return value

    def parse_value(self, value, display):
        # if not display:
        #    return value
        if value in self.codes:
            return value

        c = display.get_resource_class(self.class_name)
        if c:
            return c(display, value)
        else:
            return value

class Window(Resource):
    cast_function = '__window__'
    class_name = 'window'

class Pixmap(Resource):
    cast_function = '__pixmap__'
    class_name = 'pixmap'

class Drawable(Resource):
    cast_function = '__drawable__'
    class_name = 'drawable'

class Fontable(Resource):
    cast_function = '__fontable__'
    class_name = 'fontable'

class Font(Resource):
    cast_function = '__font__'
    class_name = 'font'

class GC(Resource):
    cast_function = '__gc__'
    class_name = 'gc'

class Colormap(Resource):
    cast_function = '__colormap__'
    class_name = 'colormap'

class Cursor(Resource):
    cast_function = '__cursor__'
    class_name = 'cursor'


class Bool(ValueField):
    structvalues = 1
    structcode = 'B'

    def check_value(self, value):
        return not not value

class Set(ValueField):
    structvalues = 1

    def __init__(self, name, size, values, default = None):
        ValueField.__init__(self, name, default)
        self.structcode = unsigned_codes[size]
        self.values = values

    def check_value(self, val):
        if val not in self.values:
            raise ValueError('field %s: argument %s not in %s'
                             % (self.name, val, self.values))

        return val

class Gravity(Set):
    def __init__(self, name):
        Set.__init__(self, name, 1, (X.ForgetGravity, X.StaticGravity,
                                    X.NorthWestGravity, X.NorthGravity,
                                    X.NorthEastGravity, X.WestGravity,
                                    X.CenterGravity, X.EastGravity,
                                    X.SouthWestGravity, X.SouthGravity,
                                    X.SouthEastGravity))


class FixedString(ValueField):
    structvalues = 1

    def __init__(self, name, size):
        ValueField.__init__(self, name)
        self.structcode = '%ds' % size


class String8(ValueField):
    structcode = None

    def __init__(self, name, pad = 1):
        ValueField.__init__(self, name)
        self.pad = pad

    def pack_value(self, val):
        slen = len(val)

        if _PY3 and type(val) is str:
            val = val.encode('UTF-8')

        if self.pad:
            return val + b'\0' * ((4 - slen % 4) % 4), slen, None
        else:
            return val, slen, None

    def parse_binary_value(self, data, display, length, format):
        if length is None:
            try:
                return data.decode('UTF-8'), b''
            except UnicodeDecodeError:
                return data, b''

        if self.pad:
            slen = length + ((4 - length % 4) % 4)
        else:
            slen = length

        s = data[:length]
        try:
            s = s.decode('UTF-8')
        except UnicodeDecodeError:
            pass  # return as bytes
        return s, data[slen:]


class String16(ValueField):
    structcode = None

    def __init__(self, name, pad = 1):
        ValueField.__init__(self, name)
        self.pad = pad

    def pack_value(self, val):
        # Convert 8-byte string into 16-byte list
        if type(val) is str:
            val = [ord(c) for c in val]

        slen = len(val)

        if self.pad:
            pad = b'\0\0' * (slen % 2)
        else:
            pad = b''

        return (struct.pack(*('>' + 'H' * slen, ) + tuple(val)) + pad,
                slen, None)

    def parse_binary_value(self, data, display, length, format):
        if length == 'odd':
            length = len(data) // 2 - 1
        elif length == 'even':
            length = len(data) // 2

        if self.pad:
            slen = length + (length % 2)
        else:
            slen = length

        return (struct.unpack('>' + 'H' * length, data[:length * 2]),
                data[slen * 2:])



class List(ValueField):
    """The List, FixedList and Object fields store compound data objects.
    The type of data objects must be provided as an object with the
    following attributes and methods:

    ...

    """

    structcode = None

    def __init__(self, name, type, pad = 1):
        ValueField.__init__(self, name)
        self.type = type
        self.pad = pad

    def parse_binary_value(self, data, display, length, format):
        if length is None:
            ret = []
            if self.type.structcode is None:
                while data:
                    val, data = self.type.parse_binary(data, display)
                    ret.append(val)
            else:
                scode = '=' + self.type.structcode
                slen = struct.calcsize(scode)
                pos = 0
                while pos + slen <= len(data):
                    v = struct.unpack(scode, data[pos: pos + slen])

                    if self.type.structvalues == 1:
                        v = v[0]

                    if self.type.parse_value is None:
                        ret.append(v)
                    else:
                        ret.append(self.type.parse_value(v, display))

                    pos = pos + slen

                data = data[pos:]

        else:
            ret = [None] * int(length)

            if self.type.structcode is None:
                for i in range(length):
                    ret[i], data = self.type.parse_binary(data, display)
            else:
                scode = '=' + self.type.structcode
                slen = struct.calcsize(scode)
                pos = 0
                for i in range(0, length):
                    # FIXME: remove try..except
                    try:
                        v = struct.unpack(scode, data[pos: pos + slen])
                    except Exception:
                        v = b'\x00\x00\x00\x00'

                    if self.type.structvalues == 1:
                        v = v[0]

                    if self.type.parse_value is None:
                        ret[i] = v
                    else:
                        ret[i] = self.type.parse_value(v, display)

                    pos = pos + slen

                data = data[pos:]

        if self.pad:
            data = data[len(data) % 4:]

        return ret, data

    def pack_value(self, val):
        # Single-char values, we'll assume that means integer lists.
        if self.type.structcode and len(self.type.structcode) == 1:
            data = array(struct_to_array_codes[self.type.structcode],
                               val).tobytes()
        else:
            data = []
            for v in val:
                data.append(self.type.pack_value(v))

            data = b''.join(data)

        if self.pad:
            dlen = len(data)
            data = data + b'\0' * ((4 - dlen % 4) % 4)

        return data, len(val), None


class FixedList(List):
    def __init__(self, name, size, type, pad = 1):
        List.__init__(self, name, type, pad)
        self.size = size

    def parse_binary_value(self, data, display, length, format):
        return List.parse_binary_value(self, data, display, self.size, format)

    def pack_value(self, val):
        if len(val) != self.size:
            raise BadDataError('length mismatch for FixedList %s' % self.name)
        return List.pack_value(self, val)


class Object(ValueField):
    structcode = None

    def __init__(self, name, type, default = None):
        ValueField.__init__(self, name, default)
        self.type = type
        self.structcode = self.type.structcode
        self.structvalues = self.type.structvalues

    def parse_binary_value(self, data, display, length, format):
        if self.type.structcode is None:
            return self.type.parse_binary(data, display)

        else:
            scode = '=' + self.type.structcode
            slen = struct.calcsize(scode)

            v = struct.unpack(scode, data[:slen])
            if self.type.structvalues == 1:
                v = v[0]

            if self.type.parse_value is not None:
                v = self.type.parse_value(v, display)

            return v, data[slen:]

    def parse_value(self, val, display):
        if self.type.parse_value is None:
            return val
        else:
            return self.type.parse_value(val, display)

    def pack_value(self, val):
        # Single-char values, we'll assume that mean an integer
        if self.type.structcode and len(self.type.structcode) == 1:
            return struct.pack('=' + self.type.structcode, val), None, None
        else:
            return self.type.pack_value(val)

    def check_value(self, val):
        if self.type.structcode is None:
            return val

        if type(val) is tuple:
            return val

        if type(val) is dict:
            data = val
        elif isinstance(val, DictWrapper):
            data = val._data
        else:
            raise TypeError('Object value must be tuple, dictionary or DictWrapper: %s' % val)

        vals = []
        for f in self.type.fields:
            if f.name:
                vals.append(data[f.name])

        return vals


class PropertyData(ValueField):
    structcode = None

    def parse_binary_value(self, data, display, length, format):
        if length is None:
            length = len(data) // (format // 8)
        else:
            length = int(length)

        if format == 0:
            ret = None
            return ret, data

        elif format == 8:
            ret = (8, data[:length])
            data = data[length + ((4 - length % 4) % 4):]

        elif format == 16:
            ret = (16, array(array_unsigned_codes[2], data[:2 * length]))
            data = data[2 * (length + length % 2):]

        elif format == 32:
            ret = (32, array(array_unsigned_codes[4], data[:4 * length]))
            data = data[4 * length:]

        if type(ret[1]) is bytes:
            try:
                ret = (ret[0], ret[1].decode('UTF-8'))
            except UnicodeDecodeError:
                pass  # return as bytes

        return ret, data

    def pack_value(self, value):
        fmt, val = value

        if fmt not in (8, 16, 32):
            raise BadDataError('Invalid property data format %d' % fmt)

        if _PY3 and type(val) is str:
            val = val.encode('UTF-8')

        if type(val) is bytes:
            size = fmt // 8
            vlen = len(val)
            if vlen % size:
                vlen = vlen - vlen % size
                data = val[:vlen]
            else:
                data = val

            dlen = vlen // size

        else:
            if type(val) is tuple:
                val = list(val)

            size = fmt // 8
            data =  array(array_unsigned_codes[size], val).tobytes()
            dlen = len(val)

        dl = len(data)
        data = data + b'\0' * ((4 - dl % 4) % 4)

        return data, dlen, fmt


class FixedPropertyData(PropertyData):
    def __init__(self, name, size):
        PropertyData.__init__(self, name)
        self.size = size

    def parse_binary_value(self, data, display, length, format):
        return PropertyData.parse_binary_value(self, data, display,
                                               self.size // (format // 8), format)

    def pack_value(self, value):
        data, dlen, fmt = PropertyData.pack_value(self, value)

        if len(data) != self.size:
            raise BadDataError('Wrong data length for FixedPropertyData: %s'
                               % (value, ))

        return data, dlen, fmt


class ValueList(Field):
    structcode = None
    keyword_args = 1
    default = 'usekeywords'

    def __init__(self, name, mask, pad, *fields):
        self.name = name
        self.maskcode = '=%s%dx' % (unsigned_codes[mask], pad)
        self.maskcodelen = struct.calcsize(self.maskcode)
        self.fields = []

        flag = 1
        for f in fields:
            if f.name:
                self.fields.append((f, flag))
                flag = flag << 1

    def pack_value(self, arg, keys):
        mask = 0
        data = b''

        if arg == self.default:
            arg = keys

        for field, flag in self.fields:
            if field.name in arg:
                mask = mask | flag

                val = arg[field.name]
                if field.check_value is not None:
                    val = field.check_value(val)

                d = struct.pack('=' + field.structcode, val)
                data = data + d + b'\0' * (4 - len(d))

        return struct.pack(self.maskcode, mask) + data, None, None

    def parse_binary_value(self, data, display, length, format):
        r = {}

        mask = int(struct.unpack(self.maskcode, data[:self.maskcodelen])[0])
        data = data[self.maskcodelen:]

        for field, flag in self.fields:
            if mask & flag:
                if field.structcode:
                    vals = struct.unpack('=' + field.structcode,
                                         data[:struct.calcsize('=' + field.structcode)])
                    if field.structvalues == 1:
                        vals = vals[0]

                    if field.parse_value is not None:
                        vals = field.parse_value(vals, display)

                else:
                    vals, d = field.parse_binary_value(data[:4], display, None, None)

                r[field.name] = vals
                data = data[4:]

        return DictWrapper(r), data


class KeyboardMapping(ValueField):
    structcode = None

    def parse_binary_value(self, data, display, length, format):
        if length is None:
            dlen = len(data)
        else:
            dlen = 4 * length * format

        a = array(array_unsigned_codes[4], data[:dlen])

        ret = []
        for i in range(0, len(a), format):
            ret.append(a[i : i + format])

        return ret, data[dlen:]

    def pack_value(self, value):
        keycodes = 0
        for v in value:
            keycodes = max(keycodes, len(v))

        a = array(array_unsigned_codes[4])

        for v in value:
            for k in v:
                a.append(k)
            for i in range(len(v), keycodes):
                a.append(X.NoSymbol)

        return a.tobytes(), len(value), keycodes


class ModifierMapping(ValueField):
    structcode = None

    def parse_binary_value(self, data, display, length, format):
        a = array(array_unsigned_codes[1], data[:8 * format])

        ret = []
        for i in range(0, 8):
            ret.append(a[i * format : (i + 1) * format])

        return ret, data[8 * format:]

    def pack_value(self, value):
        if len(value) != 8:
            raise BadDataError('ModifierMapping list should have eight elements')

        keycodes = 0
        for v in value:
            keycodes = max(keycodes, len(v))

        a = array(array_unsigned_codes[1])

        for v in value:
            for k in v:
                a.append(k)
            for i in range(len(v), keycodes):
                a.append(0)

        return a.tobytes(), len(value), keycodes

class EventField(ValueField):
    structcode = None

    def pack_value(self, value):
        if not isinstance(value, Event):
            raise BadDataError('%s is not an Event for field %s' % (value, self.name))

        return value._binary, None, None

    def parse_binary_value(self, data, display, length, format):
        from Xlib.protocol import event

        estruct = display.event_classes.get(_bytes_item(data[0]) & 0x7f, event.AnyEvent)

        return estruct(display = display, binarydata = data[:32]), data[32:]


#
# Objects usable for List and FixedList fields.
# Struct is also usable.
#

class ScalarObj:
    def __init__(self, code):
        self.structcode = code
        self.structvalues = 1
        self.parse_value = None

Card8Obj  = ScalarObj('B')
Card16Obj = ScalarObj('H')
Card32Obj = ScalarObj('L')

class ResourceObj:
    structcode = 'L'
    structvalues = 1

    def __init__(self, class_name):
        self.class_name = class_name

    def parse_value(self, value, display):
        # if not display:
        #     return value
        c = display.get_resource_class(self.class_name)
        if c:
            return c(display, value)
        else:
            return value

WindowObj = ResourceObj('window')
ColormapObj = ResourceObj('colormap')

class StrClass:
    structcode = None

    def pack_value(self, val):
        if type(val) is not bytes:
            val = val.encode('UTF-8')
        if _PY3:
            val = bytes([len(val)]) + val
        else:
            val = chr(len(val)) + val
        return val

    def parse_binary(self, data, display):
        slen = _bytes_item(data[0]) + 1
        s = data[1:slen]
        try:
            s = s.decode('UTF-8')
        except UnicodeDecodeError:
            pass  # return as bytes
        return s, data[slen:]

Str = StrClass()


class Struct:

    """Struct objects represents a binary data structure.  It can
    contain both fields with static and dynamic sizes.  However, all
    static fields must appear before all dynamic fields.

    Fields are represented by various subclasses of the abstract base
    class Field.  The fields of a structure are given as arguments
    when instantiating a Struct object.

    Struct objects have two public methods:

      to_binary()    -- build a binary representation of the structure
                        with the values given as arguments
      parse_binary() -- convert a binary (string) representation into
                        a Python dictionary or object.

    These functions will be generated dynamically for each Struct
    object to make conversion as fast as possible.  They are
    generated the first time the methods are called.

    """

    def __init__(self, *fields):
        self.fields = fields

        # Structures for to_binary, parse_value and parse_binary
        self.static_codes = '='
        self.static_values = 0
        self.static_fields = []
        self.static_size = None
        self.var_fields = []

        for f in self.fields:
            # Append structcode if there is one and we haven't
            # got any varsize fields yet.
            if f.structcode is not None:
                assert not self.var_fields

                self.static_codes = self.static_codes + f.structcode

                # Only store fields with values
                if f.structvalues > 0:
                    self.static_fields.append(f)
                    self.static_values = self.static_values + f.structvalues

            # If we have got one varsize field, all the rest must
            # also be varsize fields.
            else:
                self.var_fields.append(f)

        self.static_size = struct.calcsize(self.static_codes)
        if self.var_fields:
            self.structcode = None
            self.structvalues = 0
        else:
            self.structcode = self.static_codes[1:]
            self.structvalues = self.static_values


    # These functions get called only once, as they will override
    # themselves with dynamically created functions in the Struct
    # object

    def to_binary(self, *varargs, **keys):

        """data = s.to_binary(...)

        Convert Python values into the binary representation.  The
        arguments will be all value fields with names, in the order
        given when the Struct object was instantiated.  With one
        exception: fields with default arguments will be last.

        Returns the binary representation as the string DATA.

        """

        code = ''
        total_length = str(self.static_size)
        joins = []
        args = []
        defargs = []
        kwarg = 0

        # First pack all varfields so their lengths and formats are
        # available when we pack their static LengthFields and
        # FormatFields

        i = 0
        for f in self.var_fields:
            if f.keyword_args:
                kwarg = 1
                kw = ', _keyword_args'
            else:
                kw = ''

            # Call pack_value method for each field, storing
            # the return values for later use
            code = code + ('  _%(name)s, _%(name)s_length, _%(name)s_format'
                           ' = self.var_fields[%(fno)d].pack_value(%(name)s%(kw)s)\n'
                           % { 'name': f.name,
                               'fno': i,
                               'kw': kw })

            total_length = total_length + ' + len(_%s)' % f.name
            joins.append('_%s' % f.name)

            i = i + 1


        # Construct argument list for struct.pack call, packing all
        # static fields.  First argument is the structcode, the
        # remaining are values.


        pack_args = ['"%s"' % self.static_codes]

        i = 0
        for f in self.static_fields:
            if isinstance(f, LengthField):

                # If this is a total length field, insert
                # the calculated field value here
                if isinstance(f, TotalLengthField):
                    if self.var_fields:
                        pack_args.append('self.static_fields[%d].calc_length(%s)'
                                         % (i, total_length))
                    else:
                        pack_args.append(str(f.calc_length(self.static_size)))
                else:
                    pack_args.append('self.static_fields[%d].calc_length(_%s_length)'
                                       % (i, f.name))

            # Format field, just insert the value we got previously
            elif isinstance(f, FormatField):
                pack_args.append('_%s_format' % f.name)

            # A constant field, insert its value directly
            elif isinstance(f, ConstantField):
                pack_args.append(str(f.value))

            # Value fields
            else:
                if f.structvalues == 1:

                    # If there's a value check/convert function, call it
                    if f.check_value is not None:
                        pack_args.append('self.static_fields[%d].check_value(%s)'
                                           % (i, f.name))

                    # Else just use the argument as provided
                    else:
                        pack_args.append(f.name)

                # Multivalue field.  Handled like single valuefield,
                # but the value are tuple unpacked into seperate arguments
                # which are appended to pack_args
                else:
                    a = []
                    for j in range(f.structvalues):
                        a.append('_%s_%d' % (f.name, j))

                    if f.check_value is not None:
                        code = code + ('  %s = self.static_fields[%d].check_value(%s)\n'
                                       % (', '.join(a), i, f.name))
                    else:
                        code = code + '  %s = %s\n' % (', '.join(a), f.name)

                    pack_args = pack_args + a

                # Add field to argument list
                if f.name:
                    if f.default is None:
                        args.append(f.name)
                    else:
                        defargs.append('%s = %s' % (f.name, repr(f.default)))

            i = i + 1

        # Construct call to struct.pack
        pack = 'struct.pack(%s)' % ', '.join(pack_args)

        # If there are any varfields, we append the packed strings to build
        # the resulting binary value
        if self.var_fields:
            code = code + '  return %s + %s\n' % (pack, ' + '.join(joins))

        # If there's only static fields, return the packed value
        else:
            code = code + '  return %s\n' % pack

        # Add all varsize fields to argument list.  We do it here
        # to ensure that they appear after the static fields.
        for f in self.var_fields:
            if f.name:
                if f.default is None:
                    args.append(f.name)
                else:
                    defargs.append('%s = %s' % (f.name, repr(f.default)))

        args = args + defargs
        if kwarg:
            args.append('**_keyword_args')

        # Add function header
        code = 'def to_binary(self, %s):\n' % ', '.join(args) + code

        # self._pack_code = code

        # print
        # print code
        # print

        # Finally, compile function by evaluating it.  This will store
        # the function in the local variable to_binary, thanks to the
        # def: line.  Convert it into a instance metod bound to self,
        # and store it in self.

        # Unfortunately, this creates a circular reference.  However,
        # Structs are not really created dynamically so the potential
        # memory leak isn't that serious.  Besides, Python 2.0 has
        # real garbage collect.

        g = globals().copy()
        exec(code, g)
        self.to_binary = types.MethodType(g['to_binary'], self)

        # Finally call it manually
        return self.to_binary(*varargs, **keys)


    def pack_value(self, value):

        """ This function allows Struct objects to be used in List and
        Object fields.  Each item represents the arguments to pass to
        to_binary, either a tuple, a dictionary or a DictWrapper.

        """

        if type(value) is tuple:
            return self.to_binary(*value, **{})
        elif type(value) is dict:
            return self.to_binary(*(), **value)
        elif isinstance(value, DictWrapper):
            return self.to_binary(*(), **value._data)
        else:
            raise BadDataError('%s is not a tuple or a list' % (value))


    def parse_value(self, val, display, rawdict = 0):

        """This function is used by List and Object fields to convert
        Struct objects with no var_fields into Python values.

        """

        code = ('def parse_value(self, val, display, rawdict = 0):\n'
                '  ret = {}\n')

        vno = 0
        fno = 0
        for f in self.static_fields:
            # Fields without names should be ignored, and there should
            # not be any length or format fields if this function
            # ever gets called.  (If there were such fields, there should
            # be a matching field in var_fields and then parse_binary
            # would have been called instead.

            if not f.name:
                pass

            elif isinstance(f, LengthField):
                pass

            elif isinstance(f, FormatField):
                pass

            # Value fields
            else:

                # Get the index or range in val representing this field.

                if f.structvalues == 1:
                    vrange = str(vno)
                else:
                    vrange = '%d:%d' % (vno, vno + f.structvalues)

                # If this field has a parse_value method, call it, otherwise
                # use the unpacked value as is.

                if f.parse_value is None:
                    code = code + '  ret["%s"] = val[%s]\n' % (f.name, vrange)
                else:
                    code = code + ('  ret["%s"] = self.static_fields[%d].'
                                   'parse_value(val[%s], display)\n'
                                   % (f.name, fno, vrange))

            fno = fno + 1
            vno = vno + f.structvalues

        code = code + '  if not rawdict: return DictWrapper(ret)\n'
        code = code + '  return ret\n'

        # print
        # print code
        # print

        # Finally, compile function as for to_binary.

        g = globals().copy()
        exec(code, g)
        self.parse_value = types.MethodType(g['parse_value'], self)

        # Call it manually
        return self.parse_value(val, display, rawdict)


    def parse_binary(self, data, display, rawdict = 0):

        """values, remdata = s.parse_binary(data, display, rawdict = 0)

        Convert a binary representation of the structure into Python values.

        DATA is a string or a buffer containing the binary data.
        DISPLAY should be a Xlib.protocol.display.Display object if
        there are any Resource fields or Lists with ResourceObjs.

        The Python values are returned as VALUES.  If RAWDICT is true,
        a Python dictionary is returned, where the keys are field
        names and the values are the corresponding Python value.  If
        RAWDICT is false, a DictWrapper will be returned where all
        fields are available as attributes.

        REMDATA are the remaining binary data, unused by the Struct object.

        """

        code = ('def parse_binary(self, data, display, rawdict = 0):\n'
                '  ret = {}\n'
                '  val = struct.unpack("%s", data[:%d])\n'
                % (self.static_codes, self.static_size))

        lengths = {}
        formats = {}

        vno = 0
        fno = 0
        for f in self.static_fields:

            # Fields without name should be ignored.  This is typically
            # pad and constant fields

            if not f.name:
                pass

            # Store index in val for Length and Format fields, to be used
            # when treating varfields.

            elif isinstance(f, LengthField):
                if f.parse_value is None:
                    lengths[f.name] = 'val[%d]' % vno
                else:
                    lengths[f.name] = ('self.static_fields[%d].'
                                       'parse_value(val[%d], display)'
                                       % (fno, vno))

            elif isinstance(f, FormatField):
                formats[f.name] = 'val[%d]' % vno

            # Treat value fields the same was as in parse_value.
            else:
                if f.structvalues == 1:
                    vrange = str(vno)
                else:
                    vrange = '%d:%d' % (vno, vno + f.structvalues)

                if f.parse_value is None:
                    code = code + '  ret["%s"] = val[%s]\n' % (f.name, vrange)
                else:
                    code = code + ('  ret["%s"] = self.static_fields[%d].'
                                   'parse_value(val[%s], display)\n'
                                   % (f.name, fno, vrange))

            fno = fno + 1
            vno = vno + f.structvalues

        code = code + '  data = data[%d:]\n' % self.static_size

        # Call parse_binary_value for each var_field, passing the
        # length and format values from the unpacked val.

        fno = 0
        for f in self.var_fields:
            code = code + ('  ret["%s"], data = '
                           'self.var_fields[%d].parse_binary_value'
                           '(data, display, %s, %s)\n'
                           % (f.name, fno,
                              lengths.get(f.name, 'None'),
                              formats.get(f.name, 'None')))
            fno = fno + 1

        code = code + '  if not rawdict: ret = DictWrapper(ret)\n'
        code = code + '  return ret, data\n'

        # print
        # print code
        # print

        # Finally, compile function as for to_binary.

        g = globals().copy()
        exec(code, g)
        self.parse_binary = types.MethodType(g['parse_binary'], self)

        # Call it manually
        return self.parse_binary(data, display, rawdict)


class TextElements8(ValueField):
    string_textitem = Struct( LengthOf('string', 1),
                              Int8('delta'),
                              String8('string', pad = 0) )

    def pack_value(self, value):
        data = b''
        args = {}

        for v in value:
            # Let values be simple strings, meaning a delta of 0
            if _PY3 and type(v) is str:
                v = v.encode('UTF-8')

            if type(v) is bytes:
                v = (0, v)

            # A tuple, it should be (delta, string)
            # Encode it as one or more textitems

            if type(v) in (tuple, dict) or \
               isinstance(v, DictWrapper):

                if type(v) is tuple:
                    delta, s = v
                else:
                    delta = v['delta']
                    s = v['string']

                while delta or s:
                    args['delta'] = delta
                    args['string'] = s[:254]

                    data = data + self.string_textitem.to_binary(*(), **args)

                    delta = 0
                    s = s[254:]

            # Else an integer, i.e. a font change
            else:
                # Use fontable cast function if instance
                if hasattr(v, '__fontable__'):
                    v = v.__fontable__()

                data = data + struct.pack('>BL', 255, v)

        # Pad out to four byte length
        dlen = len(data)
        return data + b'\0' * ((4 - dlen % 4) % 4), None, None

    def parse_binary_value(self, data, display, length, format):
        values = []
        while 1:
            if len(data) < 2:
                break

            # font change
            if _bytes_item(data[0]) == 255:
                values.append(struct.unpack('>L', data[1:5])[0])
                data = data[5:]

            # skip null strings
            elif _bytes_item(data[0]) == 0 and _bytes_item(data[1]) == 0:
                data = data[2:]

            # string with delta
            else:
                v, data = self.string_textitem.parse_binary(data, display)
                values.append(v)

        return values, b''



class TextElements16(TextElements8):
    string_textitem = Struct( LengthOf('string', 1),
                              Int8('delta'),
                              String16('string', pad = 0) )



class GetAttrData(object):
    def __getattr__(self, attr):
        try:
            if self._data:
                return self._data[attr]
            else:
                raise AttributeError(attr)
        except KeyError:
            raise AttributeError(attr)

class DictWrapper(GetAttrData):
    def __init__(self, dict):
        self.__dict__['_data'] = dict

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __setattr__(self, key, value):
        self._data[key] = value

    def __delattr__(self, key):
        del self._data[key]

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return '%s(%s)' % (self.__class__, repr(self._data))

    def __eq__(self, other):
        if isinstance(other, DictWrapper):
            return self._data == other._data
        else:
            return self._data == other

    def __ne__(self, other):
        return not self.__eq__(other)

class Request:
    def __init__(self, display, onerror = None, *args, **keys):
        self._errorhandler = onerror
        self._binary = self._request.to_binary(*args, **keys)
        self._serial = None
        display.send_request(self, onerror is not None)

    def _set_error(self, error):
        if self._errorhandler is not None:
            return call_error_handler(self._errorhandler, error, self)
        else:
            return 0

class ReplyRequest(GetAttrData):
    def __init__(self, display, defer = 0, *args, **keys):
        self._display = display
        self._binary = self._request.to_binary(*args, **keys)
        self._serial = None
        self._data = None
        self._error = None

        self._response_lock = lock.allocate_lock()

        self._display.send_request(self, 1)
        if not defer:
            self.reply()

    def reply(self):
        # Send request and wait for reply if we hasn't
        # already got one.  This means that reply() can safely
        # be called more than one time.

        self._response_lock.acquire()
        while self._data is None and self._error is None:
            self._display.send_recv_lock.acquire()
            self._response_lock.release()

            self._display.send_and_recv(request = self._serial)
            self._response_lock.acquire()

        self._response_lock.release()
        self._display = None

        # If error has been set, raise it
        if self._error:
            raise self._error

    def _parse_response(self, data):
        self._response_lock.acquire()
        self._data, d = self._reply.parse_binary(data, self._display, rawdict = 1)
        self._response_lock.release()

    def _set_error(self, error):
        self._response_lock.acquire()
        self._error = error
        self._response_lock.release()
        return 1

    def __repr__(self):
        return '<%s serial = %s, data = %s, error = %s>' % (self.__class__, self._serial, self._data, self._error)


class Event(GetAttrData):
    def __init__(self, binarydata = None, display = None,
                 **keys):
        if binarydata:
            self._binary = binarydata
            self._data, data = self._fields.parse_binary(binarydata, display,
                                                         rawdict = 1)
            # split event type into type and send_event bit
            self._data['send_event'] = not not self._data['type'] & 0x80
            self._data['type'] = self._data['type'] & 0x7f
        else:
            if self._code:
                keys['type'] = self._code

            keys['sequence_number'] = 0

            self._binary = self._fields.to_binary(*(), **keys)

            keys['send_event'] = 0
            self._data = keys

    def __repr__(self):
        kwlist = []
        for kw, val in self._data.items():
            if kw == 'send_event':
                continue
            if kw == 'type' and self._data['send_event']:
                val = val | 0x80
            kwlist.append('%s = %s' % (kw, repr(val)))

        kws = ', '.join(kwlist)
        return '%s(%s)' % (self.__class__, kws)

    def __eq__(self, other):
        if isinstance(other, Event):
            return self._data == other._data
        else:
            return cmp(self._data, other)

def call_error_handler(handler, error, request):
    try:
        return handler(error, request)
    except:
        sys.stderr.write('Exception raised by error handler.\n')
        traceback.print_exc()
        return 0
