"""
Configuration for Studio API Django application
"""

from __future__ import absolute_import

from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'cms.djangoapps.api'
    verbose_name = 'API'
