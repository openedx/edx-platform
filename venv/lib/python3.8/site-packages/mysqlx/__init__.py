# Copyright (c) 2016, 2020, Oracle and/or its affiliates.
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

"""MySQL X DevAPI Python implementation"""

import re
import json
import logging
import ssl

from urllib.parse import parse_qsl, unquote, urlparse

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from .connection import Client, Session
from .constants import (Auth, LockContention, OPENSSL_CS_NAMES, SSLMode,
                        TLS_VERSIONS, TLS_CIPHER_SUITES)
from .crud import Schema, Collection, Table, View
from .dbdoc import DbDoc
# pylint: disable=W0622
from .errors import (Error, InterfaceError, DatabaseError, NotSupportedError,
                     DataError, IntegrityError, ProgrammingError,
                     OperationalError, InternalError, PoolError, TimeoutError)
from .result import (Column, Row, Result, BufferingResult, RowResult,
                     SqlResult, DocResult, ColumnType)
from .statement import (Statement, FilterableStatement, SqlStatement,
                        FindStatement, AddStatement, RemoveStatement,
                        ModifyStatement, SelectStatement, InsertStatement,
                        DeleteStatement, UpdateStatement,
                        CreateCollectionIndexStatement, Expr, ReadStatement,
                        WriteStatement)
from .expr import ExprParser as expr


_SPLIT_RE = re.compile(r",(?![^\(\)]*\))")
_PRIORITY_RE = re.compile(r"^\(address=(.+),priority=(\d+)\)$", re.VERBOSE)
_ROUTER_RE = re.compile(r"^\(address=(.+)[,]*\)$", re.VERBOSE)
_URI_SCHEME_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+\-.]+)://(.*)")
_SSL_OPTS = ["ssl-cert", "ssl-ca", "ssl-key", "ssl-crl", "tls-versions",
             "tls-ciphersuites"]
_SESS_OPTS = _SSL_OPTS + ["user", "password", "schema", "host", "port",
                          "routers", "socket", "ssl-mode", "auth", "use-pure",
                          "connect-timeout", "connection-attributes",
                          "compression", "compression-algorithms", "dns-srv"]

logging.getLogger(__name__).addHandler(logging.NullHandler())

DUPLICATED_IN_LIST_ERROR = (
    "The '{list}' list must not contain repeated values, the value "
    "'{value}' is duplicated.")

TLS_VERSION_ERROR = ("The given tls-version: '{}' is not recognized as a "
                     "valid TLS protocol version (should be one of {}).")

TLS_VERSION_DEPRECATED_ERROR = ("The given tls_version: '{}' are no longer "
                                "allowed (should be one of {}).")

TLS_VER_NO_SUPPORTED = ("No supported TLS protocol version found in the "
                        "'tls-versions' list '{}'. ")

TLS_VERSIONS = ["TLSv1.2", "TLSv1.3"]

DEPRECATED_TLS_VERSIONS = ["TLSv1", "TLSv1.1"]

TLS_V1_3_SUPPORTED = False
if hasattr(ssl, "HAS_TLSv1_3") and ssl.HAS_TLSv1_3:
    TLS_V1_3_SUPPORTED = True


def _parse_address_list(path):
    """Parses a list of host, port pairs

    Args:
        path: String containing a list of routers or just router

    Returns:
        Returns a dict with parsed values of host, port and priority if
        specified.
    """
    path = path.replace(" ", "")
    array = not("," not in path and path.count(":") > 1
                and path.count("[") == 1) and path.startswith("[") \
                and path.endswith("]")

    routers = []
    address_list = _SPLIT_RE.split(path[1:-1] if array else path)
    priority_count = 0
    for address in address_list:
        router = {}

        match = _PRIORITY_RE.match(address)
        if match:
            address = match.group(1)
            router["priority"] = int(match.group(2))
            priority_count += 1
        else:
            match = _ROUTER_RE.match(address)
            if match:
                address = match.group(1)
                router["priority"] = 100

        match = urlparse("//{0}".format(address))
        if not match.hostname:
            raise InterfaceError("Invalid address: {0}".format(address))

        try:
            router.update(host=match.hostname, port=match.port)
        except ValueError as err:
            raise ProgrammingError("Invalid URI: {0}".format(err), 4002)

        routers.append(router)

    if 0 < priority_count < len(address_list):
        raise ProgrammingError("You must either assign no priority to any "
                               "of the routers or give a priority for "
                               "every router", 4000)

    return {"routers": routers} if array else routers[0]


def _parse_connection_uri(uri):
    """Parses the connection string and returns a dictionary with the
    connection settings.

    Args:
        uri: mysqlx URI scheme to connect to a MySQL server/farm.

    Returns:
        Returns a dict with parsed values of credentials and address of the
        MySQL server/farm.

    Raises:
        :class:`mysqlx.InterfaceError`: If contains a invalid option.
    """
    settings = {"schema": ""}

    match = _URI_SCHEME_RE.match(uri)
    scheme, uri = match.groups() if match else ("mysqlx", uri)

    if scheme not in ("mysqlx", "mysqlx+srv"):
        raise InterfaceError("Scheme '{0}' is not valid".format(scheme))

    if scheme == "mysqlx+srv":
        settings["dns-srv"] = True

    userinfo, tmp = uri.partition("@")[::2]
    host, query_str = tmp.partition("?")[::2]

    pos = host.rfind("/")
    if host[pos:].find(")") == -1 and pos > 0:
        host, settings["schema"] = host.rsplit("/", 1)
    host = host.strip("()")

    if not host or not userinfo or ":" not in userinfo:
        raise InterfaceError("Malformed URI '{0}'".format(uri))
    user, password = userinfo.split(":", 1)
    settings["user"], settings["password"] = unquote(user), unquote(password)

    if host.startswith(("/", "..", ".")):
        settings["socket"] = unquote(host)
    elif host.startswith("\\."):
        raise InterfaceError("Windows Pipe is not supported")
    else:
        settings.update(_parse_address_list(host))

    invalid_options = ("user", "password", "dns-srv")
    for key, val in parse_qsl(query_str, True):
        opt = key.replace("_", "-").lower()
        if opt in invalid_options:
            raise InterfaceError("Invalid option: '{0}'".format(key))
        if opt in _SSL_OPTS:
            settings[opt] = unquote(val.strip("()"))
        else:
            val_str = val.lower()
            if val_str in ("1", "true"):
                settings[opt] = True
            elif val_str in ("0", "false"):
                settings[opt] = False
            else:
                settings[opt] = val_str
    return settings


def _validate_settings(settings):
    """Validates the settings to be passed to a Session object
    the port values are converted to int if specified or set to 33060
    otherwise. The priority values for each router is converted to int
    if specified.

    Args:
        settings: dict containing connection settings.

    Raises:
        :class:`mysqlx.InterfaceError`: On any configuration issue.
    """
    invalid_opts = set(settings.keys()).difference(_SESS_OPTS)
    if invalid_opts:
        raise InterfaceError("Invalid option(s): '{0}'"
                             "".format("', '".join(invalid_opts)))

    if "routers" in settings:
        for router in settings["routers"]:
            _validate_hosts(router, 33060)
    elif "host" in settings:
        _validate_hosts(settings)

    if "ssl-mode" in settings:
        try:
            settings["ssl-mode"] = settings["ssl-mode"].lower()
            SSLMode.index(settings["ssl-mode"])
        except (AttributeError, ValueError):
            raise InterfaceError("Invalid SSL Mode '{0}'"
                                 "".format(settings["ssl-mode"]))

    if "ssl-crl" in settings and not "ssl-ca" in settings:
        raise InterfaceError("CA Certificate not provided")
    if "ssl-key" in settings and not "ssl-cert" in settings:
        raise InterfaceError("Client Certificate not provided")

    if not "ssl-ca" in settings and settings.get("ssl-mode") \
        in [SSLMode.VERIFY_IDENTITY, SSLMode.VERIFY_CA]:
        raise InterfaceError("Cannot verify Server without CA")
    if "ssl-ca" in settings and settings.get("ssl-mode") \
        not in [SSLMode.VERIFY_IDENTITY, SSLMode.VERIFY_CA, SSLMode.DISABLED]:
        raise InterfaceError("Must verify Server if CA is provided")

    if "auth" in settings:
        try:
            settings["auth"] = settings["auth"].lower()
            Auth.index(settings["auth"])
        except (AttributeError, ValueError):
            raise InterfaceError("Invalid Auth '{0}'".format(settings["auth"]))

    if "compression" in settings:
        compression = settings["compression"].lower().strip()
        if compression not in ("preferred", "required", "disabled"):
            raise InterfaceError(
                "The connection property 'compression' acceptable values are: "
                "'preferred', 'required', or 'disabled'. The value '{0}' is "
                "not acceptable".format(settings["compression"]))
        settings["compression"] = compression

    if "compression-algorithms" in settings:
        if isinstance(settings["compression-algorithms"], str):
            compression_algorithms = \
                settings["compression-algorithms"].strip().strip("[]")
            if compression_algorithms:
                settings["compression-algorithms"] = \
                    compression_algorithms.split(",")
            else:
                settings["compression-algorithms"] = None
        elif not isinstance(settings["compression-algorithms"], (list, tuple)):
            raise InterfaceError("Invalid type of the connection property "
                                 "'compression-algorithms'")
        if settings.get("compression") == "disabled":
            settings["compression-algorithms"] = None

    if "connection-attributes" in settings:
        _validate_connection_attributes(settings)

    if "connect-timeout" in settings:
        try:
            if isinstance(settings["connect-timeout"], str):
                settings["connect-timeout"] = int(settings["connect-timeout"])
            if not isinstance(settings["connect-timeout"], int) \
               or settings["connect-timeout"] < 0:
                raise ValueError
        except ValueError:
            raise TypeError("The connection timeout value must be a positive "
                            "integer (including 0)")

    if "dns-srv" in settings:
        if not isinstance(settings["dns-srv"], bool):
            raise InterfaceError("The value of 'dns-srv' must be a boolean")
        if settings.get("socket"):
            raise InterfaceError("Using Unix domain sockets with DNS SRV "
                                 "lookup is not allowed")
        if settings.get("port"):
            raise InterfaceError("Specifying a port number with DNS SRV "
                                 "lookup is not allowed")
        if settings.get("routers"):
            raise InterfaceError("Specifying multiple hostnames with DNS "
                                 "SRV look up is not allowed")
    elif "host" in settings and not settings.get("port"):
        settings["port"] = 33060

    if "tls-versions" in settings:
        _validate_tls_versions(settings)

    if "tls-ciphersuites" in settings:
        _validate_tls_ciphersuites(settings)


def _validate_hosts(settings, default_port=None):
    """Validate hosts.

    Args:
        settings (dict): Settings dictionary.
        default_port (int): Default connection port.

    Raises:
        :class:`mysqlx.InterfaceError`: If priority or port are invalid.
    """
    if "priority" in settings and settings["priority"]:
        try:
            settings["priority"] = int(settings["priority"])
            if settings["priority"] < 0 or settings["priority"] > 100:
                raise ProgrammingError("Invalid priority value, "
                                       "must be between 0 and 100", 4007)
        except NameError:
            raise ProgrammingError("Invalid priority", 4007)
        except ValueError:
            raise ProgrammingError(
                "Invalid priority: {}".format(settings["priority"]), 4007)

    if "port" in settings and settings["port"]:
        try:
            settings["port"] = int(settings["port"])
        except NameError:
            raise InterfaceError("Invalid port")
    elif "host" in settings and default_port:
        settings["port"] = default_port


def _validate_connection_attributes(settings):
    """Validate connection-attributes.

    Args:
        settings (dict): Settings dictionary.

    Raises:
        :class:`mysqlx.InterfaceError`: If attribute name or value exceeds size.
    """
    attributes = {}
    if "connection-attributes" not in settings:
        return

    conn_attrs = settings["connection-attributes"]

    if isinstance(conn_attrs, str):
        if conn_attrs == "":
            settings["connection-attributes"] = {}
            return
        if not (conn_attrs.startswith("[") and conn_attrs.endswith("]")) and \
           not conn_attrs in ['False', "false", "True", "true"]:
            raise InterfaceError("The value of 'connection-attributes' must "
                                 "be a boolean or a list of key-value pairs, "
                                 "found: '{}'".format(conn_attrs))
        elif conn_attrs in ['False', "false", "True", "true"]:
            if conn_attrs in ['False', "false"]:
                settings["connection-attributes"] = False
            else:
                settings["connection-attributes"] = {}
            return
        else:
            conn_attributes = conn_attrs[1:-1].split(",")
            for attr in conn_attributes:
                if attr == "":
                    continue
                attr_name_val = attr.split('=')
                attr_name = attr_name_val[0]
                attr_val = attr_name_val[1] if len(attr_name_val) > 1 else ""
                if attr_name in attributes:
                    raise InterfaceError("Duplicate key '{}' used in "
                                         "connection-attributes"
                                         "".format(attr_name))
                else:
                    attributes[attr_name] = attr_val
    elif isinstance(conn_attrs, dict):
        for attr_name in conn_attrs:
            attr_value = conn_attrs[attr_name]
            if not isinstance(attr_value, str):
                attr_value = repr(attr_value)
            attributes[attr_name] = attr_value
    elif isinstance(conn_attrs, bool) or conn_attrs in [0, 1]:
        if conn_attrs:
            settings["connection-attributes"] = {}
        else:
            settings["connection-attributes"] = False
        return
    elif isinstance(conn_attrs, set):
        for attr_name in conn_attrs:
            attributes[attr_name] = ""
    elif isinstance(conn_attrs, list):
        for attr in conn_attrs:
            if attr == "":
                continue
            attr_name_val = attr.split('=')
            attr_name = attr_name_val[0]
            attr_val = attr_name_val[1] if len(attr_name_val) > 1 else ""
            if attr_name in attributes:
                raise InterfaceError("Duplicate key '{}' used in "
                                     "connection-attributes"
                                     "".format(attr_name))
            else:
                attributes[attr_name] = attr_val
    elif not isinstance(conn_attrs, bool):
        raise InterfaceError("connection-attributes must be Boolean or a list "
                             "of key-value pairs, found: '{}'"
                             "".format(conn_attrs))

    if attributes:
        for attr_name in attributes:
            attr_value = attributes[attr_name]

            # Validate name type
            if not isinstance(attr_name, str):
                raise InterfaceError("Attribute name '{}' must be a string"
                                     "type".format(attr_name))
            # Validate attribute name limit 32 characters
            if len(attr_name) > 32:
                raise InterfaceError("Attribute name '{}' exceeds 32 "
                                     "characters limit size".format(attr_name))
            # Validate names in connection-attributes cannot start with "_"
            if attr_name.startswith("_"):
                raise InterfaceError("Key names in connection-attributes "
                                     "cannot start with '_', found: '{}'"
                                     "".format(attr_name))

            # Validate value type
            if not isinstance(attr_value, str):
                raise InterfaceError("Attribute '{}' value: '{}' must "
                                     "be a string type"
                                     "".format(attr_name, attr_value))
            # Validate attribute value limit 1024 characters
            if len(attr_value) > 1024:
                raise InterfaceError("Attribute '{}' value: '{}' "
                                     "exceeds 1024 characters limit size"
                                     "".format(attr_name, attr_value))

    settings["connection-attributes"] = attributes


def _validate_tls_versions(settings):
    """Validate tls-versions.

    Args:
        settings (dict): Settings dictionary.

    Raises:
        :class:`mysqlx.InterfaceError`: If tls-versions name is not valid.
    """
    tls_versions = []
    if "tls-versions" not in settings:
        return

    tls_versions_settings = settings["tls-versions"]

    if isinstance(tls_versions_settings, str):
        if not (tls_versions_settings.startswith("[") and
                tls_versions_settings.endswith("]")):
            raise InterfaceError("tls-versions must be a list, found: '{}'"
                                 "".format(tls_versions_settings))
        else:
            tls_vers = tls_versions_settings[1:-1].split(",")
            for tls_ver in tls_vers:
                tls_version = tls_ver.strip()
                if tls_version == "":
                    continue
                else:
                    if tls_version in tls_versions:
                        raise InterfaceError(
                            DUPLICATED_IN_LIST_ERROR.format(
                                list="tls_versions", value=tls_version))
                    tls_versions.append(tls_version)
    elif isinstance(tls_versions_settings, list):
        if not tls_versions_settings:
            raise InterfaceError("At least one TLS protocol version must be "
                                 "specified in 'tls-versions' list.")
        for tls_ver in tls_versions_settings:
            if tls_ver in tls_versions:
                raise InterfaceError(
                    DUPLICATED_IN_LIST_ERROR.format(list="tls_versions",
                                                    value=tls_ver))
            else:
                tls_versions.append(tls_ver)

    elif isinstance(tls_versions_settings, set):
        for tls_ver in tls_versions_settings:
            tls_versions.append(tls_ver)
    else:
        raise InterfaceError("tls-versions should be a list with one or more "
                             "of versions in {}. found: '{}'"
                             "".format(", ".join(TLS_VERSIONS), tls_versions))

    if not tls_versions:
        raise InterfaceError("At least one TLS protocol version must be "
                             "specified in 'tls-versions' list.")

    use_tls_versions = []
    deprecated_tls_versions = []
    not_tls_versions = []
    for tls_ver in tls_versions:
        if tls_ver in TLS_VERSIONS:
            use_tls_versions.append(tls_ver)
        if tls_ver in DEPRECATED_TLS_VERSIONS:
            deprecated_tls_versions.append(tls_ver)
        else:
            not_tls_versions.append(tls_ver)

    if use_tls_versions:
        if use_tls_versions == ["TLSv1.3"] and not TLS_V1_3_SUPPORTED:
            raise NotSupportedError(
                TLS_VER_NO_SUPPORTED.format(tls_versions, TLS_VERSIONS))
        use_tls_versions.sort()
        settings["tls-versions"] = use_tls_versions
    elif deprecated_tls_versions:
        raise NotSupportedError(
            TLS_VERSION_DEPRECATED_ERROR.format(deprecated_tls_versions,
                                                TLS_VERSIONS))
    elif not_tls_versions:
        raise InterfaceError(
            TLS_VERSION_ERROR.format(tls_ver, TLS_VERSIONS))


def _validate_tls_ciphersuites(settings):
    """Validate tls-ciphersuites.

    Args:
        settings (dict): Settings dictionary.

    Raises:
        :class:`mysqlx.InterfaceError`: If tls-ciphersuites name is not valid.
    """
    tls_ciphersuites = []
    if "tls-ciphersuites" not in settings:
        return

    tls_ciphersuites_settings = settings["tls-ciphersuites"]

    if isinstance(tls_ciphersuites_settings, str):
        if not (tls_ciphersuites_settings.startswith("[") and
                tls_ciphersuites_settings.endswith("]")):
            raise InterfaceError("tls-ciphersuites must be a list, found: '{}'"
                                 "".format(tls_ciphersuites_settings))
        else:
            tls_css = tls_ciphersuites_settings[1:-1].split(",")
            if not tls_css:
                raise InterfaceError("No valid cipher suite found in the "
                                     "'tls-ciphersuites' list.")
            for tls_cs in tls_css:
                tls_cs = tls_cs.strip().upper()
                if tls_cs:
                    tls_ciphersuites.append(tls_cs)
    elif isinstance(tls_ciphersuites_settings, list):
        tls_ciphersuites = [tls_cs for tls_cs in tls_ciphersuites_settings
                            if tls_cs]

    elif isinstance(tls_ciphersuites_settings, set):
        for tls_cs in tls_ciphersuites:
            if tls_cs:
                tls_ciphersuites.append(tls_cs)
    else:
        raise InterfaceError("tls-ciphersuites should be a list with one or "
                             "more ciphersuites. Found: '{}'"
                             "".format(tls_ciphersuites_settings))

    tls_versions = TLS_VERSIONS[:] if settings.get("tls-versions", None) \
       is None else settings["tls-versions"][:]

    # A newer TLS version can use a cipher introduced on
    # an older version.
    tls_versions.sort(reverse=True)
    newer_tls_ver = tls_versions[0]

    translated_names = []
    iani_cipher_suites_names = {}
    ossl_cipher_suites_names = []

    # Old ciphers can work with new TLS versions.
    # Find all the ciphers introduced on previous TLS versions
    for tls_ver in TLS_VERSIONS[:TLS_VERSIONS.index(newer_tls_ver) + 1]:
        iani_cipher_suites_names.update(TLS_CIPHER_SUITES[tls_ver])
        ossl_cipher_suites_names.extend(OPENSSL_CS_NAMES[tls_ver])

    for name in tls_ciphersuites:
        if "-" in name and name in ossl_cipher_suites_names:
            translated_names.append(name)
        elif name in iani_cipher_suites_names:
            translated_name = iani_cipher_suites_names[name]
            if translated_name in translated_names:
                raise AttributeError(
                    DUPLICATED_IN_LIST_ERROR.format(
                        list="tls_ciphersuites", value=translated_name))
            else:
                translated_names.append(translated_name)
        else:
            raise InterfaceError(
                "The value '{}' in cipher suites is not a valid "
                "cipher suite".format(name))

    if not translated_names:
        raise InterfaceError("No valid cipher suite found in the "
                             "'tls-ciphersuites' list.")

    settings["tls-ciphersuites"] = translated_names


def _get_connection_settings(*args, **kwargs):
    """Parses the connection string and returns a dictionary with the
    connection settings.

    Args:
        *args: Variable length argument list with the connection data used
               to connect to the database. It can be a dictionary or a
               connection string.
        **kwargs: Arbitrary keyword arguments with connection data used to
                  connect to the database.

    Returns:
        mysqlx.Session: Session object.

    Raises:
        TypeError: If connection timeout is not a positive integer.
        :class:`mysqlx.InterfaceError`: If settings not provided.
    """
    settings = {}
    if args:
        if isinstance(args[0], str):
            settings = _parse_connection_uri(args[0])
        elif isinstance(args[0], dict):
            for key, val in args[0].items():
                settings[key.replace("_", "-")] = val
    elif kwargs:
        for key, val in kwargs.items():
            settings[key.replace("_", "-")] = val

    if not settings:
        raise InterfaceError("Settings not provided")

    _validate_settings(settings)
    return settings


def get_session(*args, **kwargs):
    """Creates a Session instance using the provided connection data.

    Args:
        *args: Variable length argument list with the connection data used
               to connect to a MySQL server. It can be a dictionary or a
               connection string.
        **kwargs: Arbitrary keyword arguments with connection data used to
                  connect to the database.

    Returns:
        mysqlx.Session: Session object.
    """
    settings = _get_connection_settings(*args, **kwargs)
    return Session(settings)


def get_client(connection_string, options_string):
    """Creates a Client instance with the provided connection data and settings.

    Args:
        connection_string: A string or a dict type object to indicate the \
            connection data used to connect to a MySQL server.

            The string must have the following uri format::

                cnx_str = 'mysqlx://{user}:{pwd}@{host}:{port}'
                cnx_str = ('mysqlx://{user}:{pwd}@['
                           '    (address={host}:{port}, priority=n),'
                           '    (address={host}:{port}, priority=n), ...]'
                           '       ?[option=value]')

            And the dictionary::

                cnx_dict = {
                    'host': 'The host where the MySQL product is running',
                    'port': '(int) the port number configured for X protocol',
                    'user': 'The user name account',
                    'password': 'The password for the given user account',
                    'ssl-mode': 'The flags for ssl mode in mysqlx.SSLMode.FLAG',
                    'ssl-ca': 'The path to the ca.cert'
                    "connect-timeout": '(int) milliseconds to wait on timeout'
                }

        options_string: A string in the form of a document or a dictionary \
            type with configuration for the client.

            Current options include::

                options = {
                    'pooling': {
                        'enabled': (bool), # [True | False], True by default
                        'max_size': (int), # Maximum connections per pool
                        "max_idle_time": (int), # milliseconds that a
                            # connection will remain active while not in use.
                            # By default 0, means infinite.
                        "queue_timeout": (int), # milliseconds a request will
                            # wait for a connection to become available.
                            # By default 0, means infinite.
                    }
                }

    Returns:
        mysqlx.Client: Client object.

    .. versionadded:: 8.0.13
    """
    if not isinstance(connection_string, (str, dict)):
        raise InterfaceError("connection_data must be a string or dict")

    settings_dict = _get_connection_settings(connection_string)

    if not isinstance(options_string, (str, dict)):
        raise InterfaceError("connection_options must be a string or dict")

    if isinstance(options_string, str):
        try:
            options_dict = json.loads(options_string)
        except JSONDecodeError:
            raise InterfaceError("'pooling' options must be given in the form "
                                 "of a document or dict")
    else:
        options_dict = {}
        for key, value in options_string.items():
            options_dict[key.replace("-", "_")] = value

    if not isinstance(options_dict, dict):
        raise InterfaceError("'pooling' options must be given in the form of a "
                             "document or dict")
    pooling_options_dict = {}
    if "pooling" in options_dict:
        pooling_options = options_dict.pop("pooling")
        if not isinstance(pooling_options, (dict)):
            raise InterfaceError("'pooling' options must be given in the form "
                                 "document or dict")
        # Fill default pooling settings
        pooling_options_dict["enabled"] = pooling_options.pop("enabled", True)
        pooling_options_dict["max_size"] = pooling_options.pop("max_size", 25)
        pooling_options_dict["max_idle_time"] = \
            pooling_options.pop("max_idle_time", 0)
        pooling_options_dict["queue_timeout"] = \
            pooling_options.pop("queue_timeout", 0)

        # No other options besides pooling are supported
        if len(pooling_options) > 0:
            raise InterfaceError("Unrecognized pooling options: {}"
                                 "".format(pooling_options))
        # No other options besides pooling are supported
        if len(options_dict) > 0:
            raise InterfaceError("Unrecognized connection options: {}"
                                 "".format(options_dict.keys()))

    return Client(settings_dict, pooling_options_dict)


__all__ = [
    # mysqlx.connection
    "Client", "Session", "get_client", "get_session", "expr",

    # mysqlx.constants
    "Auth", "LockContention", "SSLMode",

    # mysqlx.crud
    "Schema", "Collection", "Table", "View",

    # mysqlx.errors
    "Error", "InterfaceError", "DatabaseError", "NotSupportedError",
    "DataError", "IntegrityError", "ProgrammingError", "OperationalError",
    "InternalError", "PoolError", "TimeoutError",

    # mysqlx.result
    "Column", "Row", "Result", "BufferingResult", "RowResult",
    "SqlResult", "DocResult", "ColumnType",

    # mysqlx.statement
    "DbDoc", "Statement", "FilterableStatement", "SqlStatement",
    "FindStatement", "AddStatement", "RemoveStatement", "ModifyStatement",
    "SelectStatement", "InsertStatement", "DeleteStatement", "UpdateStatement",
    "ReadStatement", "WriteStatement", "CreateCollectionIndexStatement",
    "Expr",
]
