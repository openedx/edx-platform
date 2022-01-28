"""
Toggles for courseware in-course experience.
"""

from edx_toggles.toggles import LegacyWaffleFlagNamespace, SettingToggle
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace for courseware waffle flags.
WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='courseware')


# .. toggle_name: courseware.use_legacy_frontend
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to direct learners to the legacy courseware experience - the default behavior
#   directs to the new MFE-based courseware in frontend-app-learning. Supports the ability to globally flip back to
#   the legacy courseware experience.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-06-03
# .. toggle_target_removal_date: 2021-10-09
# .. toggle_tickets: DEPR-109
COURSEWARE_USE_LEGACY_FRONTEND = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'use_legacy_frontend', __name__
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

# .. toggle_name: courseware.mfe_progress_milestones_streak_discount_enabled
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables an engagement discount incentive message.
# .. toggle_warnings: This flag depends on the streak celebration feature being enabled
# .. toggle_use_cases: opt_out, open_edx
# .. toggle_creation_date: 2021-08-26
# .. toggle_target_removal_date: None
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-950
COURSEWARE_MFE_MILESTONES_STREAK_DISCOUNT = CourseWaffleFlag(
    WAFFLE_FLAG_NAMESPACE, 'streak_discount_enabled',
    __name__,
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
    WAFFLE_FLAG_NAMESPACE, 'optimized_render_xblock', __name__
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


def courseware_mfe_is_active(course_key: CourseKey) -> bool:
    """
    Should we serve the Learning MFE as the canonical courseware experience?
    """
    #Avoid circular imports.
    from lms.djangoapps.courseware.access_utils import in_preview_mode
    # NO: Old Mongo courses are always served in the Legacy frontend,
    #     regardless of configuration.
    if course_key.deprecated:
        return False
    # NO: MFE courseware can be disabled for users/courses/globally via this
    #     Waffle flag.
    if COURSEWARE_USE_LEGACY_FRONTEND.is_enabled(course_key):
        return False
    # NO: Course preview doesn't work in the MFE
    if in_preview_mode():
        return False
    # OTHERWISE: MFE courseware experience is active by default.
    return True


def courseware_mfe_is_visible(
        course_key: CourseKey,
        is_global_staff=False,
        is_course_staff=False,
) -> bool:
    """
    Can we see a course run's content in the Learning MFE?
    """
    #Avoid circular imports.
    from lms.djangoapps.courseware.access_utils import in_preview_mode
    # DENY: Old Mongo courses don't work in the MFE.
    if course_key.deprecated:
        return False
    # DENY: Course preview doesn't work in the MFE
    if in_preview_mode():
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


def courseware_mfe_is_advertised(
        course_key: CourseKey,
        is_global_staff=False,
        is_course_staff=False,
) -> bool:
    """
    Should we invite the user to view a course run's content in the Learning MFE?

    This check is slightly different than `courseware_mfe_is_visible`, in that
    we always *permit* global staff to view MFE content (assuming it's deployed),
    but we do not shove the New Experience in their face if the preview isn't
    enabled.
    """
    #Avoid circular imports.
    from lms.djangoapps.courseware.access_utils import in_preview_mode
    # DENY: Old Mongo courses don't work in the MFE.
    if course_key.deprecated:
        return False
    # DENY: Course preview doesn't work in the MFE
    if in_preview_mode():
        return False
    # ALLOW: Both global and course staff can see the MFE link if the course team
    #        preview is enabled.
    is_staff = is_global_staff or is_course_staff
    if is_staff and COURSEWARE_MICROFRONTEND_COURSE_TEAM_PREVIEW.is_enabled(course_key):
        return True
    # OTHERWISE: The MFE is only advertised if it's the active (ie canonical) experience.
    return courseware_mfe_is_active(course_key)


def courseware_legacy_is_visible(
        course_key: CourseKey,
        is_global_staff=False,
) -> bool:
    """
    Can we see a course run's content in the Legacy frontend?

    Note: This function will always return True for Old Mongo courses,
    since `courseware_mfe_is_active` will always return False for them.
    """
    #Avoid circular imports.
    from lms.djangoapps.courseware.access_utils import in_preview_mode
    # ALLOW: Global staff may always see the Legacy experience.
    if is_global_staff:
        return True
    # ALLOW: All course previews will be shown in Legacy experience
    if in_preview_mode():
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
        courseware_mfe_progress_milestones_are_active(course_key) and
        COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_STREAK_CELEBRATION.is_enabled(course_key)
    )


def course_is_invitation_only(courselike) -> bool:
    """Returns whether the course is invitation only or not."""
    return COURSES_INVITE_ONLY.is_enabled() or courselike.invitation_only
