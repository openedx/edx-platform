"""
Custom session serializer to deal with going from python2 and python3.
"""
import pickle
import six


class PickleSerializer(object):
    """
    Set the pickle protocol version explicitly because we don't want
    to have session thrashing when we upgrade to newer versions of
    python.

    Based on the PickleSerializer built into django:
    https://github.com/django/django/blob/master/django/contrib/sessions/serializers.py
    """

    protocol = 4

    def dumps(self, obj):
        """
        Return a pickled representation of object.
        """
        return pickle.dumps(obj, self.protocol)

    def loads(self, data):
        """
        Return a python object from pickled data.
        """
        return pickle.loads(data)
