import logging

LOG = logging.getLogger(__name__)


# TODO: consider using a LoggerAdapter instead of this mixin:
# https://docs.python.org/2/library/logging.html#logging.LoggerAdapter
class PrefixedDebugLoggerMixin(object):
    def __init__(self, *args, **kwargs):
        super(PrefixedDebugLoggerMixin, self).__init__(*args, **kwargs)
        self.log_prefix = self.__class__.__name__

    def log_debug(self, message, *args, **kwargs):
        LOG.debug(self.log_prefix + ': ' + message, *args, **kwargs)
