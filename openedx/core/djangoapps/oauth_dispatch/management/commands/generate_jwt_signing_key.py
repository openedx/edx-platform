"""
Management command for generating an asymmetric keypair to sign JSON Web Tokens.
"""
# pylint: disable=missing-docstring
from __future__ import print_function, unicode_literals

import logging
import json
import random
import string

from argparse import RawTextHelpFormatter
from django.conf import settings
from django.core.management.base import BaseCommand

from Cryptodome.PublicKey import RSA
from jwkest import jwk


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Generates an asymmetric keypair to sign JSON Web Tokens."""
    help = '''
    Generates an asymmetric keypair to sign JSON Web Tokens. Outputs the
    generated public and private keys in YAML format as required by Open edX
    configuration settings.

    This same command can be used over time to rotate keys. Simply rerun this
    command and public keys configured in the past will be automatically
    included in the JWK keyset in the YAML output (unless the option
    not-add-previous-public-keys is provided).

    New keys are identified by a "kid" value that is automatically generated of
    length 'key-id-size' (unless you explicitly provide a "kid" of your own via
    the 'key-id' option).

    See https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0008-use-asymmetric-jwts.rst
    '''

    def create_parser(self, *args, **kwargs):  # pylint: disable=arguments-differ
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser

    def add_arguments(self, parser):
        parser.add_argument(
            '--key-size',
            action='store',
            dest='key_size',
            default=2048,
            type=int,
            help='Size of RSA key, in bits; defaults to 2048',
        )

        parser.add_argument(
            '--add-previous-public-keys',
            action='store_true',
            dest='add_previous_public_keys',
            default=True,
            help='Whether to add the previous set of public keys to the new public key set',
        )
        parser.add_argument(
            '--not-add-previous-public-keys',
            action='store_false',
            dest='add_previous_public_keys',
            help='Whether to NOT add the previous set of public keys to the new public key set',
        )

        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--key-id',
            action='store',
            dest='key_id',
            help='Unique identifier ("kid") of new key; defaults to a random value',
        )
        group.add_argument(
            '--key-id-size',
            action='store',
            dest='key_id_size',
            default=8,
            type=int,
            help='Size of randomly generated unique identifier ("kid") of the new key; defaults to 8',
        )

    def handle(self, *args, **options):
        jwk_key = self._generate_key_pair(
            options['key_size'],
            options['key_id'] or self._generate_key_id(options['key_id_size']),
        )
        self._output_public_keys(jwk_key, options['add_previous_public_keys'])
        self._output_private_keys(jwk_key)

    def _generate_key_id(self, size, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def _generate_key_pair(self, key_size, key_id):
        log.info('Generating new JWT signing keypair for key id %s.', key_id)
        rsa_key = RSA.generate(key_size)
        rsa_jwk = jwk.RSAKey(kid=key_id, key=rsa_key)
        return rsa_jwk

    def _output_public_keys(self, jwk_key, add_previous):
        public_keys = jwk.KEYS()
        if add_previous:
            self._add_previous_public_keys(public_keys)
        public_keys.append(jwk_key)
        serialized_public_keys = public_keys.dump_jwks()

        log.info('New JWT_PUBLIC_SIGNING_JWK_SET: %s.', serialized_public_keys)
        print("  ")
        print("  ")
        print("  *** YAML to share with ALL IDAs ***")
        print("  ")
        print("  # The following is the string representation of a JSON Web Key Set (JWK set)")
        print("  # containing all active public keys for verifying JWT signatures.")
        print(
            "  # See https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/"
            "docs/decisions/0008-use-asymmetric-jwts.rst"
        )
        print("  ")
        print("  COMMON_JWT_PUBLIC_SIGNING_JWK_SET: '{}'".format(serialized_public_keys))

    def _add_previous_public_keys(self, public_keys):
        previous_signing_keys = settings.JWT_AUTH.get('JWT_PUBLIC_SIGNING_JWK_SET')
        if previous_signing_keys:
            log.info('Old JWT_PUBLIC_SIGNING_JWK_SET: %s.', previous_signing_keys)
            public_keys.load_jwks(previous_signing_keys)

    def _output_private_keys(self, jwk_key):
        serialized_keypair = jwk_key.serialize(private=True)
        serialized_keypair_json = json.dumps(serialized_keypair)
        print("  ")
        print("  ")
        print("  *** YAML to keep PRIVATE within a single authentication service (LMS) ***")
        print("  ")
        print("  # The following is the string representation of a JSON Web Key (JWK)")
        print("  # containing the single active private key for signing JSON Web Tokens (JWTs).")
        print(
            "  # See https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/"
            "docs/decisions/0008-use-asymmetric-jwts.rst"
        )
        print("  ")
        print("  EDXAPP_JWT_PRIVATE_SIGNING_JWK: '{}'".format(serialized_keypair_json))
        print("  ")
        print("  EDXAPP_JWT_SIGNING_ALGORITHM: 'RS512'")
