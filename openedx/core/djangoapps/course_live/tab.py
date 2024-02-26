"""
Configurations to render Course Live Tab
"""
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import gettext_lazy
from lti_consumer.models import LtiConfiguration
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole, GlobalStaff
from lms.djangoapps.courseware.tabs import EnrolledTab
from openedx.core.djangoapps.course_live.models import CourseLiveConfiguration
from openedx.core.djangoapps.course_live.providers import HasGlobalCredentials, ProviderManager
from openedx.core.lib.cache_utils import request_cached
from openedx.features.course_experience.url_helpers import get_learning_mfe_home_url
from openedx.features.lti_course_tab.tab import LtiCourseLaunchMixin
from xmodule.course_block import CourseBlock
from xmodule.tabs import TabFragmentViewMixin


@request_cached()
def provider_is_zoom(course_key: CourseKey) -> bool:
    """
    Check if the provider exists and is Zoom.
    """
    course_live_configurations = CourseLiveConfiguration.get(course_key)

    if not course_live_configurations:
        return False
    return course_live_configurations.provider_type == "zoom"


def user_is_staff_or_instructor(user: AbstractBaseUser, course: CourseBlock) -> bool:
    """
    Check if the user is a staff or instructor for the course.
    """
    return CourseStaffRole(course.id).has_user(user) or CourseInstructorRole(course.id).has_user(user)


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
            super().is_enabled(course, user) and
            CourseLiveConfiguration.is_enabled(course.id)
        )

    def _get_pii_lti_parameters(self, course, request):
        pii_config = super()._get_pii_lti_parameters(course, request)
        if provider_is_zoom(course.id) and user_is_staff_or_instructor(request.user, course):
            pii_config['person_contact_email_primary'] = request.user.email
        return pii_config

    def _get_lti_roles(self, user: AbstractBaseUser, course_key: CourseKey) -> str:
        """
        Get LTI roles for the user and course.
        If the user is a global staff member, return the student role.
        """
        if provider_is_zoom(course_key) and GlobalStaff().has_user(user):
            return self.ROLE_MAP.get('student')
        return super()._get_lti_roles(user, course_key)
