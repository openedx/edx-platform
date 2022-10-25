"""
Utility functions for the edx-platform test suite.
"""


def attr(*args, **kwargs):
    """
    Set the given attributes on the decorated test class, function or method.
    Replacement for nose.plugins.attrib.attr, used with pytest-attrib to
    run tests with particular attributes.
    """
    def decorator(test):
        """
        Apply the decorator's arguments as arguments to the given test.
        """
        for arg in args:
            setattr(test, arg, True)
        for key in kwargs:
            setattr(test, key, kwargs[key])
        return test
    return decorator
