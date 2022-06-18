"""JSON Web Token"""
import base64
import logging
import re
import struct
import six

try:
    from builtins import zip
    from builtins import hex
    from builtins import str
except ImportError:
    pass

from binascii import unhexlify

__version__ = "1.4.2"

logger = logging.getLogger(__name__)

JWT_TYPES = (u"JWT", u"application/jws", u"JWS", u"JWE")

JWT_CLAIMS = {"iss": str, "sub": str, "aud": str, "exp": int, "nbf": int,
              "iat": int, "jti": str, "typ": str}

JWT_HEADERS = ["typ", "cty"]


class JWKESTException(Exception):
    pass


# XXX Should this be a subclass of ValueError?
class Invalid(JWKESTException):
    """The JWT is invalid."""


class WrongNumberOfParts(Invalid):
    pass


class BadSyntax(Invalid):
    """The JWT could not be parsed because the syntax is invalid."""

    def __init__(self, value, msg):
        Invalid.__init__(self)
        self.value = value
        self.msg = msg

    def __str__(self):
        return "%s: %r" % (self.msg, self.value)


class BadSignature(Invalid):
    """The signature of the JWT is invalid."""


class Expired(Invalid):
    """The JWT claim has expired or is not yet valid."""


class UnknownAlgorithm(Invalid):
    """The JWT uses an unknown signing algorithm"""


class BadType(Invalid):
    """The JWT has an unexpected "typ" value."""


class MissingKey(JWKESTException):
    """ No usable key """


class UnknownKeytype(Invalid):
    """An unknown key type"""


# ---------------------------------------------------------------------------
# Helper functions


def intarr2bin(arr):
    return unhexlify(''.join(["%02x" % byte for byte in arr]))


def long2hexseq(l):
    try:
        return unhexlify(hex(l)[2:])
    except TypeError:
        return unhexlify(hex(l)[2:-1])


def intarr2long(arr):
    return int(''.join(["%02x" % byte for byte in arr]), 16)


def long2intarr(long_int):
    _bytes = []
    while long_int:
        long_int, r = divmod(long_int, 256)
        _bytes.insert(0, r)
    return _bytes


def long_to_base64(n, mlen=0):
    bys = long2intarr(n)
    if mlen:
        _len = mlen - len(bys)
        if _len:
            bys = [0] * _len + bys
    data = struct.pack('%sB' % len(bys), *bys)
    if not len(data):
        data = '\x00'
    s = base64.urlsafe_b64encode(data).rstrip(b'=')
    return s.decode("ascii")


def base64_to_long(data):
    if isinstance(data, six.text_type):
        data = data.encode("ascii")

    # urlsafe_b64decode will happily convert b64encoded data
    _d = base64.urlsafe_b64decode(bytes(data) + b'==')
    return intarr2long(struct.unpack('%sB' % len(_d), _d))


def base64url_to_long(data):
    """
    Stricter then base64_to_long since it really checks that it's
    base64url encoded

    :param data: The base64 string
    :return:
    """
    _d = base64.urlsafe_b64decode(bytes(data) + b'==')
    # verify that it's base64url encoded and not just base64
    # that is no '+' and '/' characters and not trailing "="s.
    if [e for e in [b'+', b'/', b'='] if e in data]:
        raise ValueError("Not base64url encoded")
    return intarr2long(struct.unpack('%sB' % len(_d), _d))


# =============================================================================

def b64e(b):
    """Base64 encode some bytes.

    Uses the url-safe - and _ characters, and doesn't pad with = characters."""
    return base64.urlsafe_b64encode(b).rstrip(b"=")


_b64_re = re.compile(b"^[A-Za-z0-9_-]*$")


def add_padding(b):
    # add padding chars
    m = len(b) % 4
    if m == 1:
        # NOTE: for some reason b64decode raises *TypeError* if the
        # padding is incorrect.
        raise BadSyntax(b, "incorrect padding")
    elif m == 2:
        b += b"=="
    elif m == 3:
        b += b"="
    return b


def b64d(b):
    """Decode some base64-encoded bytes.

    Raises BadSyntax if the string contains invalid characters or padding.

    :param b: bytes
    """

    cb = b.rstrip(b"=")  # shouldn't but there you are

    # Python's base64 functions ignore invalid characters, so we need to
    # check for them explicitly.
    if not _b64_re.match(cb):
        raise BadSyntax(cb, "base64-encoded data contains illegal characters")

    if cb == b:
        b = add_padding(b)

    return base64.urlsafe_b64decode(b)


def b64e_enc_dec(str, encode="utf-8", decode="ascii"):
    return b64e(str.encode(encode)).decode(decode)


def b64d_enc_dec(str, encode="ascii", decode="utf-8"):
    return b64d(str.encode(encode)).decode(decode)


# 'Stolen' from Werkzeug
def safe_str_cmp(a, b):
    """Compare two strings in constant time."""
    if len(a) != len(b):
        return False
    r = 0
    for c, d in zip(a, b):
        r |= ord(c) ^ ord(d)
    return r == 0


def constant_time_compare(a, b):
    """Compare two strings in constant time."""
    if len(a) != len(b):
        return False
    r = 0
    for c, d in zip(a, b):
        r |= c ^ d
    return r == 0


def as_bytes(s):
    """
    Convert an unicode string to bytes.
    :param s: Unicode / bytes string
    :return: bytes string
    """
    try:
        s = s.encode()
    except (AttributeError, UnicodeDecodeError):
        pass
    return s


def as_unicode(b):
    """
    Convert a byte string to a unicode string
    :param b: byte string
    :return: unicode string
    """
    try:
        b = b.decode()
    except (AttributeError, UnicodeDecodeError):
        pass
    return b
