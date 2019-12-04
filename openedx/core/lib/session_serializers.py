"""
Custom session serializer to deal with going from python2 and python3.
"""
import pickle
import six


class PickleV2Serializer(object):
    """
    Lock the pickle serializer to version 2 of the protocol
    because we don't want python 2 to be able to read session
    data written by python3 while both are running at the same
    time in production.

    Based on the PickleSerializer built into django:
    https://github.com/django/django/blob/master/django/contrib/sessions/serializers.py
    """

    protocol = 2

    def dumps(self, obj):
        """
        Return a pickled representation of object.
        """
        return pickle.dumps(obj, self.protocol)

    def loads(self, data):
        """
        Return a python object from pickled data.
        """
        if six.PY2:
            # Params used below don't exist in python 2
            return pickle.loads(data)
        else:
            # See notes here about pickling python2 objects in python3
            # https://docs.python.org/3/library/pickle.html#pickle.Unpickler
            return pickle.loads(data, encoding='latin1')  # pylint: disable=unexpected-keyword-arg
