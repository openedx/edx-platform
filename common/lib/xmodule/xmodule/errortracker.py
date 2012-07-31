import logging
import sys

log = logging.getLogger(__name__)

def in_exception_handler():
    '''Is there an active exception?'''
    return sys.exc_info() != (None, None, None)


def make_error_tracker():
    '''Return a tuple (logger, error_list), where
    the logger appends a tuple (message, exc_info=None)
    to the error_list on every call.

    error_list is a simple list.  If the caller messes with it, info
    will be lost.
    '''
    errors = []

    def error_tracker(msg):
        '''Log errors'''
        exc_info = None
        if in_exception_handler():
            exc_info = sys.exc_info()

        errors.append((msg, exc_info))

    return (error_tracker, errors)

def null_error_tracker(msg):
    '''A dummy error tracker that just ignores the messages'''
    pass
