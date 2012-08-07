

def lazyproperty(fn):
    """
    Use this decorator for lazy generation of properties that
    are expensive to compute. From http://stackoverflow.com/a/3013910/86828
    
    
    Example:
    class Test(object):

        @lazyproperty
        def a(self):
            print 'generating "a"'
            return range(5)
    
    Interactive Session:
    >>> t = Test()
    >>> t.__dict__
    {}
    >>> t.a
    generating "a"
    [0, 1, 2, 3, 4]
    >>> t.__dict__
    {'_lazy_a': [0, 1, 2, 3, 4]}
    >>> t.a
    [0, 1, 2, 3, 4]
    """
    
    attr_name = '_lazy_' + fn.__name__
    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazyprop