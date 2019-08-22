"""
Extra methods to do some python 2 to 3 things we need to do in edx-platform.

This is internal and should not be referenced outside of the edx-platform repo.
"""
import six


def get_gettext(o):
    """
    In python 2 return the ugettext attribute. In python 3 return gettext.
    """
    if six.PY3:
        return o.gettext
    else:
        return o.ugettext
