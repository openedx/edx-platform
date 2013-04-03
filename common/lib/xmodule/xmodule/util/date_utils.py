import time
import datetime


def get_default_time_display(time_struct):
    """
    Converts a time struct to a string representation. This is the default
    representation used in Studio and LMS.
    It is of the form "Apr 09, 2013 at 04:00 PM".

    If None is passed in, an empty string will be returned.
    """
    return get_time_struct_display(time_struct, "%b %d, %Y at %I:%M %p")


def get_time_struct_display(time_struct, format):
    """
    Converts a time struct to a string based on the given format.

    If None is passed in, an empty string will be returned.
    """
    return '' if time_struct is None else time.strftime(format, time_struct)


def time_to_datetime(time_struct):
    """
    Convert a time struct to a datetime.

    If None is passed in, None will be returned.
    """
    return datetime.datetime(*time_struct[:6]) if time_struct else None
