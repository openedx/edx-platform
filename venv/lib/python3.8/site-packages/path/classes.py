import functools


class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class multimethod:
    """
    Acts like a classmethod when invoked from the class and like an
    instancemethod when invoked from the instance.
    """

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        """
        If called on an instance, pass the instance as the first
        argument.
        """
        return (
            functools.partial(self.func, owner)
            if instance is None
            else functools.partial(self.func, owner, instance)
        )
