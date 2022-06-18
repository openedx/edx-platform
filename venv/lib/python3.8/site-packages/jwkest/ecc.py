#!/usr/bin/env python

# pylint: disable=invalid-name

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from Cryptodome.Util.number import long_to_bytes
from Cryptodome.Util.number import bytes_to_long
from jwkest.elliptic import inv
from jwkest.elliptic import mulp
from jwkest.elliptic import sign_bit
from jwkest.elliptic import muladdp
from jwkest.elliptic import y_from_x
from jwkest.curves import get_curve
from random import getrandbits
from math import ceil


class ECCException(Exception):
    pass


# Make the EC interface more OO
class NISTEllipticCurve(object):
    def __init__(self, bits):
        # (bits, prime, order, p, q, point)
        (self.bits, self.p, self.N, self.a, self.b, self.G) = get_curve(bits)
        self.bytes = int(ceil(self.bits / 8.0))

    @staticmethod
    def by_name(name):
        if name == "P-256" or name == b'P-256':
            return NISTEllipticCurve(256)
        if name == "P-384" or name == b'P-384':
            return NISTEllipticCurve(384)
        if name == "P-521" or name == b'P-521':
            return NISTEllipticCurve(521)
        else:
            raise ECCException("Unknown curve {0}".format(name))

    # Get the name of this curve
    # XXX This only works because we only support prime curves right now
    def name(self):
        return "P-{0}".format(self.bits)

    # Integer-to-byte-string conversion
    def int2bytes(self, x):
        return long_to_bytes(x, self.bytes)

    @staticmethod
    def bytes2int(x):
        return bytes_to_long(x)

    # Point compression
    @staticmethod
    def compress(p):
        return p[0], sign_bit(p)

    def uncompress(self, p):
        return p[0], y_from_x(p[0], self.a, self.b, self.p, p[1])

    # Return a new key pair for this curve
    def key_pair(self):
        priv = (getrandbits(self.bits) % (self.N - 1)) + 1
        pub = mulp(self.a, self.b, self.p, self.G, priv)
        return priv, pub

    def public_key_for(self, priv):
        return mulp(self.a, self.b, self.p, self.G, priv)

    # Compute the DH shared secret (X coordinate) from a public key and private
    # key
    def dh_z(self, priv, pub):
        return self.int2bytes(mulp(self.a, self.b, self.p, pub, priv)[0])

    def _sign_loop(self, r, s, h, k, priv):
        while r == 0 or s == 0:
            if k is None:
                k = (getrandbits(self.bits) % (self.N - 1)) + 1
            kinv = inv(k, self.N)
            kg = mulp(self.a, self.b, self.p, self.G, k)
            r = kg[0] % self.N
            if r == 0:
                continue
            s = (kinv * (h + r * priv)) % self.N
        return r, s

    # ECDSA (adapted from ecdsa.py)
    def sign(self, h, priv, k=None):
        while h > self.N:
            h >>= 1

        r = s = 0

        r, s = self._sign_loop(r, s, h, k, priv)

        return self.int2bytes(r) + self.int2bytes(s)

    def verify(self, h, sig, pub):
        while h > self.N:
            h >>= 1
        r = self.bytes2int(sig[:self.bytes])
        s = self.bytes2int(sig[self.bytes:])
        if 0 < r < self.N and 0 < s < self.N:
            w = inv(s, self.N)
            u1 = (h * w) % self.N
            u2 = (r * w) % self.N
            x, y = muladdp(self.a, self.b, self.p, self.G, u1, pub, u2)
            return r % self.N == x % self.N
        return False


P256 = NISTEllipticCurve(256)
P384 = NISTEllipticCurve(384)
P521 = NISTEllipticCurve(521)
