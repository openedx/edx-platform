"""
Toggles for courseware in-course experience.
"""

from edx_toggles.toggles import SettingToggle, WaffleSwitch

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace for courseware waffle flags.
WAFFLE_FLAG_NAMESPACE = 'courseware'


# Waffle flag to enable the course exit page in the learning MFE.
#
# .. toggle_name: courseware.microfrontend_course_exit_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout of the new micro-frontend-based implementation of the course exit page.
# .. toggle_use_cases: open_edx, temporary
# .. toggle_creation_date: 2020-10-02
# .. toggle_target_removal_date: None
# .. toggle_warning: Also set settings.LEARNING_MICROFRONTEND_URL.
# .. toggle_tickets: AA-188
COURSEWARE_MICROFRONTEND_COURSE_EXIT_PAGE = CourseWaffleFlag(
    f'{WAFFLE_FLAG_NAMESPACE}.microfrontend_course_exit_page', __name__
)

# .. toggle_name: courseware.mfe_progress_milestones
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to display learner progress milestones in a course. Supports staged
#   rollout to students for a new micro-frontend-based implementation of the courseware page.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-10-07
# .. toggle_target_removal_date: none
# .. toggle_warning: Also set settings.LEARNING_MICROFRONTEND_URL.
# .. toggle_tickets: AA-371
COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES = CourseWaffleFlag(
    f'{WAFFLE_FLAG_NAMESPACE}.mfe_progress_milestones', __name__
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
# .. toggle_warning: Also set settings.LEARNING_MICROFRONTEND_URL and
#   COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES.
# .. toggle_tickets: AA-304
COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_STREAK_CELEBRATION = CourseWaffleFlag(
    f'{WAFFLE_FLAG_NAMESPACE}.mfe_progress_milestones_streak_celebration', __name__
)

# .. toggle_name: courseware.mfe_progress_milestones_streak_discount_enabled
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables an engagement discount incentive message.
# .. toggle_warning: This flag depends on the streak celebration feature being enabled
# .. toggle_use_cases: opt_out, open_edx
# .. toggle_creation_date: 2021-08-26
# .. toggle_target_removal_date: None
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-950
COURSEWARE_MFE_MILESTONES_STREAK_DISCOUNT = CourseWaffleFlag(
    f'{WAFFLE_FLAG_NAMESPACE}.streak_discount_enabled', __name__
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
COURSEWARE_OPTIMIZED_RENDER_XBLOCK = CourseWaffleFlag(
    f'{WAFFLE_FLAG_NAMESPACE}.optimized_render_xblock', __name__
)

# .. toggle_name: COURSES_INVITE_ONLY
# .. toggle_implementation: SettingToggle
# .. toggle_type: feature_flag
# .. toggle_default: False
# .. toggle_description: Setting this sets the default value of INVITE_ONLY across all courses in a given deployment
# .. toggle_category: admin
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2019-05-16
# .. toggle_expiration_date: None
# .. toggle_tickets: https://github.com/mitodl/edx-platform/issues/123
# .. toggle_status: unsupported
COURSES_INVITE_ONLY = SettingToggle('COURSES_INVITE_ONLY', default=False)

ENABLE_OPTIMIZELY_IN_COURSEWARE = WaffleSwitch(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    'RET.enable_optimizely_in_courseware', __name__
)


def courseware_mfe_is_active() -> bool:
    """
    Should we serve the Learning MFE as the canonical courseware experience?
    """
    from lms.djangoapps.courseware.access_utils import in_preview_mode  # avoid a circular import

    # We only use legacy views for the Studio "preview mode" feature these days, while everyone else gets the MFE
    return not in_preview_mode()


def course_exit_page_is_active(course_key):
    return (
        courseware_mfe_is_active() and
        COURSEWARE_MICROFRONTEND_COURSE_EXIT_PAGE.is_enabled(course_key)
    )


def courseware_mfe_progress_milestones_are_active(course_key):
    return (
        courseware_mfe_is_active() and
        COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES.is_enabled(course_key)
    )


def streak_celebration_is_active(course_key):
    return (
        courseware_mfe_progress_milestones_are_active(course_key) and
        COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_STREAK_CELEBRATION.is_enabled(course_key)
    )


def course_is_invitation_only(courselike) -> bool:
    """Returns whether the course is invitation only or not."""
    # We also mark Old Mongo courses (deprecated keys) as invitation only to cut off enrollment
    return COURSES_INVITE_ONLY.is_enabled() or courselike.invitation_only or courselike.id.deprecated
