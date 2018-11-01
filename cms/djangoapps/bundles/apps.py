"""
Django app configuration for the Studio Bundles API
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from django.apps import AppConfig


class BundlesConfig(AppConfig):
    name = 'cms.djangoapps.bundles'
    verbose_name = 'Bundle API'
