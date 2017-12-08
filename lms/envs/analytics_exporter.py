"""
This is the settings file used during execution of the analytics-exporter job.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .aws import *

ENABLE_COMPREHENSIVE_THEMING = False
