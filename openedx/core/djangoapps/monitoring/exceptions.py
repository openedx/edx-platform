"""
Signal handler for exceptions.
"""
from django.core.signals import got_request_exception
from django.dispatch import receiver
import logging


@receiver(got_request_exception)
def record_request_exception(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Logs the stack trace whenever an exception
    occurs in processing a request.
    """
    logging.exception("Uncaught exception from {sender}".format(
        sender=sender
    ))
