""" API implementation for Secure api calls. """

import socket
import struct
import json
import datetime
from django.utils.timezone import now
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta, MO
from django.conf import settings


def address_exists_in_network(ip_address, net_n_bits):
    """
    return True if the ip address exists in the subnet address
    otherwise return False
    """
    ip_address = struct.unpack('<L', socket.inet_aton(ip_address))[0]
    net, bits = net_n_bits.split('/')
    net_address = struct.unpack('<L', socket.inet_aton(net))[0]
    net_mask = ((1L << int(bits)) - 1)
    return ip_address & net_mask == net_address & net_mask


def get_client_ip_address(request):
    """
    get the client IP Address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[-1].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    return ip_address


def str2bool(value):
    """
    convert string to bool
    """
    if value:
        return value.lower() in ("true",)
    else:
        return False


def generate_base_uri(request, strip_qs=False):
    """
    Build absolute uri
    """
    if strip_qs:
        return request.build_absolute_uri(request.path)  # Don't need querystring that why giving location parameter
    else:
        return request.build_absolute_uri()


def is_int(value):
    """
    checks if a string value can be interpreted as integer
    """
    try:
        int(value)
        return True
    except ValueError:
        return False


def dict_has_items(obj, items):
    """
    examine a `obj` for given `items`. if all `items` are found in `obj`
    return True otherwise false. where `obj` is a dictionary and `items`
    is list of dictionaries
    """
    has_items = False
    if isinstance(obj, basestring):
        obj = json.loads(obj)
    for item in items:
        for lookup_key, lookup_val in item.iteritems():
            if lookup_key in obj and obj[lookup_key] == lookup_val:
                has_items = True
            else:
                return False
    return has_items


def extract_data_params(request):
    """
    extracts all query params which starts with data__
    """
    data_params = []
    for key, val in request.QUERY_PARAMS.iteritems():
        if key.startswith('data__'):
            data_params.append({key[6:]: val})
    return data_params


def strip_time(dt):
    """
    Removes time part of datetime
    """
    tzinfo = getattr(dt, 'tzinfo', now().tzinfo) or now().tzinfo
    return datetime.datetime(dt.year, dt.month, dt.day, tzinfo=tzinfo)


def parse_datetime(date_val, defaultdt=None):
    """
    Parses datetime value from string
    """
    if isinstance(date_val, basestring):
        return parse(date_val, yearfirst=True, default=defaultdt)
    return date_val


def get_interval_bounds(date_val, interval):
    """
    Returns interval bounds the datetime is in.
    """

    day = strip_time(date_val)

    if interval == 'day':
        begin = day
        end = day + relativedelta(days=1)
    elif interval == 'week':
        begin = day - relativedelta(weekday=MO(-1))
        end = begin + datetime.timedelta(days=7)
    elif interval == 'month':
        begin = strip_time(datetime.datetime(date_val.year, date_val.month, 1, tzinfo=date_val.tzinfo))
        end = begin + relativedelta(months=1)
    end = end - relativedelta(microseconds=1)
    return begin, end


def detect_db_engine():
    """
    detects database engine used
    """
    engine = 'mysql'
    backend = settings.DATABASES['default']['ENGINE']
    if 'sqlite' in backend:
        engine = 'sqlite'
    return engine


def get_time_series_data(queryset, start, end, interval='days', date_field='created', aggregate=None):
    """
    Aggregate over time intervals to compute time series representation of data
    """
    engine = detect_db_engine()
    start, _ = get_interval_bounds(start, interval.rstrip('s'))
    _, end = get_interval_bounds(end, interval.rstrip('s'))

    sql = {
        'mysql': {
            'days': "DATE_FORMAT(`{}`, '%%Y-%%m-%%d')".format(date_field),
            'weeks': "DATE_FORMAT(DATE_SUB(`{}`, INTERVAL(WEEKDAY(`{}`)) DAY), '%%Y-%%m-%%d')".format(date_field,
                                                                                                      date_field),
            'months': "DATE_FORMAT(`{}`, '%%Y-%%m-01')".format(date_field)
        },
        'sqlite': {
            'days': "strftime('%%Y-%%m-%%d', `{}`)".format(date_field),
            'weeks': "strftime('%%Y-%%m-%%d', julianday(`{}`) - strftime('%%w', `{}`) + 1)".format(date_field,
                                                                                                   date_field),
            'months': "strftime('%%Y-%%m-01', `{}`)".format(date_field)
        }
    }
    interval_sql = sql[engine][interval]
    kwargs = {'{}__range'.format(date_field): (start, end)}
    aggregate_data = queryset.extra(select={'d': interval_sql}).filter(**kwargs).order_by().values('d').\
        annotate(agg=aggregate)

    today = strip_time(now())
    data = dict((strip_time(parse_datetime(item['d'], today)), item['agg']) for item in aggregate_data)

    series = []
    dt_key = start
    while dt_key < end:
        value = data.get(dt_key, 0)
        series.append((dt_key, value,))
        dt_key += relativedelta(**{interval: 1})
    return series
