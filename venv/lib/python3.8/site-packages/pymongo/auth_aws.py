# Copyright 2020-present MongoDB, Inc.
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

"""MONGODB-AWS Authentication helpers."""

try:
    import pymongo_auth_aws
    from pymongo_auth_aws import (AwsCredential,
                                  AwsSaslContext,
                                  PyMongoAuthAwsError)
    _HAVE_MONGODB_AWS = True
except ImportError:
    class AwsSaslContext(object):
        def __init__(self, credentials):
            pass
    _HAVE_MONGODB_AWS = False

import bson
from bson.binary import Binary
from bson.son import SON
from pymongo.errors import ConfigurationError, OperationFailure


class _AwsSaslContext(AwsSaslContext):
    # Dependency injection:
    def binary_type(self):
        """Return the bson.binary.Binary type."""
        return Binary

    def bson_encode(self, doc):
        """Encode a dictionary to BSON."""
        return bson.encode(doc)

    def bson_decode(self, data):
        """Decode BSON to a dictionary."""
        return bson.decode(data)


def _authenticate_aws(credentials, sock_info):
    """Authenticate using MONGODB-AWS.
    """
    if not _HAVE_MONGODB_AWS:
        raise ConfigurationError(
            "MONGODB-AWS authentication requires pymongo-auth-aws: "
            "install with: python -m pip install 'pymongo[aws]'")

    if sock_info.max_wire_version < 9:
        raise ConfigurationError(
            "MONGODB-AWS authentication requires MongoDB version 4.4 or later")

    try:
        ctx = _AwsSaslContext(AwsCredential(
            credentials.username, credentials.password,
            credentials.mechanism_properties.aws_session_token))
        client_payload = ctx.step(None)
        client_first = SON([('saslStart', 1),
                            ('mechanism', 'MONGODB-AWS'),
                            ('payload', client_payload)])
        server_first = sock_info.command('$external', client_first)
        res = server_first
        # Limit how many times we loop to catch protocol / library issues
        for _ in range(10):
            client_payload = ctx.step(res['payload'])
            cmd = SON([('saslContinue', 1),
                       ('conversationId', server_first['conversationId']),
                       ('payload', client_payload)])
            res = sock_info.command('$external', cmd)
            if res['done']:
                # SASL complete.
                break
    except PyMongoAuthAwsError as exc:
        # Convert to OperationFailure and include pymongo-auth-aws version.
        raise OperationFailure('%s (pymongo-auth-aws version %s)' % (
            exc, pymongo_auth_aws.__version__))
