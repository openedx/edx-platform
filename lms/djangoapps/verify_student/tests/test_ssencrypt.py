import base64
from nose.tools import assert_equals

from verify_student.ssencrypt import (
    aes_decrypt, aes_encrypt, encrypt_and_encode, decode_and_decrypt,
    rsa_decrypt, rsa_encrypt
)


def test_aes():
    key_str = "32fe72aaf2abb44de9e161131b5435c8d37cbdb6f5df242ae860b283115f2dae"
    key = key_str.decode("hex")

    def assert_roundtrip(text):
        assert_equals(text, aes_decrypt(aes_encrypt(text, key), key))
        assert_equals(
            text,
            decode_and_decrypt(
                encrypt_and_encode(text, key),
                key
            )
        )

    assert_roundtrip("Hello World!")
    assert_roundtrip("1234567890123456")  # AES block size, padding corner case
    # Longer string
    assert_roundtrip("12345678901234561234567890123456123456789012345601")
    assert_roundtrip("")
    assert_roundtrip("\xe9\xe1a\x13\x1bT5\xc8")  # Random, non-ASCII text


def test_rsa():
    # Make up some garbage keys for testing purposes.
    pub_key_str = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1hLVjP0oV0Uy/+jQ+Upz
c+eYc4Pyflb/WpfgYATggkoQdnsdplmvPtQr85+utgqKPxOh+PvYGW8QNUzjLIu4
5/GlmvBa82i1jRMgEAxGI95bz7j9DtH+7mnj+06zR5xHwT49jK0zMs5MjMaz5WRq
BUNkz7dxWzDrYJZQx230sPp6upy1Y5H5O8SnJVdghsh8sNciS4Bo4ZONQ3giBwxz
h5svjspz1MIsOoShjbAdfG+4VX7sVwYlw2rnQeRsMH5/xpnNeqtScyOMoz0N9UDG
dtRMNGa2MihAg7zh7/zckbUrtf+o5wQtlCJL1Kdj4EjshqYvCxzWnSM+MaYAjb3M
EQIDAQAB
-----END PUBLIC KEY-----"""
    priv_key_str = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1hLVjP0oV0Uy/+jQ+Upzc+eYc4Pyflb/WpfgYATggkoQdnsd
plmvPtQr85+utgqKPxOh+PvYGW8QNUzjLIu45/GlmvBa82i1jRMgEAxGI95bz7j9
DtH+7mnj+06zR5xHwT49jK0zMs5MjMaz5WRqBUNkz7dxWzDrYJZQx230sPp6upy1
Y5H5O8SnJVdghsh8sNciS4Bo4ZONQ3giBwxzh5svjspz1MIsOoShjbAdfG+4VX7s
VwYlw2rnQeRsMH5/xpnNeqtScyOMoz0N9UDGdtRMNGa2MihAg7zh7/zckbUrtf+o
5wQtlCJL1Kdj4EjshqYvCxzWnSM+MaYAjb3MEQIDAQABAoIBAQCviuA87fdfoOoS
OerrEacc20QDLaby/QoGUtZ2RmmHzY40af7FQ3PWFIw6Ca5trrTwxnuivXnWWWG0
I2mCRM0Kvfgr1n7ubOW7WnyHTFlT3mnxK2Ov/HmNLZ36nO2cgkXA6/Xy3rBGMC9L
nUE1kSLzT/Fh965ntfS9zmVNNBhb6no0rVkGx5nK3vTI6kUmaa0m+E7KL/HweO4c
JodhN8CX4gpxSrkuwJ7IHEPYspqc0jInMYKLmD3d2g3BiOctjzFmaj3lV5AUlujW
z7/LVe5WAEaaxjwaMvwqrJLv9ogxWU3etJf22+Yy7r5gbPtqpqJrCZ5+WpGnUHws
3mMGP2QBAoGBAOc3pzLFgGUREVPSFQlJ06QFtfKYqg9fFHJCgWu/2B2aVZc2aO/t
Zhuoz+AgOdzsw+CWv7K0FH9sUkffk2VKPzwwwufLK3avD9gI0bhmBAYvdhS6A3nO
YM3W+lvmaJtFL00K6kdd+CzgRnBS9cZ70WbcbtqjdXI6+mV1WdGUTLhBAoGBAO0E
xhD4z+GjubSgfHYEZPgRJPqyUIfDH+5UmFGpr6zlvNN/depaGxsbhW8t/V6xkxsG
MCgic7GLMihEiUMx1+/snVs5bBUx7OT9API0d+vStHCFlTTe6aTdmiduFD4PbDsq
6E4DElVRqZhpIYusdDh7Z3fO2hm5ad4FfMlx65/RAoGAPYEfV7ETs06z9kEG2X6q
7pGaUZrsecRH8xDfzmKswUshg2S0y0WyCJ+CFFNeMPdGL4LKIWYnobGVvYqqcaIr
af5qijAQMrTkmQnXh56TaXXMijzk2czdEUQjOrjykIL5zxudMDi94GoUMqLOv+qF
zD/MuRoMDsPDgaOSrd4t/kECgYEAzwBNT8NOIz3P0Z4cNSJPYIvwpPaY+IkE2SyO
vzuYj0Mx7/Ew9ZTueXVGyzv6PfqOhJqZ8mNscZIlIyAAVWwxsHwRTfvPlo882xzP
97i1R4OFTYSNNFi+69sSZ/9utGjZ2K73pjJuj487tD2VK5xZAH9edTd2KeNSP7LB
MlpJNBECgYAmIswPdldm+G8SJd5j9O2fcDVTURjKAoSXCv2j4gEZzzfudpLWNHYu
l8N6+LEIVTMAytPk+/bImHvGHKZkCz5rEMSuYJWOmqKI92rUtI6fz5DUb3XSbrwT
3W+sdGFUK3GH1NAX71VxbAlFVLUetcMwai1+wXmGkRw6A7YezVFnhw==
-----END RSA PRIVATE KEY-----"""
    aes_key_str = "32fe72aaf2abb44de9e161131b5435c8d37cbdb6f5df242ae860b283115f2dae"

    aes_key = aes_key_str.decode('hex')

    encrypted_aes_key = rsa_encrypt(aes_key, pub_key_str)
    assert_equals(aes_key, rsa_decrypt(encrypted_aes_key, priv_key_str))

    # Even though our AES key is only 32 bytes, RSA encryption will make it 256
    # bytes, and base64 encoding will blow that up to 344
    assert_equals(len(base64.urlsafe_b64encode(encrypted_aes_key)), 344)
