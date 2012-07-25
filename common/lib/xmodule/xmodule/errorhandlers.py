import sys

def strict_error_handler(msg, exc_info=None):
    '''
    Do not let errors pass.  If exc_info is not None, ignore msg, and just
    re-raise.  Otherwise, check if we are in an exception-handling context.
    If so, re-raise.  Otherwise, raise Exception(msg).

    Meant for use in validation, where any errors should trap.
    '''
    if exc_info is not None:
        raise exc_info[0], exc_info[1], exc_info[2]

    # Check if there is an exception being handled somewhere up the stack
    if sys.exc_info() != (None, None, None):
        raise

    raise Exception(msg)


def ignore_errors_handler(msg, exc_info=None):
    '''Ignore all errors, relying on the caller to workaround.
    Meant for use in the LMS, where an error in one part of the course
    shouldn't bring down the whole system'''
    pass
