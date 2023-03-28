"""
This module contains configuration settings via waffle flags for the xmodule modulestore.
"""

from edx_toggles.toggles import WaffleSwitch

# XModule Namespace
WAFFLE_NAMESPACE = 'xmodule'

# .. toggle_name: xmodule.enable_atlas_translations
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Waffle switch for loading XBlock translations from external directory in line with to OEP-58.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-03-28
# .. toggle_tickets: TODO: add here the docs.openedx.org document link.

ENABLE_ATLAS_TRANSLATIONS = WaffleSwitch(
    f'{WAFFLE_NAMESPACE}.enable_atlas_translations', __name__
)
