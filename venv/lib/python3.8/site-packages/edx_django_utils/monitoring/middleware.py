"""
Deprecated Middleware for backward-compatibility.

IMPORTANT: No new classes should be added to this file.
TODO: Remove this file once these classes are no longer used.

"""
import warnings

from .internal.middleware import CachedCustomMonitoringMiddleware as InternalCachedCustomMonitoringMiddleware
from .internal.middleware import MonitoringMemoryMiddleware as InternalMonitoringMemoryMiddleware
from .internal.utils import set_custom_attribute


class CachedCustomMonitoringMiddleware(InternalCachedCustomMonitoringMiddleware):
    """
    Deprecated class for handling middleware. Class has been moved to public API.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        msg = "Use 'edx_django_utils.monitoring.CachedCustomMonitoringMiddleware' in place of " \
              "'edx_django_utils.monitoring.middleware.CachedCustomMonitoringMiddleware'."
        warnings.warn(msg, DeprecationWarning)
        set_custom_attribute('deprecated_monitoring_middleware', 'CachedCustomMonitoringMiddleware')


class MonitoringCustomMetricsMiddleware(InternalCachedCustomMonitoringMiddleware):
    """
    Deprecated class for handling middleware. Class has been renamed to CachedCustomMonitoringMiddleware.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        msg = "Use 'edx_django_utils.monitoring.CachedCustomMonitoringMiddleware' in place of " \
              "'edx_django_utils.monitoring.middleware.MonitoringCustomMetricsMiddleware'."
        warnings.warn(msg, DeprecationWarning)
        set_custom_attribute('deprecated_monitoring_middleware', 'MonitoringCustomMetricsMiddleware')


class MonitoringMemoryMiddleware(InternalMonitoringMemoryMiddleware):
    """
    Deprecated class for handling middleware. Class has been moved to public API.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        msg = "Use 'edx_django_utils.monitoring.MonitoringMemoryMiddleware' in place of " \
              "'edx_django_utils.monitoring.middleware.MonitoringMemoryMiddleware'."
        warnings.warn(msg, DeprecationWarning)
        set_custom_attribute('deprecated_monitoring_middleware', 'MonitoringMemoryMiddleware')
