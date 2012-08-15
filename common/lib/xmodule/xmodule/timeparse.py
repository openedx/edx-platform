"""
Helper functions for handling time in the format we like.
"""
import time

TIME_FORMAT = "%Y-%m-%dT%H:%M"

def parse_time(time_str):
    """
    Takes a time string in TIME_FORMAT, returns
    it as a time_struct.  Raises ValueError if the string is not in the right format.
    """
    return time.strptime(time_str, TIME_FORMAT)

def stringify_time(time_struct):
    """
    Convert a time struct to a string
    """
    return time.strftime(TIME_FORMAT, time_struct)
