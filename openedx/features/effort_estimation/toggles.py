"""
Feature/experiment toggles used for effort estimation.
"""

from edx_toggles.toggles import LegacyWaffleFlagNamespace

from lms.djangoapps.experiments.flags import ExperimentWaffleFlag


WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='effort_estimation')

# Temporary flag while we test which location works best:
# - Bucket 0: off
# - Bucket 1: section (chapter) estimations
# - Bucket 2: subsection (sequential) estimations
EFFORT_ESTIMATION_LOCATION_FLAG = ExperimentWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'location', __name__, num_buckets=3,
                                                       use_course_aware_bucketing=False)
