from Cryptodome.PublicKey.RSA import RsaKey

from Cryptodome.Signature.pkcs1_15 import PKCS115_SigScheme


def new(rsa_key: RsaKey) -> PKCS115_SigScheme: ...