"""
Helper functions for handling time in the format we like.
"""
import re
from datetime import timedelta, datetime

TIME_FORMAT = "%Y-%m-%dT%H:%M"

TIMEDELTA_REGEX = re.compile(r'^((?P<days>\d+?) day(?:s?))?(\s)?((?P<hours>\d+?) hour(?:s?))?(\s)?((?P<minutes>\d+?) minute(?:s)?)?(\s)?((?P<seconds>\d+?) second(?:s)?)?$')

def parse_time(time_str):
    """
    Takes a time string in TIME_FORMAT

    Returns it as a time_struct.

    Raises ValueError if the string is not in the right format.
    """
    return datetime.strptime(time_str, TIME_FORMAT)


def stringify_time(dt):
    """
    Convert a datetime struct to a string
    """
    return dt.isoformat()

def parse_timedelta(time_str):
    """
    time_str: A string with the following components:
        <D> day[s] (optional)
        <H> hour[s] (optional)
        <M> minute[s] (optional)
        <S> second[s] (optional)

    Returns a datetime.timedelta parsed from the string
    """
    parts = TIMEDELTA_REGEX.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.iteritems():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)
