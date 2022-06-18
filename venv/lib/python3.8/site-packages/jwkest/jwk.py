import base64
import binascii
import hashlib
import re
import logging
import json
import sys
import six

from binascii import a2b_base64

from Cryptodome.PublicKey import RSA
from Cryptodome.PublicKey.RSA import importKey
from Cryptodome.PublicKey.RSA import RsaKey
from Cryptodome.Util.asn1 import DerSequence

from requests import request

from jwkest import as_bytes
from jwkest import as_unicode
from jwkest import base64_to_long
from jwkest import base64url_to_long
from jwkest import long_to_base64
from jwkest import JWKESTException
from jwkest import b64d
from jwkest import b64e
from jwkest import UnknownAlgorithm
from jwkest.ecc import NISTEllipticCurve
from jwkest.jwt import b2s_conv

if sys.version > '3':
    long = int
else:
    from __builtin__ import long

__author__ = 'rohe0002'

logger = logging.getLogger(__name__)

PREFIX = "-----BEGIN CERTIFICATE-----"
POSTFIX = "-----END CERTIFICATE-----"


class JWKException(JWKESTException):
    pass


class FormatError(JWKException):
    pass


class SerializationNotPossible(JWKException):
    pass


class DeSerializationNotPossible(JWKException):
    pass


class HeaderError(JWKESTException):
    pass


def dicthash(d):
    return hash(repr(sorted(d.items())))


def intarr2str(arr):
    return "".join([chr(c) for c in arr])


def sha256_digest(msg):
    return hashlib.sha256(as_bytes(msg)).digest()


def sha384_digest(msg):
    return hashlib.sha384(as_bytes(msg)).digest()


def sha512_digest(msg):
    return hashlib.sha512(as_bytes(msg)).digest()


DIGEST_HASH = {
    'SHA-256': sha256_digest,
    'SHA-384': sha384_digest,
    'SHA-512': sha512_digest
}


# =============================================================================


def import_rsa_key_from_file(filename, passphrase=None):
    content = None
    with open(filename, 'r') as f:
        content = f.read()

    return RSA.importKey(content, passphrase=passphrase)


def import_rsa_key(key, passphrase=None):
    """
    Extract an RSA key from a PEM-encoded certificate
    :param key: RSA key encoded in standard form
    :param passphrase: Password to open the certificate (Optional)
    :return: RSA key instance
    """
    return importKey(key, passphrase=passphrase)


def der2rsa(der):
    # Extract subjectPublicKeyInfo field from X.509 certificate (see RFC3280)
    cert = DerSequence()
    cert.decode(der)
    tbs_certificate = DerSequence()
    tbs_certificate.decode(cert[0])
    subject_public_key_info = tbs_certificate[6]

    # Initialize RSA key
    return RSA.importKey(subject_public_key_info)


def pem_cert2rsa(pem_file):
    # Convert from PEM to DER
    pem = None
    with open(pem_file) as f:
        pem = f.read()

    _rsa = RSA.importKey(pem)
    lines = pem.replace(" ", '').split()
    return der2rsa(a2b_base64(''.join(lines[1:-1])))


def der_cert2rsa(der):
    """
    Extract an RSA key from a DER certificate

    @param der: DER-encoded certificate
    @return: RSA instance
    """
    pem = re.sub(r'[^A-Za-z0-9+/]', '', der)
    return der2rsa(base64.b64decode(pem))


def load_x509_cert(url, spec2key, *args, **kwargs):
    """
    Get and transform a X509 cert into a key

    :param url: Where the X509 cert can be found
    :param spec2key: A dictionary over keys already seen
    :return: List of 2-tuples (keytype, key)
    """
    try:
        r = request("GET", url, allow_redirects=True, **kwargs)
        if r.status_code == 200:
            cert = str(r.text)
            try:
                _key = spec2key[cert]
            except KeyError:
                _key = import_rsa_key(cert)
                spec2key[cert] = _key
            return [("rsa", _key)]
        else:
            raise Exception("HTTP Get error: %s" % r.status_code)
    except Exception as err:  # not a RSA key
        logger.warning("Can't load key: %s" % err)
        return []


def rsa_load(filename):
    """Read a PEM-encoded RSA key pair from a file."""
    pem = None
    with open(filename, 'r') as f:
        pem = f.read()
    return import_rsa_key(pem)


def rsa_eq(key1, key2):
    # Check if two RSA keys are in fact the same
    if key1.n == key2.n and key1.e == key2.e:
        return True
    else:
        return False


def key_eq(key1, key2):
    if type(key1) == type(key2):
        if isinstance(key1, str):
            return key1 == key2
        elif isinstance(key1, RSA):
            return rsa_eq(key1, key2)

    return False


def x509_rsa_load(txt):
    """ So I get the same output format as loads produces
    :param txt:
    :return:
    """
    return [("rsa", import_rsa_key(txt))]


def key_from_jwk_dict(jwk_dict, private=True):
    """Load JWK from dictionary"""
    if jwk_dict['kty'] == 'EC':
        if private:
            return ECKey(kid=jwk_dict['kid'],
                         crv=jwk_dict['crv'],
                         x=jwk_dict['x'],
                         y=jwk_dict['y'],
                         d=jwk_dict['d'])
        else:
            return ECKey(kid=jwk_dict['kid'],
                         crv=jwk_dict['crv'],
                         x=jwk_dict['x'],
                         y=jwk_dict['y'])
    elif jwk_dict['kty'] == 'RSA':
        if private:
            return RSAKey(kid=jwk_dict['kid'],
                          n=jwk_dict['n'],
                          e=jwk_dict['e'],
                          d=jwk_dict['d'],
                          p=jwk_dict['p'],
                          q=jwk_dict['q'])
        else:
            return RSAKey(kid=jwk_dict['kid'],
                          n=jwk_dict['n'],
                          e=jwk_dict['e'])
    elif jwk_dict['kty'] == 'oct':
        return SYMKey(kid=jwk_dict['kid'],
                      k=jwk_dict['k'])
    else:
        raise UnknownAlgorithm


class Key(object):
    """
    Basic JSON Web key class
    """
    members = ["kty", "alg", "use", "kid", "x5c", "x5t", "x5u"]
    longs = []
    public_members = ["kty", "alg", "use", "kid", "x5c", "x5t", "x5u"]
    required = ['kty']

    def __init__(self, kty="", alg="", use="", kid="", key=None, x5c=None,
            x5t="", x5u="", **kwargs):
        self.key = key
        self.extra_args = kwargs

        # want kty, alg, use and kid to be strings
        if isinstance(kty, six.string_types):
            self.kty = kty
        else:
            self.kty = as_unicode(kty)

        if isinstance(alg, six.string_types):
            self.alg = alg
        else:
            self.alg = as_unicode(alg)

        if isinstance(use, six.string_types):
            self.use = use
        else:
            self.use = as_unicode(use)

        if isinstance(kid, six.string_types):
            self.kid = kid
        else:
            self.kid = as_unicode(kid)

        self.x5c = x5c or []
        self.x5t = x5t
        self.x5u = x5u
        self.inactive_since = 0
        self._hash = None

    def to_dict(self):
        """
        A wrapper for to_dict the makes sure that all the private information
        as well as extra arguments are included. This method should *not* be
        used for exporting information about the key.
        """
        res = self.serialize(private=True)
        res.update(self.extra_args)
        return res

    def common(self):
        res = {"kty": self.kty}
        if self.use:
            res["use"] = self.use
        if self.kid:
            res["kid"] = self.kid
        if self.alg:
            res["alg"] = self.alg
        return res

    def __str__(self):
        return str(self.to_dict())

    def deserialize(self):
        """
        Starting with information gathered from the on-the-wire representation
        initiate an appropriate key.
        """
        pass

    def serialize(self, private=False):
        """
        map key characteristics into attribute values that can be used
        to create an on-the-wire representation of the key
        """
        pass

    def get_key(self, **kwargs):
        return self.key

    def verify(self):
        """
        Verify that the information gathered from the on-the-wire
        representation is of the right types.
        This is supposed to be run before the info is deserialized.
        """
        for param in self.longs:
            item = getattr(self, param)
            if not item or isinstance(item, six.integer_types):
                continue

            if isinstance(item, bytes):
                item = item.decode('utf-8')
                setattr(self, param, item)

            try:
                _ = base64url_to_long(item)
            except Exception:
                return False
            else:
                if [e for e in ['+', '/', '='] if e in item]:
                    return False

        if self.kid:
            try:
                assert isinstance(self.kid, six.string_types)
            except AssertionError:
                raise HeaderError("kid of wrong value type")
        return True

    def __eq__(self, other):
        try:
            assert isinstance(other, Key)
            assert set(self.__dict__.keys()) == set(other.__dict__.keys())

            for key in self.public_members:
                assert getattr(other, key) == getattr(self, key)
        except AssertionError:
            return False
        else:
            return True

    def keys(self):
        return list(self.to_dict().keys())

    def thumbprint(self, hash_function, members=None):
        if members is None:
            members = self.required

        members.sort()
        ser = self.serialize()
        _se = []
        for elem in members:
            try:
                _val = ser[elem]
            except KeyError:  # should never happen with the required set
                pass
            else:
                _se.append('"{}":{}'.format(elem, json.dumps(_val)))
        _json = '{{{}}}'.format(','.join(_se))

        return DIGEST_HASH[hash_function](_json)

    def get_hash(self, hash_function=None):
        if not hash_function:
            hash_function = 'SHA-256'
        self._hash = int(binascii.hexlify(self.thumbprint(hash_function)), 16)
        return self._hash

    def add_kid(self):
        _tp = self.thumbprint('SHA-256')
        self.kid = b64e(_tp).decode('utf8')
        self._hash = int(binascii.hexlify(_tp), 16)

    def __hash__(self):
        if not self._hash:
            if self.kid:
                self.get_hash()
            else:
                self.add_kid()
        return self._hash


def deser(val):
    if isinstance(val, str):
        _val = val.encode("utf-8")
    else:
        _val = val

    return base64_to_long(_val)


class RSAKey(Key):
    """
    JSON Web key representation of a RSA key
    """
    members = Key.members
    members.extend(["n", "e", "d", "p", "q"])
    longs = ["n", "e", "d", "p", "q", "dp", "dq", "di", "qi"]
    public_members = Key.public_members
    public_members.extend(["n", "e"])
    required = ['kty', 'n', 'e']

    def __init__(self, kty="RSA", alg="", use="", kid="", key=None,
            x5c=None, x5t="", x5u="", n="", e="", d="", p="", q="",
            dp="", dq="", di="", qi="", **kwargs):
        Key.__init__(self, kty, alg, use, kid, key, x5c, x5t, x5u, **kwargs)
        self.n = n
        self.e = e
        self.d = d
        self.p = p
        self.q = q
        self.dp = dp
        self.dq = dq
        self.di = di
        self.qi = qi

        has_public_key_parts = len(self.n) > 0 and len(self.e)
        has_x509_cert_chain = len(self.x5c) > 0

        if not self.key and (has_public_key_parts or has_x509_cert_chain):
            self.deserialize()
        elif self.key and not (self.n and self.e):
            self._split()

    def deserialize(self):
        if self.n and self.e:
            try:
                for param in self.longs:
                    item = getattr(self, param)
                    if not item or isinstance(item, six.integer_types):
                        continue
                    else:
                        try:
                            val = long(deser(item))
                        except Exception:
                            raise
                        else:
                            setattr(self, param, val)

                lst = [self.n, self.e]
                if self.d:
                    lst.append(self.d)
                if self.p:
                    lst.append(self.p)
                    if self.q:
                        lst.append(self.q)
                    self.key = RSA.construct(tuple(lst))
                else:
                    self.key = RSA.construct(lst)
            except ValueError as err:
                raise DeSerializationNotPossible("%s" % err)
        elif self.x5c:
            der_cert = base64.b64decode(self.x5c[0].encode("ascii"))

            if self.x5t:  # verify the cert
                if not b64d(self.x5t.encode("ascii")) == hashlib.sha1(
                        der_cert).digest():
                    raise DeSerializationNotPossible(
                        "The thumbprint ('x5t') does not match the "
                        "certificate.")

            self.key = der2rsa(der_cert)
            self._split()
            if len(self.x5c) > 1:  # verify chain
                pass
        else:
            raise DeSerializationNotPossible()

    def serialize(self, private=False):
        if not self.key:
            raise SerializationNotPossible()

        res = self.common()

        public_longs = list(set(self.public_members) & set(self.longs))
        for param in public_longs:
            item = getattr(self, param)
            if item:
                res[param] = long_to_base64(item)

        if private:
            for param in self.longs:
                if not private and param in ["d", "p", "q", "dp", "dq", "di",
                                             "qi"]:
                    continue
                item = getattr(self, param)
                if item:
                    res[param] = long_to_base64(item)
        return res

    def _split(self):
        if not self.key:
            raise SerializationNotPossible()

        self.n = self.key.n
        self.e = self.key.e
        try:
            self.d = self.key.d
        except AttributeError:
            pass
        else:
            for param in ["p", "q"]:
                try:
                    val = getattr(self.key, param)
                except AttributeError:
                    pass
                else:
                    if val:
                        setattr(self, param, val)

    def load(self, filename):
        """
        Load the key from a file.

        :param filename: File name
        """
        self.key = rsa_load(filename)
        self._split()
        return self

    def load_key(self, key):
        """
        Use this RSA key

        :param key: An RSA key instance
        """
        self.key = key
        self._split()
        return self

    def encryption_key(self, **kwargs):
        """
        Make sure there is a key instance present that can be used for
        encrypting/signing.
        """
        if not self.key:
            self.deserialize()

        return self.key


class ECKey(Key):
    """
    JSON Web key representation of a Elliptic curve key
    """
    members = ["kty", "alg", "use", "kid", "crv", "x", "y", "d"]
    longs = ['x', 'y', 'd']
    public_members = ["kty", "alg", "use", "kid", "crv", "x", "y"]
    required = ['crv', 'key', 'x', 'y']

    def __init__(self, kty="EC", alg="", use="", kid="", key=None,
            crv="", x="", y="", d="", curve=None, **kwargs):
        Key.__init__(self, kty, alg, use, kid, key, **kwargs)
        self.crv = crv
        self.x = x
        self.y = y
        self.d = d
        self.curve = curve

        # Initiated guess as to what state the key is in
        # To be usable for encryption/signing/.. it has to be deserialized
        if self.crv and not self.curve:
            self.verify()
            self.deserialize()
        elif self.key:
            if not self.crv and not self.curve:
                self.load_key(key)

    def deserialize(self):
        """
        Starting with information gathered from the on-the-wire representation
        of an elliptic curve key initiate an Elliptic Curve.
        """
        if not (self.x and self.y and self.crv):
            DeSerializationNotPossible()

        try:
            if not isinstance(self.x, six.integer_types):
                self.x = deser(self.x)
            if not isinstance(self.y, six.integer_types):
                self.y = deser(self.y)
        except TypeError:
            raise DeSerializationNotPossible()
        except ValueError as err:
            raise DeSerializationNotPossible("%s" % err)

        self.curve = NISTEllipticCurve.by_name(self.crv)
        if self.d:
            try:
                if isinstance(self.d, six.string_types):
                    self.d = deser(self.d)
            except ValueError as err:
                raise DeSerializationNotPossible(str(err))

    def get_key(self, private=False, **kwargs):
        if private:
            if self.d:
                return self.d
            else:
                raise ValueError()
        else:
            if self.x and self.y:
                return self.x, self.y
            else:
                raise ValueError()

    def serialize(self, private=False):
        if not self.crv and not self.curve:
            raise SerializationNotPossible()

        res = self.common()
        blen = self.curve.bytes
        res.update({
            "crv": self.curve.name(),
            "x": long_to_base64(self.x, blen),
            "y": long_to_base64(self.y, blen)
        })

        if private and self.d:
            res["d"] = long_to_base64(self.d, blen)

        return res

    def load_key(self, key):
        self.curve = key
        self.d, (self.x, self.y) = key.key_pair()
        return self

    def decryption_key(self):
        return self.get_key(private=True)

    def encryption_key(self, private=False, **kwargs):
        # both for encryption and decryption.
        return self.get_key(private=private)


ALG2KEYLEN = {
    "A128KW": 16,
    "A192KW": 24,
    "A256KW": 32,
    "HS256": 32,
    "HS384": 48,
    "HS512": 64
}


class SYMKey(Key):
    members = ["kty", "alg", "use", "kid", "k"]
    public_members = members[:]
    required = ['k', 'kty']

    def __init__(self, kty="oct", alg="", use="", kid="", key=None,
            x5c=None, x5t="", x5u="", k="", mtrl="", **kwargs):
        Key.__init__(self, kty, alg, use, kid, as_bytes(key), x5c, x5t, x5u,
                     **kwargs)
        self.k = k
        if not self.key and self.k:
            if isinstance(self.k, str):
                self.k = self.k.encode("utf-8")
            self.key = b64d(bytes(self.k))

    def deserialize(self):
        if self.k:
            self.key = b64d(bytes(self.k))
        else:
            raise DeSerializationNotPossible()

    def serialize(self, private=True):
        res = self.common()
        res["k"] = as_unicode(b64e(bytes(self.key)))
        return res

    def encryption_key(self, alg, **kwargs):
        """
        Return an encryption key as per
        http://openid.net/specs/openid-connect-core-1_0.html#Encryption

        :param alg: encryption algorithm
        :param kwargs:
        :return: encryption key as byte string
        """
        if not self.key:
            self.deserialize()

        tsize = ALG2KEYLEN[alg]
        # _keylen = len(self.key)

        if tsize <= 32:
            # SHA256
            _enc_key = sha256_digest(self.key)[:tsize]
        elif tsize <= 48:
            # SHA384
            _enc_key = sha384_digest(self.key)[:tsize]
        elif tsize <= 64:
            # SHA512
            _enc_key = sha512_digest(self.key)[:tsize]
        else:
            raise JWKException("No support for symmetric keys > 512 bits")

        logger.debug('Symmetric encryption key: {}'.format(
            as_unicode(b64e(_enc_key))))

        return _enc_key


# -----------------------------------------------------------------------------


def keyitems2keyreps(keyitems):
    keys = []
    for key_type, _keys in list(keyitems.items()):
        if key_type.upper() == "RSA":
            keys.extend([RSAKey(key=k) for k in _keys])
        elif key_type.lower() == "oct":
            keys.extend([SYMKey(key=k) for k in _keys])
        elif key_type.upper() == "EC":
            keys.extend([ECKey(key=k) for k in _keys])
        else:
            keys.extend([Key(key=k) for k in _keys])
    return keys


def keyrep(kspec, enc="utf-8"):
    """
    Instantiate a Key given a set of key/word arguments

    :param kspec: Key specification, arguments to the Key initialization
    :param enc: The encoding of the strings. If it's JSON which is the default
     the encoding is utf-8.
    :return: Key instance
    """
    if enc:
        _kwargs = {}
        for key, val in kspec.items():
            if isinstance(val, str):
                _kwargs[key] = val.encode(enc)
            else:
                _kwargs[key] = val
    else:
        _kwargs = kspec

    if kspec["kty"] == "RSA":
        item = RSAKey(**_kwargs)
    elif kspec["kty"] == "oct":
        item = SYMKey(**_kwargs)
    elif kspec["kty"] == "EC":
        item = ECKey(**_kwargs)
    else:
        item = Key(**_kwargs)
    return item


def jwk_wrap(key, use="", kid=""):
    """
    Instantiate a Key instance with the given key

    :param key: The keys to wrap
    :param use: What the key are expected to be use for
    :param kid: A key id
    :return: The Key instance
    """
    if isinstance(key, RsaKey):
        kspec = RSAKey(use=use, kid=kid).load_key(key)
    elif isinstance(key, str):
        kspec = SYMKey(key=key, use=use, kid=kid)
    elif isinstance(key, NISTEllipticCurve):
        kspec = ECKey(use=use, kid=kid).load_key(key)
    else:
        raise Exception("Unknown key type:key=" + str(type(key)))

    kspec.serialize()
    return kspec


class KEYS(object):
    def __init__(self):
        self._keys = []

    def load_dict(self, dikt):
        for kspec in dikt["keys"]:
            self._keys.append(keyrep(kspec))

    def load_jwks(self, jwks):
        """
        Load and create keys from a JWKS JSON representation

        Expects something on this form::

            {"keys":
                [
                    {"kty":"EC",
                     "crv":"P-256",
                     "x":"MKBCTNIcKUSDii11ySs3526iDZ8AiTo7Tu6KPAqv7D4",
                    "y":"4Etl6SRW2YiLUrN5vfvVHuhp7x8PxltmWWlbbM4IFyM",
                    "use":"enc",
                    "kid":"1"},

                    {"kty":"RSA",
                    "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFb....."
                    "e":"AQAB",
                    "kid":"2011-04-29"}
                ]
            }

        :param jwks: The JWKS JSON string representation
        :return: list of 2-tuples containing key, type
        """
        self.load_dict(json.loads(jwks))
        return self

    def dump_jwks(self):
        """
        :return: A JWKS representation of the held keys
        """
        res = []
        for key in self._keys:
            res.append(b2s_conv(key.serialize()))

        return json.dumps({"keys": res})

    def load_from_url(self, url, *args, **kwargs):
        """
        Get and transform a JWKS into keys

        :param url: Where the JWKS can be found
        :param verify: SSL cert verification
        :return: list of keys
        """

        if 'verify' not in kwargs:
            kwargs['verify'] = True
        r = request("GET", url, allow_redirects=True, **kwargs)
        if r.status_code == 200:
            return self.load_jwks(r.text)
        else:
            raise Exception("HTTP Get error: %s" % r.status_code)

    def __getitem__(self, item):
        """
        Get all keys of a specific key type

        :param kty: Key type
        :return: list of keys
        """
        kty = item.lower()
        return [k for k in self._keys if k.kty.lower() == kty]

    def __iter__(self):
        for k in self._keys:
            yield k

    def __len__(self):
        return len(self._keys)

    def keys(self):
        return self._keys

    def key_types(self):
        """

        :return: A list of key types !!! not keys
        """
        return list(set([k.kty for k in self._keys]))

    def __repr__(self):
        return self.dump_jwks()

    def __str__(self):
        return self.__repr__()

    def kids(self):
        return [k.kid for k in self._keys if k.kid]

    def by_kid(self, kid):
        return [k for k in self._keys if kid == k.kid]

    def wrap_add(self, keyinst, use="", kid=''):
        self._keys.append(jwk_wrap(keyinst, use, kid))

    def as_dict(self):
        _res = {}
        for kty, k in [(k.kty, k) for k in self._keys]:
            if kty not in ["RSA", "EC", "oct"]:
                if kty in ["rsa", "ec"]:
                    kty = kty.upper()
                else:
                    kty = kty.lower()

            try:
                _res[kty].append(k)
            except KeyError:
                _res[kty] = [k]
        return _res

    def add(self, item, enc="utf-8"):
        self._keys.append(keyrep(item, enc))

    def append(self, key):
        self._keys.append(key)


def load_jwks_from_url(url, verify=True):
    return KEYS().load_from_url(url, verify=verify).keys()


def load_jwks(spec):
    return KEYS().load_jwks(spec).keys()


def make_public_copy(key):
    if not isinstance(key, Key):
        raise ValueError("Wrong type of class instance")

    c = key.__class__()
    for attr in key.public_members:
        try:
            v = getattr(key, attr)
        except AttributeError:
            pass
        else:
            setattr(c, attr, v)

    return c
