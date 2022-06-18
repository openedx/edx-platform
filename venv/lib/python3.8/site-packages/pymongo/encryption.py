# Copyright 2019-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Support for explicit client-side field level encryption."""

import contextlib
import os
import subprocess
import uuid
import weakref

try:
    from pymongocrypt.auto_encrypter import AutoEncrypter
    from pymongocrypt.errors import MongoCryptError
    from pymongocrypt.explicit_encrypter import ExplicitEncrypter
    from pymongocrypt.mongocrypt import MongoCryptOptions
    from pymongocrypt.state_machine import MongoCryptCallback
    _HAVE_PYMONGOCRYPT = True
except ImportError:
    _HAVE_PYMONGOCRYPT = False
    MongoCryptCallback = object

from bson import _dict_to_bson, decode, encode
from bson.codec_options import CodecOptions
from bson.binary import (Binary,
                         STANDARD,
                         UUID_SUBTYPE)
from bson.errors import BSONError
from bson.raw_bson import (DEFAULT_RAW_BSON_OPTIONS,
                           RawBSONDocument,
                           _inflate_bson)
from bson.son import SON

from pymongo.errors import (ConfigurationError,
                            EncryptionError,
                            InvalidOperation,
                            ServerSelectionTimeoutError)
from pymongo.mongo_client import MongoClient
from pymongo.pool import _configured_socket, PoolOptions
from pymongo.read_concern import ReadConcern
from pymongo.ssl_support import get_ssl_context, HAVE_SSL
from pymongo.uri_parser import parse_host
from pymongo.write_concern import WriteConcern
from pymongo.daemon import _spawn_daemon

if HAVE_SSL:
    from ssl import CERT_REQUIRED
else:
    CERT_REQUIRED = None

_HTTPS_PORT = 443
_KMS_CONNECT_TIMEOUT = 10  # TODO: CDRIVER-3262 will define this value.
_MONGOCRYPTD_TIMEOUT_MS = 10000

_DATA_KEY_OPTS = CodecOptions(document_class=SON, uuid_representation=STANDARD)
# Use RawBSONDocument codec options to avoid needlessly decoding
# documents from the key vault.
_KEY_VAULT_OPTS = CodecOptions(document_class=RawBSONDocument,
                               uuid_representation=STANDARD)


@contextlib.contextmanager
def _wrap_encryption_errors():
    """Context manager to wrap encryption related errors."""
    try:
        yield
    except BSONError:
        # BSON encoding/decoding errors are unrelated to encryption so
        # we should propagate them unchanged.
        raise
    except Exception as exc:
        raise EncryptionError(exc)


class _EncryptionIO(MongoCryptCallback):
    def __init__(self, client, key_vault_coll, mongocryptd_client, opts):
        """Internal class to perform I/O on behalf of pymongocrypt."""
        # Use a weak ref to break reference cycle.
        if client is not None:
            self.client_ref = weakref.ref(client)
        else:
            self.client_ref = None
        self.key_vault_coll = key_vault_coll.with_options(
            codec_options=_KEY_VAULT_OPTS,
            read_concern=ReadConcern(level='majority'),
            write_concern=WriteConcern(w='majority'))
        self.mongocryptd_client = mongocryptd_client
        self.opts = opts
        self._spawned = False

    def kms_request(self, kms_context):
        """Complete a KMS request.

        :Parameters:
          - `kms_context`: A :class:`MongoCryptKmsContext`.

        :Returns:
          None
        """
        endpoint = kms_context.endpoint
        message = kms_context.message
        host, port = parse_host(endpoint, _HTTPS_PORT)
        # Enable strict certificate verification, OCSP, match hostname, and
        # SNI using the system default CA certificates.
        ctx = get_ssl_context(
            None,  # certfile
            None,  # keyfile
            None,  # passphrase
            None,  # ca_certs
            CERT_REQUIRED,  # cert_reqs
            None,  # crlfile
            True,  # match_hostname
            True)  # check_ocsp_endpoint
        opts = PoolOptions(connect_timeout=_KMS_CONNECT_TIMEOUT,
                           socket_timeout=_KMS_CONNECT_TIMEOUT,
                           ssl_context=ctx)
        conn = _configured_socket((host, port), opts)
        try:
            conn.sendall(message)
            while kms_context.bytes_needed > 0:
                data = conn.recv(kms_context.bytes_needed)
                if not data:
                    raise OSError('KMS connection closed')
                kms_context.feed(data)
        finally:
            conn.close()

    def collection_info(self, database, filter):
        """Get the collection info for a namespace.

        The returned collection info is passed to libmongocrypt which reads
        the JSON schema.

        :Parameters:
          - `database`: The database on which to run listCollections.
          - `filter`: The filter to pass to listCollections.

        :Returns:
          The first document from the listCollections command response as BSON.
        """
        with self.client_ref()[database].list_collections(
                filter=RawBSONDocument(filter)) as cursor:
            for doc in cursor:
                return _dict_to_bson(doc, False, _DATA_KEY_OPTS)

    def spawn(self):
        """Spawn mongocryptd.

        Note this method is thread safe; at most one mongocryptd will start
        successfully.
        """
        self._spawned = True
        args = [self.opts._mongocryptd_spawn_path or 'mongocryptd']
        args.extend(self.opts._mongocryptd_spawn_args)
        _spawn_daemon(args)

    def mark_command(self, database, cmd):
        """Mark a command for encryption.

        :Parameters:
          - `database`: The database on which to run this command.
          - `cmd`: The BSON command to run.

        :Returns:
          The marked command response from mongocryptd.
        """
        if not self._spawned and not self.opts._mongocryptd_bypass_spawn:
            self.spawn()
        # Database.command only supports mutable mappings so we need to decode
        # the raw BSON command first.
        inflated_cmd = _inflate_bson(cmd, DEFAULT_RAW_BSON_OPTIONS)
        try:
            res = self.mongocryptd_client[database].command(
                inflated_cmd,
                codec_options=DEFAULT_RAW_BSON_OPTIONS)
        except ServerSelectionTimeoutError:
            if self.opts._mongocryptd_bypass_spawn:
                raise
            self.spawn()
            res = self.mongocryptd_client[database].command(
                inflated_cmd,
                codec_options=DEFAULT_RAW_BSON_OPTIONS)
        return res.raw

    def fetch_keys(self, filter):
        """Yields one or more keys from the key vault.

        :Parameters:
          - `filter`: The filter to pass to find.

        :Returns:
          A generator which yields the requested keys from the key vault.
        """
        with self.key_vault_coll.find(RawBSONDocument(filter)) as cursor:
            for key in cursor:
                yield key.raw

    def insert_data_key(self, data_key):
        """Insert a data key into the key vault.

        :Parameters:
          - `data_key`: The data key document to insert.

        :Returns:
          The _id of the inserted data key document.
        """
        raw_doc = RawBSONDocument(data_key)
        data_key_id = raw_doc.get('_id')
        if not isinstance(data_key_id, uuid.UUID):
            raise TypeError('data_key _id must be a UUID')

        self.key_vault_coll.insert_one(raw_doc)
        return Binary(data_key_id.bytes, subtype=UUID_SUBTYPE)

    def bson_encode(self, doc):
        """Encode a document to BSON.

        A document can be any mapping type (like :class:`dict`).

        :Parameters:
          - `doc`: mapping type representing a document

        :Returns:
          The encoded BSON bytes.
        """
        return encode(doc)

    def close(self):
        """Release resources.

        Note it is not safe to call this method from __del__ or any GC hooks.
        """
        self.client_ref = None
        self.key_vault_coll = None
        if self.mongocryptd_client:
            self.mongocryptd_client.close()
            self.mongocryptd_client = None


class _Encrypter(object):
    """Encrypts and decrypts MongoDB commands.

    This class is used to support automatic encryption and decryption of
    MongoDB commands."""
    def __init__(self, client, opts):
        """Create a _Encrypter for a client.

        :Parameters:
          - `client`: The encrypted MongoClient.
          - `opts`: The encrypted client's :class:`AutoEncryptionOpts`.
        """
        if opts._schema_map is None:
            schema_map = None
        else:
            schema_map = _dict_to_bson(opts._schema_map, False, _DATA_KEY_OPTS)
        self._bypass_auto_encryption = opts._bypass_auto_encryption
        self._internal_client = None

        def _get_internal_client(encrypter, mongo_client):
            if mongo_client.max_pool_size is None:
                # Unlimited pool size, use the same client.
                return mongo_client
            # Else - limited pool size, use an internal client.
            if encrypter._internal_client is not None:
                return encrypter._internal_client
            internal_client = mongo_client._duplicate(
                minPoolSize=0, auto_encryption_opts=None)
            encrypter._internal_client = internal_client
            return internal_client

        if opts._key_vault_client is not None:
            key_vault_client = opts._key_vault_client
        else:
            key_vault_client = _get_internal_client(self, client)

        if opts._bypass_auto_encryption:
            metadata_client = None
        else:
            metadata_client = _get_internal_client(self, client)

        db, coll = opts._key_vault_namespace.split('.', 1)
        key_vault_coll = key_vault_client[db][coll]

        mongocryptd_client = MongoClient(
            opts._mongocryptd_uri, connect=False,
            serverSelectionTimeoutMS=_MONGOCRYPTD_TIMEOUT_MS)

        io_callbacks = _EncryptionIO(
            metadata_client, key_vault_coll, mongocryptd_client, opts)
        self._auto_encrypter = AutoEncrypter(io_callbacks, MongoCryptOptions(
            opts._kms_providers, schema_map))
        self._closed = False

    def encrypt(self, database, cmd, check_keys, codec_options):
        """Encrypt a MongoDB command.

        :Parameters:
          - `database`: The database for this command.
          - `cmd`: A command document.
          - `check_keys`: If True, check `cmd` for invalid keys.
          - `codec_options`: The CodecOptions to use while encoding `cmd`.

        :Returns:
          The encrypted command to execute.
        """
        self._check_closed()
        # Workaround for $clusterTime which is incompatible with
        # check_keys.
        cluster_time = check_keys and cmd.pop('$clusterTime', None)
        encoded_cmd = _dict_to_bson(cmd, check_keys, codec_options)
        with _wrap_encryption_errors():
            encrypted_cmd = self._auto_encrypter.encrypt(database, encoded_cmd)
            # TODO: PYTHON-1922 avoid decoding the encrypted_cmd.
            encrypt_cmd = _inflate_bson(
                encrypted_cmd, DEFAULT_RAW_BSON_OPTIONS)
            if cluster_time:
                encrypt_cmd['$clusterTime'] = cluster_time
            return encrypt_cmd

    def decrypt(self, response):
        """Decrypt a MongoDB command response.

        :Parameters:
          - `response`: A MongoDB command response as BSON.

        :Returns:
          The decrypted command response.
        """
        self._check_closed()
        with _wrap_encryption_errors():
            return self._auto_encrypter.decrypt(response)

    def _check_closed(self):
        if self._closed:
            raise InvalidOperation("Cannot use MongoClient after close")

    def close(self):
        """Cleanup resources."""
        self._closed = True
        self._auto_encrypter.close()
        if self._internal_client:
            self._internal_client.close()
            self._internal_client = None


class Algorithm(object):
    """An enum that defines the supported encryption algorithms."""
    AEAD_AES_256_CBC_HMAC_SHA_512_Deterministic = (
        "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic")
    AEAD_AES_256_CBC_HMAC_SHA_512_Random = (
        "AEAD_AES_256_CBC_HMAC_SHA_512-Random")


class ClientEncryption(object):
    """Explicit client-side field level encryption."""

    def __init__(self, kms_providers, key_vault_namespace, key_vault_client,
                 codec_options):
        """Explicit client-side field level encryption.

        The ClientEncryption class encapsulates explicit operations on a key
        vault collection that cannot be done directly on a MongoClient. Similar
        to configuring auto encryption on a MongoClient, it is constructed with
        a MongoClient (to a MongoDB cluster containing the key vault
        collection), KMS provider configuration, and keyVaultNamespace. It
        provides an API for explicitly encrypting and decrypting values, and
        creating data keys. It does not provide an API to query keys from the
        key vault collection, as this can be done directly on the MongoClient.

        See :ref:`explicit-client-side-encryption` for an example.

        :Parameters:
          - `kms_providers`: Map of KMS provider options. Two KMS providers
            are supported: "aws" and "local". The kmsProviders map values
            differ by provider:

              - `aws`: Map with "accessKeyId" and "secretAccessKey" as strings.
                These are the AWS access key ID and AWS secret access key used
                to generate KMS messages. An optional "sessionToken" may be
                included to support temporary AWS credentials.
              - `azure`: Map with "tenantId", "clientId", and "clientSecret" as
                strings. Additionally, "identityPlatformEndpoint" may also be
                specified as a string (defaults to 'login.microsoftonline.com').
                These are the Azure Active Directory credentials used to
                generate Azure Key Vault messages.
              - `gcp`: Map with "email" as a string and "privateKey"
                as `bytes` or a base64 encoded string (unicode on Python 2).
                Additionally, "endpoint" may also be specified as a string
                (defaults to 'oauth2.googleapis.com'). These are the
                credentials used to generate Google Cloud KMS messages.
              - `local`: Map with "key" as `bytes` (96 bytes in length) or
                a base64 encoded string (unicode on Python 2) which decodes
                to 96 bytes. "key" is the master key used to encrypt/decrypt
                data keys. This key should be generated and stored as securely
                as possible.

          - `key_vault_namespace`: The namespace for the key vault collection.
            The key vault collection contains all data keys used for encryption
            and decryption. Data keys are stored as documents in this MongoDB
            collection. Data keys are protected with encryption by a KMS
            provider.
          - `key_vault_client`: A MongoClient connected to a MongoDB cluster
            containing the `key_vault_namespace` collection.
          - `codec_options`: An instance of
            :class:`~bson.codec_options.CodecOptions` to use when encoding a
            value for encryption and decoding the decrypted BSON value. This
            should be the same CodecOptions instance configured on the
            MongoClient, Database, or Collection used to access application
            data.

        .. versionadded:: 3.9
        """
        if not _HAVE_PYMONGOCRYPT:
            raise ConfigurationError(
                "client-side field level encryption requires the pymongocrypt "
                "library: install a compatible version with: "
                "python -m pip install 'pymongo[encryption]'")

        if not isinstance(codec_options, CodecOptions):
            raise TypeError("codec_options must be an instance of "
                            "bson.codec_options.CodecOptions")

        self._kms_providers = kms_providers
        self._key_vault_namespace = key_vault_namespace
        self._key_vault_client = key_vault_client
        self._codec_options = codec_options

        db, coll = key_vault_namespace.split('.', 1)
        key_vault_coll = key_vault_client[db][coll]

        self._io_callbacks = _EncryptionIO(None, key_vault_coll, None, None)
        self._encryption = ExplicitEncrypter(
            self._io_callbacks, MongoCryptOptions(kms_providers, None))

    def create_data_key(self, kms_provider, master_key=None,
                        key_alt_names=None):
        """Create and insert a new data key into the key vault collection.

        :Parameters:
          - `kms_provider`: The KMS provider to use. Supported values are
            "aws" and "local".
          - `master_key`: Identifies a KMS-specific key used to encrypt the
            new data key. If the kmsProvider is "local" the `master_key` is
            not applicable and may be omitted.

            If the `kms_provider` is "aws" it is required and has the
            following fields::

              - `region` (string): Required. The AWS region, e.g. "us-east-1".
              - `key` (string): Required. The Amazon Resource Name (ARN) to
                 the AWS customer.
              - `endpoint` (string): Optional. An alternate host to send KMS
                requests to. May include port number, e.g.
                "kms.us-east-1.amazonaws.com:443".

            If the `kms_provider` is "azure" it is required and has the
            following fields::

              - `keyVaultEndpoint` (string): Required. Host with optional
                 port, e.g. "example.vault.azure.net".
              - `keyName` (string): Required. Key name in the key vault.
              - `keyVersion` (string): Optional. Version of the key to use.

            If the `kms_provider` is "gcp" it is required and has the
            following fields::

              - `projectId` (string): Required. The Google cloud project ID.
              - `location` (string): Required. The GCP location, e.g. "us-east1".
              - `keyRing` (string): Required. Name of the key ring that contains
                the key to use.
              - `keyName` (string): Required. Name of the key to use.
              - `keyVersion` (string): Optional. Version of the key to use.
              - `endpoint` (string): Optional. Host with optional port.
                Defaults to "cloudkms.googleapis.com".

          - `key_alt_names` (optional): An optional list of string alternate
            names used to reference a key. If a key is created with alternate
            names, then encryption may refer to the key by the unique alternate
            name instead of by ``key_id``. The following example shows creating
            and referring to a data key by alternate name::

              client_encryption.create_data_key("local", keyAltNames=["name1"])
              # reference the key with the alternate name
              client_encryption.encrypt("457-55-5462", keyAltName="name1",
                                        algorithm=Algorithm.AEAD_AES_256_CBC_HMAC_SHA_512_Random)

        :Returns:
          The ``_id`` of the created data key document as a
          :class:`~bson.binary.Binary` with subtype
          :data:`~bson.binary.UUID_SUBTYPE`.
        """
        self._check_closed()
        with _wrap_encryption_errors():
            return self._encryption.create_data_key(
                kms_provider, master_key=master_key,
                key_alt_names=key_alt_names)

    def encrypt(self, value, algorithm, key_id=None, key_alt_name=None):
        """Encrypt a BSON value with a given key and algorithm.

        Note that exactly one of ``key_id`` or  ``key_alt_name`` must be
        provided.

        :Parameters:
          - `value`: The BSON value to encrypt.
          - `algorithm` (string): The encryption algorithm to use. See
            :class:`Algorithm` for some valid options.
          - `key_id`: Identifies a data key by ``_id`` which must be a
            :class:`~bson.binary.Binary` with subtype 4 (
            :attr:`~bson.binary.UUID_SUBTYPE`).
          - `key_alt_name`: Identifies a key vault document by 'keyAltName'.

        :Returns:
          The encrypted value, a :class:`~bson.binary.Binary` with subtype 6.
        """
        self._check_closed()
        if (key_id is not None and not (
                isinstance(key_id, Binary) and
                key_id.subtype == UUID_SUBTYPE)):
            raise TypeError(
                'key_id must be a bson.binary.Binary with subtype 4')

        doc = encode({'v': value}, codec_options=self._codec_options)
        with _wrap_encryption_errors():
            encrypted_doc = self._encryption.encrypt(
                doc, algorithm, key_id=key_id, key_alt_name=key_alt_name)
            return decode(encrypted_doc)['v']

    def decrypt(self, value):
        """Decrypt an encrypted value.

        :Parameters:
          - `value` (Binary): The encrypted value, a
            :class:`~bson.binary.Binary` with subtype 6.

        :Returns:
          The decrypted BSON value.
        """
        self._check_closed()
        if not (isinstance(value, Binary) and value.subtype == 6):
            raise TypeError(
                'value to decrypt must be a bson.binary.Binary with subtype 6')

        with _wrap_encryption_errors():
            doc = encode({'v': value})
            decrypted_doc = self._encryption.decrypt(doc)
            return decode(decrypted_doc,
                          codec_options=self._codec_options)['v']

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _check_closed(self):
        if self._encryption is None:
            raise InvalidOperation("Cannot use closed ClientEncryption")

    def close(self):
        """Release resources.

        Note that using this class in a with-statement will automatically call
        :meth:`close`::

            with ClientEncryption(...) as client_encryption:
                encrypted = client_encryption.encrypt(value, ...)
                decrypted = client_encryption.decrypt(encrypted)

        """
        if self._io_callbacks:
            self._io_callbacks.close()
            self._encryption.close()
            self._io_callbacks = None
            self._encryption = None
