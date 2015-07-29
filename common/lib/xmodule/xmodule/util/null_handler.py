# pylint: disable=missing-docstring


class NullHandler(object):
    """
    Responds to an any method call.
    """
    def __getattr__(self, name):
        def method(*args, **kwargs):  # pylint: disable=unused-argument
            pass
        return method
