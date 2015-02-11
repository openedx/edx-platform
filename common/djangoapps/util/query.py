""" Utility functions related to database queries """
from django.conf import settings
from django.db.utils import ConnectionDoesNotExist


def use_read_replica_if_available(queryset):
    """
    If there is a database called 'read_replica', use that database for the queryset.
    """
    return queryset.using("read_replica") if "read_replica" in settings.DATABASES else queryset


def get_read_replica_cursor_if_available(db):  # pylint: disable=invalid-name
    """
    Returns cursor to read_replica or default if not available
    """
    try:
        cursor = db.connections['read_replica'].cursor()
    except ConnectionDoesNotExist:
        cursor = db.connection.cursor()

    return cursor
