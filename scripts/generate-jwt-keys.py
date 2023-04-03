#!/usr/bin/env python
# Generate public/private JWKs for asymmetric JWTs (RSA 4096).
#
# To use: Open a virtualenv, run `make requirements`, and then run this script as:
#
# ./scripts/generate-jwt-keys.py some-key-id
#
# The public and private keys will be printed to standard out.

import json
import sys
from Cryptodome.PublicKey import RSA
from jwt.algorithms import get_default_algorithms


args = sys.argv[1:]
if len(args) == 1:
    kid = args[0]
else:
    print("Call this script with an ID for the new key, e.g. lms-prod-20230403")
    exit(1)


private_rsa_key = RSA.generate(2048)
public_rsa_key = private_rsa_key.publickey()

algo = get_default_algorithms()['RS512']

def print_key(k):
    pem = k.export_key('PEM').decode()
    jwk = json.loads(algo.to_jwk(algo.prepare_key(pem)))
    jwk['kid'] = kid
    jwk_pretty = json.dumps(jwk, indent=4, sort_keys=True)
    print(jwk_pretty)

print("Public key, to add to \"keys\" list of JWT_PUBLIC_SIGNING_JWK_SET:\n")
print_key(public_rsa_key)
print("\n\n")
print("Private key, to encrypt and set as JWT_PRIVATE_SIGNING_JWK:\n")
print_key(private_rsa_key)

# private_jwk_key_dict = json.loads(private_jwk_key_str)
# public_jwk_key_dict = json.loads(public_jwk_key_str)


# ###################################
# # Storing keys in JWK JSON format #
# ###################################
# with open('keys/private_jwk_key.json', 'w') as f:
#     json.dump(private_jwk_key_dict, f, indent=4, sort_keys=True)

# with open('keys/public_jwk_key.json', 'w') as f:
#     json.dump(public_jwk_key_dict, f, indent=4, sort_keys=True)

