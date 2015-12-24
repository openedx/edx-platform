"""
Settings file for running unit tests
"""
# pylint: disable=wildcard-import
from .test_base import *


# This hack disables migrations during tests. We want to create tables directly from the models for speed.
# See https://groups.google.com/d/msg/django-developers/PWPj3etj3-U/kCl6pMsQYYoJ.
MIGRATION_MODULES = {app: "app.migrations_not_used_in_tests" for app in INSTALLED_APPS}
