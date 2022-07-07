# Copyright (c) 2009, 2021, Oracle and/or its affiliates.
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

"""Utilities
"""

import os
import subprocess
from stringprep import (in_table_a1, in_table_b1, in_table_c11, in_table_c12,
                        in_table_c21_c22, in_table_c3, in_table_c4, in_table_c5,
                        in_table_c6, in_table_c7, in_table_c8, in_table_c9,
                        in_table_c12, in_table_d1, in_table_d2)
import platform
import struct
import sys
import unicodedata

from decimal import Decimal
from functools import lru_cache

from .custom_types import HexLiteral


__MYSQL_DEBUG__ = False

NUMERIC_TYPES = (int, float, Decimal, HexLiteral)


def intread(buf):
    """Unpacks the given buffer to an integer"""
    try:
        if isinstance(buf, int):
            return buf
        length = len(buf)
        if length == 1:
            return buf[0]
        elif length <= 4:
            tmp = buf + b'\x00'*(4-length)
            return struct.unpack('<I', tmp)[0]
        tmp = buf + b'\x00'*(8-length)
        return struct.unpack('<Q', tmp)[0]
    except:
        raise


def int1store(i):
    """
    Takes an unsigned byte (1 byte) and packs it as a bytes-object.

    Returns string.
    """
    if i < 0 or i > 255:
        raise ValueError('int1store requires 0 <= i <= 255')
    else:
        return bytearray(struct.pack('<B', i))


def int2store(i):
    """
    Takes an unsigned short (2 bytes) and packs it as a bytes-object.

    Returns string.
    """
    if i < 0 or i > 65535:
        raise ValueError('int2store requires 0 <= i <= 65535')
    else:
        return bytearray(struct.pack('<H', i))


def int3store(i):
    """
    Takes an unsigned integer (3 bytes) and packs it as a bytes-object.

    Returns string.
    """
    if i < 0 or i > 16777215:
        raise ValueError('int3store requires 0 <= i <= 16777215')
    else:
        return bytearray(struct.pack('<I', i)[0:3])


def int4store(i):
    """
    Takes an unsigned integer (4 bytes) and packs it as a bytes-object.

    Returns string.
    """
    if i < 0 or i > 4294967295:
        raise ValueError('int4store requires 0 <= i <= 4294967295')
    else:
        return bytearray(struct.pack('<I', i))


def int8store(i):
    """
    Takes an unsigned integer (8 bytes) and packs it as string.

    Returns string.
    """
    if i < 0 or i > 18446744073709551616:
        raise ValueError('int8store requires 0 <= i <= 2^64')
    else:
        return bytearray(struct.pack('<Q', i))


def intstore(i):
    """
    Takes an unsigned integers and packs it as a bytes-object.

    This function uses int1store, int2store, int3store,
    int4store or int8store depending on the integer value.

    returns string.
    """
    if i < 0 or i > 18446744073709551616:
        raise ValueError('intstore requires 0 <= i <=  2^64')

    if i <= 255:
        formed_string = int1store
    elif i <= 65535:
        formed_string = int2store
    elif i <= 16777215:
        formed_string = int3store
    elif i <= 4294967295:
        formed_string = int4store
    else:
        formed_string = int8store

    return formed_string(i)


def lc_int(i):
    """
    Takes an unsigned integer and packs it as bytes,
    with the information of how much bytes the encoded int takes.
    """
    if i < 0 or i > 18446744073709551616:
        raise ValueError('Requires 0 <= i <= 2^64')

    if i < 251:
        return bytearray(struct.pack('<B', i))
    elif i <= 65535:
        return b'\xfc' + bytearray(struct.pack('<H', i))
    elif i <= 16777215:
        return b'\xfd' + bytearray(struct.pack('<I', i)[0:3])

    return b'\xfe' + bytearray(struct.pack('<Q', i))


def read_bytes(buf, size):
    """
    Reads bytes from a buffer.

    Returns a tuple with buffer less the read bytes, and the bytes.
    """
    res = buf[0:size]
    return (buf[size:], res)


def read_lc_string(buf):
    """
    Takes a buffer and reads a length coded string from the start.

    This is how Length coded strings work

    If the string is 250 bytes long or smaller, then it looks like this:

      <-- 1b  -->
      +----------+-------------------------
      |  length  | a string goes here
      +----------+-------------------------

    If the string is bigger than 250, then it looks like this:

      <- 1b -><- 2/3/8 ->
      +------+-----------+-------------------------
      | type |  length   | a string goes here
      +------+-----------+-------------------------

      if type == \xfc:
          length is code in next 2 bytes
      elif type == \xfd:
          length is code in next 3 bytes
      elif type == \xfe:
          length is code in next 8 bytes

    NULL has a special value. If the buffer starts with \xfb then
    it's a NULL and we return None as value.

    Returns a tuple (trucated buffer, bytes).
    """
    if buf[0] == 251:  # \xfb
        # NULL value
        return (buf[1:], None)

    length = lsize = 0
    fst = buf[0]

    if fst <= 250:  # \xFA
        length = fst
        return (buf[1 + length:], buf[1:length + 1])
    elif fst == 252:
        lsize = 2
    elif fst == 253:
        lsize = 3
    if fst == 254:
        lsize = 8

    length = intread(buf[1:lsize + 1])
    return (buf[lsize + length + 1:], buf[lsize + 1:length + lsize + 1])


def read_lc_string_list(buf):
    """Reads all length encoded strings from the given buffer

    Returns a list of bytes
    """
    byteslst = []

    sizes = {252: 2, 253: 3, 254: 8}

    buf_len = len(buf)
    pos = 0

    while pos < buf_len:
        first = buf[pos]
        if first == 255:
            # Special case when MySQL error 1317 is returned by MySQL.
            # We simply return None.
            return None
        if first == 251:
            # NULL value
            byteslst.append(None)
            pos += 1
        else:
            if first <= 250:
                length = first
                byteslst.append(buf[(pos + 1):length + (pos + 1)])
                pos += 1 + length
            else:
                lsize = 0
                try:
                    lsize = sizes[first]
                except KeyError:
                    return None
                length = intread(buf[(pos + 1):lsize + (pos + 1)])
                byteslst.append(
                    buf[pos + 1 + lsize:length + lsize + (pos + 1)])
                pos += 1 + lsize + length

    return tuple(byteslst)


def read_string(buf, end=None, size=None):
    """
    Reads a string up until a character or for a given size.

    Returns a tuple (trucated buffer, string).
    """
    if end is None and size is None:
        raise ValueError('read_string() needs either end or size')

    if end is not None:
        try:
            idx = buf.index(end)
        except ValueError:
            raise ValueError("end byte not present in buffer")
        return (buf[idx + 1:], buf[0:idx])
    elif size is not None:
        return read_bytes(buf, size)

    raise ValueError('read_string() needs either end or size (weird)')


def read_int(buf, size):
    """Read an integer from buffer

    Returns a tuple (truncated buffer, int)
    """

    try:
        res = intread(buf[0:size])
    except:
        raise

    return (buf[size:], res)


def read_lc_int(buf):
    """
    Takes a buffer and reads an length code string from the start.

    Returns a tuple with buffer less the integer and the integer read.
    """
    if not buf:
        raise ValueError("Empty buffer.")

    lcbyte = buf[0]
    if lcbyte == 251:
        return (buf[1:], None)
    elif lcbyte < 251:
        return (buf[1:], int(lcbyte))
    elif lcbyte == 252:
        return (buf[3:], struct.unpack('<xH', buf[0:3])[0])
    elif lcbyte == 253:
        return (buf[4:], struct.unpack('<I', buf[1:4] + b'\x00')[0])
    elif lcbyte == 254:
        return (buf[9:], struct.unpack('<xQ', buf[0:9])[0])
    else:
        raise ValueError("Failed reading length encoded integer")


#
# For debugging
#
def _digest_buffer(buf):
    """Debug function for showing buffers"""
    if not isinstance(buf, str):
        return ''.join(["\\x%02x" % c for c in buf])
    return ''.join(["\\x%02x" % ord(c) for c in buf])


def print_buffer(abuffer, prefix=None, limit=30):
    """Debug function printing output of _digest_buffer()"""
    if prefix:
        if limit and limit > 0:
            digest = _digest_buffer(abuffer[0:limit])
        else:
            digest = _digest_buffer(abuffer)
        print(prefix + ': ' + digest)
    else:
        print(_digest_buffer(abuffer))


def _parse_os_release():
    """Parse the contents of /etc/os-release file.

    Returns:
        A dictionary containing release information.
    """
    distro = {}
    os_release_file = os.path.join("/etc", "os-release")
    if not os.path.exists(os_release_file):
        return distro
    with open(os_release_file) as file_obj:
        for line in file_obj:
            key_value = line.split("=")
            if len(key_value) != 2:
                continue
            key = key_value[0].lower()
            value = key_value[1].rstrip("\n").strip('"')
            distro[key] = value
    return distro


def _parse_lsb_release():
    """Parse the contents of /etc/lsb-release file.

    Returns:
        A dictionary containing release information.
    """
    distro = {}
    lsb_release_file = os.path.join("/etc", "lsb-release")
    if os.path.exists(lsb_release_file):
        with open(lsb_release_file) as file_obj:
            for line in file_obj:
                key_value = line.split("=")
                if len(key_value) != 2:
                    continue
                key = key_value[0].lower()
                value = key_value[1].rstrip("\n").strip('"')
                distro[key] = value
    return distro


def _parse_lsb_release_command():
    """Parse the output of the lsb_release command.

    Returns:
        A dictionary containing release information.
    """
    distro = {}
    with open(os.devnull, "w") as devnull:
        try:
            stdout = subprocess.check_output(
                ("lsb_release", "-a"), stderr=devnull)
        except OSError:
            return None
        lines = stdout.decode(sys.getfilesystemencoding()).splitlines()
        for line in lines:
            key_value = line.split(":")
            if len(key_value) != 2:
                continue
            key = key_value[0].replace(" ", "_").lower()
            value = key_value[1].strip("\t")
            distro[key] = value
    return distro


def linux_distribution():
    """Tries to determine the name of the Linux OS distribution name.

    First tries to get information from ``/etc/os-release`` file.
    If fails, tries to get the information of ``/etc/lsb-release`` file.
    And finally the information of ``lsb-release`` command.

    Returns:
        A tuple with (`name`, `version`, `codename`)
    """
    distro = _parse_lsb_release()
    if distro:
        return (distro.get("distrib_id", ""),
                distro.get("distrib_release", ""),
                distro.get("distrib_codename", ""))

    distro = _parse_lsb_release_command()
    if distro:
        return (distro.get("distributor_id", ""),
                distro.get("release", ""),
                distro.get("codename", ""))

    distro = _parse_os_release()
    if distro:
        return (distro.get("name", ""),
                distro.get("version_id", ""),
                distro.get("version_codename", ""))

    return ("", "", "")


def _get_unicode_read_direction(unicode_str):
    """Get the readiness direction of the unicode string.

    We assume that the direction is "L-to-R" if the first character does not
    indicate the direction is "R-to-L" or an "AL" (Arabic Letter).
    """
    if unicode_str and unicodedata.bidirectional(unicode_str[0]) in ("R", "AL"):
        return "R-to-L"
    return "L-to-R"


def _get_unicode_direction_rule(unicode_str):
    """
        1) The characters in section 5.8 MUST be prohibited.

        2) If a string contains any RandALCat character, the string MUST NOT
           contain any LCat character.

        3) If a string contains any RandALCat character, a RandALCat
           character MUST be the first character of the string, and a
           RandALCat character MUST be the last character of the string.
    """
    read_dir = _get_unicode_read_direction(unicode_str)

    # point 3)
    if read_dir == "R-to-L":
        if not (in_table_d1(unicode_str[0]) and in_table_d1(unicode_str[-1])):
            raise ValueError("Invalid unicode Bidirectional sequence, if the "
                             "first character is RandALCat, the final character"
                             "must be RandALCat too.")
        # characters from in_table_d2 are prohibited.
        return {"Bidirectional Characters requirement 2 [StringPrep, d2]":
                in_table_d2}

    # characters from in_table_d1 are prohibited.
    return {"Bidirectional Characters requirement 2 [StringPrep, d2]":
            in_table_d1}


def validate_normalized_unicode_string(normalized_str):
    """Check for Prohibited Output according to rfc4013 profile.

    This profile specifies the following characters as prohibited input:

       - Non-ASCII space characters [StringPrep, C.1.2]
       - ASCII control characters [StringPrep, C.2.1]
       - Non-ASCII control characters [StringPrep, C.2.2]
       - Private Use characters [StringPrep, C.3]
       - Non-character code points [StringPrep, C.4]
       - Surrogate code points [StringPrep, C.5]
       - Inappropriate for plain text characters [StringPrep, C.6]
       - Inappropriate for canonical representation characters [StringPrep, C.7]
       - Change display properties or deprecated characters [StringPrep, C.8]
       - Tagging characters [StringPrep, C.9]

    In addition of checking of Bidirectional Characters [StringPrep, Section 6]
    and the Unassigned Code Points [StringPrep, A.1].

    Returns:
        A tuple with ("probited character", "breaked_rule")
    """
    rules = {
        "Space characters that contains the ASCII code points": in_table_c11,
        "Space characters non-ASCII code points": in_table_c12,
        "Unassigned Code Points [StringPrep, A.1]": in_table_a1,
        "Non-ASCII space characters [StringPrep, C.1.2]": in_table_c12,
        "ASCII control characters [StringPrep, C.2.1]": in_table_c21_c22,
        "Private Use characters [StringPrep, C.3]": in_table_c3,
        "Non-character code points [StringPrep, C.4]": in_table_c4,
        "Surrogate code points [StringPrep, C.5]": in_table_c5,
        "Inappropriate for plain text characters [StringPrep, C.6]": in_table_c6,
        "Inappropriate for canonical representation characters [StringPrep, C.7]": in_table_c7,
        "Change display properties or deprecated characters [StringPrep, C.8]": in_table_c8,
        "Tagging characters [StringPrep, C.9]": in_table_c9
    }

    try:
        rules.update(_get_unicode_direction_rule(normalized_str))
    except ValueError as err:
        return normalized_str, str(err)

    for char in normalized_str:
        for rule in rules:
            if rules[rule](char) and char != u' ':
                return char, rule

    return None


def normalize_unicode_string(a_string):
    """normalizes a unicode string according to rfc4013

    Normalization of a unicode string according to rfc4013: The SASLprep profile
    of the "stringprep" algorithm.

    Normalization Unicode equivalence is the specification by the Unicode
    character encoding standard that some sequences of code points represent
    essentially the same character.

    This method normalizes using the Normalization Form Compatibility
    Composition (NFKC), as described in rfc4013 2.2.

    Returns:
        Normalized unicode string according to rfc4013.
    """
    # Per rfc4013 2.1. Mapping
    # non-ASCII space characters [StringPrep, C.1.2] are mapped to ' ' (U+0020)
    # "commonly mapped to nothing" characters [StringPrep, B.1] are mapped to ''
    nstr_list = [
        u' ' if in_table_c12(char) else u'' if in_table_b1(char) else char
        for char in a_string]

    nstr = u''.join(nstr_list)

    # Per rfc4013 2.2. Use NFKC Normalization Form Compatibility Composition
    # Characters are decomposed by compatibility, then recomposed by canonical
    # equivalence.
    nstr = unicodedata.normalize('NFKC', nstr)
    if not nstr:
        # Normilization results in empty string.
        return u''

    return nstr


def make_abc(base_class):
    """Decorator used to create a abstract base class.

    We use this decorator to create abstract base classes instead of
    using the abc-module. The decorator makes it possible to do the
    same in both Python v2 and v3 code.
    """
    def wrapper(class_):
        """Wrapper"""
        attrs = class_.__dict__.copy()
        for attr in '__dict__', '__weakref__':
            attrs.pop(attr, None)  # ignore missing attributes

        bases = class_.__bases__
        bases = (class_,) + bases
        return base_class(class_.__name__, bases, attrs)
    return wrapper


def init_bytearray(payload=b'', encoding='utf-8'):
    """Initialize a bytearray from the payload."""
    if isinstance(payload, bytearray):
        return payload
    if isinstance(payload, int):
        return bytearray(payload)
    if not isinstance(payload, bytes):
        try:
            return bytearray(payload.encode(encoding=encoding))
        except AttributeError:
            raise ValueError("payload must be a str or bytes")

    return bytearray(payload)


@lru_cache()
def get_platform():
    """Return a dict with the platform arch and OS version."""
    plat = {"arch": None, "version": None}
    if os.name == "nt":
        if "64" in platform.architecture()[0]:
            plat["arch"] = "x86_64"
        elif "32" in platform.architecture()[0]:
            plat["arch"] = "i386"
        else:
            plat["arch"] = platform.architecture()
        plat["version"] = "Windows-{}".format(platform.win32_ver()[1])
    else:
        plat["arch"] = platform.machine()
        if platform.system() == "Darwin":
            plat["version"] = "{}-{}".format("macOS", platform.mac_ver()[0])
        else:
            plat["version"] = "-".join(linux_distribution()[0:2])

    return plat
