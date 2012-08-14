"""
Helper functions for handling time in the format we like.
"""
import time

def parse_time(time_str):
    """
    Takes a time string in our format ("%Y-%m-%dT%H:%M"), and returns
    it as a time_struct.  Raises ValueError if the string is not in the right format.
    """
    return time.strptime(time_str, "%Y-%m-%dT%H:%M")
