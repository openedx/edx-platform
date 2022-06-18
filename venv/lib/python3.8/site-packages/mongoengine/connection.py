import warnings

from pymongo import MongoClient, ReadPreference, uri_parser
from pymongo.database import _check_name

from mongoengine.pymongo_support import PYMONGO_VERSION

__all__ = [
    "DEFAULT_CONNECTION_NAME",
    "DEFAULT_DATABASE_NAME",
    "ConnectionFailure",
    "connect",
    "disconnect",
    "disconnect_all",
    "get_connection",
    "get_db",
    "register_connection",
]


DEFAULT_CONNECTION_NAME = "default"
DEFAULT_DATABASE_NAME = "test"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 27017

_connection_settings = {}
_connections = {}
_dbs = {}

READ_PREFERENCE = ReadPreference.PRIMARY


class ConnectionFailure(Exception):
    """Error raised when the database connection can't be established or
    when a connection with a requested alias can't be retrieved.
    """

    pass


def _check_db_name(name):
    """Check if a database name is valid.
    This functionality is copied from pymongo Database class constructor.
    """
    if not isinstance(name, str):
        raise TypeError("name must be an instance of %s" % str)
    elif name != "$external":
        _check_name(name)


def _get_connection_settings(
    db=None,
    name=None,
    host=None,
    port=None,
    read_preference=READ_PREFERENCE,
    username=None,
    password=None,
    authentication_source=None,
    authentication_mechanism=None,
    **kwargs,
):
    """Get the connection settings as a dict

    :param db: the name of the database to use, for compatibility with connect
    :param name: the name of the specific database to use
    :param host: the host name of the: program: `mongod` instance to connect to
    :param port: the port that the: program: `mongod` instance is running on
    :param read_preference: The read preference for the collection
    :param username: username to authenticate with
    :param password: password to authenticate with
    :param authentication_source: database to authenticate against
    :param authentication_mechanism: database authentication mechanisms.
        By default, use SCRAM-SHA-1 with MongoDB 3.0 and later,
        MONGODB-CR (MongoDB Challenge Response protocol) for older servers.
    :param is_mock: explicitly use mongomock for this connection
        (can also be done by using `mongomock: // ` as db host prefix)
    :param kwargs: ad-hoc parameters to be passed into the pymongo driver,
        for example maxpoolsize, tz_aware, etc. See the documentation
        for pymongo's `MongoClient` for a full list.
    """
    conn_settings = {
        "name": name or db or DEFAULT_DATABASE_NAME,
        "host": host or DEFAULT_HOST,
        "port": port or DEFAULT_PORT,
        "read_preference": read_preference,
        "username": username,
        "password": password,
        "authentication_source": authentication_source,
        "authentication_mechanism": authentication_mechanism,
    }

    _check_db_name(conn_settings["name"])
    conn_host = conn_settings["host"]

    # Host can be a list or a string, so if string, force to a list.
    if isinstance(conn_host, str):
        conn_host = [conn_host]

    resolved_hosts = []
    for entity in conn_host:

        # Handle Mongomock
        if entity.startswith("mongomock://"):
            conn_settings["is_mock"] = True
            # `mongomock://` is not a valid url prefix and must be replaced by `mongodb://`
            new_entity = entity.replace("mongomock://", "mongodb://", 1)
            resolved_hosts.append(new_entity)

            uri_dict = uri_parser.parse_uri(new_entity)

            database = uri_dict.get("database")
            if database:
                conn_settings["name"] = database

        # Handle URI style connections, only updating connection params which
        # were explicitly specified in the URI.
        elif "://" in entity:
            uri_dict = uri_parser.parse_uri(entity)
            resolved_hosts.append(entity)

            database = uri_dict.get("database")
            if database:
                conn_settings["name"] = database

            for param in ("read_preference", "username", "password"):
                if uri_dict.get(param):
                    conn_settings[param] = uri_dict[param]

            uri_options = uri_dict["options"]
            if "replicaset" in uri_options:
                conn_settings["replicaSet"] = uri_options["replicaset"]
            if "authsource" in uri_options:
                conn_settings["authentication_source"] = uri_options["authsource"]
            if "authmechanism" in uri_options:
                conn_settings["authentication_mechanism"] = uri_options["authmechanism"]
            if "readpreference" in uri_options:
                read_preferences = (
                    ReadPreference.NEAREST,
                    ReadPreference.PRIMARY,
                    ReadPreference.PRIMARY_PREFERRED,
                    ReadPreference.SECONDARY,
                    ReadPreference.SECONDARY_PREFERRED,
                )

                # Starting with PyMongo v3.5, the "readpreference" option is
                # returned as a string (e.g. "secondaryPreferred") and not an
                # int (e.g. 3).
                # TODO simplify the code below once we drop support for
                # PyMongo v3.4.
                read_pf_mode = uri_options["readpreference"]
                if isinstance(read_pf_mode, str):
                    read_pf_mode = read_pf_mode.lower()
                for preference in read_preferences:
                    if (
                        preference.name.lower() == read_pf_mode
                        or preference.mode == read_pf_mode
                    ):
                        conn_settings["read_preference"] = preference
                        break
        else:
            resolved_hosts.append(entity)
    conn_settings["host"] = resolved_hosts

    # Deprecated parameters that should not be passed on
    kwargs.pop("slaves", None)
    kwargs.pop("is_slave", None)

    if "uuidRepresentation" not in kwargs:
        warnings.warn(
            "No uuidRepresentation is specified! Falling back to "
            "'pythonLegacy' which is the default for pymongo 3.x. "
            "For compatibility with other MongoDB drivers this should be "
            "specified as 'standard' or '{java,csharp}Legacy' to work with "
            "older drivers in those languages. This will be changed to "
            "'standard' in a future release.",
            DeprecationWarning,
        )
        kwargs["uuidRepresentation"] = "pythonLegacy"

    conn_settings.update(kwargs)
    return conn_settings


def register_connection(
    alias,
    db=None,
    name=None,
    host=None,
    port=None,
    read_preference=READ_PREFERENCE,
    username=None,
    password=None,
    authentication_source=None,
    authentication_mechanism=None,
    **kwargs,
):
    """Register the connection settings.

    :param alias: the name that will be used to refer to this connection throughout MongoEngine
    :param db: the name of the database to use, for compatibility with connect
    :param name: the name of the specific database to use
    :param host: the host name of the: program: `mongod` instance to connect to
    :param port: the port that the: program: `mongod` instance is running on
    :param read_preference: The read preference for the collection
    :param username: username to authenticate with
    :param password: password to authenticate with
    :param authentication_source: database to authenticate against
    :param authentication_mechanism: database authentication mechanisms.
        By default, use SCRAM-SHA-1 with MongoDB 3.0 and later,
        MONGODB-CR (MongoDB Challenge Response protocol) for older servers.
    :param is_mock: explicitly use mongomock for this connection
        (can also be done by using `mongomock: // ` as db host prefix)
    :param kwargs: ad-hoc parameters to be passed into the pymongo driver,
        for example maxpoolsize, tz_aware, etc. See the documentation
        for pymongo's `MongoClient` for a full list.
    """
    conn_settings = _get_connection_settings(
        db=db,
        name=name,
        host=host,
        port=port,
        read_preference=read_preference,
        username=username,
        password=password,
        authentication_source=authentication_source,
        authentication_mechanism=authentication_mechanism,
        **kwargs,
    )
    _connection_settings[alias] = conn_settings


def disconnect(alias=DEFAULT_CONNECTION_NAME):
    """Close the connection with a given alias."""
    from mongoengine import Document
    from mongoengine.base.common import _get_documents_by_db

    if alias in _connections:
        get_connection(alias=alias).close()
        del _connections[alias]

    if alias in _dbs:
        # Detach all cached collections in Documents
        for doc_cls in _get_documents_by_db(alias, DEFAULT_CONNECTION_NAME):
            if issubclass(doc_cls, Document):  # Skip EmbeddedDocument
                doc_cls._disconnect()

        del _dbs[alias]

    if alias in _connection_settings:
        del _connection_settings[alias]


def disconnect_all():
    """Close all registered database."""
    for alias in list(_connections.keys()):
        disconnect(alias)


def get_connection(alias=DEFAULT_CONNECTION_NAME, reconnect=False):
    """Return a connection with a given alias."""

    # Connect to the database if not already connected
    if reconnect:
        disconnect(alias)

    # If the requested alias already exists in the _connections list, return
    # it immediately.
    if alias in _connections:
        return _connections[alias]

    # Validate that the requested alias exists in the _connection_settings.
    # Raise ConnectionFailure if it doesn't.
    if alias not in _connection_settings:
        if alias == DEFAULT_CONNECTION_NAME:
            msg = "You have not defined a default connection"
        else:
            msg = 'Connection with alias "%s" has not been defined' % alias
        raise ConnectionFailure(msg)

    def _clean_settings(settings_dict):
        if PYMONGO_VERSION < (4,):
            irrelevant_fields_set = {
                "name",
                "username",
                "password",
                "authentication_source",
                "authentication_mechanism",
            }
            rename_fields = {}
        else:
            irrelevant_fields_set = {"name"}
            rename_fields = {
                "authentication_source": "authSource",
                "authentication_mechanism": "authMechanism",
            }
        return {
            rename_fields.get(k, k): v
            for k, v in settings_dict.items()
            if k not in irrelevant_fields_set and v is not None
        }

    raw_conn_settings = _connection_settings[alias].copy()

    # Retrieve a copy of the connection settings associated with the requested
    # alias and remove the database name and authentication info (we don't
    # care about them at this point).
    conn_settings = _clean_settings(raw_conn_settings)

    # Determine if we should use PyMongo's or mongomock's MongoClient.
    is_mock = conn_settings.pop("is_mock", False)
    if is_mock:
        try:
            import mongomock
        except ImportError:
            raise RuntimeError("You need mongomock installed to mock MongoEngine.")
        connection_class = mongomock.MongoClient
    else:
        connection_class = MongoClient

    # Re-use existing connection if one is suitable.
    existing_connection = _find_existing_connection(raw_conn_settings)
    if existing_connection:
        connection = existing_connection
    else:
        connection = _create_connection(
            alias=alias, connection_class=connection_class, **conn_settings
        )
    _connections[alias] = connection
    return _connections[alias]


def _create_connection(alias, connection_class, **connection_settings):
    """
    Create the new connection for this alias. Raise
    ConnectionFailure if it can't be established.
    """
    try:
        return connection_class(**connection_settings)
    except Exception as e:
        raise ConnectionFailure(f"Cannot connect to database {alias} :\n{e}")


def _find_existing_connection(connection_settings):
    """
    Check if an existing connection could be reused

    Iterate over all of the connection settings and if an existing connection
    with the same parameters is suitable, return it

    :param connection_settings: the settings of the new connection
    :return: An existing connection or None
    """
    connection_settings_bis = (
        (db_alias, settings.copy())
        for db_alias, settings in _connection_settings.items()
    )

    def _clean_settings(settings_dict):
        # Only remove the name but it's important to
        # keep the username/password/authentication_source/authentication_mechanism
        # to identify if the connection could be shared (cfr https://github.com/MongoEngine/mongoengine/issues/2047)
        return {k: v for k, v in settings_dict.items() if k != "name"}

    cleaned_conn_settings = _clean_settings(connection_settings)
    for db_alias, connection_settings in connection_settings_bis:
        db_conn_settings = _clean_settings(connection_settings)
        if cleaned_conn_settings == db_conn_settings and _connections.get(db_alias):
            return _connections[db_alias]


def get_db(alias=DEFAULT_CONNECTION_NAME, reconnect=False):
    if reconnect:
        disconnect(alias)

    if alias not in _dbs:
        conn = get_connection(alias)
        conn_settings = _connection_settings[alias]
        db = conn[conn_settings["name"]]
        # Authenticate if necessary
        if (
            PYMONGO_VERSION < (4,)
            and conn_settings["username"]
            and (
                conn_settings["password"]
                or conn_settings["authentication_mechanism"] == "MONGODB-X509"
            )
        ):
            auth_kwargs = {"source": conn_settings["authentication_source"]}
            if conn_settings["authentication_mechanism"] is not None:
                auth_kwargs["mechanism"] = conn_settings["authentication_mechanism"]
            db.authenticate(
                conn_settings["username"], conn_settings["password"], **auth_kwargs
            )
        _dbs[alias] = db
    return _dbs[alias]


def connect(db=None, alias=DEFAULT_CONNECTION_NAME, **kwargs):
    """Connect to the database specified by the 'db' argument.

    Connection settings may be provided here as well if the database is not
    running on the default port on localhost. If authentication is needed,
    provide username and password arguments as well.

    Multiple databases are supported by using aliases. Provide a separate
    `alias` to connect to a different instance of: program: `mongod`.

    In order to replace a connection identified by a given alias, you'll
    need to call ``disconnect`` first

    See the docstring for `register_connection` for more details about all
    supported kwargs.
    """
    if alias in _connections:
        prev_conn_setting = _connection_settings[alias]
        new_conn_settings = _get_connection_settings(db, **kwargs)

        if new_conn_settings != prev_conn_setting:
            err_msg = (
                "A different connection with alias `{}` was already "
                "registered. Use disconnect() first"
            ).format(alias)
            raise ConnectionFailure(err_msg)
    else:
        register_connection(alias, db, **kwargs)

    return get_connection(alias)


# Support old naming convention
_get_connection = get_connection
_get_db = get_db
