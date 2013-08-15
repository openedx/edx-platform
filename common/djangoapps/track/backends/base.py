from __future__ import absolute_import

import abc


class BaseBackend(object):
    """
    Abstract base class for a Tracker Backend.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, **options):
        return

    @abc.abstractmethod
    def send(self, event):
        return
