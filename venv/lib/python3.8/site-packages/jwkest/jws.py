"""JSON Web Token"""
import six

try:
    from builtins import str
    from builtins import object
except ImportError:
    pass

# Most of the code, ideas herein I have borrowed/stolen from other people
# Most notably Jeff Lindsay, Ryan Kelly and Richard Barnes

import json
import logging

import struct
from Cryptodome.Hash import SHA256
from Cryptodome.Hash import SHA384
from Cryptodome.Hash import SHA512
from Cryptodome.Hash import HMAC
from Cryptodome.Signature import PKCS1_v1_5
from Cryptodome.Signature import PKCS1_PSS
from Cryptodome.Util.number import bytes_to_long
import sys

from jwkest import b64d
from jwkest import as_unicode
from jwkest import WrongNumberOfParts
from jwkest import b64d_enc_dec
from jwkest import b64e_enc_dec
from jwkest import b64e
from jwkest import constant_time_compare
from jwkest import safe_str_cmp
from jwkest import JWKESTException
from jwkest import BadSignature
from jwkest import UnknownAlgorithm
from jwkest.ecc import P256
from jwkest.ecc import P384
from jwkest.ecc import P521

from jwkest.jwk import load_x509_cert
from jwkest.jwk import KEYS
from jwkest.jwk import HeaderError
from jwkest.jwk import sha256_digest
from jwkest.jwk import sha384_digest
from jwkest.jwk import sha512_digest
from jwkest.jwk import keyrep

from jwkest.jwt import JWT
from jwkest.jwt import b64encode_item

logger = logging.getLogger(__name__)


KDESC = ['use', 'kid', 'kty']

class JWSException(JWKESTException):
    pass


class NoSuitableSigningKeys(JWSException):
    pass


class FormatError(JWSException):
    pass


class WrongTypeOfKey(JWSException):
    pass


class UnknownSignerAlg(JWSException):
    pass


class SignerAlgError(JWSException):
    pass


def left_hash(msg, func="HS256"):
    """ 128 bits == 16 bytes """
    if func == 'HS256':
        return as_unicode(b64e(sha256_digest(msg)[:16]))
    elif func == 'HS384':
        return as_unicode(b64e(sha384_digest(msg)[:24]))
    elif func == 'HS512':
        return as_unicode(b64e(sha512_digest(msg)[:32]))


def mpint(b):
    b += b"\x00"
    return struct.pack(">L", len(b)) + b


def mp2bin(b):
    # just ignore the length...
    if b[4] == '\x00':
        return b[5:]
    else:
        return b[4:]


class Signer(object):
    """Abstract base class for signing algorithms."""

    def sign(self, msg, key):
        """Sign ``msg`` with ``key`` and return the signature."""
        raise NotImplementedError()

    def verify(self, msg, sig, key):
        """Return True if ``sig`` is a valid signature for ``msg``."""
        raise NotImplementedError()


class HMACSigner(Signer):
    def __init__(self, digest):
        self.digest = digest

    def sign(self, msg, key):
        h = HMAC.new(key, msg, digestmod=self.digest)
        return h.digest()
        # return hmac.new(key, msg, digestmod=self.digest).digest()

    def verify(self, msg, sig, key):
        if sys.version < '3':
            if safe_str_cmp(self.sign(msg, key), sig):
                return True
        elif constant_time_compare(self.sign(msg, key), sig):
            return True
        raise BadSignature(repr(sig))


class RSASigner(Signer):
    def __init__(self, digest):
        self.digest = digest

    def sign(self, msg, key):
        h = self.digest.new(msg)
        signer = PKCS1_v1_5.new(key)
        return signer.sign(h)

    def verify(self, msg, sig, key):
        h = self.digest.new(msg)
        verifier = PKCS1_v1_5.new(key)
        try:
            if verifier.verify(h, sig):
                return True
            else:
                raise BadSignature()
        except ValueError as e:
            raise BadSignature(str(e))


class DSASigner(Signer):
    def __init__(self, digest, sign):
        self.digest = digest
        self._sign = sign

    def sign(self, msg, key):
        # verify the key
        h = bytes_to_long(self.digest.new(msg).digest())
        return self._sign.sign(h, key)

    def verify(self, msg, sig, key):
        h = bytes_to_long(self.digest.new(msg).digest())
        if self._sign.verify(h, sig, key):
            return True
        else:
            raise BadSignature()


class PSSSigner(Signer):
    def __init__(self, digest):
        self.digest = digest

    def sign(self, msg, key):
        h = self.digest.new(msg)
        signer = PKCS1_PSS.new(key)
        return signer.sign(h)

    def verify(self, msg, sig, key):
        h = self.digest.new(msg)
        verifier = PKCS1_PSS.new(key)
        res = verifier.verify(h, sig)
        if not res:
            raise BadSignature()
        else:
            return True


SIGNER_ALGS = {
    'HS256': HMACSigner(SHA256),
    'HS384': HMACSigner(SHA384),
    'HS512': HMACSigner(SHA512),

    'RS256': RSASigner(SHA256),
    'RS384': RSASigner(SHA384),
    'RS512': RSASigner(SHA512),

    'ES256': DSASigner(SHA256, P256),
    'ES384': DSASigner(SHA384, P384),
    'ES512': DSASigner(SHA512, P521),

    'PS256': PSSSigner(SHA256),
    'PS384': PSSSigner(SHA384),
    'PS512': PSSSigner(SHA512),

    'none': None
}


def alg2keytype(alg):
    if not alg or alg.lower() == "none":
        return "none"
    elif alg.startswith("RS") or alg.startswith("PS"):
        return "RSA"
    elif alg.startswith("HS") or alg.startswith("A"):
        return "oct"
    elif alg.startswith("ES") or alg.startswith("ECDH-ES"):
        return "EC"
    else:
        return None


class JWSig(JWT):
    def sign_input(self):
        return self.b64part[0] + b'.' + self.b64part[1]

    def signature(self):
        return self.part[2]

    def __len__(self):
        return len(self.part)

    def valid(self):
        if len(self) != 3:
            return False

        return True


class JWx(object):
    args = ["alg", "jku", "jwk", "x5u", "x5t", "x5c", "kid", "typ", "cty",
            "crit"]
    """
    :param alg: The signing algorithm
    :param jku: a URI that refers to a resource for a set of JSON-encoded
        public keys, one of which corresponds to the key used to digitally
        sign the JWS
    :param jwk: A JSON Web Key that corresponds to the key used to
        digitally sign the JWS
    :param x5u: a URI that refers to a resource for the X.509 public key
        certificate or certificate chain [RFC5280] corresponding to the key
        used to digitally sign the JWS.
    :param x5t: a base64url encoded SHA-1 thumbprint (a.k.a. digest) of the
        DER encoding of the X.509 certificate [RFC5280] corresponding to
        the key used to digitally sign the JWS.
    :param x5c: the X.509 public key certificate or certificate chain
        corresponding to the key used to digitally sign the JWS.
    :param kid: a hint indicating which key was used to secure the JWS.
    :param typ: the type of this object. 'JWS' == JWS Compact Serialization
        'JWS+JSON' == JWS JSON Serialization
    :param cty: the type of the secured content
    :param crit: indicates which extensions that are being used and MUST
        be understood and processed.
    :param kwargs: Extra header parameters
    :return: A class instance
    """

    def __init__(self, msg=None, with_digest=False, **kwargs):
        self.msg = msg

        self._dict = {}
        self.with_digest = with_digest
        self.jwt = None

        if kwargs:
            for key in self.args:
                try:
                    _val = kwargs[key]
                except KeyError:
                    if key == "alg":
                        self._dict[key] = "none"
                    continue

                if key == "jwk":
                    if isinstance(_val, dict):
                        self._dict["jwk"] = keyrep(_val)
                    elif isinstance(_val, str):
                        self._dict["jwk"] = keyrep(json.loads(_val))
                    else:
                        self._dict["jwk"] = _val
                elif key == "x5c" or key == "crit":
                    self._dict["x5c"] = _val or []
                else:
                    self._dict[key] = _val

    def __contains__(self, item):
        return item in self._dict

    def __getitem__(self, item):
        return self._dict[item]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getattr__(self, item):
        try:
            return self._dict[item]
        except KeyError:
            raise AttributeError(item)

    def keys(self):
        return list(self._dict.keys())

    def headers(self, extra=None):
        _extra = extra or {}
        _header = {}
        for param in self.args:
            try:
                _header[param] = _extra[param]
            except KeyError:
                try:
                    if self._dict[param]:
                        _header[param] = self._dict[param]
                except KeyError:
                    pass

        if "jwk" in self:
            _header["jwk"] = self["jwk"].serialize()
        elif "jwk" in _extra:
            _header["jwk"] = extra["jwk"].serialize()

        if "kid" in self:
            try:
                assert isinstance(self["kid"], six.string_types)
            except AssertionError:
                raise HeaderError("kid of wrong value type")

        return _header

    def _get_keys(self):
        logger.debug("_get_keys(): self._dict.keys={0}".format(
            self._dict.keys()))

        if "jwk" in self:
            return [self["jwk"]]
        elif "jku" in self:
            keys = KEYS()
            keys.load_from_url(self["jku"])
            return keys.as_dict()
        elif "x5u" in self:
            try:
                return {"rsa": [load_x509_cert(self["x5u"], {})]}
            except Exception:
                # ca_chain = load_x509_cert_chain(self["x5u"])
                pass

        return {}

    def alg2keytype(self, alg):
        return alg2keytype(alg)

    def pick_keys(self, keys, use="", alg=""):
        """
        The assumption is that upper layer has made certain you only get
        keys you can use.

        :param keys: A list of KEY instances
        :return: A list of KEY instances that fulfill the requirements
        """
        if not alg:
            alg = self["alg"]

        if alg == "none":
            return []

        _k = self.alg2keytype(alg)
        if _k is None:
            logger.error("Unknown algorithm '%s'" % alg)
            return []

        logger.debug("Picking key by key type={0}".format(_k))
        _kty = [_k.lower(), _k.upper(), _k.lower().encode("utf-8"),
                _k.upper().encode("utf-8")]
        _keys = [k for k in keys if k.kty in _kty]
        try:
            _kid = self["kid"]
        except KeyError:
            try:
                _kid = self.jwt.headers["kid"]
            except (AttributeError, KeyError):
                _kid = None

        logger.debug("Picking key based on alg={0}, kid={1} and use={2}".format(
            alg, _kid, use))

        pkey = []
        for _key in _keys:
            logger.debug(
                "Picked: kid:{}, use:{}, kty:{}".format(
                    _key.kid, _key.use, _key.kty))
            if _kid:
                try:
                    assert _kid == _key.kid
                except (KeyError, AttributeError):
                    pass
                except AssertionError:
                    continue

            if use and _key.use and _key.use != use:
                continue

            if alg and _key.alg and _key.alg != alg:
                continue

            pkey.append(_key)

        return pkey

    def _pick_alg(self, keys):
        alg = None
        try:
            alg = self["alg"]
        except KeyError:
            # try to get alg from key if there is only one
            if keys is not None and len(keys) == 1:
                key = next(iter(keys))  # first element from either list or dict
                if key.alg:
                    self["alg"] = alg = key.alg

        if not alg:
            self["alg"] = alg = "none"

        return alg

    def _decode(self, payload):
        _msg = b64d(bytes(payload))
        if "cty" in self:
            if self["cty"] == "JWT":
                _msg = json.loads(_msg)
        return _msg

    def dump_header(self):
        return dict([(x, self._dict[x]) for x in self.args if x in self._dict])


class JWS(JWx):
    def alg_keys(self, keys, use, protected=None):
        _alg = self._pick_alg(keys)

        if keys:
            keys = self.pick_keys(keys, use=use, alg=_alg)
        else:
            keys = self.pick_keys(self._get_keys(), use=use, alg=_alg)

        xargs = protected or {}
        xargs["alg"] = _alg

        if keys:
            key = keys[0]
            if key.kid:
                xargs["kid"] = key.kid
        elif not _alg or _alg.lower() == "none":
            key = None
        else:
            if "kid" in self:
                raise NoSuitableSigningKeys(
                    "No key for algorithm: %s and kid: %s" % (_alg,
                                                              self["kid"]))
            else:
                raise NoSuitableSigningKeys("No key for algorithm: %s" % _alg)

        return key, xargs, _alg

    def sign_compact(self, keys=None, protected=None):
        """
        Produce a JWS using the JWS Compact Serialization

        :param keys: A dictionary of keys
        :param protected: The protected headers (a dictionary)
        :return:
        """

        key, xargs, _alg = self.alg_keys(keys, 'sig', protected)

        if "typ" in self:
            xargs["typ"] = self["typ"]

        jwt = JWSig(**xargs)
        if _alg == "none":
            return jwt.pack(parts=[self.msg, ""])

        # All other cases
        try:
            _signer = SIGNER_ALGS[_alg]
        except KeyError:
            raise UnknownAlgorithm(_alg)

        _input = jwt.pack(parts=[self.msg])
        sig = _signer.sign(_input.encode("utf-8"),
                           key.get_key(alg=_alg, private=True))
        logger.debug("Signed message using key with kid=%s" % key.kid)
        return ".".join([_input, b64encode_item(sig).decode("utf-8")])

    def verify_compact(self, jws, keys=None, allow_none=False, sigalg=None):
        """
        Verify a JWT signature

        :param jws:
        :param keys:
        :param allow_none: If signature algorithm 'none' is allowed
        :param sigalg: Expected sigalg
        :return:
        """
        return self.verify_compact_verbose(jws, keys, allow_none, sigalg)['msg']

    def verify_compact_verbose(self, jws, keys=None, allow_none=False, sigalg=None):
        """
        Verify a JWT signature and return dict with validation results

        :param jws:
        :param keys:
        :param allow_none: If signature algorithm 'none' is allowed
        :param sigalg: Expected sigalg
        :return:
        """
        jwt = JWSig().unpack(jws)
        if len(jwt) != 3:
            raise WrongNumberOfParts(len(jwt))

        self.jwt = jwt

        try:
            _alg = jwt.headers["alg"]
        except KeyError:
            _alg = None
        else:
            if _alg is None or _alg.lower() == "none":
                if allow_none:
                    self.msg = jwt.payload()
                    return {'msg': self.msg}
                else:
                    raise SignerAlgError("none not allowed")

        if "alg" in self and _alg:
            if self["alg"] != _alg:
                raise SignerAlgError("Wrong signing algorithm")

        if sigalg and sigalg != _alg:
            raise SignerAlgError("Expected {0} got {1}".format(
                sigalg, jwt.headers["alg"]))

        self["alg"] = _alg

        if keys:
            _keys = self.pick_keys(keys)
        else:
            _keys = self.pick_keys(self._get_keys())

        if not _keys:
            if "kid" in self:
                raise NoSuitableSigningKeys(
                    "No key with kid: %s" % (self["kid"]))
            elif "kid" in self.jwt.headers:
                raise NoSuitableSigningKeys(
                    "No key with kid: %s" % (self.jwt.headers["kid"]))
            else:
                raise NoSuitableSigningKeys("No key for algorithm: %s" % _alg)

        verifier = SIGNER_ALGS[_alg]

        for key in _keys:
            try:
                res = verifier.verify(jwt.sign_input(), jwt.signature(),
                                      key.get_key(alg=_alg, private=False))
            except (BadSignature, IndexError):
                pass
            else:
                if res is True:
                    logger.debug(
                        "Verified message using key with kid=%s" % key.kid)
                    self.msg = jwt.payload()
                    self.key = key
                    return {'msg': self.msg, 'key': key}

        raise BadSignature()

    def sign_json(self, keys=None, headers=None, flatten=False):
        """
        Produce JWS using the JWS JSON Serialization

        :param keys: list of keys to use for signing the JWS
        :param headers: list of tuples (protected headers, unprotected
        headers) for each signature
        :return:
        """

        def create_signature(protected, unprotected):
            protected_headers = protected or {}
            # always protect the signing alg header
            protected_headers.setdefault("alg", self.alg)
            _jws = JWS(self.msg, **protected_headers)
            encoded_header, payload, signature = _jws.sign_compact(
                protected=protected,
                keys=keys).split(".")
            signature_entry = {"signature": signature}
            if unprotected:
                signature_entry["header"] = unprotected
            if encoded_header:
                signature_entry["protected"] = encoded_header

            return signature_entry

        res = {"payload": b64e_enc_dec(self.msg, "utf-8", "ascii")}

        if headers is None:
            headers = [(dict(alg=self.alg), None)]

        if flatten and len(
                headers) == 1:  # Flattened JWS JSON Serialization Syntax
            signature_entry = create_signature(*headers[0])
            res.update(signature_entry)
        else:
            res["signatures"] = []
            for protected, unprotected in headers:
                signature_entry = create_signature(protected, unprotected)
                res["signatures"].append(signature_entry)

        return json.dumps(res)

    def verify_json(self, jws, keys=None, allow_none=False, sigalg=None):
        """

        :param jws:
        :param keys:
        :return:
        """

        _jwss = json.loads(jws)

        try:
            _payload = _jwss["payload"]
        except KeyError:
            raise FormatError("Missing payload")

        try:
            _signs = _jwss["signatures"]
        except KeyError:
            # handle Flattened JWKS Serialization Syntax
            signature = {}
            for key in ["protected", "header", "signature"]:
                if key in _jwss:
                    signature[key] = _jwss[key]
            _signs = [signature]

        _claim = None
        for _sign in _signs:
            protected_headers = _sign.get("protected", "")
            token = b".".join([protected_headers.encode(), _payload.encode(),
                               _sign["signature"].encode()])

            unprotected_headers = _sign.get("header", {})
            all_headers = unprotected_headers.copy()
            all_headers.update(
                json.loads(b64d_enc_dec(protected_headers) or {}))
            self.__init__(**all_headers)

            _tmp = self.verify_compact(token, keys, allow_none, sigalg)
            if _claim is None:
                _claim = _tmp
            else:
                assert _claim == _tmp

        return _claim

    def is_jws(self, jws):
        """

        :param jws:
        :return:
        """

        try:
            # JWS JSON serialization
            try:
                json_jws = json.loads(jws)
            except TypeError:
                jws = jws.decode('utf8')
                json_jws = json.loads(jws)

            return self._is_json_serialized_jws(json_jws)
        except ValueError:
            return self._is_compact_jws(jws)

    def _is_json_serialized_jws(self, json_jws):
        json_ser_keys = set(["payload", "signatures"])
        flattened_json_ser_keys = set(["payload", "signature"])
        if not json_ser_keys.issubset(
                json_jws.keys()) and not flattened_json_ser_keys.issubset(
                json_jws.keys()):
            return False
        return True

    def _is_compact_jws(self, jws):
        try:
            jwt = JWSig().unpack(jws)
        except Exception:
            return False

        try:
            assert "alg" in jwt.headers
        except AssertionError:
            return False
        else:
            if jwt.headers["alg"] is None:
                jwt.headers["alg"] = "none"

            try:
                assert jwt.headers["alg"] in SIGNER_ALGS
            except AssertionError:
                logger.debug("UnknownSignerAlg: %s" % jwt.headers["alg"])
                return False
            else:
                self.jwt = jwt
                return True


def factory(token):
    _jw = JWS()
    if _jw.is_jws(token):
        return _jw
    else:
        return None
