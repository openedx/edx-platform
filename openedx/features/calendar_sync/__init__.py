"""
Calendar syncing Course dates with a User.
"""


def get_calendar_event_id(user, block_key, date_type):
    """
    Creates a unique event id based on a user and a course block key

    Parameters:
        user (User): The user requesting a calendar event
        block_key (str): The block key containing the date for the calendar event
        date_type (str): The type of the date (e.g. 'due', 'start', 'end', etc.)
    Returns:
        event id (str)
    """
    return user.username + '.' + block_key + '.' + date_type
