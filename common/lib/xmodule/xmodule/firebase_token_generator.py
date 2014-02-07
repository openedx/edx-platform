'''
    Firebase - library to generate a token
    License: https://github.com/firebase/firebase-token-generator-python/blob/master/LICENSE
    Tweaked and Edited by @danielcebrianr and @lduarte1991

    This library will take either objects or strings and use python's built-in encoding
    system as specified by RFC 3548. Thanks to the firebase team for their open-source
    library. This was made specifically for speaking with the annotation_storage_url and
    can be used and expanded, but not modified by anyone else needing such a process.
'''
from base64 import urlsafe_b64encode
import hashlib
import hmac
try:
    import json
except ImportError:
    import simplejson as json

__all__ = ['create_token']

TOKEN_SEP = '.'


def create_token(secret, data):
    '''
    Simply takes in the secret key and the data and
    passes it to the local function _encode_token
    '''
    return _encode_token(secret, data)


def _encode(bytes_info):
    '''
    Takes a json object, string, or binary and
    uses python's urlsafe_b64encode to encode data
    and make it safe pass along in a url.
    To make sure it does not conflict with variables
    we make sure equal signs are removed.
    More info: docs.python.org/2/library/base64.html
    '''
    encoded = urlsafe_b64encode(bytes_info)
    return encoded.decode('utf-8').replace('=', '')


def _encode_json(obj):
    '''
    Before a python dict object can be properly encoded,
    it must be transformed into a jason object and then
    transformed into bytes to be encoded using the function
    defined above.
    '''
    return _encode(bytearray(json.dumps(obj), 'utf-8'))


def _sign(secret, to_sign):
    '''
    This function creates a sign that goes at the end of the
    message that is specific to the secret and not the actual
    content of the encoded body.
    More info on hashing: http://docs.python.org/2/library/hmac.html
    The function creates a hashed values of the secret and to_sign
    and returns the digested values based the secure hash
    algorithm, 256
    '''
    def portable_bytes(string):
        '''
        Simply transforms a string into a bytes object,
        which is a series of immutable integers 0<=x<=256.
        Always try to encode as utf-8, unless it is not
        compliant.
        '''
        try:
            return bytes(string, 'utf-8')
        except TypeError:
            return bytes(string)
    return _encode(hmac.new(portable_bytes(secret), portable_bytes(to_sign), hashlib.sha256).digest())  # pylint: disable=E1101


def _encode_token(secret, claims):
    '''
    This is the main function that takes the secret token and
    the data to be transmitted. There is a header created for decoding
    purposes. Token_SEP means that a period/full stop separates the
    header, data object/message, and signatures.
    '''
    encoded_header = _encode_json({'typ': 'JWT', 'alg': 'HS256'})
    encoded_claims = _encode_json(claims)
    secure_bits = '%s%s%s' % (encoded_header, TOKEN_SEP, encoded_claims)
    sig = _sign(secret, secure_bits)
    return '%s%s%s' % (secure_bits, TOKEN_SEP, sig)
