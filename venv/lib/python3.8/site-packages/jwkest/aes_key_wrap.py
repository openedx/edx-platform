"""
Key wrapping and unwrapping as defined in RFC 3394.
Also a padding mechanism that was used in openssl at one time.  
The purpose of this algorithm is to encrypt a key multiple times to add an
extra layer of security.
 
Personally, I wouldn't recommend using this for most applications.  
Just use AES/mode CTR to encrypt your keys, the same as you would any other
data.
The time to use this code is when you need compatibility with another system
that implements the RFC.
(For example, these functions are compatible with the openssl functions of
the same name.)
 
Performance should be reasonable, since the heavy lifting is all done in
PyCrypto's AES.
"""
from __future__ import division

try:
    from builtins import hex
    from builtins import range
except ImportError:
    pass

import struct
from Cryptodome.Cipher.AES import MODE_ECB
from Cryptodome.Cipher import AES

QUAD = struct.Struct('>Q')


def aes_unwrap_key_and_iv(kek, wrapped, mode=MODE_ECB):
    n = (len(wrapped) // 8) - 1
    #NOTE: R[0] is never accessed, left in for consistency with RFC indices
    r = [None] + [wrapped[i * 8:i * 8 + 8] for i in range(1, n + 1)]
    a = QUAD.unpack(wrapped[:8])[0]
    decrypt = AES.new(kek, mode).decrypt
    for j in range(5, -1, -1):  #counting down
        for i in range(n, 0, -1):  #(n, n-1, ..., 1)
            ciphertext = QUAD.pack(a ^ (n * j + i)) + r[i]
            B = decrypt(ciphertext)
            a = QUAD.unpack(B[:8])[0]
            r[i] = B[8:]
    return b"".join(r[1:]), a


def aes_unwrap_key(kek, wrapped, iv=0xa6a6a6a6a6a6a6a6):
    key, key_iv = aes_unwrap_key_and_iv(kek, wrapped)
    if key_iv != iv:
        raise ValueError(
            "Integrity Check Failed: " + hex(key_iv) + " (expected " + hex(
                iv) + ")")
    return key


def aes_unwrap_key_withpad(kek, wrapped):
    key, key_iv = aes_unwrap_key_and_iv(kek, wrapped)
    key_iv = "{0:016X}".format(key_iv)
    if key_iv[:8] != "A65959A6":
        raise ValueError(
            "Integrity Check Failed: " + key_iv[:8] + " (expected A65959A6)")
    key_len = int(key_iv[8:], 16)
    return key[:key_len]


def aes_wrap_key(kek, plaintext, iv=0xa6a6a6a6a6a6a6a6, mode=MODE_ECB):
    n = len(plaintext) // 8
    r = [None] + [plaintext[i * 8:i * 8 + 8] for i in range(0, n)]
    a = iv
    encrypt = AES.new(kek, mode).encrypt
    for j in range(6):
        for i in range(1, n + 1):
            b = encrypt(QUAD.pack(a) + r[i])
            a = QUAD.unpack(b[:8])[0] ^ (n * j + i)
            r[i] = b[8:]
    return QUAD.pack(a) + b''.join(r[1:])


def aes_wrap_key_withpad(kek, plaintext):
    iv = 0xA65959A600000000 + len(plaintext)
    plaintext += "\0" * (8 - len(plaintext) % 8)
    return aes_wrap_key(kek, plaintext, iv)


def test():
    #test vector from RFC 3394
    import binascii

    KEK = binascii.unhexlify("000102030405060708090A0B0C0D0E0F")
    CIPHER = binascii.unhexlify(
        "1FA68B0A8112B447AEF34BD8FB5A7B829D3E862371D2CFE5")
    PLAIN = binascii.unhexlify("00112233445566778899AABBCCDDEEFF")
    assert aes_unwrap_key(KEK, CIPHER) == PLAIN
    assert aes_wrap_key(KEK, PLAIN) == CIPHER
