
"""
Toggles for content tagging
"""

from edx_toggles.toggles import WaffleSwitch

# .. toggle_name: content_tagging.auto
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Setting this enables automatic tagging of content
# .. toggle_type: feature_flag
# .. toggle_category: admin
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2023-08-30
# .. toggle_tickets: https://github.com/openedx/modular-learning/issues/79
CONTENT_TAGGING_AUTO = WaffleSwitch('content_tagging.auto', __name__)
