"""
Utilities for logging sensitive information.
"""

from base64 import b64decode, b64encode

import click
from nacl.public import Box, PrivateKey, PublicKey

# Background:
#
# The NaCl "Box" construction provides asymmetric encryption, allowing
# the sender to encrypt something for a recipient without having a
# shared secret. This encryption is authenticated, meaning that the
# recipient verifies that the message matches the sender's public key
# (proof of sender). But it's also *repudiable* authentication; the
# design allows both the sender and the receiver to read (or have
# created!) the encrypted message, so the receipient can't prove to
# anyone *else* that the sender was the author.
#
# Why we use ephemeral sender keys:
#
# The Box is normally an ideal construction to use for
# communications. However, we don't want the logger to be able to read
# the messages it writes, especially not messages from a different
# server instance or from days or weeks ago. Only developers (or
# others) in possession of the recipient keypair should be able to
# read it, not anyone who compromises a server at some later
# date. Luckily, we also don't care about authenticating the logged
# messages as truly being from the server! The solution is for each
# server to create a fresh public/private keypair at startup and to
# include a copy of the public key in any encrypted logs it writes.


# Generate an ephemeral private key for the logger to use during this
# logging session.
logger_private_key = PrivateKey.generate()


def encrypt_for_log(message, reader_public_key_b64):
    """
    Encrypt a message so that it can be logged but only read by someone
    possessing the given public key. The public key is provided in base64.

    A separate public key should be used for each recipient or purpose.

    Returns a string <sender public key> "|" <ciphertext> which can be
    decrypted with decrypt_log_message.
    """
    reader_public_key = PublicKey(b64decode(reader_public_key_b64.encode()))

    encrypted = Box(logger_private_key, reader_public_key).encrypt(message.encode())

    pubkey = logger_private_key.public_key
    return b64encode(bytes(pubkey)).decode() + '|' + b64encode(encrypted).decode()


def decrypt_log_message(encrypted_message, reader_private_key_b64):
    """
    Decrypt a message using the private key that has been stored somewhere
    secure and *not* on the server.
    """
    reader_private_key = PrivateKey(b64decode(reader_private_key_b64))
    sender_public_key_data, encrypted_raw = \
        [b64decode(part.encode()) for part in encrypted_message.split('|', 1)]
    return Box(reader_private_key, PublicKey(sender_public_key_data)).decrypt(encrypted_raw).decode()


def generate_reader_keys():
    """
    Utility method for generating a public/private keypair for use with these
    logging functions. Returns a pair of base64
    """
    reader_private_key = PrivateKey.generate()
    return {
        'public': b64encode(bytes(reader_private_key.public_key)).decode(),
        'private': b64encode(bytes(reader_private_key)).decode(),
    }


@click.group()
def cli():
    pass


@click.command('gen-keys')
def cli_gen_keys():
    """
    Generate and print a keypair for reading sensitive logs.
    """
    reader_keys = generate_reader_keys()
    public_64 = reader_keys['public']
    private_64 = reader_keys['private']
    print(
        "This is your PUBLIC key, which should be included in the server's "
        "configuration, and does not need protection:"
        "\n\n"
        f"  \"{public_64}\" (public)"
        "\n\n"
        "This is your PRIVATE key, which must never be present on the server "
        "and should instead be kept encrypted in a separate, safe place "
        "such as a password manager:"
        "\n\n"
        f"  \"{private_64}\" (private)"
    )


cli.add_command(cli_gen_keys)

if __name__ == '__main__':
    cli()
