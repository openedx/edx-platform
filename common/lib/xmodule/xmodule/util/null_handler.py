class NullHandler(object):
    """
    Responds to an any method call.
    """
    def __getattr__(self, name):
        def method(*args, **kwargs):
            pass
        return method

