"""
A handy util to print a django-debug-screen-like stack trace with
values of local variables.
"""

import sys
import traceback
from django.utils.encoding import smart_unicode


def supertrace(max_len=160):
    """
    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.  Should be called from an exception handler.

    if max_len is not None, will print up to max_len chars for each local variable.

    (cite: modified from somewhere on stackoverflow)
    """
    tb = sys.exc_info()[2]
    while True:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    stack = []
    frame = tb.tb_frame
    while frame:
        stack.append(f)
        frame = frame.f_back
    stack.reverse()
    # First print the regular traceback
    traceback.print_exc()

    print "Locals by frame, innermost last"
    for frame in stack:
        print
        print "Frame %s in %s at line %s" % (frame.f_code.co_name,
                                             frame.f_code.co_filename,
                                             frame.f_lineno)
        for key, value in frame.f_locals.items():
            print ("\t%20s = " % smart_unicode(key, errors='ignore')),
            # We have to be careful not to cause a new error in our error
            # printer! Calling str() on an unknown object could cause an
            # error.
            try:
                s = smart_unicode(value, errors='ignore')
                if max_len is not None:
                    s = s[:max_len]
                print s
            except:
                print "<ERROR WHILE PRINTING VALUE>"
