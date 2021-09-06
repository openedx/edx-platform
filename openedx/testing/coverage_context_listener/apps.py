"""
Django AppConfig for the CoverageContextListener
"""
from django.apps import AppConfig


class CoverageContextListenerConfig(AppConfig):
    name = 'openedx.testing.coverage_context_listener'
    verbose_name = "Coverage Context Listener"
