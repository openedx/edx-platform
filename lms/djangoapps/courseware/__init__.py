import warnings

if __name__ == 'courseware':
    # Show the call stack that imported us wrong.
    msg = "Importing 'lms.djangoapps.courseware' as 'courseware' is no longer supported"
    warnings.warn(msg, DeprecationWarning)
