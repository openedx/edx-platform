"""
This is a localdev test for the Microsite processing pipeline
"""
# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .dev import *

MICROSITE_NAMES = ['openedx']
MICROSITE_CONFIGURATION = {}
FEATURES['USE_MICROSITES'] = True
