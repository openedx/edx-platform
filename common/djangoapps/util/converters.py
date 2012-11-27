import time, datetime
import re

def time_to_date(time_obj):
    """
    Convert a time.time_struct to a true universal time (can pass to js Date constructor)
    """
    return time.mktime(time_obj) * 1000

def jsdate_to_time(field):
    """
    Convert a true universal time (msec since epoch) from a string to a time obj
    """
    if field is None:
        return field
    elif isinstance(field, unicode):  # iso format but ignores time zone assuming it's Z
        d=datetime.datetime(*map(int, re.split('[^\d]', field)[:-1]))  
        return d.utctimetuple()
    elif isinstance(field, int):
        return time.gmtime(field / 1000)