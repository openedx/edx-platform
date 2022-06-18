# from future import standard_library
# standard_library.install_aliases()
try:
    from builtins import object
except ImportError:
    pass

import struct
import io
import logging
import zlib
import six

from Cryptodome import Random
from Cryptodome.Hash import SHA, SHA256
from Cryptodome.Util.number import bytes_to_long
from Cryptodome.Util.number import long_to_bytes
from Cryptodome.Cipher import PKCS1_v1_5
from Cryptodome.Cipher import PKCS1_OAEP

from jwkest import b64d
from jwkest import b64e
from jwkest import as_bytes
from jwkest import WrongNumberOfParts
from jwkest import JWKESTException
from jwkest import MissingKey
from jwkest.aes_gcm import AES_GCM
from jwkest.aes_key_wrap import aes_wrap_key
from jwkest.aes_key_wrap import aes_unwrap_key
from jwkest.ecc import NISTEllipticCurve
from jwkest.extra import aes_cbc_hmac_encrypt
from jwkest.extra import ecdh_derive_key
from jwkest.extra import aes_cbc_hmac_decrypt
from jwkest.jwk import intarr2str, SYMKey
from jwkest.jwk import ECKey
from jwkest.jws import JWx
from jwkest.jwt import JWT, b64encode_item

logger = logging.getLogger(__name__)

__author__ = 'rohe0002'

ENC = 1
DEC = 0


class JWEException(JWKESTException):
    pass


class CannotDecode(JWEException):
    pass


class NotSupportedAlgorithm(JWEException):
    pass


class MethodNotSupported(JWEException):
    pass


class ParameterError(JWEException):
    pass


class NoSuitableEncryptionKey(JWEException):
    pass


class NoSuitableDecryptionKey(JWEException):
    pass


class NoSuitableECDHKey(JWEException):
    pass


class DecryptionFailed(JWEException):
    pass


class WrongEncryptionAlgorithm(JWEException):
    pass


# ---------------------------------------------------------------------------
# Base class

KEYLEN = {
    "A128GCM": 128,
    "A192GCM": 192,
    "A256GCM": 256,
    "A128CBC-HS256": 256,
    "A192CBC-HS384": 384,
    "A256CBC-HS512": 512
}


class Encrypter(object):
    """Abstract base class for encryption algorithms."""

    def __init__(self, with_digest=False):
        self.with_digest = with_digest

    def encrypt(self, msg, key):
        """Encrypt ``msg`` with ``key`` and return the encrypted message."""
        raise NotImplementedError

    def decrypt(self, msg, key):
        """Return decrypted message."""
        raise NotImplementedError


class RSAEncrypter(Encrypter):
    def encrypt(self, msg, key, padding="pkcs1_padding"):
        if padding == "pkcs1_padding":
            cipher = PKCS1_v1_5.new(key)
            if self.with_digest:  # add a SHA digest to the message
                h = SHA.new(msg)
                msg += h.digest()
        elif padding == "pkcs1_oaep_padding":
            cipher = PKCS1_OAEP.new(key)
        elif padding == "pkcs1_oaep_256_padding":
            cipher = PKCS1_OAEP.new(key, SHA256)
        else:
            raise Exception("Unsupported padding")
        return cipher.encrypt(msg)

    def decrypt(self, ciphertext, key, padding="pkcs1_padding"):
        if padding == "pkcs1_padding":
            cipher = PKCS1_v1_5.new(key)
            if self.with_digest:
                dsize = SHA.digest_size
            else:
                dsize = 0
            sentinel = Random.new().read(32 + dsize)
            text = cipher.decrypt(ciphertext, sentinel)
            if dsize:
                _digest = text[-dsize:]
                _msg = text[:-dsize]
                digest = SHA.new(_msg).digest()
                if digest == _digest:
                    text = _msg
                else:
                    raise DecryptionFailed()
            else:
                if text == sentinel:
                    raise DecryptionFailed()
        elif padding == "pkcs1_oaep_padding":
            cipher = PKCS1_OAEP.new(key)
            text = cipher.decrypt(ciphertext)
        elif padding == "pkcs1_oaep_256_padding":
            cipher = PKCS1_OAEP.new(key, SHA256)
            text = cipher.decrypt(ciphertext)
        else:
            raise Exception("Unsupported padding")

        return text


# ---------------------------------------------------------------------------


def int2bigendian(n):
    return [ord(c) for c in struct.pack('>I', n)]


def party_value(pv):
    if pv:
        s = b64e(pv)
        r = int2bigendian(len(s))
        r.extend(s)
        return r
    else:
        return [0, 0, 0, 0]


def _hash_input(cmk, enc, label, rond=1, length=128, hashsize=256,
                epu="", epv=""):
    r = [0, 0, 0, rond]
    r.extend(cmk)
    r.extend([0, 0, 0, length])
    r.extend([ord(c) for c in enc])
    r.extend(party_value(epu))
    r.extend(party_value(epv))
    r.extend(label)
    return r


# ---------------------------------------------------------------------------

def cipher_filter(cipher, inf, outf):
    while 1:
        buf = inf.read()
        if not buf:
            break
        outf.write(cipher.update(buf))
    outf.write(cipher.final())
    return outf.getvalue()


def aes_enc(key, txt):
    pbuf = io.StringIO(txt)
    cbuf = io.StringIO()
    ciphertext = cipher_filter(key, pbuf, cbuf)
    pbuf.close()
    cbuf.close()
    return ciphertext


def aes_dec(key, ciptxt):
    pbuf = io.StringIO()
    cbuf = io.StringIO(ciptxt)
    plaintext = cipher_filter(key, cbuf, pbuf)
    pbuf.close()
    cbuf.close()
    return plaintext


def keysize(spec):
    if spec.startswith("HS"):
        return int(spec[2:])
    elif spec.startswith("CS"):
        return int(spec[2:])
    elif spec.startswith("A"):
        return int(spec[1:4])
    return 0


ENC2ALG = {"A128CBC": "aes_128_cbc", "A192CBC": "aes_192_cbc",
           "A256CBC": "aes_256_cbc"}

SUPPORTED = {
    "alg": ["RSA1_5", "RSA-OAEP", "RSA-OAEP-256", "A128KW", "A192KW", "A256KW",
            "ECDH-ES", "ECDH-ES+A128KW", "ECDH-ES+A192KW", "ECDH-ES+A256KW"],
    "enc": ["A128CBC-HS256", "A192CBC-HS384", "A256CBC-HS512",
            "A128GCM", "A192GCM", "A256GCM"],
}


def alg2keytype(alg):
    if alg.startswith("RSA"):
        return "RSA"
    elif alg.startswith("A"):
        return "oct"
    elif alg.startswith("ECDH"):
        return "EC"
    else:
        return None


# =============================================================================

ENCALGLEN1 = {
    "A128GCM": 16,
    "A192GCM": 24,
    "A256GCM": 32
}

ENCALGLEN2 = {
    "A128CBC-HS256": 32,
    "A192CBC-HS384": 48,
    "A256CBC-HS512": 64,
}


class JWEnc(JWT):
    def b64_protected_header(self):
        return self.b64part[0]

    def b64_encrypted_key(self):
        return self.b64part[1]

    def b64_initialization_vector(self):
        return self.b64part[2]

    def b64_ciphertext(self):
        return self.b64part[3]

    def b64_authentication_tag(self):
        return self.b64part[4]

    def protected_header(self):
        return self.part[0]

    def encrypted_key(self):
        return self.part[1]

    def initialization_vector(self):
        return self.part[2]

    def ciphertext(self):
        return self.part[3]

    def authentication_tag(self):
        return self.part[4]

    def b64_encode_header(self):
        return b64encode_item(self.headers)

    def is_jwe(self):
        if "typ" in self.headers and self.headers["typ"].lower() == "jwe":
            return True

        try:
            assert "alg" in self.headers and "enc" in self.headers
        except AssertionError:
            return False
        else:
            for typ in ["alg", "enc"]:
                try:
                    assert self.headers[typ] in SUPPORTED[typ]
                except AssertionError:
                    logger.debug("Not supported %s algorithm: %s" % (
                        typ, self.headers[typ]))
                    return False
        return True

    def __len__(self):
        return len(self.part)


class JWe(JWx):
    @staticmethod
    def _generate_key_and_iv(encalg, cek="", iv=""):
        if cek and iv:
            return cek, iv

        try:
            _key = Random.get_random_bytes(ENCALGLEN1[encalg])
            _iv = Random.get_random_bytes(12)
        except KeyError:
            try:
                _key = Random.get_random_bytes(ENCALGLEN2[encalg])
                _iv = Random.get_random_bytes(16)
            except KeyError:
                raise Exception("Unsupported encryption algorithm %s" % encalg)
        if cek:
            _key = cek
        if iv:
            _iv = iv

        return _key, _iv

    def alg2keytype(self, alg):
        return alg2keytype(alg)

    def enc_setup(self, enc_alg, msg, auth_data, key=None, iv=""):
        """ Encrypt JWE content.

        :param enc_alg: The JWE "enc" value specifying the encryption algorithm
        :param msg: The plain text message
        :param auth_data: Additional authenticated data
        :param key: Key (CEK)
        :return: Tuple (ciphertext, tag), both as bytes
        """

        key, iv = self._generate_key_and_iv(enc_alg, key, iv)

        if enc_alg in ["A192GCM", "A128GCM", "A256GCM"]:
            gcm = AES_GCM(bytes_to_long(key))
            ctxt, tag = gcm.encrypt(bytes_to_long(iv), msg, auth_data)
            tag = long_to_bytes(tag)
        elif enc_alg in ["A128CBC-HS256", "A192CBC-HS384", "A256CBC-HS512"]:
            assert enc_alg in SUPPORTED["enc"]
            ctxt, tag = aes_cbc_hmac_encrypt(key, iv, auth_data, msg)
        else:
            raise NotSupportedAlgorithm(enc_alg)

        return ctxt, tag, key

    @staticmethod
    def _decrypt(enc, key, ctxt, auth_data, iv, tag):
        """ Decrypt JWE content.

        :param enc: The JWE "enc" value specifying the encryption algorithm
        :param key: Key (CEK)
        :param iv : Initialization vector
        :param auth_data: Additional authenticated data (AAD)
        :param ctxt : Ciphertext
        :param tag: Authentication tag
        :return: plain text message or None if decryption failed
        """
        if enc in ["A128GCM", "A192GCM", "A256GCM"]:
            gcm = AES_GCM(bytes_to_long(key))
            try:
                text = gcm.decrypt(bytes_to_long(iv), ctxt, bytes_to_long(tag),
                                   auth_data)
                return text
            except DecryptionFailed:
                raise
        elif enc in ["A128CBC-HS256", "A192CBC-HS384", "A256CBC-HS512"]:
            return aes_cbc_hmac_decrypt(key, iv, auth_data, ctxt, tag)
        else:
            raise Exception("Unsupported encryption algorithm %s" % enc)


class JWE_SYM(JWe):
    args = JWe.args[:]
    args.append("enc")

    def encrypt(self, key, iv="", cek="", **kwargs):
        """

        :param key: Shared symmetric key
        :param iv: initialization vector
        :param cek:
        :param kwargs: Extra keyword arguments, just ignore for now.
        :return:
        """
        _msg = self.msg

        _args = self._dict
        try:
            _args["kid"] = kwargs["kid"]
        except KeyError:
            pass

        jwe = JWEnc(**_args)

        # If no iv and cek are given generate them
        cek, iv = self._generate_key_and_iv(self["enc"], cek, iv)
        if isinstance(key, SYMKey):
            try:
                kek = key.key.encode('utf8')
            except AttributeError:
                kek = key.key
        elif isinstance(key, six.binary_type):
            kek = key
        else:
            kek = intarr2str(key)

        # The iv for this function must be 64 bit
        # Which is certainly different from the one above
        jek = aes_wrap_key(kek, cek)

        _enc = self["enc"]

        ctxt, tag, cek = self.enc_setup(_enc, _msg.encode(),
                                        jwe.b64_encode_header(),
                                        cek, iv=iv)
        return jwe.pack(parts=[jek, iv, ctxt, tag])

    def decrypt(self, token, key=None, cek=None):
        logger.debug('SYM decrypt')
        if not key and not cek:
            raise MissingKey("On of key or cek must be specified")

        if isinstance(token, JWEnc):
            jwe = token
        else:
            jwe = JWEnc().unpack(token)

        if len(jwe) != 5:
            raise WrongNumberOfParts(len(jwe))

        if not cek:
            jek = jwe.encrypted_key()
            if isinstance(key, SYMKey):
                try:
                    key = key.key.encode('utf8')
                except AttributeError:
                    key = key.key
            # The iv for this function must be 64 bit
            cek = aes_unwrap_key(key, jek)

        msg = self._decrypt(
            jwe.headers["enc"], cek, jwe.ciphertext(),
            jwe.b64_protected_header(),
            jwe.initialization_vector(), jwe.authentication_tag())

        if "zip" in self and self["zip"] == "DEF":
            msg = zlib.decompress(msg)

        return msg


class JWE_RSA(JWe):
    args = ["msg", "alg", "enc", "epk", "zip", "jku", "jwk", "x5u", "x5t",
            "x5c", "kid", "typ", "cty", "apu", "crit"]

    def encrypt(self, key, iv="", cek="", **kwargs):
        """
        Produces a JWE using RSA algorithms

        :param key: RSA key
        :param context:
        :param iv:
        :param cek:
        :return: A jwe
        """

        _msg = as_bytes(self.msg)
        if "zip" in self:
            if self["zip"] == "DEF":
                _msg = zlib.compress(_msg)
            else:
                raise ParameterError("Zip has unknown value: %s" % self["zip"])

        kwarg_cek = cek or None

        _enc = self["enc"]
        cek, iv = self._generate_key_and_iv(_enc, cek, iv)
        self["cek"] = cek

        logger.debug("cek: %s, iv: %s" % ([c for c in cek], [c for c in iv]))

        _encrypt = RSAEncrypter(self.with_digest).encrypt

        _alg = self["alg"]
        if kwarg_cek:
            jwe_enc_key = ''
        elif _alg == "RSA-OAEP":
            jwe_enc_key = _encrypt(cek, key, 'pkcs1_oaep_padding')
        elif _alg == "RSA-OAEP-256":
            jwe_enc_key = _encrypt(cek, key, 'pkcs1_oaep_256_padding')
        elif _alg == "RSA1_5":
            jwe_enc_key = _encrypt(cek, key)
        else:
            raise NotSupportedAlgorithm(_alg)

        jwe = JWEnc(**self.headers())

        enc_header = jwe.b64_encode_header()

        ctxt, tag, key = self.enc_setup(_enc, _msg, enc_header, cek, iv)
        return jwe.pack(parts=[jwe_enc_key, iv, ctxt, tag])

    def decrypt(self, token, key, cek=None):
        """ Decrypts a JWT

        :param token: The JWT
        :param key: A key to use for decrypting
        :return: The decrypted message
        """
        if not isinstance(token, JWEnc):
            jwe = JWEnc().unpack(token)
        else:
            jwe = token

        self.jwt = jwe.encrypted_key()
        jek = jwe.encrypted_key()

        _decrypt = RSAEncrypter(self.with_digest).decrypt

        _alg = jwe.headers["alg"]
        if cek:
            pass
        elif _alg == "RSA-OAEP":
            cek = _decrypt(jek, key, 'pkcs1_oaep_padding')
        elif _alg == "RSA-OAEP-256":
            cek = _decrypt(jek, key, 'pkcs1_oaep_256_padding')
        elif _alg == "RSA1_5":
            cek = _decrypt(jek, key)
        else:
            raise NotSupportedAlgorithm(_alg)

        self["cek"] = cek
        enc = jwe.headers["enc"]
        try:
            assert enc in SUPPORTED["enc"]
        except AssertionError:
            raise NotSupportedAlgorithm(enc)

        msg = self._decrypt(enc, cek, jwe.ciphertext(),
                            jwe.b64_protected_header(),
                            jwe.initialization_vector(),
                            jwe.authentication_tag())

        if "zip" in jwe.headers and jwe.headers["zip"] == "DEF":
            msg = zlib.decompress(msg)

        return msg


class JWE_EC(JWe):
    args = JWe.args[:]
    args.append("enc")

    def enc_setup(self, msg, auth_data, key=None, **kwargs):

        encrypted_key = ""
        self.msg = msg
        self.auth_data = auth_data

        # Generate the input parameters
        try:
            apu = b64d(kwargs["apu"])
        except KeyError:
            apu = Random.get_random_bytes(16)
        try:
            apv = b64d(kwargs["apv"])
        except KeyError:
            apv = Random.get_random_bytes(16)

        # Handle Local Key and Ephemeral Public Key
        if not key:
            raise Exception("EC Key Required for ECDH-ES JWE Encrpytion Setup")

        # Generate an ephemeral key pair if none is given
        curve = NISTEllipticCurve.by_name(key.crv)
        if "epk" in kwargs:
            epk = kwargs["epk"] if isinstance(kwargs["epk"], ECKey) else ECKey(
                kwargs["epk"])
        else:
            epk = ECKey().load_key(key=NISTEllipticCurve.by_name(key.crv))

        params = {
            "apu": b64e(apu),
            "apv": b64e(apv),
            "epk": epk.serialize(False)
        }

        cek = iv = None
        if 'cek' in kwargs and kwargs['cek']:
            cek = kwargs['cek']
        if 'iv' in kwargs and kwargs['iv']:
            iv = kwargs['iv']

        cek, iv = self._generate_key_and_iv(self.enc, cek=cek, iv=iv)

        if self.alg == "ECDH-ES":
            try:
                dk_len = KEYLEN[self.enc]
            except KeyError:
                raise Exception(
                    "Unknown key length for algorithm %s" % self.enc)

            cek = ecdh_derive_key(curve, epk.d, (key.x, key.y), apu, apv,
                                  str(self.enc).encode(), dk_len)
        elif self.alg in ["ECDH-ES+A128KW", "ECDH-ES+A192KW", "ECDH-ES+A256KW"]:
            _pre, _post = self.alg.split("+")
            klen = int(_post[1:4])
            kek = ecdh_derive_key(curve, epk.d, (key.x, key.y), apu, apv,
                                  str(_post).encode(), klen)
            encrypted_key = aes_wrap_key(kek, cek)
        else:
            raise Exception("Unsupported algorithm %s" % self.alg)

        return cek, encrypted_key, iv, params, epk

    def dec_setup(self, token, key=None, **kwargs):

        self.headers = token.headers
        self.iv = token.initialization_vector()
        self.ctxt = token.ciphertext()
        self.tag = token.authentication_tag()

        # Handle EPK / Curve
        if "epk" not in self.headers or "crv" not in self.headers["epk"]:
            raise Exception(
                "Ephemeral Public Key Missing in ECDH-ES Computation")

        epubkey = ECKey(**self.headers["epk"])
        apu = apv = ""
        if "apu" in self.headers:
            apu = b64d(self.headers["apu"].encode())
        if "apv" in self.headers:
            apv = b64d(self.headers["apv"].encode())

        if self.headers["alg"] == "ECDH-ES":
            try:
                dk_len = KEYLEN[self.headers["enc"]]
            except KeyError:
                raise Exception("Unknown key length for algorithm")

            self.cek = ecdh_derive_key(epubkey.curve, key.d,
                                       (epubkey.x, epubkey.y), apu, apv,
                                       str(self.headers["enc"]).encode(),
                                       dk_len)
        elif self.headers["alg"] in ["ECDH-ES+A128KW", "ECDH-ES+A192KW",
                                     "ECDH-ES+A256KW"]:
            _pre, _post = self.headers['alg'].split("+")
            klen = int(_post[1:4])
            kek = ecdh_derive_key(epubkey.curve, key.d, (epubkey.x, epubkey.y),
                                  apu, apv, str(_post).encode(), klen)
            self.cek = aes_unwrap_key(kek, token.encrypted_key())
        else:
            raise Exception("Unsupported algorithm %s" % self.headers["alg"])

        return self.cek

    def encrypt(self, key, iv="", cek="", **kwargs):

        _msg = as_bytes(self.msg)
        _args = self._dict
        try:
            _args["kid"] = kwargs["kid"]
        except KeyError:
            pass

        if 'params' in kwargs:
            if 'apu' in kwargs['params']:
                _args['apu'] = kwargs['params']['apu']
            if 'apv' in kwargs['params']:
                _args['apv'] = kwargs['params']['apv']
            if 'epk' in kwargs['params']:
                _args['epk'] = kwargs['params']['epk']

        jwe = JWEnc(**_args)
        ctxt, tag, cek = super(JWE_EC, self).enc_setup(self["enc"], _msg,
                                                       jwe.b64_encode_header(),
                                                       cek, iv=iv)
        if 'encrypted_key' in kwargs:
            return jwe.pack(parts=[kwargs['encrypted_key'], iv, ctxt, tag])
        return jwe.pack(parts=[iv, ctxt, tag])

    def decrypt(self, token=None, key=None, **kwargs):

        if isinstance(token, JWEnc):
            jwe = token
        else:
            jwe = JWEnc().unpack(token)

        if not self.cek:
            raise Exception("Content Encryption Key is Not Yet Set")

        msg = super(JWE_EC, self)._decrypt(self.headers["enc"], self.cek,
                                           self.ctxt,
                                           jwe.b64part[0],
                                           self.iv, self.tag)
        self.msg = msg
        self.msg_valid = True
        return msg


class JWE(JWx):
    args = ["alg", "enc", "epk", "zip", "jku", "jwk", "x5u", "x5t",
            "x5c", "kid", "typ", "cty", "apu", "crit"]

    """
    :param msg: The message
    :param alg: Algorithm
    :param enc: Encryption Method
    :param epk: Ephemeral Public Key
    :param zip: Compression Algorithm
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
    :param kid: Key ID a hint indicating which key was used to secure the
        JWS.
    :param typ: the type of this object. 'JWS' == JWS Compact Serialization
        'JWS+JSON' == JWS JSON Serialization
    :param cty: Content Type
    :param apu: Agreement PartyUInfo
    :param crit: indicates which extensions that are being used and MUST
        be understood and processed.
    :return: A class instance
    """

    def encrypt(self, keys=None, cek="", iv="", **kwargs):
        """

        :param keys: A set of possibly usable keys
        :param context: If the other party's public or my private key should be
            used for encryption
        :param cek: Content master key
        :param iv: Initialization vector
        :param kwargs: Extra key word arguments
        :return: Encrypted message
        """

        # encrypted_key = cek = iv = None
        _alg = self["alg"]

        # Find Usable Keys
        if keys:
            keys = self.pick_keys(keys, use="enc")
        else:
            keys = self.pick_keys(self._get_keys(), use="enc")

        if not keys:
            logger.error(
                "Could not find any suitable encryption key for alg='{"
                "}'".format(
                    _alg))
            raise NoSuitableEncryptionKey(_alg)

        # Determine Encryption Class by Algorithm
        if _alg in ["RSA-OAEP", "RSA-OAEP-256", "RSA1_5"]:
            encrypter = JWE_RSA(self.msg, **self._dict)
        elif _alg.startswith("A") and _alg.endswith("KW"):
            encrypter = JWE_SYM(self.msg, **self._dict)
        elif _alg.startswith("ECDH-ES"):

            # ECDH-ES Requires the Server ECDH-ES Key to be set
            if not keys:
                raise NoSuitableECDHKey(_alg)

            encrypter = JWE_EC(**self._dict)
            cek, encrypted_key, iv, params, eprivk = encrypter.enc_setup(
                self.msg, self._dict, key=keys[0], **self._dict)
            kwargs["encrypted_key"] = encrypted_key
            kwargs["params"] = params
        else:
            logger.error("'{}' is not a supported algorithm".format(_alg))
            raise NotSupportedAlgorithm

        if cek:
            kwargs["cek"] = cek

        if iv:
            kwargs["iv"] = iv

        for key in keys:
            if isinstance(encrypter, JWE_EC):
                if self.enc:
                    _key = key.encryption_key(alg=self.enc, private=True)
                else:
                    _key = key.encryption_key(alg=_alg, private=True)
            else:
                _key = key.encryption_key(alg=_alg, private=True)

            if key.kid:
                encrypter["kid"] = key.kid

            try:
                token = encrypter.encrypt(_key, **kwargs)
                self["cek"] = encrypter.cek if 'cek' in encrypter else None
            except TypeError as err:
                raise err
            else:
                logger.debug(
                    "Encrypted message using key with kid={}".format(key.kid))
                return token

        logger.error("Could not find any suitable encryption key")
        raise NoSuitableEncryptionKey()

    def decrypt(self, token=None, keys=None, alg=None, cek=None):
        if token:
            jwe = JWEnc().unpack(token)
            # header, ek, eiv, ctxt, tag = token.split(b".")
            # self.parse_header(header)
        elif self.jwt:
            jwe = self.jwt

        _alg = jwe.headers["alg"]
        if alg and alg != _alg:
            raise WrongEncryptionAlgorithm()

        # Find appropriate keys
        if keys:
            keys = self.pick_keys(keys, use="enc", alg=_alg)
        else:
            keys = self.pick_keys(self._get_keys(), use="enc", alg=_alg)

        if not keys and not cek:
            raise NoSuitableDecryptionKey(_alg)

        if _alg in ["RSA-OAEP", "RSA-OAEP-256", "RSA1_5"]:
            decrypter = JWE_RSA(**self._dict)
        elif _alg.startswith("A") and _alg.endswith("KW"):
            decrypter = JWE_SYM(self.msg, **self._dict)
        elif _alg.startswith("ECDH-ES"):

            # ECDH-ES Requires the Server ECDH-ES Key to be set
            if not keys:
                raise NoSuitableECDHKey(_alg)

            decrypter = JWE_EC(**self._dict)
            cek = decrypter.dec_setup(jwe, key=keys[0])
        else:
            raise NotSupportedAlgorithm

        if cek:
            try:
                msg = decrypter.decrypt(jwe, None, cek=cek)
                self["cek"] = decrypter.cek if 'cek' in decrypter else None
            except (KeyError, DecryptionFailed):
                pass
            else:
                logger.debug("Decrypted message using exiting CEK")
                return msg

        for key in keys:
            _key = key.encryption_key(alg=_alg, private=False)
            try:
                msg = decrypter.decrypt(jwe, _key)
                self["cek"] = decrypter.cek if 'cek' in decrypter else None
            except (KeyError, DecryptionFailed):
                pass
            else:
                logger.debug(
                    "Decrypted message using key with kid=%s" % key.kid)
                return msg

        raise DecryptionFailed(
            "No available key that could decrypt the message")


def factory(token):
    _jwt = JWEnc().unpack(token)
    if _jwt.is_jwe():
        _jwe = JWE()
        _jwe.jwt = _jwt
        return _jwe
    else:
        return None
