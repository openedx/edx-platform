""" Utils for RSA keys"""
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import(
    Encoding, PublicFormat, PrivateFormat, NoEncryption
)


def generate_rsa_key_pair(key_size=2048):
    """ Generates a public and private RSA PEM encoded key pair"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    private_key_str = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    public_key_str = private_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    #  Not intented for programmatic use, so we print the keys out
    print public_key_str
    print private_key_str
