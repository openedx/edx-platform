"""
Toggles for courseware in-course experience.
"""

from edx_toggles.toggles import LegacyWaffleFlagNamespace
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


# Namespace for courseware waffle flags.
WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='courseware')

# .. toggle_name: courseware.courseware_mfe
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to redirect to another learner profile experience. Supports staged rollout to
#   students for a new micro-frontend-based implementation of the courseware page.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-01-29
# .. toggle_target_removal_date: 2020-12-31
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL.
# .. toggle_tickets: DEPR-109
REDIRECT_TO_COURSEWARE_MICROFRONTEND = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'courseware_mfe', __name__
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
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL.
# .. toggle_tickets: DEPR-109
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
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL.
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
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL.
# .. toggle_tickets: AA-371
COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'mfe_progress_milestones', __name__
)

# .. toggle_name: courseware.mfe_progress_milestones_streak_celebration
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to display a celebration modal when learner completes a configurable streak
#   Supports staged rollout to students for a new micro-frontend-based implementation of the
#   courseware page.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-02-16
# .. toggle_target_removal_date: None
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL and
#   COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES.
# .. toggle_tickets: AA-304
COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_STREAK_CELEBRATION = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'mfe_progress_milestones_streak_celebration', __name__
)

# .. toggle_name: courseware.proctoring_improvements
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to toggle various enhancements to the proctoring experience, including but
#   not limited to the display of learner facing proctoring information on the course outline, changes to the
#   Proctortrack onboarding flow, changes to IDV (identity verification) requirements, etc.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2020-10-07
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: MST-432
COURSEWARE_PROCTORING_IMPROVEMENTS = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'proctoring_improvements', __name__
)

# .. toggle_name: courseware.exam_resume_proctoring_improvements
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to toggle various exam resumption enhancements to the proctoring experience,
#   including but not limited to the addition of a "Resume" action for exam attempts in the "error" state to the
#   Student Special Exam Attempts panel of the Special Exams tab of the Instructor Dashboard, etc.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2020-01-25
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: MST-597
EXAM_RESUME_PROCTORING_IMPROVEMENTS = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'exam_resume_proctoring_improvements', __name__
)

# .. toggle_name: courseware.optimized_render_xblock
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag that determines whether we speed up the render_xblock for browsers by
#   removing unnecessary JavaScript and CSS. It is possible that this could introduce edge cases with content
#   that relies on these assets, so being a CourseWaffleFlag will give us the flexibility to exempt courses
#   from these optimizations.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-02-09
# .. toggle_target_removal_date: 2021-05-01
# .. toggle_warnings: None
COURSEWARE_OPTIMIZED_RENDER_XBLOCK = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'optimized_render_xblock', __name__
)


def courseware_mfe_is_active(course_key: CourseKey) -> bool:
    """
    Should we serve the Learning MFE as the canonical courseware experience?
    """
    # NO: Old Mongo courses are always served in the Legacy frontend,
    #     regardless of configuration.
    if course_key.deprecated:
        return False
    # OTHERWISE: Defer to value of waffle flag for this course run and user.
    return REDIRECT_TO_COURSEWARE_MICROFRONTEND.is_enabled(course_key)


def courseware_mfe_is_visible(
        course_key: CourseKey,
        is_global_staff=False,
        is_course_staff=False,
) -> bool:
    """
    Can we see a course run's content in the Learning MFE?
    """
    # DENY: Old Mongo courses don't work in the MFE.
    if course_key.deprecated:
        return False
    # ALLOW: Where techincally possible, global staff may always see the MFE.
    if is_global_staff:
        return True
    # ALLOW: If course team preview is enabled, then course staff may see their
    #        course in the MFE.
    if is_course_staff and COURSEWARE_MICROFRONTEND_COURSE_TEAM_PREVIEW.is_enabled(course_key):
        return True
    # OTHERWISE: The MFE is only visible if it's the active (ie canonical) experience.
    return courseware_mfe_is_active(course_key)


def courseware_legacy_is_visible(
        course_key: CourseKey,
        is_global_staff=False,
        is_course_staff=False,
) -> bool:
    """
    Can we see a course run's content in the Legacy frontend?

    Note: This function will always return True for Old Mongo courses,
    since `courseware_mfe_is_active` will always return False for them.
    """
    # ALLOW: Global staff may always see the Legacy experience.
    if is_global_staff:
        return True
    # ALLOW: The course team may always see their course in the Legacy experience.
    if is_course_staff:
        return True
    # OTHERWISE: Legacy is only visible if it's the active (ie canonical) experience.
    #            Note that Old Mongo courses are never the active experience,
    #            so we effectively always ALLOW them to be viewed in Legacy.
    return not courseware_mfe_is_active(course_key)


def course_exit_page_is_active(course_key):
    return (
        courseware_mfe_is_active(course_key) and
        COURSEWARE_MICROFRONTEND_COURSE_EXIT_PAGE.is_enabled(course_key)
    )


def courseware_mfe_progress_milestones_are_active(course_key):
    return (
        courseware_mfe_is_active(course_key) and
        COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES.is_enabled(course_key)
    )


def streak_celebration_is_active(course_key):
    return (
        courseware_mfe_is_active(course_key) and
        COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_STREAK_CELEBRATION.is_enabled(course_key)
    )
