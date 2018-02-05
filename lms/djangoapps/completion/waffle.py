"""
This module contains various configuration settings via
waffle switches for the completion app.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = 'completion'

# Switches
# Full name: completion.enable_completion_tracking
# Indicates whether or not to track completion of individual blocks.  Keeping
# this disabled will prevent creation of BlockCompletion objects in the
# database, as well as preventing completion-related network access by certain
# xblocks.
ENABLE_COMPLETION_TRACKING = 'enable_completion_tracking'

# Full name completion.enable_visual_progress
# Overrides completion.enable_course_visual_progress
# Acts as a global override -- enable visual progress indicators
# sitewide.
ENABLE_VISUAL_PROGRESS = 'enable_visual_progress'

# Full name completion.enable_course_visual_progress
# Acts as a course-by-course enabling of visual progress
# indicators, e.g. updated 'resume button' functionality
ENABLE_COURSE_VISUAL_PROGRESS = 'enable_course_visual_progress'

# SiteConfiguration visual progress enablement
ENABLE_SITE_VISUAL_PROGRESS = 'enable_site_visual_progress'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for completion.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix='completion: ')


def waffle_flag():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Completion.
    """
    namespace = WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'completion: ')
    return {
        # By default, disable visual progress. Can be enabled on a course-by-course basis.
        # And overridden site-globally by ENABLE_VISUAL_PROGRESS
        ENABLE_COURSE_VISUAL_PROGRESS: CourseWaffleFlag(
            namespace,
            ENABLE_COURSE_VISUAL_PROGRESS,
            flag_undefined_default=False
        )
    }


def visual_progress_enabled(course_key):
    """
    Exposes varia of visual progress feature.
        ENABLE_COMPLETION_TRACKING, current_site.configuration, AND
        enable_course_visual_progress OR enable_visual_progress

    :return:

        bool -> True if site/course/global enabled for visual progress tracking
    """
    if not waffle().is_enabled(ENABLE_COMPLETION_TRACKING):
        return

    try:
        current_site = get_current_site()
        if not current_site.configuration.get_value(ENABLE_SITE_VISUAL_PROGRESS, False):
            return
    except SiteConfiguration.DoesNotExist:
        return

    # Site-aware global override
    if not waffle().is_enabled(ENABLE_VISUAL_PROGRESS):
        # Course enabled
        return waffle_flag()[ENABLE_COURSE_VISUAL_PROGRESS].is_enabled(course_key)

    return True
