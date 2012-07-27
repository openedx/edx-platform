import logging
import sys

log = logging.getLogger(__name__)

def in_exception_handler():
    '''Is there an active exception?'''
    return sys.exc_info() != (None, None, None)

def strict_error_handler(msg, exc_info=None):
    '''
    Do not let errors pass.  If exc_info is not None, ignore msg, and just
    re-raise.  Otherwise, check if we are in an exception-handling context.
    If so, re-raise.  Otherwise, raise Exception(msg).

    Meant for use in validation, where any errors should trap.
    '''
    if exc_info is not None:
        raise exc_info[0], exc_info[1], exc_info[2]

    if in_exception_handler():
        raise

    raise Exception(msg)


def logging_error_handler(msg, exc_info=None):
    '''Log all errors, but otherwise let them pass, relying on the caller to
    workaround.'''
    if exc_info is not None:
        log.exception(msg, exc_info=exc_info)
        return

    if in_exception_handler():
        log.exception(msg)
        return

    log.error(msg)


def ignore_errors_handler(msg, exc_info=None):
    '''Ignore all errors, relying on the caller to workaround.
    Meant for use in the LMS, where an error in one part of the course
    shouldn't bring down the whole system'''
    pass
