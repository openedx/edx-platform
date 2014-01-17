''' library to generate a token '''
from base64 import urlsafe_b64encode
import hashlib
import hmac
import sys
try:
    import json
except ImportError:
    import simplejson as json

__all__ = ['create_token']

TOKEN_SEP = '.'


def create_token(secret, data):
    ''' Function to create the token '''
    claims = data
    return _encode_token(secret, claims)


if sys.version_info < (2, 7):
    def _encode(bytes_data):
        ''' enconde function '''
        encoded = urlsafe_b64encode(bytes(bytes_data))
        return encoded.decode('utf-8').replace('=', '')
else:
    def _encode(bytes):
        ''' enconde function '''
        encoded = urlsafe_b64encode(bytes)
        return encoded.decode('utf-8').replace('=', '')


def _encode_json(obj):
    ''' enconde json '''
    return _encode(bytearray(json.dumps(obj), 'utf-8'))


def _sign(secret, to_sign):
    ''' sign function '''
    def portable_bytes(string):
        ''' byte function '''
        try:
            return bytes(string, 'utf-8')
        except TypeError:
            return bytes(string)
    return _encode(hmac.new(portable_bytes(secret), portable_bytes(to_sign), hashlib.sha256).digest())


def _encode_token(secret, claims):
    ''' enconde function '''
    encoded_header = _encode_json({'typ': 'JWT', 'alg': 'HS256'})
    encoded_claims = _encode_json(claims)
    secure_bits = '%s%s%s' % (encoded_header, TOKEN_SEP, encoded_claims)
    sig = _sign(secret, secure_bits)
    return '%s%s%s' % (secure_bits, TOKEN_SEP, sig)
