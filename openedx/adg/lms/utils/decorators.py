"""
A utility for custom decorators
"""
import functools

from django.conf import settings
from django.dispatch import receiver


def suspendingreceiver(signal, **decorator_kwargs):
    """
    A custom decorator for tests, which can suspend receiver by overriding the SUSPEND_RECEIVERS
    setting per test method or class.
    """

    def receiver_wrapper(func):
        @receiver(signal, **decorator_kwargs)
        @functools.wraps(func)
        def fake_receiver(sender, **kwargs):
            if settings.SUSPEND_RECEIVERS:
                return
            return func(sender, **kwargs)

        return fake_receiver

    return receiver_wrapper
