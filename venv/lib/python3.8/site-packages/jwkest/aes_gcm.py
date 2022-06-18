#!/usr/bin/env python

"""
    Copyright (C) 2013 Bo Zhu http://about.bozhu.me

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
"""
from __future__ import print_function
from __future__ import division

try:
    from builtins import str
    from builtins import hex
    from builtins import range
    from builtins import object
except ImportError:
    pass
# from past.utils import old_div

from Cryptodome.Cipher import AES
from Cryptodome.Util import Counter
from Cryptodome.Util.number import bytes_to_long
from Cryptodome.Util.number import long_to_bytes


# GF(2^128) defined by 1 + a + a^2 + a^7 + a^128
# Please note the MSB is x0 and LSB is x127
def gf_2_128_mul(x, y):
    assert x < (1 << 128)
    assert y < (1 << 128)
    res = 0
    for i in range(127, -1, -1):
        res ^= x * ((y >> i) & 1)  # branchless
        x = (x >> 1) ^ ((x & 1) * 0xE1000000000000000000000000000000)
    assert res < 1 << 128
    return res


class InvalidInputException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class InvalidTagException(Exception):
    def __str__(self):
        return 'The authenticaiton tag is invalid.'


# Galois/Counter Mode with AES-128 and 96-bit IV
class AES_GCM(object):
    def __init__(self, master_key):
        self.prev_init_value = None
        self._master_key = ""
        self._aes_ecb = None
        self._auth_key = 0
        self._pre_table = None
        self.change_key(master_key)

    def change_key(self, master_key):
        # RLB: Need to allow 192-, 256-bit keys
        # if master_key >= (1 << 128):
        #    raise InvalidInputException('Master key should be 128-bit')

        self._master_key = long_to_bytes(master_key, 16)
        self._aes_ecb = AES.new(self._master_key, AES.MODE_ECB)
        self._auth_key = bytes_to_long(self._aes_ecb.encrypt(b'\x00' * 16))

        # precompute the table for multiplication in finite field
        table = []  # for 8-bit
        for i in range(16):
            row = []
            for j in range(256):
                row.append(gf_2_128_mul(self._auth_key, j << (8 * i)))
            table.append(tuple(row))
        self._pre_table = tuple(table)

        self.prev_init_value = None  # reset

    def __times_auth_key(self, val):
        res = 0
        for i in range(16):
            res ^= self._pre_table[i][val & 0xFF]
            val >>= 8
        return res

    def __ghash(self, aad, txt):
        len_aad = len(aad)
        len_txt = len(txt)

        # padding
        if 0 == len_aad % 16:
            data = aad
        else:
            data = aad + b'\x00' * (16 - len_aad % 16)
        if 0 == len_txt % 16:
            data += txt
        else:
            data += txt + b'\x00' * (16 - len_txt % 16)

        tag = 0
        assert len(data) % 16 == 0
        for i in range(int(len(data) / 16)):
            tag ^= bytes_to_long(data[i * 16: (i + 1) * 16])
            tag = self.__times_auth_key(tag)
            # print 'X\t', hex(tag)
        tag ^= ((8 * len_aad) << 64) | (8 * len_txt)
        tag = self.__times_auth_key(tag)

        return tag

    def encrypt(self, init_value, plaintext, auth_data=b''):
        if init_value >= (1 << 96):
            raise InvalidInputException('IV should be 96-bit')
        # a naive checking for IV reuse
        if init_value == self.prev_init_value:
            raise InvalidInputException('IV must not be reused!')
        self.prev_init_value = init_value

        len_plaintext = len(plaintext)
        # len_auth_data = len(auth_data)

        if len_plaintext > 0:
            counter = Counter.new(
                nbits=32,
                prefix=long_to_bytes(init_value, 12),
                initial_value=2,  # notice this
                allow_wraparound=True)
            aes_ctr = AES.new(self._master_key, AES.MODE_CTR, counter=counter)

            if 0 != len_plaintext % 16:
                padded_plaintext = plaintext + \
                                   b'\x00' * (16 - len_plaintext % 16)
            else:
                padded_plaintext = plaintext
            ciphertext = aes_ctr.encrypt(padded_plaintext)[:len_plaintext]

        else:
            ciphertext = b''

        auth_tag = self.__ghash(auth_data, ciphertext)
        # print 'GHASH\t', hex(auth_tag)
        auth_tag ^= bytes_to_long(self._aes_ecb.encrypt(
            long_to_bytes((init_value << 32) | 1, 16)))

        # assert len(ciphertext) == len(plaintext)
        assert auth_tag < (1 << 128)
        return ciphertext, auth_tag

    def decrypt(self, init_value, ciphertext, auth_tag, auth_data=b''):
        if init_value >= (1 << 96):
            raise InvalidInputException('IV should be 96-bit')
        if auth_tag >= (1 << 128):
            raise InvalidInputException('Tag should be 128-bit')

        if auth_tag != self.__ghash(
                auth_data, ciphertext) ^ bytes_to_long(
            self._aes_ecb.encrypt(
                long_to_bytes((init_value << 32) | 1, 16))):
            raise InvalidTagException

        len_ciphertext = len(ciphertext)
        if len_ciphertext > 0:
            counter = Counter.new(
                nbits=32,
                prefix=long_to_bytes(init_value, 12),
                initial_value=2,
                allow_wraparound=True)
            aes_ctr = AES.new(self._master_key, AES.MODE_CTR, counter=counter)

            if 0 != len_ciphertext % 16:
                padded_ciphertext = ciphertext + \
                                    b'\x00' * (16 - len_ciphertext % 16)
            else:
                padded_ciphertext = ciphertext
            plaintext = aes_ctr.decrypt(padded_ciphertext)[:len_ciphertext]

        else:
            plaintext = b''

        return plaintext


if __name__ == '__main__':
    master_key = 0xfeffe9928665731c6d6a8f9467308308
    plaintext = b'\xd9\x31\x32\x25\xf8\x84\x06\xe5' + \
                b'\xa5\x59\x09\xc5\xaf\xf5\x26\x9a' + \
                b'\x86\xa7\xa9\x53\x15\x34\xf7\xda' + \
                b'\x2e\x4c\x30\x3d\x8a\x31\x8a\x72' + \
                b'\x1c\x3c\x0c\x95\x95\x68\x09\x53' + \
                b'\x2f\xcf\x0e\x24\x49\xa6\xb5\x25' + \
                b'\xb1\x6a\xed\xf5\xaa\x0d\xe6\x57' + \
                b'\xba\x63\x7b\x39'
    auth_data = b'\xfe\xed\xfa\xce\xde\xad\xbe\xef' + \
                b'\xfe\xed\xfa\xce\xde\xad\xbe\xef' + \
                b'\xab\xad\xda\xd2'
    init_value = 0xcafebabefacedbaddecaf888
    ciphertext = b'\x42\x83\x1e\xc2\x21\x77\x74\x24' + \
                 b'\x4b\x72\x21\xb7\x84\xd0\xd4\x9c' + \
                 b'\xe3\xaa\x21\x2f\x2c\x02\xa4\xe0' + \
                 b'\x35\xc1\x7e\x23\x29\xac\xa1\x2e' + \
                 b'\x21\xd5\x14\xb2\x54\x66\x93\x1c' + \
                 b'\x7d\x8f\x6a\x5a\xac\x84\xaa\x05' + \
                 b'\x1b\xa3\x0b\x39\x6a\x0a\xac\x97' + \
                 b'\x3d\x58\xe0\x91'
    auth_tag = 0x5bc94fbc3221a5db94fae95ae7121a47

    print('plaintext:', hex(bytes_to_long(plaintext)))

    my_gcm = AES_GCM(master_key)
    encrypted, new_tag = my_gcm.encrypt(init_value, plaintext, auth_data)
    print('encrypted:', hex(bytes_to_long(encrypted)))
    print('auth tag: ', hex(new_tag))

    try:
        decrypted = my_gcm.decrypt(init_value, encrypted, new_tag + 1,
                                   auth_data)
    except InvalidTagException:
        decrypted = my_gcm.decrypt(init_value, encrypted, new_tag, auth_data)
        print('decrypted:', hex(bytes_to_long(decrypted)))
