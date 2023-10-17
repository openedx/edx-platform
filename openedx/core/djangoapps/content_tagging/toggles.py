
"""
Toggles for content tagging
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# .. toggle_name: content_tagging.auto
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Setting this enables automatic tagging of content
# .. toggle_type: feature_flag
# .. toggle_category: admin
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2023-08-30
# .. toggle_tickets: https://github.com/openedx/modular-learning/issues/79
CONTENT_TAGGING_AUTO = CourseWaffleFlag('content_tagging.auto', __name__)
