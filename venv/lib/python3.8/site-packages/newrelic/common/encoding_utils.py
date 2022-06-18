# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module implements assorted utility functions for encoding/decoding
of data.

"""

import base64
import gzip
import hashlib
import io
import itertools
import json
import random
import re
import types
import zlib
from collections import OrderedDict

from newrelic.packages import six

HEXDIGLC_RE = re.compile('^[0-9a-f]+$')
DELIMITER_FORMAT_RE = re.compile('[ \t]*,[ \t]*')
PARENT_TYPE = {
    '0': 'App',
    '1': 'Browser',
    '2': 'Mobile',
}
BASE64_DECODE_STR = getattr(base64, 'decodestring', None)


# Functions for encoding/decoding JSON. These wrappers are used in order
# to hide the differences between Python 2 and Python 3 implementations
# of the json module functions as well as instigate some better defaults
# for the handling on unknown objects. All but the first argument must
# be supplied as key word arguments to allow the wrappers to supply
# defaults.

def json_encode(obj, **kwargs):
    _kwargs = {}

    # This wrapper function needs to deal with a few issues.
    #
    # The first is that when a byte string is provided, we need to
    # ensure that it is interpreted as being Latin-1. This is necessary
    # as by default JSON will treat it as UTF-8, which means if an
    # invalid UTF-8 byte string is provided, a failure will occur when
    # encoding the value.
    #
    # The json.dumps() function in Python 2 had an encoding argument
    # which needs to be used to dictate what encoding a byte string
    # should be interpreted as being. We need to supply this and set it
    # to Latin-1 to avoid the failures if the byte string is not valid
    # UTF-8.
    #
    # For Python 3, it will simply fail if provided any byte string. To
    # be compatible with Python 2, we still want to accept them, but as
    # before interpret it as being Latin-1. For Python 3 we can only do
    # this by overriding the fallback encoder used when a type is
    # encountered that the JSON encoder doesn't know what to do with.
    #
    # The second issue we want to deal with is allowing generators or
    # iterables to be supplied and for them to be automatically expanded
    # and treated as lists. This also entails overriding the fallback
    # encoder.
    #
    # The third is eliminate white space after separators to trim the
    # size of the data being sent.

    if type(b'') is type(''):  # NOQA
        _kwargs['encoding'] = 'latin-1'

    def _encode(o):
        if isinstance(o, bytes):
            return o.decode('latin-1')
        elif isinstance(o, types.GeneratorType):
            return list(o)
        elif hasattr(o, '__iter__'):
            return list(iter(o))
        raise TypeError(repr(o) + ' is not JSON serializable')

    _kwargs['default'] = _encode

    _kwargs['separators'] = (',', ':')

    # We still allow supplied arguments to override internal defaults if
    # necessary, but the caller must be sure they aren't dependent on
    # the new defaults. In particular, if they supply 'default' it will
    # override our default fallback encoder.

    _kwargs.update(kwargs)

    return json.dumps(obj, **_kwargs)


def json_decode(s, **kwargs):
    # Nothing special to do here at this point but use a wrapper to be
    # consistent with encoding and allow for changes later.

    return json.loads(s, **kwargs)

# Functions for obfuscating/deobfuscating text string based on an XOR
# cipher.


def xor_cipher_genkey(key, length=None):
    """Generates a byte array for use in XOR cipher encrypt and decrypt
    routines. In Python 2 either a byte string or Unicode string can be
    provided for the key. In Python 3, it must be a Unicode string. In
    either case, characters in the string must be within the ASCII
    character range.

    """

    return bytearray(key[:length], encoding='ascii')


def xor_cipher_encrypt(text, key):
    """Encrypts the text using an XOR cipher where the key is provided
    as a byte array. The key cannot be an empty byte array. Where the
    key is shorter than the text to be encrypted, the same key will
    continually be reapplied in succession. In Python 2 either a byte
    string or Unicode string can be provided for the text input. In
    Python 3 only a Unicode string can be provided for the text input.
    In either case where a Unicode string is being provided, characters
    must have an ordinal value less than 256. The result will be a byte
    array.

    """

    return bytearray([ord(c) ^ key[i % len(key)] for i, c in enumerate(text)])


def xor_cipher_decrypt(text, key):
    """Decrypts the text using an XOR cipher where the key is provided
    as a byte array. The key cannot be an empty byte array. Where the
    key is shorter than the text to be encrypted, the same key will
    continually be reapplied in succession. The input text must be in
    the form of a byte array. The result will in turn also be a byte
    array.

    """

    return bytearray([c ^ key[i % len(key)] for i, c in enumerate(text)])


def xor_cipher_encrypt_base64(text, key):
    """Encrypts the UTF-8 encoded representation of the text using an
    XOR cipher using the key. The key can be a byte array generated
    using xor_cipher_genkey() or an appropriate string of the correct
    type and composition, in which case if will be converted to a byte
    array using xor_cipher_genkey(). The key cannot be an empty byte
    array or string. Where the key is shorter than the text to be
    encrypted, the same key will continually be reapplied in succession.
    In Python 2 either a byte string or Unicode string can be provided
    for the text input. In the case of a byte string, it will be
    interpreted as having Latin-1 encoding. In Python 3 only a Unicode
    string can be provided for the text input. Having being encrypted,
    the result will then be base64 encoded with the result being a
    Unicode string.

    """

    if not isinstance(key, bytearray):
        key = xor_cipher_genkey(key)

    # The input to xor_cipher_encrypt() must be a Unicode string, but
    # where each character has an ordinal value less than 256. This
    # means that where the text to be encrypted is a Unicode string, we
    # need to encode it to UTF-8 and then back to Unicode as Latin-1
    # which will preserve the encoded byte string as is. Where the text
    # to be encrypted is a byte string, we will not know what encoding
    # it may have. What we therefore must do is first convert it to
    # Unicode as Latin-1 before doing the UTF-8/Latin-1 conversion. This
    # needs to be done as when decrypting we assume that the input will
    # always be UTF-8. If we do not do this extra conversion for a byte
    # string, we could later end up trying to decode a byte string which
    # isn't UTF-8 and so fail with a Unicode decoding error.

    if isinstance(text, bytes):
        text = text.decode('latin-1')
    text = text.encode('utf-8').decode('latin-1')

    result = base64.b64encode(bytes(xor_cipher_encrypt(text, key)))

    # The result from base64 encoding will be a byte string but since
    # dealing with byte strings in Python 2 and Python 3 is quite
    # different, it is safer to return a Unicode string for both. We can
    # use ASCII when decoding the byte string as base64 encoding only
    # produces characters within that codeset.

    if six.PY3:
        return result.decode('ascii')

    return result


def xor_cipher_decrypt_base64(text, key):
    """Decrypts the text using an XOR cipher where the key is provided
    as a byte array. The key cannot be an empty byte array. Where the
    key is shorter than the text to be encrypted, the same key will
    continually be reapplied in succession. The input text must be in
    the form of a base64 encoded byte string with a UTF-8 encoding. The
    base64 string itself can be either a byte string or Unicode string.
    The final result of decrypting the input will be a Unicode string.

    """

    if not isinstance(key, bytearray):
        key = xor_cipher_genkey(key)

    result = xor_cipher_decrypt(bytearray(base64.b64decode(text)), key)

    return bytes(result).decode('utf-8')


obfuscate = xor_cipher_encrypt_base64
deobfuscate = xor_cipher_decrypt_base64


def unpack_field(field):
    """Decodes data that was compressed before being sent to the collector.
    For example, 'pack_data' in a transaction trace, or 'params_data' in a
    slow sql trace is run through zlib.compress, base64.standard_b64encode
    and json_encode before being sent. This function reverses the compression
    and encoding, and returns a Python object.

    """

    if not isinstance(field, bytes):
        field = field.encode('UTF-8')

    data = getattr(base64, 'decodebytes', BASE64_DECODE_STR)(field)
    data = zlib.decompress(data)

    if isinstance(data, bytes):
        data = data.decode('Latin-1')

    data = json_decode(data)
    return data


def generate_path_hash(name, seed):
    """Algorithm for generating the path hash:
    * Rotate Left the seed value and truncate to 32-bits.
    * Compute the md5 digest of the name, take the last 4 bytes (32-bits).
    * XOR the 4 bytes of digest with the seed and return the result.

    """

    rotated = ((seed << 1) | (seed >> 31)) & 0xffffffff

    if not isinstance(name, bytes):
        name = name.encode('UTF-8')

    path_hash = (rotated ^ int(hashlib.md5(name).hexdigest()[-8:], base=16))
    return '%08x' % path_hash


def base64_encode(text):
    """Base 64 encodes the UTF-8 encoded representation of the text. In Python
    2 either a byte string or Unicode string can be provided for the text
    input. In the case of a byte string, it will be interpreted as having
    Latin-1 encoding. In Python 3 only a Unicode string can be provided for the
    text input. The result will then a base64 encoded Unicode string.

    """

    # The input text must be a Unicode string, but where each character has an
    # ordinal value less than 256. This means that where the text to be
    # encrypted is a Unicode string, we need to encode it to UTF-8 and then
    # back to Unicode as Latin-1 which will preserve the encoded byte string as
    # is. Where the text to be b64 encoded is a byte string, we will not know
    # what encoding it may have. What we therefore must do is first convert it
    # to Unicode as Latin-1 before doing the UTF-8/Latin-1 conversion. This
    # needs to be done as when deserializing we assume that the input will
    # always be UTF-8. If we do not do this extra conversion for a byte string,
    # we could later end up trying to decode a byte string which isn't UTF-8
    # and so fail with a Unicode decoding error.

    if isinstance(text, bytes):
        text = text.decode('latin-1')
    text = text.encode('utf-8').decode('latin-1')

    # Re-encode as utf-8 when passing to b64 encoder
    result = base64.b64encode(text.encode('utf-8'))

    # The result from base64 encoding will be a byte string but since
    # dealing with byte strings in Python 2 and Python 3 is quite
    # different, it is safer to return a Unicode string for both. We can
    # use ASCII when decoding the byte string as base64 encoding only
    # produces characters within that codeset.

    if six.PY3:
        return result.decode('ascii')

    return result


def base64_decode(text):
    """Base 64 decodes text into a UTF-8 encoded string. This function assumes
    the decoded text is UTF-8 encoded.

    """
    return base64.b64decode(text).decode('utf-8')


def gzip_compress(text):
    """GZip compresses input text. This function takes in a string
    or UTF-8 input and returns compressed bytes.

    """
    compressed_data = io.BytesIO()

    if six.PY3 and isinstance(text, str):
        text = text.encode('utf-8')

    with gzip.GzipFile(fileobj=compressed_data, mode='wb') as f:
        f.write(text)

    return compressed_data.getvalue()


def gzip_decompress(payload):
    """GZip decompresses input bytes. This function takes in a string
    or UTF-8 input and returns the decompressed string.

    """
    data_bytes = io.BytesIO(payload)
    decoded_data = gzip.GzipFile(fileobj=data_bytes).read()
    return decoded_data.decode('utf-8')


def serverless_payload_encode(payload):
    """This method assumes valid JSON input. The input will be json encoded,
    gzip compressed, and base64 encoded.

    """
    json_encode_data = json_encode(payload)
    compressed_data = gzip_compress(json_encode_data)
    encoded_data = base64.b64encode(compressed_data)

    return encoded_data


def ensure_str(s):
    if not isinstance(s, six.string_types):
        try:
            s = s.decode('utf-8')
        except Exception:
            return
    return s


def serverless_payload_decode(text):
    """This method takes in a string or UTF-8 input. The input will be
    base64 decoded, gzip decompressed, and json decoded. Returns a
    Python object.

    """
    if hasattr(text, 'decode'):
        text = text.decode('utf-8')

    decoded_bytes = base64.b64decode(text)
    uncompressed_data = gzip_decompress(decoded_bytes)

    data = json_decode(uncompressed_data)
    return data


def decode_newrelic_header(encoded_header, encoding_key):
    decoded_header = None
    if encoded_header:
        try:
            decoded_header = json_decode(deobfuscate(
                    encoded_header, encoding_key))
        except Exception:
            pass

    return decoded_header


def convert_to_cat_metadata_value(nr_headers):
    if not nr_headers:
        return None

    payload = json_encode(nr_headers)
    cat_linking_value = base64_encode(payload)
    return cat_linking_value


class DistributedTracePayload(dict):

    version = (0, 1)

    def text(self):
        return json_encode(self)

    @classmethod
    def from_text(cls, value):
        d = json_decode(value)
        return cls(d)

    def http_safe(self):
        return base64_encode(self.text())

    @classmethod
    def from_http_safe(cls, value):
        text = base64_decode(value)
        return cls.from_text(text)

    @classmethod
    def decode(cls, payload):
        if isinstance(payload, dict):
            return cls(payload)

        decoders = (cls.from_http_safe, cls.from_text)
        for decoder in decoders:
            try:
                payload = decoder(payload)
            except:
                pass
            else:
                return payload


class W3CTraceParent(dict):

    def text(self):
        if 'id' in self:
            guid = self['id']
        else:
            guid = '{:016x}'.format(random.getrandbits(64))

        return '00-{}-{}-{:02x}'.format(
            self['tr'].lower().zfill(32),
            guid,
            int(self.get('sa', 0)),
        )

    @classmethod
    def decode(cls, payload):
        # Only traceparent with at least 55 chars should be parsed
        if len(payload) < 55:
            return None

        fields = payload.split('-', 4)

        # Expect that there are at least 4 fields
        if len(fields) < 4:
            return None

        version = fields[0]

        # version must be a valid 2-char hex digit
        if len(version) != 2 or not HEXDIGLC_RE.match(version):
            return None

        # Version 255 is invalid
        if version == 'ff':
            return None

        # Expect exactly 4 fields if version 00
        if version == '00' and len(fields) != 4:
            return None

        # Check field lengths and values
        for field, expected_length in zip(fields[1:4], (32, 16, 2)):
            if len(field) != expected_length or not HEXDIGLC_RE.match(field):
                return None

        # trace_id or parent_id of all 0's are invalid
        trace_id, parent_id = fields[1:3]
        if parent_id == '0' * 16 or trace_id == '0' * 32:
            return None

        return cls(tr=trace_id, id=parent_id)


class W3CTraceState(OrderedDict):

    def text(self, limit=32):
        return ','.join(
                    '{}={}'.format(k, v)
                    for k, v in itertools.islice(self.items(), limit))

    @classmethod
    def decode(cls, tracestate):
        entries = DELIMITER_FORMAT_RE.split(tracestate.rstrip())

        vendors = cls()
        for entry in entries:
            vendor_value = entry.split('=', 2)
            if (len(vendor_value) != 2 or
                    any(len(v) > 256 for v in vendor_value)):
                continue

            vendor, value = vendor_value
            vendors[vendor] = value

        return vendors


class NrTraceState(dict):
    FIELDS = ('ty', 'ac', 'ap', 'id', 'tx', 'sa', 'pr')

    def text(self):
        pr = self.get('pr', '')
        if pr:
            pr = ('%.6f' % pr).rstrip('0').rstrip('.')

        payload = '-'.join((
            '0-0',
            self['ac'],
            self['ap'],
            self.get('id', ''),
            self.get('tx', ''),
            '1' if self.get('sa') else '0',
            pr,
            str(self['ti']),
        ))
        return '{}@nr={}'.format(
            self.get('tk', self['ac']),
            payload,
        )

    @classmethod
    def decode(cls, payload, tk):
        fields = payload.split('-', 9)
        if len(fields) >= 9 and all(fields[:4]) and fields[8]:
            data = cls(tk=tk)

            try:
                data['ti'] = int(fields[8])
            except:
                return

            for name, value in zip(cls.FIELDS, fields[1:]):
                if value:
                    data[name] = value

            if data['ty'] in PARENT_TYPE:
                data['ty'] = PARENT_TYPE[data['ty']]
            else:
                return

            if 'sa' in data:
                if data['sa'] == '1':
                    data['sa'] = True
                elif data['sa'] == '0':
                    data['sa'] = False
                else:
                    data['sa'] = None

            if 'pr' in data:
                try:
                    data['pr'] = float(fields[7])
                except:
                    data['pr'] = None

            return data
