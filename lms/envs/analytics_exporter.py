"""
Settings for running management commands for the Analytics Exporter.

The Analytics Exporter jobs run edxapp management commands using production
settings and configuration, however they currently DO NOT use edxapp production
environments (such as edxapp Amazon AMIs or Docker images) where theme files
get installed.  As a result we must disable comprehensive theming or else
startup checks from the theming app will throw an error due to missing themes.
"""

from .production import *  # pylint: disable=wildcard-import, unused-wildcard-import

ENABLE_COMPREHENSIVE_THEMING = False
