"""
Memory leak troubleshooting via request lifecycle signals.
"""

from __future__ import absolute_import

from django.core.signals import request_started
from django.dispatch import receiver

from . import MemoryUsageData


@receiver(request_started)
def reset_memory_statistics(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Use Django's signal for the start of request processing as the trigger to
    start tracking new objects in memory when the
    ``monitoring_utils.log_memory_tables`` Waffle switch is enabled.
    """
    MemoryUsageData.start_counting()
