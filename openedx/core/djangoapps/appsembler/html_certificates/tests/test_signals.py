"""Test appsembler.html_certificates.signals module
"""

from django.test import TestCase, override_settings
from mock import Mock

from openedx.core.djangoapps.appsembler.html_certificates.signals import (
    set_default_mode_on_course_publish
)
from lms.djangoapps.certificates.models import CertificateGenerationCourseSetting
from course_modes.models import CourseMode
from openedx.core.djangoapps.content.course_overviews.tests.factories import (
    CourseOverviewFactory
)

from course_modes.tests.factories import CourseModeFactory

from openedx.core.djangoapps.appsembler.html_certificates.tests.factories import (
    CertificateGenerationCourseSettingFactory
)


@override_settings(DEFAULT_COURSE_MODE_SLUG='anything')
@override_settings(DEFAULT_MODE_NAME_FROM_SLUG='Anything')
class SetDefaultModeOnCoursePublishSignalTests(TestCase):

    def setUp(self):
        self.course_overview = CourseOverviewFactory()
        self.sender = Mock()

    def assert_results(self):
        check_course_mode = CourseMode.objects.get(course_id=self.course_overview.id,
                                                   mode_slug='anything')
        assert check_course_mode.mode_display_name == 'Anything'
        check_cgcs = CertificateGenerationCourseSetting.objects.get(
            course_key=self.course_overview.id)
        assert check_cgcs.self_generation_enabled is True

    def test_neither_code_mode_nor_cert_gen_settings_exist_prior(self):
        # Course mode does not exist prior
        assert not CourseMode.objects.filter(course_id=self.course_overview.id,
                                             mode_slug='anything').exists()
        # Cert gen setting does not exist prior
        assert not CertificateGenerationCourseSetting.objects.filter(
            course_key=self.course_overview.id).exists()

        set_default_mode_on_course_publish(self.sender, self.course_overview.id)
        self.assert_results()

    def test_course_mode_not_exists_prior_but_cert_gen_setting_exists_prior(self):
        # Course mode does not exist prior
        assert not CourseMode.objects.filter(
            course_id=self.course_overview.id,
            mode_slug='anything').exists()
        # Cert gen setting exists prior
        CertificateGenerationCourseSettingFactory(
            course_key=self.course_overview.id,
            self_generation_enabled=False)

        set_default_mode_on_course_publish(self.sender, self.course_overview.id)
        self.assert_results()

    def test_course_mode_exists_prior_but_cert_gen_setting_not_exists_prior(self):
        # Course mode does not exist prior
        assert not CourseMode.objects.filter(
            course_id=self.course_overview.id,
            mode_slug='anything').exists()
        # Cert gen setting exists prior
        CertificateGenerationCourseSettingFactory(
            course_key=self.course_overview.id,
            self_generation_enabled=False)

        set_default_mode_on_course_publish(self.sender, self.course_overview.id)
        self.assert_results()

    def test_both_course_mode_and_cert_gen_setting_exist_prior(self):
        # Course mode exists prior
        CourseModeFactory(course_id=self.course_overview.id,
                          mode_slug='anything',
                          mode_display_name='Anything')

        # Cert gen setting exists prior
        CertificateGenerationCourseSettingFactory(
            course_key=self.course_overview.id,
            self_generation_enabled=False)

        set_default_mode_on_course_publish(self.sender, self.course_overview.id)
        self.assert_results()
