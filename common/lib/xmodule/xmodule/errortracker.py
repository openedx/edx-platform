import logging
import sys
import traceback

from collections import namedtuple

log = logging.getLogger(__name__)

ErrorLog = namedtuple('ErrorLog', 'tracker errors')

def in_exception_handler():
    '''Is there an active exception?'''
    return sys.exc_info() != (None, None, None)


def make_error_tracker():
    '''Return an ErrorLog (named tuple), with fields (tracker, errors), where
    the logger appends a tuple (message, exception_str) to the errors on every
    call.  exception_str is in the format returned by traceback.format_exception.

    error_list is a simple list.  If the caller modifies it, info
    will be lost.
    '''
    errors = []

    def error_tracker(msg):
        '''Log errors'''
        exc_str = ''
        if in_exception_handler():
            exc_str = ''.join(traceback.format_exception(*sys.exc_info()))

        errors.append((msg, exc_str))

    return ErrorLog(error_tracker, errors)

def null_error_tracker(msg):
    '''A dummy error tracker that just ignores the messages'''
    pass
