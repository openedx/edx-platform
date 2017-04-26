"""
Helpers for the edX global analytics application.
"""

import calendar
import datetime


from django.core.cache import cache

from django.db.models import Count
from django.db.models import Q
from student.models import UserProfile


def fetch_instance_information(name_to_cache, query_type, activity_period, cache_timeout=None):
    """
    Calculates instance information corresponding for particular period as like as previous calendar day and
    statistics type as like as students per country after cached if needed.
    """
    period_start, period_end = activity_period

    statistics_queries = {
        'active_students_amount': UserProfile.objects.exclude(
            Q(user__last_login=None) | Q(user__is_active=False)
        ).filter(user__last_login__gte=period_start, user__last_login__lt=period_end).count(),

        'students_per_country': dict(UserProfile.objects.exclude(
                Q(user__last_login=None) | Q(user__is_active=False)
            ).filter(user__last_login__gte=period_start, user__last_login__lt=period_end).values(
                'country'
            ).annotate(count=Count('country')).values_list('country', 'count')
        )
    }

    if cache_timeout is not None:
        return cache_instance_data(name_to_cache, statistics_queries[query_type], cache_timeout)

    return statistics_queries[query_type]


def cache_instance_data(name_to_cache, query_result, cache_timeout):
    """
     Caches queries, that calculate particular instance data,
     including long time unchangeable weekly and monthly statistics.

     Arguments:
         name_to_cache (str): Name of query.
         query_result (query result): Django-query result.
         cache_timeout (int/None): Caching for particular seconds amount.

     Returns cached query result.
     """
    cached_query_result = cache.get(name_to_cache)

    if cached_query_result is not None:
        return cached_query_result

    cache.set(name_to_cache, query_result, cache_timeout)

    return query_result


def cache_timeout_week():
    """
    Calculates how much time cache need to save data for weekly statistics.
    """
    current_datetime = datetime.datetime.now()

    days_after_week_started = datetime.date.today().weekday()

    last_datetime_of_current_week = (current_datetime + datetime.timedelta(
        6 - days_after_week_started)
    ).replace(hour=23, minute=59, second=59)

    cache_timeout_week_in_seconds = (last_datetime_of_current_week - current_datetime).total_seconds()

    return cache_timeout_week_in_seconds


def cache_timeout_month():
    """
    Calculates how much time cache need to save data for monthly statistics.
    """
    current_datetime = datetime.datetime.now()

    last_datetime_of_current_month = current_datetime.replace(
        day=calendar.monthrange(current_datetime.year, current_datetime.month)[1]
    ).replace(hour=23, minute=59, second=59)

    cache_timeout_month_in_seconds = (last_datetime_of_current_month - current_datetime).total_seconds()

    return cache_timeout_month_in_seconds


def get_previous_day_start_and_end_dates():
    """
    Get accurate start and end dates, that create segment between them equal to a full last calendar day.

    Returns:
        start_of_day (date): Previous day`s start. Example for 2017-05-15 is 2017-05-15.
        end_of_day (date): Previous day`s end, it`s a next day (tomorrow) toward day`s start,
                           that doesn't count in segment. Example for 2017-05-15 is 2017-05-16.
    """
    end_of_day = datetime.date.today()
    start_of_day = end_of_day - datetime.timedelta(days=1)

    return start_of_day, end_of_day


def get_previous_week_start_and_end_dates():
    """
    Get accurate start and end dates, that create segment between them equal to a full last calendar week.

    Returns:
        start_of_month (date): Calendar week`s start day. Example for may is 2017-05-08.
        end_of_month (date): Calendar week`s end day, it`s the first day of next week, that doesn't count in segment.
                             Example for may is 2017-05-15.
    """
    days_after_week_started = datetime.date.today().weekday() + 7

    start_of_week = datetime.date.today() - datetime.timedelta(days=days_after_week_started)
    end_of_week = start_of_week + datetime.timedelta(days=7)

    return start_of_week, end_of_week


def get_previous_month_start_and_end_dates():
    """
    Get accurate start and end dates, that create segment between them equal to a full last calendar month.

    Returns:
        start_of_month (date): Calendar month`s start day. Example for may is 2017-04-01.
        end_of_month (date): Calendar month`s end day, it`s the first day of next month, that doesn't count in segment.
                             Example for may is 2017-05-01.
    """
    previous_month_date = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)

    start_of_month = previous_month_date.replace(day=1)
    end_of_month = previous_month_date.replace(
        day=calendar.monthrange(previous_month_date.year, previous_month_date.month)[1]
    ) + datetime.timedelta(days=1)

    return start_of_month, end_of_month
