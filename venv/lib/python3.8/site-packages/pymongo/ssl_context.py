# Copyright 2014-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you
# may not use this file except in compliance with the License.  You
# may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""A fake SSLContext implementation."""

import ssl as _ssl
import sys as _sys

# PROTOCOL_TLS_CLIENT is Python 3.6+
PROTOCOL_SSLv23 = getattr(_ssl, "PROTOCOL_TLS_CLIENT", _ssl.PROTOCOL_SSLv23)
# Python 2.7.9+
OP_NO_SSLv2 = getattr(_ssl, "OP_NO_SSLv2", 0)
# Python 2.7.9+
OP_NO_SSLv3 = getattr(_ssl, "OP_NO_SSLv3", 0)
# Python 2.7.9+, OpenSSL 1.0.0+
OP_NO_COMPRESSION = getattr(_ssl, "OP_NO_COMPRESSION", 0)
# Python 3.7+, OpenSSL 1.1.0h+
OP_NO_RENEGOTIATION = getattr(_ssl, "OP_NO_RENEGOTIATION", 0)

# Python 2.7.9+
HAS_SNI = getattr(_ssl, "HAS_SNI", False)
IS_PYOPENSSL = False

# Base Exception class
SSLError = _ssl.SSLError

try:
    # CPython 2.7.9+
    from ssl import SSLContext
    if hasattr(_ssl, "VERIFY_CRL_CHECK_LEAF"):
        from ssl import VERIFY_CRL_CHECK_LEAF
    # Python 3.7 uses OpenSSL's hostname matching implementation
    # making it the obvious version to start using SSLConext.check_hostname.
    # Python 3.6 might have been a good version, but it suffers
    # from https://bugs.python.org/issue32185.
    # We'll use our bundled match_hostname for older Python
    # versions, which also supports IP address matching
    # with Python < 3.5.
    CHECK_HOSTNAME_SAFE = _sys.version_info[:2] >= (3, 7)
except ImportError:
    from pymongo.errors import ConfigurationError

    class SSLContext(object):
        """A fake SSLContext.

        This implements an API similar to ssl.SSLContext from python 3.2
        but does not implement methods or properties that would be
        incompatible with ssl.wrap_socket from python 2.7 < 2.7.9.

        You must pass protocol which must be one of the PROTOCOL_* constants
        defined in the ssl module. ssl.PROTOCOL_SSLv23 is recommended for maximum
        interoperability.
        """

        __slots__ = ('_cafile', '_certfile',
                     '_keyfile', '_protocol', '_verify_mode')

        def __init__(self, protocol):
            self._cafile = None
            self._certfile = None
            self._keyfile = None
            self._protocol = protocol
            self._verify_mode = _ssl.CERT_NONE

        @property
        def protocol(self):
            """The protocol version chosen when constructing the context.
            This attribute is read-only.
            """
            return self._protocol

        def __get_verify_mode(self):
            """Whether to try to verify other peers' certificates and how to
            behave if verification fails. This attribute must be one of
            ssl.CERT_NONE, ssl.CERT_OPTIONAL or ssl.CERT_REQUIRED.
            """
            return self._verify_mode

        def __set_verify_mode(self, value):
            """Setter for verify_mode."""
            self._verify_mode = value

        verify_mode = property(__get_verify_mode, __set_verify_mode)

        def load_cert_chain(self, certfile, keyfile=None, password=None):
            """Load a private key and the corresponding certificate. The certfile
            string must be the path to a single file in PEM format containing the
            certificate as well as any number of CA certificates needed to
            establish the certificate's authenticity. The keyfile string, if
            present, must point to a file containing the private key. Otherwise
            the private key will be taken from certfile as well.
            """
            if password is not None:
                raise ConfigurationError(
                    "Support for ssl_pem_passphrase requires "
                    "python 2.7.9+ (pypy 2.5.1+), python 3 or "
                    "PyOpenSSL")
            self._certfile = certfile
            self._keyfile = keyfile

        def load_verify_locations(self, cafile=None, dummy=None):
            """Load a set of "certification authority"(CA) certificates used to
            validate other peers' certificates when `~verify_mode` is other than
            ssl.CERT_NONE.
            """
            self._cafile = cafile

        def wrap_socket(self, sock, server_side=False,
                        do_handshake_on_connect=True,
                        suppress_ragged_eofs=True, dummy=None):
            """Wrap an existing Python socket sock and return an ssl.SSLSocket
            object.
            """
            return _ssl.wrap_socket(sock, keyfile=self._keyfile,
                                    certfile=self._certfile,
                                    server_side=server_side,
                                    cert_reqs=self._verify_mode,
                                    ssl_version=self._protocol,
                                    ca_certs=self._cafile,
                                    do_handshake_on_connect=do_handshake_on_connect,
                                    suppress_ragged_eofs=suppress_ragged_eofs)
