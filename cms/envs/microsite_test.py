# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .dev import *
from .dev import SUBDOMAIN_BRANDING, VIRTUAL_UNIVERSITIES

MICROSITE_NAMES = ['openedx']
MICROSITE_CONFIGURATION = {}

if MICROSITE_NAMES and len(MICROSITE_NAMES) > 0:
    enable_microsites(MICROSITE_NAMES, MICROSITE_CONFIGURATION, SUBDOMAIN_BRANDING, VIRTUAL_UNIVERSITIES)
