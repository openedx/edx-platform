import logging

LOG = logging.getLogger(__name__)


# TODO: consider using a LoggerAdapter instead of this mixin:
# https://docs.python.org/2/library/logging.html#logging.LoggerAdapter
class PrefixedDebugLoggerMixin(object):
    log_prefix = None

    def __init__(self, *args, **kwargs):
        super(PrefixedDebugLoggerMixin, self).__init__(*args, **kwargs)
        if self.log_prefix is None:
            self.log_prefix = self.__class__.__name__

    def log_debug(self, message, *args, **kwargs):
        """
        Wrapper around LOG.debug that prefixes the message.
        """
        LOG.debug(self.log_prefix + ': ' + message, *args, **kwargs)

    def log_info(self, message, *args, **kwargs):
        """
        Wrapper around LOG.info that prefixes the message.
        """
        LOG.info(self.log_prefix + ': ' + message, *args, **kwargs)
