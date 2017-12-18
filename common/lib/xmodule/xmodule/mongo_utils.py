"""
Common MongoDB connection functions.
"""
import logging

import pymongo
from pymongo import ReadPreference
from mongodb_proxy import MongoProxy

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


# pylint: disable=bad-continuation
def connect_to_mongodb(
    db, host,
    port=27017, tz_aware=True, user=None, password=None,
    retry_wait_time=0.1, proxy=True, **kwargs
):
    """
    Returns a MongoDB Database connection, optionally wrapped in a proxy. The proxy
    handles AutoReconnect errors by retrying read operations, since these exceptions
    typically indicate a temporary step-down condition for MongoDB.
    """
    # The MongoReplicaSetClient class is deprecated in Mongo 3.x, in favor of using
    # the MongoClient class for all connections. Update/simplify this code when using
    # PyMongo 3.x.
    if kwargs.get('replicaSet'):
        # Enable reading from secondary nodes in the MongoDB replicaset by using the
        # MongoReplicaSetClient class.
        # The 'replicaSet' parameter in kwargs is required for secondary reads.
        # The read_preference should be set to a proper value, like SECONDARY_PREFERRED.
        mongo_client_class = pymongo.MongoReplicaSetClient
    else:
        # No 'replicaSet' in kwargs - so no secondary reads.
        mongo_client_class = pymongo.MongoClient

    # If read_preference is given as a name of a valid ReadPreference.<NAME> constant
    # such as "SECONDARY_PREFERRED", convert it. Otherwise pass it through unchanged.
    if 'read_preference' in kwargs:
        read_preference = getattr(ReadPreference, kwargs['read_preference'], None)
        if read_preference is not None:
            kwargs['read_preference'] = read_preference

    mongo_conn = pymongo.database.Database(
        mongo_client_class(
            host=host,
            port=port,
            tz_aware=tz_aware,
            document_class=dict,
            **kwargs
        ),
        db
    )

    if proxy:
        mongo_conn = MongoProxy(
            mongo_conn,
            wait_time=retry_wait_time
        )

    # If credentials were provided, authenticate the user.
    if user is not None and password is not None:
        mongo_conn.authenticate(user, password)

    return mongo_conn


def create_collection_index(
    collection, keys,
    ignore_created=True, ignore_created_opts=True, **kwargs
):
    """
    Create a MongoDB index in a collection. Optionally,
    ignore errors related to the index already existing.
    """
    # For an explanation of the error codes:
    # https://github.com/mongodb/mongo/blob/v3.0/src/mongo/db/catalog/index_catalog.cpp#L542-L583
    # https://github.com/mongodb/mongo/blob/v3.0/src/mongo/base/error_codes.err#L70-L87
    # pylint: disable=invalid-name
    INDEX_ALREADY_EXISTS = 68
    INDEX_OPTIONS_CONFLICT = 85
    try:
        collection.create_index(keys, **kwargs)
    except pymongo.errors.OperationFailure as exc:
        errors_to_ignore = []
        if ignore_created:
            errors_to_ignore.append(INDEX_ALREADY_EXISTS)
        if ignore_created_opts:
            errors_to_ignore.append(INDEX_OPTIONS_CONFLICT)
        if exc.code in errors_to_ignore:
            logger.warning("Existing index in collection '{}' remained unchanged!: {}".format(
                collection.full_name, exc.details['errmsg'])
            )
        else:
            raise exc
