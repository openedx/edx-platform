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

"""Support for SSL in PyMongo."""

import atexit
import sys
import threading

from bson.py3compat import string_type
from pymongo.errors import ConfigurationError

HAVE_SSL = True

try:
    import pymongo.pyopenssl_context as _ssl
except ImportError:
    try:
        import pymongo.ssl_context as _ssl
    except ImportError:
        HAVE_SSL = False

HAVE_CERTIFI = False
try:
    import certifi
    HAVE_CERTIFI = True
except ImportError:
    pass

HAVE_WINCERTSTORE = False
try:
    from wincertstore import CertFile
    HAVE_WINCERTSTORE = True
except ImportError:
    pass

_WINCERTSLOCK = threading.Lock()
_WINCERTS = None

if HAVE_SSL:
    # Note: The validate* functions below deal with users passing
    # CPython ssl module constants to configure certificate verification
    # at a high level. This is legacy behavior, but requires us to
    # import the ssl module even if we're only using it for this purpose.
    import ssl as _stdlibssl
    from ssl import CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
    HAS_SNI = _ssl.HAS_SNI
    IPADDR_SAFE = _ssl.IS_PYOPENSSL or sys.version_info[:2] >= (3, 7)
    SSLError = _ssl.SSLError
    def validate_cert_reqs(option, value):
        """Validate the cert reqs are valid. It must be None or one of the
        three values ``ssl.CERT_NONE``, ``ssl.CERT_OPTIONAL`` or
        ``ssl.CERT_REQUIRED``.
        """
        if value is None:
            return value
        if isinstance(value, string_type) and hasattr(_stdlibssl, value):
            value = getattr(_stdlibssl, value)

        if value in (CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED):
            return value
        raise ValueError("The value of %s must be one of: "
                         "`ssl.CERT_NONE`, `ssl.CERT_OPTIONAL` or "
                         "`ssl.CERT_REQUIRED`" % (option,))

    def validate_allow_invalid_certs(option, value):
        """Validate the option to allow invalid certificates is valid."""
        # Avoid circular import.
        from pymongo.common import validate_boolean_or_string
        boolean_cert_reqs = validate_boolean_or_string(option, value)
        if boolean_cert_reqs:
            return CERT_NONE
        return CERT_REQUIRED

    def _load_wincerts():
        """Set _WINCERTS to an instance of wincertstore.Certfile."""
        global _WINCERTS

        certfile = CertFile()
        certfile.addstore("CA")
        certfile.addstore("ROOT")
        atexit.register(certfile.close)

        _WINCERTS = certfile

    def get_ssl_context(*args):
        """Create and return an SSLContext object."""
        (certfile,
         keyfile,
         passphrase,
         ca_certs,
         cert_reqs,
         crlfile,
         match_hostname,
         check_ocsp_endpoint) = args
        verify_mode = CERT_REQUIRED if cert_reqs is None else cert_reqs
        ctx = _ssl.SSLContext(_ssl.PROTOCOL_SSLv23)
        # SSLContext.check_hostname was added in CPython 2.7.9 and 3.4.
        if hasattr(ctx, "check_hostname"):
            if _ssl.CHECK_HOSTNAME_SAFE and verify_mode != CERT_NONE:
                ctx.check_hostname = match_hostname
            else:
                ctx.check_hostname = False
        if hasattr(ctx, "check_ocsp_endpoint"):
            ctx.check_ocsp_endpoint = check_ocsp_endpoint
        if hasattr(ctx, "options"):
            # Explicitly disable SSLv2, SSLv3 and TLS compression. Note that
            # up to date versions of MongoDB 2.4 and above already disable
            # SSLv2 and SSLv3, python disables SSLv2 by default in >= 2.7.7
            # and >= 3.3.4 and SSLv3 in >= 3.4.3.
            ctx.options |= _ssl.OP_NO_SSLv2
            ctx.options |= _ssl.OP_NO_SSLv3
            ctx.options |= _ssl.OP_NO_COMPRESSION
            ctx.options |= _ssl.OP_NO_RENEGOTIATION
        if certfile is not None:
            try:
                ctx.load_cert_chain(certfile, keyfile, passphrase)
            except _ssl.SSLError as exc:
                raise ConfigurationError(
                    "Private key doesn't match certificate: %s" % (exc,))
        if crlfile is not None:
            if _ssl.IS_PYOPENSSL:
                raise ConfigurationError(
                    "ssl_crlfile cannot be used with PyOpenSSL")
            if not hasattr(ctx, "verify_flags"):
                raise ConfigurationError(
                    "Support for ssl_crlfile requires "
                    "python 2.7.9+ (pypy 2.5.1+) or  3.4+")
            # Match the server's behavior.
            ctx.verify_flags = getattr(_ssl, "VERIFY_CRL_CHECK_LEAF", 0)
            ctx.load_verify_locations(crlfile)
        if ca_certs is not None:
            ctx.load_verify_locations(ca_certs)
        elif cert_reqs != CERT_NONE:
            # CPython >= 2.7.9 or >= 3.4.0, pypy >= 2.5.1
            if hasattr(ctx, "load_default_certs"):
                ctx.load_default_certs()
            # Python >= 3.2.0, useless on Windows.
            elif (sys.platform != "win32" and
                  hasattr(ctx, "set_default_verify_paths")):
                ctx.set_default_verify_paths()
            elif sys.platform == "win32" and HAVE_WINCERTSTORE:
                with _WINCERTSLOCK:
                    if _WINCERTS is None:
                        _load_wincerts()
                ctx.load_verify_locations(_WINCERTS.name)
            elif HAVE_CERTIFI:
                ctx.load_verify_locations(certifi.where())
            else:
                raise ConfigurationError(
                    "`ssl_cert_reqs` is not ssl.CERT_NONE and no system "
                    "CA certificates could be loaded. `ssl_ca_certs` is "
                    "required.")
        ctx.verify_mode = verify_mode
        return ctx
else:
    class SSLError(Exception):
        pass
    HAS_SNI = False
    IPADDR_SAFE = False
    def validate_cert_reqs(option, dummy):
        """No ssl module, raise ConfigurationError."""
        raise ConfigurationError("The value of %s is set but can't be "
                                 "validated. The ssl module is not available"
                                 % (option,))

    def validate_allow_invalid_certs(option, dummy):
        """No ssl module, raise ConfigurationError."""
        return validate_cert_reqs(option, dummy)

    def get_ssl_context(*dummy):
        """No ssl module, raise ConfigurationError."""
        raise ConfigurationError("The ssl module is not available.")
