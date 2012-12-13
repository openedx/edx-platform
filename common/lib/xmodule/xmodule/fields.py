import time
import logging

from .model import ModelType

log = logging.getLogger(__name__)


class Date(ModelType):
    time_format = "%Y-%m-%dT%H:%M"

    def from_json(self, value):
        """
        Parse an optional metadata key containing a time: if present, complain
        if it doesn't parse.
        Return None if not present or invalid.
        """
        try:
            return time.strptime(value, self.time_format)
        except ValueError as e:
            msg = "Field {0} has bad value '{1}': '{2}'".format(
                self._name, value, e)
            log.warning(msg)
            return None

    def to_json(self, value):
        """
        Convert a time struct to a string
        """
        return time.strftime(self.time_format, value)
