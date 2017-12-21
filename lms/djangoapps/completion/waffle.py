"""
This module contains various configuration settings via
waffle switches for the completion app.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = 'completion'

# Switches

# Full name: completion.enable_completion_tracking
# Indicates whether or not to track completion of individual blocks.  Keeping
# this disabled will prevent creation of BlockCompletion objects in the
# database, as well as preventing completion-related network access by certain
# xblocks.
ENABLE_COMPLETION_TRACKING = 'enable_completion_tracking'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for completion.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix='completion: ')
