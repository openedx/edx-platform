"""
Rollout waffle flags for the learning_sequences API.
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


WAFFLE_NAMESPACE = 'learning_sequences'

# .. toggle_name: learning_sequences.use_for_outlines
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_description: Waffle flag to enable the use of the Learning Sequences
#   Course Outline API (/api/learning_sequences/v1/course_outline/{course_key}).
#   If this endpoint is not enabled for a given course, it will return a 403
#   error. The Courseware MFE should know how to detect this condition. To
#   see the value of this API for a course before it has officially been rolled
#   out for it, you can bypass this check by passing force_on=1 as a querystring
#   parameter. This flag is also used to determine what is returned by the
#   public_api_available learning_sequences API function, though other apps
#   calling this API are always able to ignore this result and call any
#   learning_sequences API directly (e.g. get_course_outline).
# .. toggle_default: False
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-06-07
# .. toggle_target_removal_date: 2020-08-01
USE_FOR_OUTLINES = CourseWaffleFlag(WAFFLE_NAMESPACE, 'use_for_outlines', __name__)
