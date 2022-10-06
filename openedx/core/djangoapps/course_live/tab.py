"""
Configurations to render Course Live Tab
"""
from django.utils.translation import gettext_lazy
from lti_consumer.models import LtiConfiguration

from xmodule.course_module import CourseBlock
from xmodule.tabs import TabFragmentViewMixin
from lms.djangoapps.courseware.tabs import EnrolledTab
from openedx.core.djangoapps.course_live.config.waffle import ENABLE_COURSE_LIVE
from openedx.core.djangoapps.course_live.models import CourseLiveConfiguration
from openedx.core.djangoapps.course_live.providers import ProviderManager, HasGlobalCredentials
from openedx.core.lib.cache_utils import request_cached
from openedx.features.course_experience.url_helpers import get_learning_mfe_home_url
from openedx.features.lti_course_tab.tab import LtiCourseLaunchMixin


class CourseLiveTab(LtiCourseLaunchMixin, TabFragmentViewMixin, EnrolledTab):
    """
    Course tab that loads the associated LTI-based live provider in a tab.
    """
    type = 'lti_live'
    priority = 42
    allow_multiple = False
    is_dynamic = True
    title = gettext_lazy("Live")
    ROLE_MAP = {
        'student': 'Student',
        'staff': 'Administrator',
        'instructor': 'Administrator',
    }

    @property
    def link_func(self):
        def _link_func(course, reverse_func):
            return get_learning_mfe_home_url(course_key=course.id, url_fragment='live')

        return _link_func

    @request_cached()
    def _get_lti_config(self, course: CourseBlock) -> LtiConfiguration:
        """
        Get course live configurations
        """
        course_live_configurations = CourseLiveConfiguration.get(course.id)
        if course_live_configurations.free_tier:
            providers = ProviderManager().get_enabled_providers()
            provider = providers[course_live_configurations.provider_type]
            if isinstance(provider, HasGlobalCredentials):
                return LtiConfiguration(
                    lti_1p1_launch_url=provider.url,
                    lti_1p1_client_key=provider.key,
                    lti_1p1_client_secret=provider.secret,
                    version='lti_1p1',
                    config_store=LtiConfiguration.CONFIG_ON_DB,
                )
            else:
                raise ValueError("Provider does not support global credentials")
        return course_live_configurations.lti_configuration

    @classmethod
    @request_cached()
    def is_enabled(cls, course, user=None):
        """
        Check if the tab is enabled.
        """
        return (
            ENABLE_COURSE_LIVE.is_enabled(course.id) and
            super().is_enabled(course, user) and
            CourseLiveConfiguration.is_enabled(course.id)
        )
