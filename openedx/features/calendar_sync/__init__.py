"""
Calendar syncing Course dates with a User.
"""
default_app_config = 'openedx.features.calendar_sync.apps.UserCalendarSyncConfig'


def get_calendar_event_id(user, block_key, date_type, hostname):
    """
    Creates a unique event id based on a user and a course block key

    Parameters:
        user (User): The user requesting a calendar event
        block_key (str): The block key containing the date for the calendar event
        date_type (str): The type of the date (e.g. 'due', 'start', 'end', etc.)
        hostname (str): A hostname to namespace this id (e.g. 'open.edx.org')
    Returns:
        event id (str)
    """
    return '{}.{}.{}@{}'.format(user.id, block_key, date_type, hostname)
