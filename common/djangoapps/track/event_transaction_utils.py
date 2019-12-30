"""
Helper functions to access and update the id and type
used in event tracking.
"""


from uuid import UUID, uuid4

from openedx.core.lib.cache_utils import get_cache


def get_event_transaction_id():
    """
    Retrieves the current event transaction id from the request
    cache.
    """
    return get_cache('event_transaction').get('id', None)


def get_event_transaction_type():
    """
    Retrieves the current event transaction type from the request
    cache.
    """
    return get_cache('event_transaction').get('type', None)


def create_new_event_transaction_id():
    """
    Sets the event transaction id to a newly-
    generated UUID.
    """
    new_id = uuid4()
    get_cache('event_transaction')['id'] = new_id
    return new_id


def set_event_transaction_id(new_id):
    """
    Sets the event transaction id to a UUID object
    generated from new_id.
    new_id must be a parsable string version
    of a UUID.
    """
    get_cache('event_transaction')['id'] = UUID(new_id)


def set_event_transaction_type(action_type):
    """
    Takes a string and stores it in the request cache
    as the user action type.
    """
    get_cache('event_transaction')['type'] = action_type
