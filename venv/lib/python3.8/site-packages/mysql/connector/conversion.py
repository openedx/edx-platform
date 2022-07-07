# Copyright (c) 2009, 2022, Oracle and/or its affiliates.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0, as
# published by the Free Software Foundation.
#
# This program is also distributed with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms,
# as designated in a particular file or component or in included license
# documentation.  The authors of MySQL hereby grant you an
# additional permission to link the program and your derivative works
# with the separately licensed software that they have included with
# MySQL.
#
# Without limiting anything contained in the foregoing, this file,
# which is part of MySQL Connector/Python, is also subject to the
# Universal FOSS Exception, version 1.0, a copy of which can be found at
# http://oss.oracle.com/licenses/universal-foss-exception.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

"""Converting MySQL and Python types
"""

import datetime
import math
import struct
import time
from decimal import Decimal

from .constants import FieldType, FieldFlag, CharacterSet
from .utils import NUMERIC_TYPES
from .custom_types import HexLiteral

CONVERT_ERROR = "Could not convert '{value}' to python {pytype}"


class MySQLConverterBase(object):
    """Base class for conversion classes

    All class dealing with converting to and from MySQL data types must
    be a subclass of this class.
    """

    def __init__(self, charset='utf8', use_unicode=True, str_fallback=False):
        self.python_types = None
        self.mysql_types = None
        self.charset = None
        self.charset_id = 0
        self.use_unicode = None
        self.set_charset(charset)
        self.use_unicode = use_unicode
        self.str_fallback = str_fallback
        self._cache_field_types = {}

    def set_charset(self, charset):
        """Set character set"""
        if charset == 'utf8mb4':
            charset = 'utf8'
        if charset is not None:
            self.charset = charset
        else:
            # default to utf8
            self.charset = 'utf8'
        self.charset_id = CharacterSet.get_charset_info(self.charset)[0]

    def set_unicode(self, value=True):
        """Set whether to use Unicode"""
        self.use_unicode = value

    def to_mysql(self, value):
        """Convert Python data type to MySQL"""
        type_name = value.__class__.__name__.lower()
        try:
            return getattr(self, "_{0}_to_mysql".format(type_name))(value)
        except AttributeError:
            return value

    def to_python(self, vtype, value):
        """Convert MySQL data type to Python"""

        if (value == b'\x00' or value is None) and vtype[1] != FieldType.BIT:
            # Don't go further when we hit a NULL value
            return None

        if not self._cache_field_types:
            self._cache_field_types = {}
            for name, info in FieldType.desc.items():
                try:
                    self._cache_field_types[info[0]] = getattr(
                        self, '_{0}_to_python'.format(name))
                except AttributeError:
                    # We ignore field types which has no method
                    pass

        try:
            return self._cache_field_types[vtype[1]](value, vtype)
        except KeyError:
            return value

    def escape(self, value):
        """Escape buffer for sending to MySQL"""
        return value

    def quote(self, buf):
        """Quote buffer for sending to MySQL"""
        return str(buf)


class MySQLConverter(MySQLConverterBase):
    """Default conversion class for MySQL Connector/Python.

     o escape method: for escaping values send to MySQL
     o quoting method: for quoting values send to MySQL in statements
     o conversion mapping: maps Python and MySQL data types to
       function for converting them.

    Whenever one needs to convert values differently, a converter_class
    argument can be given while instantiating a new connection like
    cnx.connect(converter_class=CustomMySQLConverterClass).

    """

    def __init__(self, charset=None, use_unicode=True, str_fallback=False):
        MySQLConverterBase.__init__(self, charset, use_unicode, str_fallback)
        self._cache_field_types = {}

    def escape(self, value):
        """
        Escapes special characters as they are expected to by when MySQL
        receives them.
        As found in MySQL source mysys/charset.c

        Returns the value if not a string, or the escaped string.
        """
        if value is None:
            return value
        elif isinstance(value, NUMERIC_TYPES):
            return value
        if isinstance(value, (bytes, bytearray)):
            value = value.replace(b'\\', b'\\\\')
            value = value.replace(b'\n', b'\\n')
            value = value.replace(b'\r', b'\\r')
            value = value.replace(b'\047', b'\134\047')  # single quotes
            value = value.replace(b'\042', b'\134\042')  # double quotes
            value = value.replace(b'\032', b'\134\032')  # for Win32
        else:
            value = value.replace('\\', '\\\\')
            value = value.replace('\n', '\\n')
            value = value.replace('\r', '\\r')
            value = value.replace('\047', '\134\047')  # single quotes
            value = value.replace('\042', '\134\042')  # double quotes
            value = value.replace('\032', '\134\032')  # for Win32
        return value

    def quote(self, buf):
        """
        Quote the parameters for commands. General rules:
          o numbers are returns as bytes using ascii codec
          o None is returned as bytearray(b'NULL')
          o Everything else is single quoted '<buf>'

        Returns a bytearray object.
        """
        if isinstance(buf, NUMERIC_TYPES):
            return str(buf).encode('ascii')
        elif isinstance(buf, type(None)):
            return bytearray(b"NULL")
        return bytearray(b"'" + buf + b"'")

    def to_mysql(self, value):
        """Convert Python data type to MySQL"""
        type_name = value.__class__.__name__.lower()
        try:
            return getattr(self, "_{0}_to_mysql".format(type_name))(value)
        except AttributeError:
            if self.str_fallback:
                return str(value).encode()
            raise TypeError("Python '{0}' cannot be converted to a "
                            "MySQL type".format(type_name))

    def to_python(self, vtype, value):
        """Convert MySQL data type to Python"""
        if value == 0 and vtype[1] != FieldType.BIT:  # \x00
            # Don't go further when we hit a NULL value
            return None
        if value is None:
            return None

        if not self._cache_field_types:
            self._cache_field_types = {}
            for name, info in FieldType.desc.items():
                try:
                    self._cache_field_types[info[0]] = getattr(
                        self, '_{0}_to_python'.format(name))
                except AttributeError:
                    # We ignore field types which has no method
                    pass

        try:
            return self._cache_field_types[vtype[1]](value, vtype)
        except KeyError:
            # If one type is not defined, we just return the value as str
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value
        except ValueError as err:
            raise ValueError("%s (field %s)" % (err, vtype[0]))
        except TypeError as err:
            raise TypeError("%s (field %s)" % (err, vtype[0]))
        except:
            raise

    def _int_to_mysql(self, value):
        """Convert value to int"""
        return int(value)

    def _long_to_mysql(self, value):
        """Convert value to int"""
        return int(value)

    def _float_to_mysql(self, value):
        """Convert value to float"""
        if math.isnan(value):
            return None
        return float(value)

    def _str_to_mysql(self, value):
        """Convert value to string"""
        return self._unicode_to_mysql(value)

    def _unicode_to_mysql(self, value):
        """Convert unicode"""
        charset = self.charset
        charset_id = self.charset_id
        if charset == 'binary':
            charset = 'utf8'
            charset_id = CharacterSet.get_charset_info(charset)[0]
        encoded = value.encode(charset)
        if charset_id in CharacterSet.slash_charsets:
            if b'\x5c' in encoded:
                return HexLiteral(value, charset)
        return encoded

    def _bytes_to_mysql(self, value):
        """Convert value to bytes"""
        return value

    def _bytearray_to_mysql(self, value):
        """Convert value to bytes"""
        return bytes(value)

    def _bool_to_mysql(self, value):
        """Convert value to boolean"""
        if value:
            return 1
        return 0

    def _nonetype_to_mysql(self, value):
        """
        This would return what None would be in MySQL, but instead we
        leave it None and return it right away. The actual conversion
        from None to NULL happens in the quoting functionality.

        Return None.
        """
        return None

    def _datetime_to_mysql(self, value):
        """
        Converts a datetime instance to a string suitable for MySQL.
        The returned string has format: %Y-%m-%d %H:%M:%S[.%f]

        If the instance isn't a datetime.datetime type, it return None.

        Returns a bytes.
        """
        if value.microsecond:
            fmt = '{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}.{6:06d}'
            return fmt.format(
                value.year, value.month, value.day,
                value.hour, value.minute, value.second,
                value.microsecond).encode('ascii')

        fmt = '{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'
        return fmt.format(
            value.year, value.month, value.day,
            value.hour, value.minute, value.second).encode('ascii')

    def _date_to_mysql(self, value):
        """
        Converts a date instance to a string suitable for MySQL.
        The returned string has format: %Y-%m-%d

        If the instance isn't a datetime.date type, it return None.

        Returns a bytes.
        """
        return '{0:04d}-{1:02d}-{2:02d}'.format(value.year, value.month,
                                                value.day).encode('ascii')

    def _time_to_mysql(self, value):
        """
        Converts a time instance to a string suitable for MySQL.
        The returned string has format: %H:%M:%S[.%f]

        If the instance isn't a datetime.time type, it return None.

        Returns a bytes.
        """
        if value.microsecond:
            return value.strftime('%H:%M:%S.%f').encode('ascii')
        return value.strftime('%H:%M:%S').encode('ascii')

    def _struct_time_to_mysql(self, value):
        """
        Converts a time.struct_time sequence to a string suitable
        for MySQL.
        The returned string has format: %Y-%m-%d %H:%M:%S

        Returns a bytes or None when not valid.
        """
        return time.strftime('%Y-%m-%d %H:%M:%S', value).encode('ascii')

    def _timedelta_to_mysql(self, value):
        """
        Converts a timedelta instance to a string suitable for MySQL.
        The returned string has format: %H:%M:%S

        Returns a bytes.
        """
        seconds = abs(value.days * 86400 + value.seconds)

        if value.microseconds:
            fmt = '{0:02d}:{1:02d}:{2:02d}.{3:06d}'
            if value.days < 0:
                mcs = 1000000 - value.microseconds
                seconds -= 1
            else:
                mcs = value.microseconds
        else:
            fmt = '{0:02d}:{1:02d}:{2:02d}'

        if value.days < 0:
            fmt = '-' + fmt

        (hours, remainder) = divmod(seconds, 3600)
        (mins, secs) = divmod(remainder, 60)

        if value.microseconds:
            result = fmt.format(hours, mins, secs, mcs)
        else:
            result = fmt.format(hours, mins, secs)

        return result.encode('ascii')

    def _decimal_to_mysql(self, value):
        """
        Converts a decimal.Decimal instance to a string suitable for
        MySQL.

        Returns a bytes or None when not valid.
        """
        if isinstance(value, Decimal):
            return str(value).encode('ascii')

        return None

    def row_to_python(self, row, fields):
        """Convert a MySQL text result row to Python types

        The row argument is a sequence containing text result returned
        by a MySQL server. Each value of the row is converted to the
        using the field type information in the fields argument.

        Returns a tuple.
        """
        i = 0
        result = [None]*len(fields)

        if not self._cache_field_types:
            self._cache_field_types = {}
            for name, info in FieldType.desc.items():
                try:
                    self._cache_field_types[info[0]] = getattr(
                        self, '_{0}_to_python'.format(name))
                except AttributeError:
                    # We ignore field types which has no method
                    pass

        for field in fields:
            field_type = field[1]

            if (row[i] == 0 and field_type != FieldType.BIT) or row[i] is None:
                # Don't convert NULL value
                i += 1
                continue

            try:
                result[i] = self._cache_field_types[field_type](row[i], field)
            except KeyError:
                # If one type is not defined, we just return the value as str
                try:
                    result[i] = row[i].decode('utf-8')
                except UnicodeDecodeError:
                    result[i] = row[i]
            except (ValueError, TypeError) as err:
                err.message = "{0} (field {1})".format(str(err), field[0])
                raise

            i += 1

        return tuple(result)

    def _FLOAT_to_python(self, value, desc=None):  # pylint: disable=C0103
        """
        Returns value as float type.
        """
        return float(value)

    _DOUBLE_to_python = _FLOAT_to_python

    def _INT_to_python(self, value, desc=None):  # pylint: disable=C0103
        """
        Returns value as int type.
        """
        return int(value)

    _TINY_to_python = _INT_to_python
    _SHORT_to_python = _INT_to_python
    _INT24_to_python = _INT_to_python
    _LONG_to_python = _INT_to_python
    _LONGLONG_to_python = _INT_to_python

    def _DECIMAL_to_python(self, value, desc=None):  # pylint: disable=C0103
        """
        Returns value as a decimal.Decimal.
        """
        val = value.decode(self.charset)
        return Decimal(val)

    _NEWDECIMAL_to_python = _DECIMAL_to_python

    def _str(self, value, desc=None):
        """
        Returns value as str type.
        """
        return str(value)

    def _BIT_to_python(self, value, dsc=None):  # pylint: disable=C0103
        """Returns BIT columntype as integer"""
        int_val = value
        if len(int_val) < 8:
            int_val = b'\x00' * (8 - len(int_val)) + int_val
        return struct.unpack('>Q', int_val)[0]

    def _DATE_to_python(self, value, dsc=None):  # pylint: disable=C0103
        """Converts TIME column MySQL to a python datetime.datetime type.

        Raises ValueError if the value can not be converted.

        Returns DATE column type as datetime.date type.
        """
        if isinstance(value, datetime.date):
            return value
        try:
            parts = value.split(b'-')
            if len(parts) != 3:
                raise ValueError("invalid datetime format: {} len: {}"
                                 "".format(parts, len(parts)))
            try:
                return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                return None
        except (IndexError, ValueError):
            raise ValueError(
                "Could not convert {0} to python datetime.timedelta".format(
                    value))

    _NEWDATE_to_python = _DATE_to_python

    def _TIME_to_python(self, value, dsc=None):  # pylint: disable=C0103
        """Converts TIME column value to python datetime.time value type.

        Converts the TIME column MySQL type passed as bytes to a python
        datetime.datetime type.

        Raises ValueError if the value can not be converted.

        Returns datetime.time type.
        """
        try:
            (hms, mcs) = value.split(b'.')
            mcs = int(mcs.ljust(6, b'0'))
        except (TypeError, ValueError):
            hms = value
            mcs = 0
        try:
            (hours, mins, secs) = [int(d) for d in hms.split(b':')]
            if value[0] == 45 or value[0] == '-':
                mins, secs, mcs = -mins, -secs, -mcs
            return datetime.timedelta(hours=hours, minutes=mins,
                                      seconds=secs, microseconds=mcs)
        except (IndexError, TypeError, ValueError):
            raise ValueError(CONVERT_ERROR.format(value=value,
                                                  pytype="datetime.timedelta"))

    def _DATETIME_to_python(self, value, dsc=None):  # pylint: disable=C0103
        """"Converts DATETIME column value to python datetime.time value type.

        Converts the DATETIME column MySQL type passed as bytes to a python
        datetime.datetime type.

        Returns: datetime.datetime type.
        """
        if isinstance(value, datetime.datetime):
            return value
        datetime_val = None
        try:
            (date_, time_) = value.split(b' ')
            if len(time_) > 8:
                (hms, mcs) = time_.split(b'.')
                mcs = int(mcs.ljust(6, b'0'))
            else:
                hms = time_
                mcs = 0
            dtval = [int(i) for i in date_.split(b'-')] + \
                    [int(i) for i in hms.split(b':')] + [mcs, ]
            if len(dtval) < 6:
                raise ValueError("invalid datetime format: {} len: {}"
                                 "".format(dtval, len(dtval)))
            else:
                # Note that by default MySQL accepts invalid timestamps
                # (this is also backward compatibility).
                # Traditionaly C/py returns None for this well formed but
                # invalid datetime for python like '0000-00-00 HH:MM:SS'.
                try:
                    datetime_val = datetime.datetime(*dtval)
                except ValueError:
                    return None
        except (IndexError, TypeError):
            raise ValueError(CONVERT_ERROR.format(value=value,
                                                  pytype="datetime.timedelta"))

        return datetime_val

    _TIMESTAMP_to_python = _DATETIME_to_python

    def _YEAR_to_python(self, value, desc=None):  # pylint: disable=C0103
        """Returns YEAR column type as integer"""
        try:
            year = int(value)
        except ValueError:
            raise ValueError("Failed converting YEAR to int (%s)" % value)

        return year

    def _SET_to_python(self, value, dsc=None):  # pylint: disable=C0103
        """Returns SET column type as set

        Actually, MySQL protocol sees a SET as a string type field. So this
        code isn't called directly, but used by STRING_to_python() method.

        Returns SET column type as a set.
        """
        set_type = None
        val = value.decode(self.charset)
        if not val:
            return set()
        try:
            set_type = set(val.split(','))
        except ValueError:
            raise ValueError("Could not convert set %s to a sequence." % value)
        return set_type

    def _STRING_to_python(self, value, dsc=None):  # pylint: disable=C0103
        """
        Note that a SET is a string too, but using the FieldFlag we can see
        whether we have to split it.

        Returns string typed columns as string type.
        """
        if self.charset == "binary":
            return value
        if dsc is not None:
            if dsc[1] == FieldType.JSON and self.use_unicode:
                return value.decode(self.charset)
            if dsc[7] & FieldFlag.SET:
                return self._SET_to_python(value, dsc)
            if dsc[8] == 63:  # 'binary' charset
                return value
        if isinstance(value, (bytes, bytearray)) and self.use_unicode:
            try:
                return value.decode(self.charset)
            except UnicodeDecodeError:
                return value

        return value

    _VAR_STRING_to_python = _STRING_to_python
    _JSON_to_python = _STRING_to_python

    def _BLOB_to_python(self, value, dsc=None):  # pylint: disable=C0103
        """Convert BLOB data type to Python."""
        if dsc is not None:
            if dsc[7] & FieldFlag.BLOB and dsc[7] & FieldFlag.BINARY:
                return bytes(value)
        return self._STRING_to_python(value, dsc)

    _LONG_BLOB_to_python = _BLOB_to_python
    _MEDIUM_BLOB_to_python = _BLOB_to_python
    _TINY_BLOB_to_python = _BLOB_to_python
