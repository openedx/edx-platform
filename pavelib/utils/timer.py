"""
Tools for timing paver tasks
"""


import json
import logging
import os
import sys
import traceback
from datetime import datetime
from os.path import dirname, exists

import wrapt

LOGGER = logging.getLogger(__file__)
PAVER_TIMER_LOG = os.environ.get('PAVER_TIMER_LOG')


@wrapt.decorator
def timed(wrapped, instance, args, kwargs):  # pylint: disable=unused-argument
    """
    Log execution time for a function to a log file.

    Logging is only actually executed if the PAVER_TIMER_LOG environment variable
    is set. That variable is expanded for the current user and current
    environment variables. It also can have :meth:`~Datetime.strftime` format
    identifiers which are substituted using the time when the task started.

    For example, ``PAVER_TIMER_LOG='~/.paver.logs/%Y-%d-%m.log'`` will create a new
    log file every day containing reconds for paver tasks run that day, and
    will put those log files in the ``.paver.logs`` directory inside the users
    home.

    Must be earlier in the decorator stack than the paver task declaration.
    """
    start = datetime.utcnow()
    exception_info = {}
    try:
        return wrapped(*args, **kwargs)
    except Exception as exc:
        exception_info = {
            'exception': "".join(traceback.format_exception_only(type(exc), exc)).strip()
        }
        raise
    finally:
        end = datetime.utcnow()

        # N.B. This is intended to provide a consistent interface and message format
        # across all of Open edX tooling, so it deliberately eschews standard
        # python logging infrastructure.
        if PAVER_TIMER_LOG is not None:

            log_path = start.strftime(PAVER_TIMER_LOG)

            log_message = {
                'python_version': sys.version,
                'task': "{}.{}".format(wrapped.__module__, wrapped.__name__),
                'args': [repr(arg) for arg in args],
                'kwargs': {key: repr(value) for key, value in kwargs.items()},
                'started_at': start.isoformat(' '),
                'ended_at': end.isoformat(' '),
                'duration': (end - start).total_seconds(),
            }
            log_message.update(exception_info)

            try:
                log_dir = dirname(log_path)
                if log_dir and not exists(log_dir):
                    os.makedirs(log_dir)

                with open(log_path, 'a') as outfile:
                    json.dump(
                        log_message,
                        outfile,
                        separators=(',', ':'),
                        sort_keys=True,
                    )
                    outfile.write('\n')
            except OSError:
                # Squelch OSErrors, because we expect them and they shouldn't
                # interrupt the rest of the process.
                LOGGER.exception("Unable to write timing logs")
