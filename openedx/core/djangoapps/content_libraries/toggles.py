"""
Toggles for content libraries
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# .. toggle_name: content_libraries.map_v1_lib_keys_to_v2_keys
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Setting this enables automatic runtime mapping of v1 library keys to v2 library keys. This presumes that the copy_libraries_from_v1_to_v2 management command has been run sucessfully.
# .. toggle_type: feature_flag
# .. toggle_category: admin
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2023-10-23
# .. toggle_tickets:
MAP_V1_LIBRARIES_TO_V2_LIBRARIES = CourseWaffleFlag('content_libraries.map_v1_lib_keys_to_v2_keys', __name__)
