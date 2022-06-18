import json
import logging

import six
from jwkest import b64d, as_unicode
from jwkest import b64e
from jwkest import BadSyntax

__author__ = 'roland'

logger = logging.getLogger(__name__)


def split_token(token):
    if not token.count(b"."):
        raise BadSyntax(token,
                        "expected token to contain at least one dot")
    return tuple(token.split(b"."))


def b2s_conv(item):
    if isinstance(item, bytes):
        return item.decode("utf-8")
    elif item is None or isinstance(item, (six.string_types, int, bool)):
        return item
    elif isinstance(item, list):
        return [b2s_conv(i) for i in item]
    elif isinstance(item, dict):
        return dict([(k, b2s_conv(v)) for k, v in item.items()])

    raise ValueError("Can't convert {}.".format(repr(item)))


def b64encode_item(item):
    if isinstance(item, bytes):
        return b64e(item)
    elif isinstance(item, str):
        return b64e(item.encode("utf-8"))
    elif isinstance(item, int):
        return b64e(item)
    else:
        return b64e(json.dumps(b2s_conv(item),
                               separators=(",", ":")).encode("utf-8"))


class JWT(object):
    def __init__(self, **headers):
        if not headers.get("alg"):
            headers["alg"] = None
        self.headers = headers
        self.b64part = [b64encode_item(headers)]
        self.part = [b64d(self.b64part[0])]

    def unpack(self, token):
        """
        Unpacks a JWT into its parts and base64 decodes the parts
        individually

        :param token: The JWT
        """
        if isinstance(token, six.string_types):
            try:
                token = token.encode("utf-8")
            except UnicodeDecodeError:
                pass

        part = split_token(token)
        self.b64part = part
        self.part = [b64d(p) for p in part]
        self.headers = json.loads(self.part[0].decode())
        return self

    def pack(self, parts=None, headers=None):
        """
        Packs components into a JWT

        :param returns: The string representation of a JWT
        """
        if not headers:
            if self.headers:
                headers = self.headers
            else:
                headers = {'alg': 'none'}

        logging.debug('JWT header: {}'.format(headers))

        if not parts:
            return ".".join([a.decode() for a in self.b64part])

        self.part = [headers] + parts
        _all = self.b64part = [b64encode_item(headers)]
        _all.extend([b64encode_item(p) for p in parts])

        return ".".join([a.decode() for a in _all])

    def payload(self):
        _msg = as_unicode(self.part[1])

        # If not JSON web token assume JSON
        if "cty" in self.headers and self.headers["cty"].lower() != "jwt":
            pass
        else:
            try:
                _msg = json.loads(_msg)
            except ValueError:
                pass

        return _msg
