from __future__ import division

from jwkest.jws import JWSException

try:
    from builtins import bytes
except ImportError:
    pass
#from past.utils import old_div
from math import ceil
from struct import pack, unpack
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHA256
from Cryptodome.Hash import SHA384
from Cryptodome.Hash import SHA512
from Cryptodome.Hash import HMAC


LENMET = {
    32: (16, SHA256),
    48: (24, SHA384),
    64: (32, SHA512)
}


class VerificationFailure(JWSException):
    pass



# PKCS#5 padding, since it's not in PyCrypto
def pkcs5pad(x):
    """
    Add PKCS#5 padding to an octet string

    :type  x: bytes
    :rtype: bytes
    """
    n = 16 - len(x) % 16
    if n == 0:
        n = 16
    ns = pack('B', n)
    return x + (ns * n)


def pkcs5trim(x):
    """
    Trim PKCS#5 padding from an octet string

    :type  x: bytes
    :rtype: bytes
    """
    n = unpack('B', x[-1:])[0]
    # Should never have more than 16 bytes of padding
    # ... since we're only using this with AES
    if n > 16:
        raise Exception("Mal-formed PKCS#5 padding")
    return x[:-n]


def get_keys_seclen_dgst(key, iv):
    # Validate input
    if len(iv) != 16:
        raise Exception("IV for AES-CBC must be 16 octets long")

    # Select the digest to use based on key length
    try:
        seclen, dgst = LENMET[len(key)]
    except KeyError:
        raise Exception("Invalid CBC+HMAC key length: %s bytes" % len(key))

    # Split the key
    ka = key[:seclen]
    ke = key[seclen:]

    return ka, ke, seclen, dgst


def aes_cbc_hmac_encrypt(key, iv, aad, pt):
    """
    Perform authenticated encryption with the combined AES-CBC
    and HMAC algorithm.

    :param key: key; length MUST be 32, 48, or 64 octets
    :param iv: Initialization vector; length MUST be 16 octets
    :param aad: Additional authenticated data
    :param pt: Plaintext
    :return: (ciphertext, tag) tuple, with each as bytes
    """

    ka, ke, seclen, dgst = get_keys_seclen_dgst(key, iv)

    # Encrypt
    cipher = AES.new(ke, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pkcs5pad(pt))

    # MAC A || IV || E || AL
    al = pack("!Q", 8*len(aad))
    mac_input = aad + iv + ct + al
    h = HMAC.new(ka, digestmod=dgst)
    h.update(mac_input)
    tag = h.digest()[:seclen]
    return ct, tag


def aes_cbc_hmac_decrypt(key, iv, aad, ct, tag):
    """
    Perform authenticated decryption with the combined AES-CBC
    and HMAC algorithm.

    :param key  : Key; length MUST be 32, 48, or 64 octets
    :param iv : Initialization vector; length MUST be 16 octets
    :param aad: Additional authenticated data
    :param ct : Cipher text
    :param tag: Authentication tag
    :return: (plaintext, result) tuple, with plaintext as bytes
      and result as boolean
    """

    ka, ke, seclen, dgst = get_keys_seclen_dgst(key, iv)

    # Verify A || IV || E || AL
    al = pack("!Q", 8*len(aad))
    if isinstance(aad, str):
        aad = aad.encode("utf-8")
    mac_input = aad + iv + ct + al
    h = HMAC.new(ka, digestmod=dgst)
    h.update(mac_input)
    candidate = h.digest()[:seclen]

    # Decrypt if verified
    if candidate == tag:
        cipher = AES.new(ke, AES.MODE_CBC, iv)
        pt = pkcs5trim(cipher.decrypt(ct))
        return pt
    else:
        raise VerificationFailure('AES-CBC HMAC')
    

def concat_sha256(secret, dk_len, other_info):
    """
    The Concat KDF, using SHA256 as the hash function.  

    Note: Does not validate that otherInfo meets the requirements of 
    SP800-56A.

    :param secret: The shared secret value
    :param dk_len: Length of key to be derived, in bits
    :param other_info: Other info to be incorporated (see SP800-56A)
    :return: The derived key
    """
    dkm = b''
    dk_bytes = int(ceil(dk_len / 8.0))
    counter = 0
    while len(dkm) < dk_bytes:
        counter += 1
        counter_bytes = pack("!I", counter)
        dkm += SHA256.new(counter_bytes + secret + other_info ).digest()
    return dkm[:dk_bytes]


def ecdh_derive_key(curve, key, epk, apu, apv, alg, dk_len):
    """
    ECDH key derivation, as defined by JWA
    
    :param curve: Curve to be used for EC computations
    :param key  : Elliptic curve private key
    :param epk  : Elliptic curve public key (long, long)
    :param apu  : PartyUInfo
    :param apv  : PartyVInfo
    :param alg  : Algorithm identifier
    :param dk_len: Length of key to be derived, in bits
    :return: The derived key
    """
    # Compute shared secret 
    Z = curve.dh_z(key, epk)
    # Derive the key
    # AlgorithmID || PartyUInfo || PartyVInfo || SuppPubInfo
    otherInfo = bytes(alg) + \
        pack("!I", len(apu)) + apu + \
        pack("!I", len(apv)) + apv + \
        pack("!I", dk_len)
    return concat_sha256(Z, dk_len, otherInfo)
