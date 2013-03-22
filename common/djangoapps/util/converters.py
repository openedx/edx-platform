import time
import datetime
import calendar
import dateutil.parser


def time_to_date(time_obj):
    """
    Convert a time.time_struct to a true universal time (can pass to js Date
    constructor)
    """
    return calendar.timegm(time_obj) * 1000


def time_to_isodate(source):
    '''Convert to an iso date'''
    if isinstance(source, time.struct_time):
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', source)
    elif isinstance(source, datetime):
        return source.isoformat() + 'Z'


def jsdate_to_time(field):
    """
    Convert a universal time (iso format) or msec since epoch to a time obj
    """
    if field is None:
        return field
    elif isinstance(field, basestring):
        d = dateutil.parser.parse(field)
        return d.utctimetuple()
    elif isinstance(field, (int, long, float)):
        return time.gmtime(field / 1000)
    elif isinstance(field, time.struct_time):
        return field
    else:
        raise ValueError("Couldn't convert %r to time" % field)
