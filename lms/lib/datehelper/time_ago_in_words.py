from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import calendar

# only used for testing
def _timedelta(**kwargs):
    kwargs['days'] = kwargs.get('days', 0)
    if kwargs.get('years', False):
        # not really a good solution since ignoring leap years
        # but this is only for test anyways
        kwargs['days'] += kwargs['years'] * 365
        del kwargs['years']
    if kwargs.get('months', False):
        kwargs['days'] += kwargs['months'] * 30
        del kwargs['months']
    return timedelta(**kwargs)

def time_ago_in_words(from_time, include_seconds=False):
    return distance_of_time_in_words(from_time, datetime.now(tzlocal()), include_seconds=False)

distance_of_time_in_words_to_now = time_ago_in_words

def _time_in_words(before_text, unit):
    if before_text:
        before_text += ' '
    def time_in_words_generator(count):
        if count <= 1:
            if before_text == 'less than ':
                if unit == 'hour':
                    count = 'an'
                else:
                    count = 'a'
            return '{0}{1} {2}'.format(before_text, count, unit)
        else:
            return '{0}{1} {2}s'.format(before_text, count, unit)
    return time_in_words_generator

def distance_of_time_in_words(from_time, to_time=0, include_seconds=False, options = {}):
    """Return a rough description of the time interval between from_time and to_time.
       This is a direct translation from rails in ActionView::Helpers::DateHelper.
       Reference:
       http://api.rubyonrails.org/classes/ActionView/Helpers/DateHelper.html#method-i-distance_of_time_in_words

    >>> from_time = datetime.now(tzlocal())
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(minutes=50))
    'about 1 hour'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(seconds=15))
    'less than a minute'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(seconds=15), True)
    'less than 20 seconds'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(years=3))
    'about 3 years'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(hours=60))
    '3 days'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(seconds=45), True)
    'less than a minute'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(seconds=-45), True)
    'less than a minute'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(seconds=76))
    '1 minute'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(years=1, days=3))
    'about 1 year'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(years=3, months=6))
    'over 3 years'
    >>> distance_of_time_in_words(from_time, from_time + _timedelta(years=4, days=9, minutes=30, seconds=5))
    'about 4 years'
    >>> to_time = from_time + _timedelta(years=6, days=19)
    >>> distance_of_time_in_words(from_time, to_time, True)
    'about 6 years'
    >>> distance_of_time_in_words(to_time, from_time, True)
    'about 6 years'
    >>> distance_of_time_in_words(from_time, from_time)
    'less than a minute'
    """

    if isinstance(from_time, int):
        from_time = datetime.fromtimestamp(time.time()+from_time)
    if isinstance(to_time, int):
        to_time = datetime.fromtimestamp(time.time()+to_time)

    distance_in_minutes = int(round(abs((to_time - from_time).total_seconds()) / 60))
    distance_in_seconds = int(round(abs((to_time - from_time).total_seconds())))
    
    less_than_x_minutes = _time_in_words('less than', 'minute')
    less_than_x_seconds = _time_in_words('less than', 'second')
    half_a_minute       = 'half a minute'
    x_minutes           = _time_in_words('', 'minute')
    about_x_hours       = _time_in_words('about', 'hour')
    x_days              = _time_in_words('', 'day')
    about_x_months      = _time_in_words('about', 'month')
    x_months            = _time_in_words('', 'month')
    about_x_years       = _time_in_words('about', 'year')
    over_x_years        = _time_in_words('over', 'year')
    almost_x_years      = _time_in_words('almost', 'year')

    if 0 <= distance_in_minutes <= 1:
        if not include_seconds:
            if distance_in_minutes == 0:
                return less_than_x_minutes(1)
            else:
                return x_minutes(distance_in_minutes)
        else:
            if 0 <= distance_in_seconds <= 4:
                return less_than_x_seconds(5)
            elif 5 <= distance_in_seconds <= 9:
                return less_than_x_seconds(10)
            elif 10 <= distance_in_seconds <= 19:
                return less_than_x_seconds(20)
            elif 20 <= distance_in_seconds <= 39:
                return half_a_minute
            elif 40 <= distance_in_seconds <= 59:
                return less_than_x_minutes(1)
            else:
                return x_minutes(1)
    elif 2 <= distance_in_minutes <= 44:
        return x_minutes(distance_in_minutes)
    elif 45 <= distance_in_minutes <= 89:
        return about_x_hours(1)
    elif 90 <= distance_in_minutes <= 1439:
        return about_x_hours(int(round(float(distance_in_minutes) / 60.0)))
    elif 1440 <= distance_in_minutes <= 2519:
        return x_days(1)
    elif 2520 <= distance_in_minutes <= 43199:
        return x_days(int(round(float(distance_in_minutes) / 1440.0)))
    elif 43200 <= distance_in_minutes <= 86399:
        return about_x_months(1)
    elif 86400 <= distance_in_minutes <= 525599:
        return x_months(int(round(float(distance_in_minutes) / 43200.0)))
    else:
        fyear = from_time.year
        if from_time.month >= 3:
            fyear += 1
        tyear = to_time.year
        if to_time.month < 3:
            tyear -= 1
        leap_years = 0 if fyear > tyear else len([x for x in range(fyear, tyear + 1) if calendar.isleap(x)])
        minute_offset_for_leap_year = leap_years * 1440
        # Discount the leap year days when calculating year distance.
        # e.g. if there are 20 leap year days between 2 dates having the same day
        # and month then the based on 365 days calculation
        # the distance in years will come out to over 80 years when in written
        # english it would read better as about 80 years.
        minutes_with_offset         = distance_in_minutes - minute_offset_for_leap_year
        remainder                   = (minutes_with_offset % 525600)
        distance_in_years           = (minutes_with_offset / 525600)
        if remainder < 131400:
            return about_x_years(distance_in_years)
        elif remainder < 394200:
            return over_x_years(distance_in_years)
        else:
            return almost_x_years(distance_in_years + 1)
