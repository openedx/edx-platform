# Copyright (c) 2014, 2021, Oracle and/or its affiliates.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0, as
# published by the Free Software Foundation.
#
# This program is also distributed with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms,
# as designated in a particular file or component or in included license
# documentation.  The authors of MySQL hereby grant you an
# additional permission to link the program and your derivative works
# with the separately licensed software that they have included with
# MySQL.
#
# Without limiting anything contained in the foregoing, this file,
# which is part of MySQL Connector/Python, is also subject to the
# Universal FOSS Exception, version 1.0, a copy of which can be found at
# http://oss.oracle.com/licenses/universal-foss-exception.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

"""Implementing support for MySQL Authentication Plugins"""

from base64 import b64encode, b64decode
from hashlib import sha1, sha256
import getpass
import hmac
import logging
import os
import struct


from urllib.parse import quote
from uuid import uuid4

try:
    from cryptography.exceptions import UnsupportedAlgorithm
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

try:
    import gssapi
except ImportError:
    gssapi = None

try:
    import sspi
    import sspicon
    import win32api
except ImportError:
    sspi = None
    sspicon = None
    win32api = None

from . import errors
from .utils import (normalize_unicode_string as norm_ustr,
                    validate_normalized_unicode_string as valid_norm)

logging.getLogger(__name__).addHandler(logging.NullHandler())

_LOGGER = logging.getLogger(__name__)


class BaseAuthPlugin(object):
    """Base class for authentication plugins


    Classes inheriting from BaseAuthPlugin should implement the method
    prepare_password(). When instantiating, auth_data argument is
    required. The username, password and database are optional. The
    ssl_enabled argument can be used to tell the plugin whether SSL is
    active or not.

    The method auth_response() method is used to retrieve the password
    which was prepared by prepare_password().
    """

    requires_ssl = False
    plugin_name = ''

    def __init__(self, auth_data, username=None, password=None, database=None,
                 ssl_enabled=False, instance=None):
        """Initialization"""
        self._auth_data = auth_data
        self._username = username
        self._password = password
        self._database = database
        self._ssl_enabled = ssl_enabled

    def prepare_password(self):
        """Prepares and returns password to be send to MySQL

        This method needs to be implemented by classes inheriting from
        this class. It is used by the auth_response() method.

        Raises NotImplementedError.
        """
        raise NotImplementedError

    def auth_response(self):
        """Returns the prepared password to send to MySQL

        Raises InterfaceError on errors. For example, when SSL is required
        by not enabled.

        Returns str
        """
        if self.requires_ssl and not self._ssl_enabled:
            raise errors.InterfaceError("{name} requires SSL".format(
                name=self.plugin_name))
        return self.prepare_password()


class MySQLNativePasswordAuthPlugin(BaseAuthPlugin):
    """Class implementing the MySQL Native Password authentication plugin"""

    requires_ssl = False
    plugin_name = 'mysql_native_password'

    def prepare_password(self):
        """Prepares and returns password as native MySQL 4.1+ password"""
        if not self._auth_data:
            raise errors.InterfaceError("Missing authentication data (seed)")

        if not self._password:
            return b''
        password = self._password

        if isinstance(self._password, str):
            password = self._password.encode('utf-8')
        else:
            password = self._password

        auth_data = self._auth_data

        hash4 = None
        try:
            hash1 = sha1(password).digest()
            hash2 = sha1(hash1).digest()
            hash3 = sha1(auth_data + hash2).digest()
            xored = [h1 ^ h3 for (h1, h3) in zip(hash1, hash3)]
            hash4 = struct.pack('20B', *xored)
        except Exception as exc:
            raise errors.InterfaceError(
                "Failed scrambling password; {0}".format(exc))

        return hash4


class MySQLClearPasswordAuthPlugin(BaseAuthPlugin):
    """Class implementing the MySQL Clear Password authentication plugin"""

    requires_ssl = True
    plugin_name = 'mysql_clear_password'

    def prepare_password(self):
        """Returns password as as clear text"""
        if not self._password:
            return b'\x00'
        password = self._password

        if isinstance(password, str):
            password = password.encode('utf8')

        return password + b'\x00'


class MySQLSHA256PasswordAuthPlugin(BaseAuthPlugin):
    """Class implementing the MySQL SHA256 authentication plugin

    Note that encrypting using RSA is not supported since the Python
    Standard Library does not provide this OpenSSL functionality.
    """

    requires_ssl = True
    plugin_name = 'sha256_password'

    def prepare_password(self):
        """Returns password as as clear text"""
        if not self._password:
            return b'\x00'
        password = self._password

        if isinstance(password, str):
            password = password.encode('utf8')

        return password + b'\x00'


class MySQLCachingSHA2PasswordAuthPlugin(BaseAuthPlugin):
    """Class implementing the MySQL caching_sha2_password authentication plugin

    Note that encrypting using RSA is not supported since the Python
    Standard Library does not provide this OpenSSL functionality.
    """
    requires_ssl = False
    plugin_name = 'caching_sha2_password'
    perform_full_authentication = 4
    fast_auth_success = 3

    def _scramble(self):
        """ Returns a scramble of the password using a Nonce sent by the
        server.

        The scramble is of the form:
        XOR(SHA2(password), SHA2(SHA2(SHA2(password)), Nonce))
        """
        if not self._auth_data:
            raise errors.InterfaceError("Missing authentication data (seed)")

        if not self._password:
            return b''

        password = self._password.encode('utf-8') \
            if isinstance(self._password, str) else self._password
        auth_data = self._auth_data

        hash1 = sha256(password).digest()
        hash2 = sha256()
        hash2.update(sha256(hash1).digest())
        hash2.update(auth_data)
        hash2 = hash2.digest()
        xored = [h1 ^ h2 for (h1, h2) in zip(hash1, hash2)]
        hash3 = struct.pack('32B', *xored)

        return hash3

    def prepare_password(self):
        if len(self._auth_data) > 1:
            return self._scramble()
        elif self._auth_data[0] == self.perform_full_authentication:
            return self._full_authentication()
        return None

    def _full_authentication(self):
        """Returns password as as clear text"""
        if not self._ssl_enabled:
            raise errors.InterfaceError("{name} requires SSL".format(
                name=self.plugin_name))

        if not self._password:
            return b'\x00'
        password = self._password

        if isinstance(password, str):
            password = password.encode('utf8')

        return password + b'\x00'


class MySQLLdapSaslPasswordAuthPlugin(BaseAuthPlugin):
    """Class implementing the MySQL ldap sasl authentication plugin.

    The MySQL's ldap sasl authentication plugin support two authentication
    methods SCRAM-SHA-1 and GSSAPI (using Kerberos). This implementation only
    support SCRAM-SHA-1 and SCRAM-SHA-256.

    SCRAM-SHA-1 amd SCRAM-SHA-256
        This method requires 2 messages from client and 2 responses from
        server.

        The first message from client will be generated by prepare_password(),
        after receive the response from the server, it is required that this
        response is passed back to auth_continue() which will return the
        second message from the client. After send this second message to the
        server, the second server respond needs to be passed to auth_finalize()
        to finish the authentication process.
    """
    sasl_mechanisms = ['SCRAM-SHA-1', 'SCRAM-SHA-256', 'GSSAPI']
    requires_ssl = False
    plugin_name = 'authentication_ldap_sasl_client'
    def_digest_mode = sha1
    client_nonce = None
    client_salt = None
    server_salt = None
    krb_service_principal = None
    iterations = 0
    server_auth_var = None

    def _xor(self, bytes1, bytes2):
        return bytes([b1 ^ b2 for b1, b2 in zip(bytes1, bytes2)])

    def _hmac(self, password, salt):
        digest_maker = hmac.new(password, salt, self.def_digest_mode)
        return digest_maker.digest()

    def _hi(self, password, salt, count):
        """Prepares Hi
        Hi(password, salt, iterations) where Hi(p,s,i) is defined as
        PBKDF2 (HMAC, p, s, i, output length of H).

        """
        pw = password.encode()
        hi = self._hmac(pw, salt + b'\x00\x00\x00\x01')
        aux = hi
        for _ in range(count - 1):
            aux = self._hmac(pw, aux)
            hi = self._xor(hi, aux)
        return hi

    def _normalize(self, string):
        norm_str = norm_ustr(string)
        broken_rule = valid_norm(norm_str)
        if broken_rule is not None:
            raise errors.InterfaceError("broken_rule: {}".format(broken_rule))
            char, rule = broken_rule
            raise errors.InterfaceError(
                "Unable to normalice character: `{}` in `{}` due to {}"
                "".format(char, string, rule))
        return norm_str

    def _first_message(self):
        """This method generates the first message to the server to start the

        The client-first message consists of a gs2-header,
        the desired username, and a randomly generated client nonce cnonce.

        The first message from the server has the form:
            b'n,a=<user_name>,n=<user_name>,r=<client_nonce>

        Returns client's first message
        """
        cfm_fprnat = "n,a={user_name},n={user_name},r={client_nonce}"
        self.client_nonce = str(uuid4()).replace("-", "")
        cfm = cfm_fprnat.format(user_name=self._normalize(self._username),
                                client_nonce=self.client_nonce)

        if isinstance(cfm, str):
            cfm = cfm.encode('utf8')
        return cfm

    def _first_message_krb(self):
        """Get a TGT Authentication request and initiates security context.

        This method will contact the Kerberos KDC in order of obtain a TGT.
        """
        _LOGGER.debug("# user name: %s", self._username)
        user_name = gssapi.raw.names.import_name(self._username.encode('utf8'),
                                                 name_type=gssapi.NameType.user)

        # Use defaults store = {'ccache': 'FILE:/tmp/krb5cc_1000'}#, 'keytab':'/etc/some.keytab' }
        # Attempt to retrieve credential from default cache file.
        try:
            cred = gssapi.Credentials()
            _LOGGER.debug("# Stored credentials found, if password was given it"
                          " will be ignored.")
            try:
                # validate credentials has not expired.
                cred.lifetime
            except gssapi.raw.exceptions.ExpiredCredentialsError as err:
                _LOGGER.warning(" Credentials has expired: %s", err)
                cred.acquire(user_name)
                raise errors.InterfaceError("Credentials has expired: {}".format(err))
        except gssapi.raw.misc.GSSError as err:
            if not self._password:
                _LOGGER.error(" Unable to retrieve stored credentials: %s", err)
                raise errors.InterfaceError(
                    "Unable to retrieve stored credentials error: {}".format(err))
            else:
                try:
                    _LOGGER.debug("# Attempt to retrieve credentials with "
                                  "given password")
                    acquire_cred_result = gssapi.raw.acquire_cred_with_password(
                        user_name, self._password.encode('utf8'), usage="initiate")
                    cred = acquire_cred_result[0]
                except gssapi.raw.misc.GSSError as err:
                    _LOGGER.error(" Unable to retrieve credentials with the given "
                                  "password: %s", err)
                    raise errors.ProgrammingError(
                        "Unable to retrieve credentials with the given password: "
                        "{}".format(err))

        flags_l = (gssapi.RequirementFlag.mutual_authentication,
                   gssapi.RequirementFlag.extended_error,
                   gssapi.RequirementFlag.delegate_to_peer
        )

        if self.krb_service_principal:
            service_principal = self.krb_service_principal
        else:
            service_principal = "ldap/ldapauth"
        _LOGGER.debug("# service principal: %s", service_principal)
        servk = gssapi.Name(service_principal, name_type=gssapi.NameType.kerberos_principal)
        self.target_name = servk
        self.ctx = gssapi.SecurityContext(name=servk,
                                          creds=cred,
                                          flags=sum(flags_l),
                                          usage='initiate')

        try:
            initial_client_token = self.ctx.step()
        except gssapi.raw.misc.GSSError as err:
            _LOGGER.error("Unable to initiate security context: %s", err)
            raise errors.InterfaceError("Unable to initiate security context: {}".format(err))

        _LOGGER.debug("# initial client token: %s", initial_client_token)
        return initial_client_token


    def auth_continue_krb(self, tgt_auth_challenge):
        """Continue with the Kerberos TGT service request.

        With the TGT authentication service given response generate a TGT
        service request. This method must be invoked sequentially (in a loop)
        until the security context is completed and an empty response needs to
        be send to acknowledge the server.

        Args:
            tgt_auth_challenge the challenge for the negotiation.

        Returns: tuple (bytearray TGS service request,
                        bool True if context is completed otherwise False).
        """
        _LOGGER.debug("tgt_auth challenge: %s", tgt_auth_challenge)

        resp = self.ctx.step(tgt_auth_challenge)
        _LOGGER.debug("# context step response: %s", resp)
        _LOGGER.debug("# context completed?: %s", self.ctx.complete)

        return resp, self.ctx.complete

    def auth_accept_close_handshake(self, message):
        """Accept handshake and generate closing handshake message for server.

        This method verifies the server authenticity from the given message
        and included signature and generates the closing handshake for the
        server.

        When this method is invoked the security context is already established
        and the client and server can send GSSAPI formated secure messages.

        To finish the authentication handshake the server sends a message
        with the security layer availability and the maximum buffer size.

        Since the connector only uses the GSSAPI authentication mechanism to
        authenticate the user with the server, the server will verify clients
        message signature and terminate the GSSAPI authentication and send two
        messages; an authentication acceptance b'\x01\x00\x00\x08\x01' and a
        OK packet (that must be received after sent the returned message from
        this method).

        Args:
            message a wrapped hssapi message from the server.

        Returns: bytearray closing handshake message to be send to the server.
        """
        if not self.ctx.complete:
            raise errors.ProgrammingError("Security context is not completed.")
        _LOGGER.debug("# servers message: %s", message)
        _LOGGER.debug("# GSSAPI flags in use: %s", self.ctx.actual_flags)
        try:
            unwraped = self.ctx.unwrap(message)
            _LOGGER.debug("# unwraped: %s", unwraped)
        except gssapi.raw.exceptions.BadMICError as err:
            _LOGGER.debug("Unable to unwrap server message: %s", err)
            raise errors.InterfaceError("Unable to unwrap server message: {}"
                                 "".format(err))

        _LOGGER.debug("# unwrapped server message: %s", unwraped)
        # The message contents for the clients closing message:
        #   - security level 1 byte, must be always 1.
        #   - conciliated buffer size 3 bytes, without importance as no
        #     further GSSAPI messages will be sends.
        response = bytearray(b"\x01\x00\x00\00")
        # Closing handshake must not be encrypted.
        _LOGGER.debug("# message response: %s", response)
        wraped = self.ctx.wrap(response, encrypt=False)
        _LOGGER.debug("# wrapped message response: %s, length: %d",
                      wraped[0], len(wraped[0]))

        return wraped.message

    def auth_response(self, krb_service_principal=None):
        """This method will prepare the fist message to the server.

        Returns bytes to send to the server as the first message.
        """
        auth_mechanism = self._auth_data.decode()
        self.krb_service_principal = krb_service_principal
        _LOGGER.debug("read_method_name_from_server: %s", auth_mechanism)
        if auth_mechanism not in self.sasl_mechanisms:
            raise errors.InterfaceError(
                'The sasl authentication method "{}" requested from the server '
                'is not supported. Only "{}" and "{}" are supported'.format(
                    auth_mechanism, '", "'.join(self.sasl_mechanisms[:-1]),
                    self.sasl_mechanisms[-1]))

        if b'GSSAPI' in self._auth_data:
            if not gssapi:
                raise errors.ProgrammingError(
                    "Module gssapi is required for GSSAPI authentication "
                    "mechanism but was not found. Unable to authenticate "
                    "with the server")
            return self._first_message_krb()

        if self._auth_data == b'SCRAM-SHA-256':
            self.def_digest_mode = sha256

        return self._first_message()

    def _second_message(self):
        """This method generates the second message to the server

        Second message consist on the concatenation of the client and the
        server nonce, and cproof.

        c=<n,a=<user_name>>,r=<server_nonce>,p=<client_proof>
        where:
            <client_proof>: xor(<client_key>, <client_signature>)

            <client_key>: hmac(salted_password, b"Client Key")
            <client_signature>: hmac(<stored_key>, <auth_msg>)
            <stored_key>: h(<client_key>)
            <auth_msg>: <client_first_no_header>,<servers_first>,
                        c=<client_header>,r=<server_nonce>
            <client_first_no_header>: n=<username>r=<client_nonce>
        """
        if not self._auth_data:
            raise errors.InterfaceError("Missing authentication data (seed)")

        passw = self._normalize(self._password)
        salted_password = self._hi(passw,
                                   b64decode(self.server_salt),
                                   self.iterations)

        _LOGGER.debug("salted_password: %s",
                      b64encode(salted_password).decode())

        client_key = self._hmac(salted_password, b"Client Key")
        _LOGGER.debug("client_key: %s", b64encode(client_key).decode())

        stored_key = self.def_digest_mode(client_key).digest()
        _LOGGER.debug("stored_key: %s", b64encode(stored_key).decode())

        server_key = self._hmac(salted_password, b"Server Key")
        _LOGGER.debug("server_key: %s", b64encode(server_key).decode())

        client_first_no_header = ",".join([
            "n={}".format(self._normalize(self._username)),
            "r={}".format(self.client_nonce)])
        _LOGGER.debug("client_first_no_header: %s", client_first_no_header)
        auth_msg = ','.join([
            client_first_no_header,
            self.servers_first,
            "c={}".format(b64encode("n,a={},".format(
                self._normalize(self._username)).encode()).decode()),
            "r={}".format(self.server_nonce)])
        _LOGGER.debug("auth_msg: %s", auth_msg)

        client_signature = self._hmac(stored_key, auth_msg.encode())
        _LOGGER.debug("client_signature: %s",
                      b64encode(client_signature).decode())

        client_proof = self._xor(client_key, client_signature)
        _LOGGER.debug("client_proof: %s", b64encode(client_proof).decode())

        self.server_auth_var = b64encode(
            self._hmac(server_key, auth_msg.encode())).decode()
        _LOGGER.debug("server_auth_var: %s", self.server_auth_var)

        client_header = b64encode(
            "n,a={},".format(self._normalize(self._username)).encode()).decode()
        msg = ",".join(["c={}".format(client_header),
                        "r={}".format(self.server_nonce),
                        "p={}".format(b64encode(client_proof).decode())])
        _LOGGER.debug("second_message: %s", msg)
        return msg.encode()

    def _validate_first_reponse(self, servers_first):
        """Validates first message from the server.

        Extracts the server's salt and iterations from the servers 1st response.
        First message from the server is in the form:
            <server_salt>,i=<iterations>
        """
        if not servers_first or not isinstance(servers_first, (bytearray, bytes)):
            raise errors.InterfaceError("Unexpected server message: {}"
                                        "".format(servers_first))
        try:
            servers_first = servers_first.decode()
            self.servers_first = servers_first
            r_server_nonce, s_salt, i_counter = servers_first.split(",")
        except ValueError:
            raise errors.InterfaceError("Unexpected server message: {}"
                                        "".format(servers_first))
        if not r_server_nonce.startswith("r=") or \
           not s_salt.startswith("s=") or \
           not i_counter.startswith("i="):
            raise errors.InterfaceError("Incomplete reponse from the server: {}"
                                        "".format(servers_first))
        if self.client_nonce in r_server_nonce:
            self.server_nonce = r_server_nonce[2:]
            _LOGGER.debug("server_nonce: %s", self.server_nonce)
        else:
            raise errors.InterfaceError("Unable to authenticate response: "
                                        "response not well formed {}"
                                        "".format(servers_first))
        self.server_salt = s_salt[2:]
        _LOGGER.debug("server_salt: %s length: %s", self.server_salt,
                       len(self.server_salt))
        try:
            i_counter = i_counter[2:]
            _LOGGER.debug("iterations: {}".format(i_counter))
            self.iterations = int(i_counter)
        except:
            raise errors.InterfaceError("Unable to authenticate: iterations "
                                        "not found {}".format(servers_first))

    def auth_continue(self, servers_first_response):
        """return the second message from the client.

        Returns bytes to send to the server as the second message.
        """
        self._validate_first_reponse(servers_first_response)
        return self._second_message()

    def _validate_second_reponse(self, servers_second):
        """Validates second message from the server.

        The client and the server prove to each other they have the same Auth
        variable.

        The second message from the server consist of the server's proof:
            server_proof = HMAC(<server_key>, <auth_msg>)
            where:
                <server_key>: hmac(<salted_password>, b"Server Key")
                <auth_msg>: <client_first_no_header>,<servers_first>,
                            c=<client_header>,r=<server_nonce>

        Our server_proof must be equal to the Auth variable send on this second
        response.
        """
        if not servers_second or not isinstance(servers_second, bytearray) or \
           len(servers_second)<=2 or not servers_second.startswith(b"v="):
            raise errors.InterfaceError("The server's proof is not well formated.")
        server_var = servers_second[2:].decode()
        _LOGGER.debug("server auth variable: %s", server_var)
        return self.server_auth_var == server_var

    def auth_finalize(self, servers_second_response):
        """finalize the authentication process.

        Raises errors.InterfaceError if the ervers_second_response is invalid.

        Returns True in succesfull authentication False otherwise.
        """
        if not self._validate_second_reponse(servers_second_response):
            raise errors.InterfaceError("Authentication failed: Unable to "
                                        "proof server identity.")
        return True


class MySQLKerberosAuthPlugin(BaseAuthPlugin):
    """Implement the MySQL Kerberos authentication plugin."""

    plugin_name = "authentication_kerberos_client"
    requires_ssl = False
    context = None

    @staticmethod
    def get_user_from_credentials():
        """Get user from credentials without realm."""
        try:
            creds = gssapi.Credentials(usage="initiate")
            user = str(creds.name)
            if user.find("@") != -1:
                user, _ = user.split("@", 1)
            return user
        except gssapi.raw.misc.GSSError as err:
            return getpass.getuser()

    def _acquire_cred_with_password(self, upn):
        """Acquire credentials through provided password."""
        _LOGGER.debug(
            "Attempt to acquire credentials through provided password"
        )

        username = gssapi.raw.names.import_name(
            upn.encode("utf-8"),
            name_type=gssapi.NameType.user
        )

        try:
            acquire_cred_result = (
                gssapi.raw.acquire_cred_with_password(
                    username,
                    self._password.encode("utf-8"),
                    usage="initiate"
                )
            )
        except gssapi.raw.misc.GSSError as err:
            raise errors.ProgrammingError(
                f"Unable to acquire credentials with the given password: {err}"
            )
        creds = acquire_cred_result[0]
        return creds

    def _parse_auth_data(self, packet):
        """Parse authentication data.

        Get the SPN and REALM from the authentication data packet.

        Format:
            SPN string length two bytes <B1> <B2> +
            SPN string +
            UPN realm string length two bytes <B1> <B2> +
            UPN realm string

        Returns:
            tuple: With 'spn' and 'realm'.
        """
        spn_len = struct.unpack("<H", packet[:2])[0]
        packet = packet[2:]

        spn = struct.unpack(f"<{spn_len}s", packet[:spn_len])[0]
        packet = packet[spn_len:]

        realm_len = struct.unpack("<H", packet[:2])[0]
        realm = struct.unpack(f"<{realm_len}s", packet[2:])[0]

        return spn.decode(), realm.decode()

    def prepare_password(self):
        """Return password as as clear text."""
        if not self._password:
            return b"\x00"
        password = self._password

        if isinstance(password, str):
            password = password.encode("utf8")

        return password + b"\x00"

    def auth_response(self, auth_data=None):
        """Prepare the fist message to the server."""
        spn = None
        realm = None

        if auth_data:
            try:
                spn, realm = self._parse_auth_data(auth_data)
            except struct.error as err:
                raise InterruptedError(f"Invalid authentication data: {err}")

        if spn is None:
            return self.prepare_password()

        upn = f"{self._username}@{realm}" if self._username else None

        _LOGGER.debug("Service Principal: %s", spn)
        _LOGGER.debug("Realm: %s", realm)
        _LOGGER.debug("Username: %s", self._username)

        try:
            # Attempt to retrieve credentials from default cache file
            creds = gssapi.Credentials(usage="initiate")
            creds_upn = str(creds.name)

            _LOGGER.debug("Cached credentials found")
            _LOGGER.debug("Cached credentials UPN: %s", creds_upn)

            # Remove the realm from user
            if creds_upn.find("@") != -1:
                creds_user, creds_realm = creds_upn.split("@", 1)
            else:
                creds_user = creds_upn
                creds_realm = None

            upn = f"{self._username}@{realm}" if self._username else creds_upn

            # The user from cached credentials matches with the given user?
            if self._username and self._username != creds_user:
                _LOGGER.debug(
                    "The user from cached credentials doesn't match with the "
                    "given user"
                )
                if self._password is not None:
                    creds = self._acquire_cred_with_password(upn)
            if (
                creds_realm and creds_realm != realm and
                self._password is not None
            ):
                creds = self._acquire_cred_with_password(upn)
        except gssapi.raw.exceptions.ExpiredCredentialsError as err:
            if upn and self._password is not None:
                creds = self._acquire_cred_with_password(upn)
            else:
                raise errors.InterfaceError(f"Credentials has expired: {err}")
        except gssapi.raw.misc.GSSError as err:
            if upn and self._password is not None:
                creds = self._acquire_cred_with_password(upn)
            else:
                raise errors.InterfaceError(
                    f"Unable to retrieve cached credentials error: {err}"
                )

        flags = (
            gssapi.RequirementFlag.mutual_authentication,
            gssapi.RequirementFlag.extended_error,
            gssapi.RequirementFlag.delegate_to_peer
        )
        name = gssapi.Name(
            spn,
            name_type=gssapi.NameType.kerberos_principal
        )
        cname = name.canonicalize(gssapi.MechType.kerberos)
        self.context = gssapi.SecurityContext(
            name=cname,
            creds=creds,
            flags=sum(flags),
            usage="initiate"
        )

        try:
            initial_client_token = self.context.step()
        except gssapi.raw.misc.GSSError as err:
            raise errors.InterfaceError(
                f"Unable to initiate security context: {err}"
            )

        _LOGGER.debug("Initial client token: %s", initial_client_token)
        return initial_client_token

    def auth_continue(self, tgt_auth_challenge):
        """Continue with the Kerberos TGT service request.

        With the TGT authentication service given response generate a TGT
        service request. This method must be invoked sequentially (in a loop)
        until the security context is completed and an empty response needs to
        be send to acknowledge the server.

        Args:
            tgt_auth_challenge: the challenge for the negotiation.

        Returns:
            tuple (bytearray TGS service request,
            bool True if context is completed otherwise False).
        """
        _LOGGER.debug("tgt_auth challenge: %s", tgt_auth_challenge)

        resp = self.context.step(tgt_auth_challenge)

        _LOGGER.debug("Context step response: %s", resp)
        _LOGGER.debug("Context completed?: %s", self.context.complete)

        return resp, self.context.complete

    def auth_accept_close_handshake(self, message):
        """Accept handshake and generate closing handshake message for server.

        This method verifies the server authenticity from the given message
        and included signature and generates the closing handshake for the
        server.

        When this method is invoked the security context is already established
        and the client and server can send GSSAPI formated secure messages.

        To finish the authentication handshake the server sends a message
        with the security layer availability and the maximum buffer size.

        Since the connector only uses the GSSAPI authentication mechanism to
        authenticate the user with the server, the server will verify clients
        message signature and terminate the GSSAPI authentication and send two
        messages; an authentication acceptance b'\x01\x00\x00\x08\x01' and a
        OK packet (that must be received after sent the returned message from
        this method).

        Args:
            message: a wrapped gssapi message from the server.

        Returns:
            bytearray (closing handshake message to be send to the server).
        """
        if not self.context.complete:
            raise errors.ProgrammingError("Security context is not completed")
        _LOGGER.debug("Server message: %s", message)
        _LOGGER.debug("GSSAPI flags in use: %s", self.context.actual_flags)
        try:
            unwraped = self.context.unwrap(message)
            _LOGGER.debug("Unwraped: %s", unwraped)
        except gssapi.raw.exceptions.BadMICError as err:
            _LOGGER.debug("Unable to unwrap server message: %s", err)
            raise errors.InterfaceError(
                "Unable to unwrap server message: {}".format(err)
            )

        _LOGGER.debug("Unwrapped server message: %s", unwraped)
        # The message contents for the clients closing message:
        #   - security level 1 byte, must be always 1.
        #   - conciliated buffer size 3 bytes, without importance as no
        #     further GSSAPI messages will be sends.
        response = bytearray(b"\x01\x00\x00\00")
        # Closing handshake must not be encrypted.
        _LOGGER.debug("Message response: %s", response)
        wraped = self.context.wrap(response, encrypt=False)
        _LOGGER.debug(
            "Wrapped message response: %s, length: %d",
            wraped[0],
            len(wraped[0])
        )

        return wraped.message


class MySQL_OCI_AuthPlugin(BaseAuthPlugin):
    """Implement the MySQL OCI IAM authentication plugin."""

    plugin_name = "authentication_oci_client"
    requires_ssl = False
    context = None

    def _prepare_auth_response(self, signature, oci_config):
        """Prepare client's authentication response

        Prepares client's authentication response in JSON format
        Args:
            signature:  server's nonce to be signed by client.
            oci_config: OCI configuration object.

        Returns:
            JSON_STRING {"fingerprint": string, "signature": string}
        """
        signature_64 = b64encode(signature)
        auth_response = {
            "fingerprint": oci_config["fingerprint"],
            "signature": signature_64.decode()
        }
        return repr(auth_response).replace(" ", "").replace("'", '"')

    def _get_private_key(self, key_path):
        """Get the private_key form the given location"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise errors.ProgrammingError(
                "Package 'cryptography' is not installed"
            )
        try:
            with open(os.path.expanduser(key_path), "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                )
        except (TypeError, OSError, ValueError, UnsupportedAlgorithm) as err:
            raise errors.ProgrammingError(
                f'An error occurred while reading the API_KEY from "{key_path}":'
                f" {err}")

        return private_key

    def _get_valid_oci_config(self, oci_path=None, profile_name="DEFAULT"):
        """Get a valid OCI config from the given configuration file path"""
        try:
            from oci import config, exceptions
        except ImportError:
            raise errors.ProgrammingError(
                'Package "oci" (Oracle Cloud Infrastructure Python SDK)'
                ' is not installed.')
        if not oci_path:
            oci_path = config.DEFAULT_LOCATION

        error_list = []
        req_keys = {
            "fingerprint": (lambda x: len(x) > 32),
            "key_file": (lambda x: os.path.exists(os.path.expanduser(x)))
        }

        try:
            # key_file is validated by oci.config if present
            oci_config = config.from_file(oci_path, profile_name)
            for req_key in req_keys:
                try:
                    # Verify parameter in req_key is present and valid
                    if oci_config[req_key] \
                       and not req_keys[req_key](oci_config[req_key]):
                        error_list.append(f'Parameter "{req_key}" is invalid')
                except KeyError as err:
                    error_list.append(f'Does not contain parameter {req_key}')
        except (
            exceptions.ConfigFileNotFound,
            exceptions.InvalidConfig,
            exceptions.InvalidKeyFilePath,
            exceptions.InvalidPrivateKey,
            exceptions.MissingPrivateKeyPassphrase,
            exceptions.ProfileNotFound
        ) as err:
            error_list.append(str(err))

        # Raise errors if any
        if error_list:
            raise errors.ProgrammingError(
                f'Invalid profile {profile_name} in: "{oci_path}". '
                f" Errors found: {error_list}")

        return oci_config

    def auth_response(self, oci_path=None):
        """Prepare authentication string for the server."""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise errors.ProgrammingError(
                "Package 'cryptography' is not installed"
            )
        _LOGGER.debug("server nonce: %s, len %d",
                      self._auth_data, len(self._auth_data))
        _LOGGER.debug("OCI configuration file location: %s", oci_path)

        oci_config = self._get_valid_oci_config(oci_path)

        private_key = self._get_private_key(oci_config['key_file'])
        signature = private_key.sign(
            self._auth_data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        auth_response = self._prepare_auth_response(signature, oci_config)
        _LOGGER.debug("authentication response: %s", auth_response)
        return auth_response.encode()


class MySQLSSPIKerberosAuthPlugin(BaseAuthPlugin):
    """Implement the MySQL Kerberos authentication plugin with Windows SSPI"""

    plugin_name = "authentication_kerberos_client"
    requires_ssl = False
    context = None

    def _parse_auth_data(self, packet):
        """Parse authentication data.

        Get the SPN and REALM from the authentication data packet.

        Format:
            SPN string length two bytes <B1> <B2> +
            SPN string +
            UPN realm string length two bytes <B1> <B2> +
            UPN realm string

        Returns:
            tuple: With 'spn' and 'realm'.
        """
        spn_len = struct.unpack("<H", packet[:2])[0]
        packet = packet[2:]

        spn = struct.unpack(f"<{spn_len}s", packet[:spn_len])[0]
        packet = packet[spn_len:]

        realm_len = struct.unpack("<H", packet[:2])[0]
        realm = struct.unpack(f"<{realm_len}s", packet[2:])[0]

        return spn.decode(), realm.decode()

    def auth_response(self, auth_data=None):
        """Prepare the first message to the server."""
        _LOGGER.debug("auth_response for sspi")
        spn = None
        realm = None

        if auth_data:
            try:
                spn, realm = self._parse_auth_data(auth_data)
            except struct.error as err:
                raise InterruptedError(f"Invalid authentication data: {err}")

        _LOGGER.debug("Service Principal: %s", spn)
        _LOGGER.debug("Realm: %s", realm)
        _LOGGER.debug("Username: %s", self._username)

        if sspicon is None or sspi is None:
            raise errors.ProgrammingError(
                'Package "pywin32" (Python for Win32 (pywin32) extensions)'
                ' is not installed.')

        flags = (
            sspicon.ISC_REQ_MUTUAL_AUTH,
            sspicon.ISC_REQ_DELEGATE
        )

        if self._username and self._password:
            _auth_info = (self._username, realm, self._password)
        else:
            _auth_info = None

        targetspn = spn
        _LOGGER.debug("targetspn: %s", targetspn)
        _LOGGER.debug("_auth_info is None: %s", _auth_info is None)

        self.clientauth = sspi.ClientAuth(
            'Kerberos', targetspn=targetspn, auth_info=_auth_info,
            scflags=sum(flags), datarep=sspicon.SECURITY_NETWORK_DREP)

        try:
            data = None
            err, out_buf = self.clientauth.authorize(data)
            _LOGGER.debug("Context step err: %s", err)
            _LOGGER.debug("Context step out_buf: %s", out_buf)
            _LOGGER.debug("Context completed?: %s", self.clientauth.authenticated)
            initial_client_token = out_buf[0].Buffer
            _LOGGER.debug("pkg_info: %s", self.clientauth.pkg_info)
        except Exception as err:
            raise errors.InterfaceError(
                f"Unable to initiate security context: {err}"
            )

        _LOGGER.debug("Initial client token: %s", initial_client_token)
        return initial_client_token

    def auth_continue(self, tgt_auth_challenge):
        """Continue with the Kerberos TGT service request.

        With the TGT authentication service given response generate a TGT
        service request. This method must be invoked sequentially (in a loop)
        until the security context is completed and an empty response needs to
        be send to acknowledge the server.

        Args:
            tgt_auth_challenge: the challenge for the negotiation.

        Returns:
            tuple (bytearray TGS service request,
            bool True if context is completed otherwise False).
        """
        _LOGGER.debug("tgt_auth challenge: %s", tgt_auth_challenge)

        err, out_buf = self.clientauth.authorize(tgt_auth_challenge)

        _LOGGER.debug("Context step err: %s", err)
        _LOGGER.debug("Context step out_buf: %s", out_buf)
        resp = out_buf[0].Buffer
        _LOGGER.debug("Context step resp: %s", resp)
        _LOGGER.debug("Context completed?: %s", self.clientauth.authenticated)

        return resp, self.clientauth.authenticated


if os.name == 'nt':
    MySQLKerberosAuthPlugin = MySQLSSPIKerberosAuthPlugin


def get_auth_plugin(plugin_name):
    """Return authentication class based on plugin name

    This function returns the class for the authentication plugin plugin_name.
    The returned class is a subclass of BaseAuthPlugin.

    Raises errors.NotSupportedError when plugin_name is not supported.

    Returns subclass of BaseAuthPlugin.
    """
    for authclass in BaseAuthPlugin.__subclasses__():  # pylint: disable=E1101
        if authclass.plugin_name == plugin_name:
            return authclass

    raise errors.NotSupportedError(
        "Authentication plugin '{0}' is not supported".format(plugin_name))
