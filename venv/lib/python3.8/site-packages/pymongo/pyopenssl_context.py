# Copyright 2019-present MongoDB, Inc.
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

"""A CPython compatible SSLContext implementation wrapping PyOpenSSL's
context.
"""

import socket as _socket
import ssl as _stdlibssl

from errno import EINTR as _EINTR

# service_identity requires this for py27, so it should always be available
from ipaddress import ip_address as _ip_address

from OpenSSL import SSL as _SSL
from service_identity.pyopenssl import (
    verify_hostname as _verify_hostname,
    verify_ip_address as _verify_ip_address)
from service_identity import (
    CertificateError as _SICertificateError,
    VerificationError as _SIVerificationError)

from cryptography.hazmat.backends import default_backend as _default_backend

from bson.py3compat import _unicode
from pymongo.errors import CertificateError as _CertificateError
from pymongo.monotonic import time as _time
from pymongo.ocsp_support import (
    _load_trusted_ca_certs,
    _ocsp_callback)
from pymongo.ocsp_cache import _OCSPCache
from pymongo.socket_checker import (
    _errno_from_exception, SocketChecker as _SocketChecker)

PROTOCOL_SSLv23 = _SSL.SSLv23_METHOD
# Always available
OP_NO_SSLv2 = _SSL.OP_NO_SSLv2
OP_NO_SSLv3 = _SSL.OP_NO_SSLv3
OP_NO_COMPRESSION = _SSL.OP_NO_COMPRESSION
# This isn't currently documented for PyOpenSSL
OP_NO_RENEGOTIATION = getattr(_SSL, "OP_NO_RENEGOTIATION", 0)

# Always available
HAS_SNI = True
CHECK_HOSTNAME_SAFE = True
IS_PYOPENSSL = True

# Base Exception class
SSLError = _SSL.Error

# https://github.com/python/cpython/blob/v3.8.0/Modules/_ssl.c#L2995-L3002
_VERIFY_MAP = {
    _stdlibssl.CERT_NONE: _SSL.VERIFY_NONE,
    _stdlibssl.CERT_OPTIONAL: _SSL.VERIFY_PEER,
    _stdlibssl.CERT_REQUIRED: _SSL.VERIFY_PEER | _SSL.VERIFY_FAIL_IF_NO_PEER_CERT
}

_REVERSE_VERIFY_MAP = dict(
    (value, key) for key, value in _VERIFY_MAP.items())

def _is_ip_address(address):
    try:
        _ip_address(_unicode(address))
        return True
    except (ValueError, UnicodeError):
        return False

# According to the docs for Connection.send it can raise
# WantX509LookupError and should be retried.
_RETRY_ERRORS = (
    _SSL.WantReadError, _SSL.WantWriteError, _SSL.WantX509LookupError)


def _ragged_eof(exc):
    """Return True if the OpenSSL.SSL.SysCallError is a ragged EOF."""
    return exc.args == (-1, 'Unexpected EOF')


# https://github.com/pyca/pyopenssl/issues/168
# https://github.com/pyca/pyopenssl/issues/176
# https://docs.python.org/3/library/ssl.html#notes-on-non-blocking-sockets
class _sslConn(_SSL.Connection):

    def __init__(self, ctx, sock, suppress_ragged_eofs):
        self.socket_checker = _SocketChecker()
        self.suppress_ragged_eofs = suppress_ragged_eofs
        super(_sslConn, self).__init__(ctx, sock)

    def _call(self, call, *args, **kwargs):
        timeout = self.gettimeout()
        if timeout:
            start = _time()
        while True:
            try:
                return call(*args, **kwargs)
            except _RETRY_ERRORS:
                self.socket_checker.select(
                    self, True, True, timeout)
                if timeout and _time() - start > timeout:
                    raise _socket.timeout("timed out")
                continue

    def do_handshake(self, *args, **kwargs):
        return self._call(super(_sslConn, self).do_handshake, *args, **kwargs)

    def recv(self, *args, **kwargs):
        try:
            return self._call(super(_sslConn, self).recv, *args, **kwargs)
        except _SSL.SysCallError as exc:
            # Suppress ragged EOFs to match the stdlib.
            if self.suppress_ragged_eofs and _ragged_eof(exc):
                return b""
            raise

    def recv_into(self, *args, **kwargs):
        try:
            return self._call(super(_sslConn, self).recv_into, *args, **kwargs)
        except _SSL.SysCallError as exc:
            # Suppress ragged EOFs to match the stdlib.
            if self.suppress_ragged_eofs and _ragged_eof(exc):
                return 0
            raise

    def sendall(self, buf, flags=0):
        view = memoryview(buf)
        total_length = len(buf)
        total_sent = 0
        sent = 0
        while total_sent < total_length:
            try:
                sent = self._call(
                    super(_sslConn, self).send, view[total_sent:], flags)
            # XXX: It's not clear if this can actually happen. PyOpenSSL
            # doesn't appear to have any interrupt handling, nor any interrupt
            # errors for OpenSSL connections.
            except (IOError, OSError) as exc:
                if _errno_from_exception(exc) == _EINTR:
                    continue
                raise
            # https://github.com/pyca/pyopenssl/blob/19.1.0/src/OpenSSL/SSL.py#L1756
            # https://www.openssl.org/docs/man1.0.2/man3/SSL_write.html
            if sent <= 0:
                raise Exception("Connection closed")
            total_sent += sent


class _CallbackData(object):
    """Data class which is passed to the OCSP callback."""
    def __init__(self):
        self.trusted_ca_certs = None
        self.check_ocsp_endpoint = None
        self.ocsp_response_cache = _OCSPCache()


class SSLContext(object):
    """A CPython compatible SSLContext implementation wrapping PyOpenSSL's
    context.
    """

    __slots__ = ('_protocol', '_ctx', '_callback_data', '_check_hostname')

    def __init__(self, protocol):
        self._protocol = protocol
        self._ctx = _SSL.Context(self._protocol)
        self._callback_data = _CallbackData()
        self._check_hostname = True
        # OCSP
        # XXX: Find a better place to do this someday, since this is client
        # side configuration and wrap_socket tries to support both client and
        # server side sockets.
        self._callback_data.check_ocsp_endpoint = True
        self._ctx.set_ocsp_client_callback(
            callback=_ocsp_callback, data=self._callback_data)

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
        return _REVERSE_VERIFY_MAP[self._ctx.get_verify_mode()]

    def __set_verify_mode(self, value):
        """Setter for verify_mode."""
        def _cb(connobj, x509obj, errnum, errdepth, retcode):
            # It seems we don't need to do anything here. Twisted doesn't,
            # and OpenSSL's SSL_CTX_set_verify let's you pass NULL
            # for the callback option. It's weird that PyOpenSSL requires
            # this.
            return retcode
        self._ctx.set_verify(_VERIFY_MAP[value], _cb)

    verify_mode = property(__get_verify_mode, __set_verify_mode)

    def __get_check_hostname(self):
        return self._check_hostname

    def __set_check_hostname(self, value):
        if not isinstance(value, bool):
            raise TypeError("check_hostname must be True or False")
        self._check_hostname = value

    check_hostname = property(__get_check_hostname, __set_check_hostname)

    def __get_check_ocsp_endpoint(self):
        return self._callback_data.check_ocsp_endpoint

    def __set_check_ocsp_endpoint(self, value):
        if not isinstance(value, bool):
            raise TypeError("check_ocsp must be True or False")
        self._callback_data.check_ocsp_endpoint = value

    check_ocsp_endpoint = property(__get_check_ocsp_endpoint,
                                   __set_check_ocsp_endpoint)

    def __get_options(self):
        # Calling set_options adds the option to the existing bitmask and
        # returns the new bitmask.
        # https://www.pyopenssl.org/en/stable/api/ssl.html#OpenSSL.SSL.Context.set_options
        return self._ctx.set_options(0)

    def __set_options(self, value):
        # Explcitly convert to int, since newer CPython versions
        # use enum.IntFlag for options. The values are the same
        # regardless of implementation.
        self._ctx.set_options(int(value))

    options = property(__get_options, __set_options)

    def load_cert_chain(self, certfile, keyfile=None, password=None):
        """Load a private key and the corresponding certificate. The certfile
        string must be the path to a single file in PEM format containing the
        certificate as well as any number of CA certificates needed to
        establish the certificate's authenticity. The keyfile string, if
        present, must point to a file containing the private key. Otherwise
        the private key will be taken from certfile as well.
        """
        # Match CPython behavior
        # https://github.com/python/cpython/blob/v3.8.0/Modules/_ssl.c#L3930-L3971
        # Password callback MUST be set first or it will be ignored.
        if password:
            def _pwcb(max_length, prompt_twice, user_data):
                # XXX:We could check the password length against what OpenSSL
                # tells us is the max, but we can't raise an exception, so...
                # warn?
                return password.encode('utf-8')
            self._ctx.set_passwd_cb(_pwcb)
        self._ctx.use_certificate_chain_file(certfile)
        self._ctx.use_privatekey_file(keyfile or certfile)
        self._ctx.check_privatekey()

    def load_verify_locations(self, cafile=None, capath=None):
        """Load a set of "certification authority"(CA) certificates used to
        validate other peers' certificates when `~verify_mode` is other than
        ssl.CERT_NONE.
        """
        self._ctx.load_verify_locations(cafile, capath)
        self._callback_data.trusted_ca_certs = _load_trusted_ca_certs(cafile)

    def set_default_verify_paths(self):
        """Specify that the platform provided CA certificates are to be used
        for verification purposes."""
        # Note: See PyOpenSSL's docs for limitations, which are similar
        # but not that same as CPython's.
        self._ctx.set_default_verify_paths()

    def wrap_socket(self, sock, server_side=False,
                    do_handshake_on_connect=True,
                    suppress_ragged_eofs=True,
                    server_hostname=None, session=None):
        """Wrap an existing Python socket sock and return a TLS socket
        object.
        """
        ssl_conn = _sslConn(self._ctx, sock, suppress_ragged_eofs)
        if session:
            ssl_conn.set_session(session)
        if server_side is True:
            ssl_conn.set_accept_state()
        else:
            # SNI
            if server_hostname and not _is_ip_address(server_hostname):
                # XXX: Do this in a callback registered with
                # SSLContext.set_info_callback? See Twisted for an example.
                ssl_conn.set_tlsext_host_name(server_hostname.encode('idna'))
            if self.verify_mode != _stdlibssl.CERT_NONE:
                # Request a stapled OCSP response.
                ssl_conn.request_ocsp()
            ssl_conn.set_connect_state()
        # If this wasn't true the caller of wrap_socket would call
        # do_handshake()
        if do_handshake_on_connect:
            # XXX: If we do hostname checking in a callback we can get rid
            # of this call to do_handshake() since the handshake
            # will happen automatically later.
            ssl_conn.do_handshake()
            # XXX: Do this in a callback registered with
            # SSLContext.set_info_callback? See Twisted for an example.
            if self.check_hostname and server_hostname is not None:
                try:
                    if _is_ip_address(server_hostname):
                        _verify_ip_address(ssl_conn, _unicode(server_hostname))
                    else:
                        _verify_hostname(ssl_conn, _unicode(server_hostname))
                except (_SICertificateError, _SIVerificationError) as exc:
                    raise _CertificateError(str(exc))
        return ssl_conn
