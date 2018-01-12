"""
This module contains various configuration settings via
waffle switches for the course experience app.
"""
from __future__ import unicode_literals

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = 'course_experience'

# Switches
# Full name course_experience.enable_new_course_outline
# Enables the UI changes to the course outline for all courses
ENABLE_NEW_COURSE_OUTLINE = 'enable_new_course_outline'

# Full name course_experience.enable_new_course_outline_for_course
# Enables the UI changes to the course outline for a course
ENABLE_NEW_COURSE_OUTLINE_FOR_COURSE = 'enable_new_course_outline_for_course'

# Full name course_experience.enable_new_course_outline_for_site
# Enables the UI changes to the course outline for a site configuration
ENABLE_NEW_COURSE_OUTLINE_FOR_SITE = 'enable_new_course_outline_for_site'


def waffle_switch():
    """
    Returns the namespaced, cached, audited Waffle class for course experience.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix='course_experience: ')


def waffle_flag():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for course experience.
    """
    namespace = WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'course_experience: ')
    # By default, disable the new course outline. Can be enabled on a course-by-course basis.
    # And overridden site-globally by ENABLE_SITE_NEW_COURSE_OUTLINE
    return CourseWaffleFlag(
        namespace,
        ENABLE_NEW_COURSE_OUTLINE_FOR_COURSE,
        flag_undefined_default=False
    )


def new_course_outline_enabled(course_key):
    """
    Returns whether the new course outline is enabled.
    """
    try:
        current_site = get_current_site()
        if not current_site.configuration.get_value(ENABLE_NEW_COURSE_OUTLINE_FOR_SITE, False):
            return
    except SiteConfiguration.DoesNotExist:
        return

    if not waffle_switch().is_enabled(ENABLE_NEW_COURSE_OUTLINE):
        return waffle_flag().is_enabled(course_key)

    return True
