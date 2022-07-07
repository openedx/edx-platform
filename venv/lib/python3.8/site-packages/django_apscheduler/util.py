import logging
from datetime import datetime
from functools import wraps

from apscheduler.schedulers.base import BaseScheduler
from django import db
from django.conf import settings
from django.utils import formats
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_dt_format() -> str:
    """Return the configured format for displaying datetimes in the Django admin views"""
    return formats.get_format(
        getattr(settings, "APSCHEDULER_DATETIME_FORMAT", "N j, Y, f:s a")
    )


def get_local_dt_format(dt: datetime) -> str:
    """Get the datetime in the localized datetime format"""
    if dt and settings.USE_TZ and timezone.is_aware(dt):
        dt = timezone.localtime(dt)

    return formats.date_format(dt, get_dt_format())


def get_django_internal_datetime(dt: datetime) -> datetime:
    """
    Get the naive or aware version of the datetime based on the configured `USE_TZ` Django setting. This is also the
    format that Django uses to store datetimes internally.
    """
    if dt:
        if settings.USE_TZ and timezone.is_naive(dt):
            return timezone.make_aware(dt)

        elif not settings.USE_TZ and timezone.is_aware(dt):
            return timezone.make_naive(dt)

    return dt


def get_apscheduler_datetime(dt: datetime, scheduler: BaseScheduler) -> datetime:
    """
    Make the datetime timezone aware (if necessary), using the same timezone as is currently configured for the
    scheduler.
    """
    if dt and timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone=scheduler.timezone)

    return dt


def retry_on_db_operational_error(func):
    """
    This decorator can be used to wrap a database-related method so that it will be retried when a
    django.db.OperationalError or django.db.InterfaceError is encountered.

    The rationale is that these exceptions are usually raised when attempting to use an old database connection that
    the database backend has since closed. Closing the Django connection as well, and re-trying with a fresh connection,
    is usually sufficient to solve the problem.

    It is a reluctant workaround for users that persistently have issues with stale database connections (most notably:
    2006, 'MySQL server has gone away').

    The recommended approach is still to rather install a database connection pooler (like pgbouncer), to take care of
    database connection management for you, but the issue has been raised enough times by different individuals that a
    workaround is probably justified.

    CAUTION: any method that this decorator is applied to MUST be idempotent (i.e. the method can be retried a second
    time without any unwanted side effects). If your method performs any actions before the database exception is
    raised then those actions will be repeated. If you don't want that to happen then it would be best to handle the
    exception manually and call `db.close_old_connections()` in an appropriate fashion inside your own method instead.

    The following list of alternative workarounds were also considered:

    1. Calling db.close_old_connections() pre-emptively before the job store executes a DB operation: this would break
       Django's standard connection management. For example, if the `CONN_MAX_AGE` setting is set to 0, a new connection
       will be required for *every* database operation (as opposed to at the end of every *request* like in the Django
       standard). The database overhead, and associated performance penalty, that this approach would impose seem
       unreasonable. See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-CONN_MAX_AGE.

    2. Using a custom QuerySet or database backend that handles the relevant database exceptions automatically: this
       would be more convenient than having to decorate individual methods, but it would also break when a DB operation
       needs to be re-tried as part of an atomic transaction. See: https://github.com/django/django/pull/2740

    3. Pinging the database before each operation to see if it is still available: django-apscheduler used to make use
       of this approach (see: https://github.com/jcass77/django-apscheduler/blob/9ac06b33d19961da6c36d5ac814d4338beb11309/django_apscheduler/models.py#L16-L51).
       Injecting an additional database query, on an arbitrary schedule, seems like an unreasonable thing to do,
       especially considering that this would be unnecessary for users that already make use of a database connection
       pooler to manage their connections properly.
    """

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except (db.OperationalError, db.InterfaceError) as e:
            logger.warning(
                f"DB error executing '{func.__name__}' ({e}). Retrying with a new DB connection..."
            )
            db.close_old_connections()
            result = func(*args, **kwargs)

        return result

    return func_wrapper


def close_old_connections(func):
    """
    A decorator that ensures that Django database connections that have become unusable, or are obsolete, are closed
    before and after a method is executed (see: https://docs.djangoproject.com/en/dev/ref/databases/#general-notes
    for background).

    This decorator is intended to be used to wrap APScheduler jobs, and provides functionality comparable to the
    Django standard approach of closing old connections before and after each HTTP request is processed.

    It only makes sense for APScheduler jobs that require database access, and prevents `django.db.OperationalError`s.
    """

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        db.close_old_connections()
        try:
            result = func(*args, **kwargs)
        finally:
            db.close_old_connections()

        return result

    return func_wrapper
