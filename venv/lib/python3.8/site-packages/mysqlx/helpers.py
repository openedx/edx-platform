# Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
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

"""This module contains helper functions."""

import binascii
import decimal
import functools
import inspect
import warnings

from .constants import TLS_CIPHER_SUITES, TLS_VERSIONS
from .errors import InterfaceError


BYTE_TYPES = (bytearray, bytes,)
NUMERIC_TYPES = (int, float, decimal.Decimal,)


def encode_to_bytes(value, encoding="utf-8"):
    """Returns an encoded version of the string as a bytes object.

    Args:
        encoding (str): The encoding.

    Resturns:
        bytes: The encoded version of the string as a bytes object.
    """
    return value if isinstance(value, bytes) else value.encode(encoding)


def decode_from_bytes(value, encoding="utf-8"):
    """Returns a string decoded from the given bytes.

    Args:
        value (bytes): The value to be decoded.
        encoding (str): The encoding.

    Returns:
        str: The value decoded from bytes.
    """
    return value.decode(encoding) if isinstance(value, bytes) else value


def get_item_or_attr(obj, key):
    """Get item from dictionary or attribute from object.

    Args:
        obj (object): Dictionary or object.
        key (str): Key.

    Returns:
        object: The object for the provided key.
    """
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def escape(*args):
    """Escapes special characters as they are expected to be when MySQL
    receives them.
    As found in MySQL source mysys/charset.c

    Args:
        value (object): Value to be escaped.

    Returns:
        str: The value if not a string, or the escaped string.
    """
    def _escape(value):
        """Escapes special characters."""
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
    if len(args) > 1:
        return [_escape(arg) for arg in args]
    return _escape(args[0])


def quote_identifier(identifier, sql_mode=""):
    """Quote the given identifier with backticks, converting backticks (`)
    in the identifier name with the correct escape sequence (``) unless the
    identifier is quoted (") as in sql_mode set to ANSI_QUOTES.

    Args:
        identifier (str): Identifier to quote.

    Returns:
        str: Returns string with the identifier quoted with backticks.
    """
    if sql_mode == "ANSI_QUOTES":
        return '"{0}"'.format(identifier.replace('"', '""'))
    return "`{0}`".format(identifier.replace("`", "``"))


def deprecated(version=None, reason=None):
    """This is a decorator used to mark functions as deprecated.

    Args:
        version (Optional[string]): Version when was deprecated.
        reason (Optional[string]): Reason or extra information to be shown.

    Usage:

    .. code-block:: python

       from mysqlx.helpers import deprecated

       @deprecated('8.0.12', 'Please use other_function() instead')
       def deprecated_function(x, y):
           return x + y
    """
    def decorate(func):
        """Decorate function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function.

            Args:
                *args: Variable length argument list.
                **kwargs: Arbitrary keyword arguments.
            """
            message = ["'{}' is deprecated".format(func.__name__)]
            if version:
                message.append(" since version {}".format(version))
            if reason:
                message.append(". {}".format(reason))
            frame = inspect.currentframe().f_back
            warnings.warn_explicit("".join(message),
                                   category=DeprecationWarning,
                                   filename=inspect.getfile(frame.f_code),
                                   lineno=frame.f_lineno)
            return func(*args, **kwargs)
        return wrapper
    return decorate


def iani_to_openssl_cs_name(tls_version, cipher_suites_names):
    """Translates a cipher suites names list; from IANI names to OpenSSL names.

    Args:
        TLS_version (str): The TLS version to look at for a translation.
        cipher_suite_names (list): A list of cipher suites names.
    """
    translated_names = []

    cipher_suites = {}#TLS_CIPHER_SUITES[TLS_version]

    # Find the previews TLS versions of the given on TLS_version
    for index in range(TLS_VERSIONS.index(tls_version) + 1):
        cipher_suites.update(TLS_CIPHER_SUITES[TLS_VERSIONS[index]])

    for name in cipher_suites_names:
        if "-" in name:
            translated_names.append(name)
        elif name in cipher_suites:
            translated_names.append(cipher_suites[name])
        else:
            raise InterfaceError("The '{}' in cipher suites is not a valid "
                                 "cipher suite".format(name))
    return translated_names


def hexlify(data):
    """Return the hexadecimal representation of the binary data.

    Args:
        data (str): The binary data.

    Returns:
        bytes: The hexadecimal representation of data.
    """
    return binascii.hexlify(data).decode("utf-8")
