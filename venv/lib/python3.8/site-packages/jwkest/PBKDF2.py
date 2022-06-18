#!/usr/bin/python
# -*- coding: ascii -*-
###########################################################################
# PBKDF2.py - PKCS#5 v2.0 Password-Based Key Derivation
#
# Copyright (C) 2007, 2008 Dwayne C. Litzenberger <dlitz@dlitz.net>
# All rights reserved.
# 
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation.
# 
# THE AUTHOR PROVIDES THIS SOFTWARE ``AS IS'' AND ANY EXPRESSED OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, 
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY 
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Country of origin: Canada
#
###########################################################################
# Sample PBKDF2 usage:
#   from Crypto.Cipher import AES
#   from PBKDF2 import PBKDF2
#   import os
#
#   salt = os.urandom(8)    # 64-bit salt
#   key = PBKDF2("This passphrase is a secret.", salt).read(32) # 256-bit key
#   iv = os.urandom(16)     # 128-bit IV
#   cipher = AES.new(key, AES.MODE_CBC, iv)
#     ...
#
# Sample crypt() usage:
#   from PBKDF2 import crypt
#   pwhash = crypt("secret")
#   alleged_pw = raw_input("Enter password: ")
#   if pwhash == crypt(alleged_pw, pwhash):
#       print "Password good"
#   else:
#       print "Invalid password"
#
###########################################################################
# History:
#
#  2007-07-27 Dwayne C. Litzenberger <dlitz@dlitz.net>
#   - Initial Release (v1.0)
#
#  2007-07-31 Dwayne C. Litzenberger <dlitz@dlitz.net>
#   - Bugfix release (v1.1)
#   - SECURITY: The PyCrypto XOR cipher (used, if available, in the _strxor
#   function in the previous release) silently truncates all keys to 64
#   bytes.  The way it was used in the previous release, this would only be
#   problem if the pseudorandom function that returned values larger than
#   64 bytes (so SHA1, SHA256 and SHA512 are fine), but I don't like
#   anything that silently reduces the security margin from what is
#   expected.
#  
# 2008-06-17 Dwayne C. Litzenberger <dlitz@dlitz.net>
#   - Compatibility release (v1.2)
#   - Add support for older versions of Python (2.2 and 2.3).
#
###########################################################################

__version__ = "1.2"

from builtins import chr
from builtins import zip
from builtins import range
from builtins import object

import string
from struct import pack
from binascii import b2a_hex
from random import randint

try:
    # Use PyCryptoDome (if available)
    from Cryptodome.Hash import HMAC
    from Cryptodome.Hash import SHA as SHA1
except ImportError:
    # PyCrypto not available.  Use the Python standard library.
    import hmac as HMAC
    import sha as SHA1

def strxor(a, b):
    return "".join([chr(ord(x) ^ ord(y)) for (x, y) in zip(a, b)])

def b64encode(data, chars="+/"):
    tt = string.maketrans("+/", chars)
    return data.encode('base64').replace("\n", "").translate(tt)

class PBKDF2(object):
    """PBKDF2.py : PKCS#5 v2.0 Password-Based Key Derivation
    
    This implementation takes a passphrase and a salt (and optionally an
    iteration count, a digest module, and a MAC module) and provides a
    file-like object from which an arbitrarily-sized key can be read.

    If the passphrase and/or salt are unicode objects, they are encoded as
    UTF-8 before they are processed.

    The idea behind PBKDF2 is to derive a cryptographic key from a
    passphrase and a salt.
    
    PBKDF2 may also be used as a strong salted password hash.  The
    'crypt' function is provided for that purpose.
    
    Remember: Keys generated using PBKDF2 are only as strong as the
    passphrases they are derived from.
    """

    def __init__(self, passphrase, salt, iterations=1000,
                 digestmodule=SHA1, macmodule=HMAC):
        self.__macmodule = macmodule
        self.__digestmodule = digestmodule
        self._setup(passphrase, salt, iterations, self._pseudorandom)

    def _pseudorandom(self, key, msg):
        """Pseudorandom function.  e.g. HMAC-SHA1"""
        return self.__macmodule.new(key=key, msg=msg,
            digestmod=self.__digestmodule).digest()
    
    def read(self, bytes):
        """Read the specified number of key bytes."""
        if self.closed:
            raise ValueError("file-like object is closed")

        size = len(self.__buf)
        blocks = [self.__buf]
        i = self.__blockNum
        while size < bytes:
            i += 1
            if i > 0xffffffff or i < 1:
                # We could return "" here, but 
                raise OverflowError("derived key too long")
            block = self.__f(i)
            blocks.append(block)
            size += len(block)
        buf = "".join(blocks)
        retval = buf[:bytes]
        self.__buf = buf[bytes:]
        self.__blockNum = i
        return retval
    
    def __f(self, i):
        # i must fit within 32 bits
        assert 1 <= i <= 0xffffffff
        U = self.__prf(self.__passphrase, self.__salt + pack("!L", i))
        result = U
        for j in range(2, 1+self.__iterations):
            U = self.__prf(self.__passphrase, U)
            result = strxor(result, U)
        return result
    
    def hexread(self, octets):
        """Read the specified number of octets. Return them as hexadecimal.

        Note that len(obj.hexread(n)) == 2*n.
        """
        return b2a_hex(self.read(octets))

    def _setup(self, passphrase, salt, iterations, prf):
        # Sanity checks:
        
        # passphrase and salt must be str or unicode (in the latter
        # case, we convert to UTF-8)
        if isinstance(passphrase, str):
            passphrase = passphrase.encode("UTF-8")
        if not isinstance(passphrase, str):
            raise TypeError("passphrase must be str or unicode")
        if isinstance(salt, str):
            salt = salt.encode("UTF-8")
        if not isinstance(salt, str):
            raise TypeError("salt must be str or unicode")

        # iterations must be an integer >= 1
        if not isinstance(iterations, (int, int)):
            raise TypeError("iterations must be an integer")
        if iterations < 1:
            raise ValueError("iterations must be at least 1")
        
        # prf must be callable
        if not callable(prf):
            raise TypeError("prf must be callable")

        self.__passphrase = passphrase
        self.__salt = salt
        self.__iterations = iterations
        self.__prf = prf
        self.__blockNum = 0
        self.__buf = ""
        self.closed = False
    
    def close(self):
        """Close the stream."""
        if not self.closed:
            del self.__passphrase
            del self.__salt
            del self.__iterations
            del self.__prf
            del self.__blockNum
            del self.__buf
            self.closed = True

def crypt(word, salt=None, iterations=None):
    """PBKDF2-based unix crypt(3) replacement.
    
    The number of iterations specified in the salt overrides the 'iterations'
    parameter.

    The effective hash length is 192 bits.
    """
    
    # Generate a (pseudo-)random salt if the user hasn't provided one.
    if salt is None:
        salt = _makesalt()

    # salt must be a string or the us-ascii subset of unicode
    if isinstance(salt, str):
        salt = salt.encode("us-ascii")
    if not isinstance(salt, str):
        raise TypeError("salt must be a string")

    # word must be a string or unicode (in the latter case, we convert to UTF-8)
    if isinstance(word, str):
        word = word.encode("UTF-8")
    if not isinstance(word, str):
        raise TypeError("word must be a string or unicode")

    # Try to extract the real salt and iteration count from the salt
    if salt.startswith("$p5k2$"):
        (iterations, salt, dummy) = salt.split("$")[2:5]
        if iterations == "":
            iterations = 400
        else:
            converted = int(iterations, 16)
            if iterations != "%x" % converted:  # lowercase hex, minimum digits
                raise ValueError("Invalid salt")
            iterations = converted
            if not (iterations >= 1):
                raise ValueError("Invalid salt")
    
    # Make sure the salt matches the allowed character set
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./"
    for ch in salt:
        if ch not in allowed:
            raise ValueError("Illegal character %r in salt" % (ch,))

    if iterations is None or iterations == 400:
        iterations = 400
        salt = "$p5k2$$" + salt
    else:
        salt = "$p5k2$%x$%s" % (iterations, salt)
    rawhash = PBKDF2(word, salt, iterations).read(24)
    return salt + "$" + b64encode(rawhash, "./")

# Add crypt as a static method of the PBKDF2 class
# This makes it easier to do "from PBKDF2 import PBKDF2" and still use
# crypt.
PBKDF2.crypt = staticmethod(crypt)

def _makesalt():
    """Return a 48-bit pseudorandom salt for crypt().
    
    This function is not suitable for generating cryptographic secrets.
    """
    binarysalt = "".join([pack("@H", randint(0, 0xffff)) for i in range(3)])
    return b64encode(binarysalt, "./")

def test_pbkdf2():
    """Module self-test"""
    from binascii import a2b_hex
    
    #
    # Test vectors from RFC 3962
    #

    # Test 1
    result = PBKDF2("password", "ATHENA.MIT.EDUraeburn", 1).read(16)
    expected = a2b_hex("cdedb5281bb2f801565a1122b2563515")
    if result != expected:
        raise RuntimeError("self-test failed")

    # Test 2
    result = PBKDF2("password", "ATHENA.MIT.EDUraeburn", 1200).hexread(32)
    expected = ("5c08eb61fdf71e4e4ec3cf6ba1f5512b"
                "a7e52ddbc5e5142f708a31e2e62b1e13")
    if result != expected:
        raise RuntimeError("self-test failed")

    # Test 3
    result = PBKDF2("X"*64, "pass phrase equals block size", 1200).hexread(32)
    expected = ("139c30c0966bc32ba55fdbf212530ac9"
                "c5ec59f1a452f5cc9ad940fea0598ed1")
    if result != expected:
        raise RuntimeError("self-test failed")
    
    # Test 4
    result = PBKDF2("X"*65, "pass phrase exceeds block size", 1200).hexread(32)
    expected = ("9ccad6d468770cd51b10e6a68721be61"
                "1a8b4d282601db3b36be9246915ec82a")
    if result != expected:
        raise RuntimeError("self-test failed")
    
    #
    # Other test vectors
    #
    
    # Chunked read
    f = PBKDF2("kickstart", "workbench", 256)
    result = f.read(17)
    result += f.read(17)
    result += f.read(1)
    result += f.read(2)
    result += f.read(3)
    expected = PBKDF2("kickstart", "workbench", 256).read(40)
    if result != expected:
        raise RuntimeError("self-test failed")
    
    #
    # crypt() test vectors
    #

    # crypt 1
    result = crypt("cloadm", "exec")
    expected = '$p5k2$$exec$r1EWMCMk7Rlv3L/RNcFXviDefYa0hlql'
    if result != expected:
        raise RuntimeError("self-test failed")
    
    # crypt 2
    result = crypt("gnu", '$p5k2$c$u9HvcT4d$.....')
    expected = '$p5k2$c$u9HvcT4d$Sd1gwSVCLZYAuqZ25piRnbBEoAesaa/g'
    if result != expected:
        raise RuntimeError("self-test failed")

    # crypt 3
    result = crypt("dcl", "tUsch7fU", iterations=13)
    expected = "$p5k2$d$tUsch7fU$nqDkaxMDOFBeJsTSfABsyn.PYUXilHwL"
    if result != expected:
        raise RuntimeError("self-test failed")
    
    # crypt 4 (unicode)
    result = crypt(u'\u0399\u03c9\u03b1\u03bd\u03bd\u03b7\u03c2',
        '$p5k2$$KosHgqNo$9mjN8gqjt02hDoP0c2J0ABtLIwtot8cQ')
    expected = '$p5k2$$KosHgqNo$9mjN8gqjt02hDoP0c2J0ABtLIwtot8cQ'
    if result != expected:
        raise RuntimeError("self-test failed")

if __name__ == '__main__':
    test_pbkdf2()

# vim:set ts=4 sw=4 sts=4 expandtab:
