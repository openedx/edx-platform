"""
Toggles for courseware in-course experience.
"""

from edx_toggles.toggles import WaffleFlagNamespace
from lms.djangoapps.experiments.flags import ExperimentWaffleFlag
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace for courseware waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='courseware')

# .. toggle_name: courseware.courseware_mfe
# .. toggle_implementation: ExperimentWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to redirect to another learner profile experience. Supports staged rollout to
#   students for a new micro-frontend-based implementation of the courseware page.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-01-29
# .. toggle_target_removal_date: 2020-12-31
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL and
#   ENABLE_COURSEWARE_MICROFRONTEND.
# .. toggle_tickets: TNL-7000
REDIRECT_TO_COURSEWARE_MICROFRONTEND = ExperimentWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'courseware_mfe', __name__, use_course_aware_bucketing=False
)

# .. toggle_name: courseware.microfrontend_course_team_preview
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to display a link for the new learner experience to course teams without
#   redirecting students. Supports staged rollout to course teams of a new micro-frontend-based implementation of the
#   courseware page.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-03-09
# .. toggle_target_removal_date: 2020-12-31
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL and
#   ENABLE_COURSEWARE_MICROFRONTEND.
# .. toggle_tickets: TNL-6982
COURSEWARE_MICROFRONTEND_COURSE_TEAM_PREVIEW = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'microfrontend_course_team_preview', __name__
)

# Waffle flag to enable the course exit page in the learning MFE.
#
# .. toggle_name: courseware.microfrontend_course_exit_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout of the new micro-frontend-based implementation of the course exit page.
# .. toggle_category: micro-frontend
# .. toggle_use_cases: open_edx, temporary
# .. toggle_creation_date: 2020-10-02
# .. toggle_target_removal_date: None
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL and ENABLE_COURSEWARE_MICROFRONTEND.
# .. toggle_tickets: AA-188
COURSEWARE_MICROFRONTEND_COURSE_EXIT_PAGE = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'microfrontend_course_exit_page', __name__
)

# .. toggle_name: courseware.mfe_progress_milestones
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to display learner progress milestones in a course. Supports staged
#   rollout to students for a new micro-frontend-based implementation of the courseware page.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-10-07
# .. toggle_target_removal_date: none
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL and ENABLE_COURSEWARE_MICROFRONTEND.
# .. toggle_tickets: AA-371
COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'mfe_progress_milestones', __name__
)

# .. toggle_name: courseware.mfe_progress_milestones_first_section_celebration
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to display a celebration modal on learner completion of their first section.
#   Supports staged rollout to students for a new micro-frontend-based implementation of the
#   courseware page.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-10-07
# .. toggle_target_removal_date: None
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL and ENABLE_COURSEWARE_MICROFRONTEND and
#   COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES.
# .. toggle_tickets: AA-371
COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_FIRST_SECTION_CELEBRATION = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'mfe_progress_milestones_first_section_celebration', __name__
)

# .. toggle_name: courseware.proctoring_improvements
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to toggle various enhancements to the proctoring experience, including but
#   not limited to the display of learner facing proctoring information on the course outline, changes to the Proctortrack
#   onboarding flow, changes to IDV (identity verification) requirements, etc.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2020-10-07
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: MST-432
COURSEWARE_PROCTORING_IMPROVEMENTS = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'proctoring_improvements', __name__
)


def course_exit_page_is_active(course_key):
    return (
        REDIRECT_TO_COURSEWARE_MICROFRONTEND.is_enabled(course_key) and
        COURSEWARE_MICROFRONTEND_COURSE_EXIT_PAGE.is_enabled(course_key)
    )


def courseware_mfe_first_section_celebration_is_active(course_key):
    return (
        REDIRECT_TO_COURSEWARE_MICROFRONTEND.is_enabled(course_key) and
        COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES.is_enabled(course_key) and
        COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_FIRST_SECTION_CELEBRATION.is_enabled(course_key)
    )
