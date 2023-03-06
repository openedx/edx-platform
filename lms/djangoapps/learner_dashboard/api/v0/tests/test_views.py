"""
Unit tests for Learner Dashboard REST APIs and Views
"""

from unittest import mock
from uuid import uuid4

import ddt
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse_lazy
from edx_toggles.toggles.testutils import override_waffle_flag
from enterprise.models import EnterpriseCourseEnrollment
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import (
    CourseFactory as ModuleStoreCourseFactory,
)

from common.djangoapps.student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
)
from common.djangoapps.student.toggles import ENABLE_FALLBACK_RECOMMENDATIONS
from lms.djangoapps.program_enrollments.rest_api.v1.tests.test_views import (
    ProgramCacheMixin,
)
from lms.djangoapps.program_enrollments.tests.factories import ProgramEnrollmentFactory
from openedx.core.djangoapps.catalog.cache import SITE_PROGRAM_UUIDS_CACHE_KEY_TPL
from openedx.core.djangoapps.catalog.constants import PathwayType
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    PathwayFactory,
    ProgramFactory,
)
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.site_configuration.tests.test_util import (
    with_site_configuration,
)
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.tests.factories import (
    EnterpriseCourseEnrollmentFactory,
    EnterpriseCustomerFactory,
    EnterpriseCustomerUserFactory,
)

PROGRAMS_UTILS_MODULE = 'openedx.core.djangoapps.programs.utils'


@skip_unless_lms
@mock.patch(PROGRAMS_UTILS_MODULE + '.get_pathways')
@mock.patch(PROGRAMS_UTILS_MODULE + '.get_programs')
class TestProgramProgressDetailView(ProgramsApiConfigMixin, SharedModuleStoreTestCase):
    """Unit tests for the program progress detail page."""
    program_uuid = str(uuid4())
    password = 'test'
    url = reverse_lazy('learner_dashboard:v0:program_progress_detail', kwargs={'program_uuid': program_uuid})

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        modulestore_course = ModuleStoreCourseFactory()
        course_run = CourseRunFactory(key=str(modulestore_course.id))  # lint-amnesty, pylint: disable=no-member
        course = CourseFactory(course_runs=[course_run])

        cls.program_data = ProgramFactory(uuid=cls.program_uuid, courses=[course])
        cls.pathway_data = PathwayFactory()
        cls.program_data['pathway_ids'] = [cls.pathway_data['id']]
        cls.pathway_data['program_uuids'] = [cls.program_data['uuid']]
        del cls.pathway_data['programs']  # lint-amnesty, pylint: disable=unsupported-delete-operation

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.client.login(username=self.user.username, password=self.password)

    def assert_program_data_present(self, response):
        """Verify that program data is present."""
        self.assertContains(response, 'program_data')
        self.assertContains(response, 'course_data')
        self.assertContains(response, 'urls')
        self.assertContains(response, 'certificate_data')
        self.assertContains(response, self.program_data['title'])

    def assert_pathway_data_present(self, response):
        """ Verify that the correct pathway data is present. """
        self.assertContains(response, 'industry_pathways')
        self.assertContains(response, 'credit_pathways')

        industry_pathways = response.data['industry_pathways']
        credit_pathways = response.data['credit_pathways']
        if self.pathway_data['pathway_type'] == PathwayType.CREDIT.value:
            credit_pathway, = credit_pathways  # Verify that there is only one credit pathway
            assert self.pathway_data == credit_pathway
            assert [] == industry_pathways
        elif self.pathway_data['pathway_type'] == PathwayType.INDUSTRY.value:
            industry_pathway, = industry_pathways  # Verify that there is only one industry pathway
            assert self.pathway_data == industry_pathway
            assert [] == credit_pathways

    def test_api_returns_correct_program_data(self, mock_get_programs, mock_get_pathways):
        """
        Verify that API returns program data in the correct format.
        """
        self.create_programs_config()
        mock_get_programs.return_value = self.program_data
        mock_get_pathways.return_value = self.pathway_data

        with mock.patch('lms.djangoapps.learner_dashboard.api.v0.views.get_certificates') as certs:
            certs.return_value = [{'type': 'program', 'url': '/'}]
            response = self.client.get(self.url)

        assert response.status_code == 200
        self.assert_program_data_present(response)
        self.assert_pathway_data_present(response)

    def test_login_required(self, mock_get_programs, mock_get_pathways):
        """
        Verify that API returns 401 to an unauthenticated user.
        """
        self.create_programs_config()
        mock_get_programs.return_value = self.program_data
        mock_get_pathways.return_value = self.pathway_data

        self.client.logout()

        response = self.client.get(self.url)
        assert response.status_code == 401

    def test_404_if_no_program_data(self, mock_get_programs, _mock_get_pathways):
        """
        Verify that the API returns 404 if program data is not available.
        """
        self.create_programs_config()

        mock_get_programs.return_value = {}

        response = self.client.get(self.url)
        assert response.status_code == 404
        assert response.data['error_code'] == 'No program data available.'


class TestProgramsView(SharedModuleStoreTestCase, ProgramCacheMixin):
    """Unit tests for the program details page."""

    enterprise_uuid = str(uuid4())
    program_uuid = str(uuid4())
    password = 'test'
    url = reverse_lazy('learner_dashboard:v0:program_list', kwargs={'enterprise_uuid': enterprise_uuid})

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = UserFactory()
        modulestore_course = ModuleStoreCourseFactory()
        course_run = CourseRunFactory(key=str(modulestore_course.id))
        course = CourseFactory(course_runs=[course_run])
        enterprise_customer = EnterpriseCustomerFactory(uuid=cls.enterprise_uuid)
        enterprise_customer_user = EnterpriseCustomerUserFactory(
            user_id=cls.user.id,
            enterprise_customer=enterprise_customer
        )
        CourseEnrollmentFactory(
            is_active=True,
            course_id=modulestore_course.id,
            user=cls.user
        )
        EnterpriseCourseEnrollmentFactory(
            course_id=modulestore_course.id,
            enterprise_customer_user=enterprise_customer_user
        )

        cls.program = ProgramFactory(
            uuid=cls.program_uuid,
            courses=[course],
            title='Journey to cooking',
            type='MicroMasters',
            authoring_organizations=[{
                'key': 'MAX',
                'logo_image_url': 'http://test.org/media/organization/logos/test-logo.png'
            }],
        )
        cls.site = SiteFactory(domain='test.localhost')

    def setUp(self):
        super().setUp()
        self.client.login(username=self.user.username, password=self.password)
        self.set_program_in_catalog_cache(self.program_uuid, self.program)
        ProgramEnrollmentFactory.create(
            user=self.user,
            program_uuid=self.program_uuid,
            external_user_key='0001',
        )

    @with_site_configuration(configuration={'COURSE_CATALOG_API_URL': 'foo'})
    def test_program_list(self):
        """
        Verify API returns proper response.
        """
        cache.set(
            SITE_PROGRAM_UUIDS_CACHE_KEY_TPL.format(domain=self.site.domain),
            [self.program_uuid],
            None
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        program = response.data[0]

        assert len(program)
        assert program['uuid'] == self.program['uuid']
        assert program['title'] == self.program['title']
        assert program['type'] == self.program['type']
        assert program['authoring_organizations'] == self.program['authoring_organizations']
        assert program['banner_image'] == self.program['banner_image']
        assert program['progress'] == {
            'uuid': self.program['uuid'],
            'completed': 0,
            'in_progress': 0,
            'not_started': 1
        }

    @with_site_configuration(configuration={'COURSE_CATALOG_API_URL': 'foo'})
    def test_program_empty_list_if_no_enterprise_enrollments(self):
        """
        Verify API returns empty response if no enterprise enrollments exists for a learner.
        """
        # delete all enterprise course enrollments for the user
        EnterpriseCourseEnrollment.objects.filter(
            enterprise_customer_user__user_id=self.user.id
        ).delete()

        cache.set(
            SITE_PROGRAM_UUIDS_CACHE_KEY_TPL.format(domain=self.site.domain),
            [self.program_uuid],
            None
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])


@ddt.ddt
class TestCourseRecommendationApiView(TestCase):
    """Unit tests for the course recommendations on dashboard page."""

    url = reverse_lazy("learner_dashboard:v0:courses")
    GENERAL_RECOMMENDATIONS = [
        {
            "course_key": "HogwartsX+6.00.1x",
            "logo_image_url": "https://discovery/organization/logos/logo1.png",
            "marketing_url": "https://marketing-site.com/course/hogwarts-101",
            "title": "Defense Against the Dark Arts",
        },
        {
            "course_key": "MonstersX+SC101EN",
            "logo_image_url": "https://discovery/organization/logos/logo2.png",
            "marketing_url": "https://marketing-site.com/course/monsters-anatomy-101",
            "title": "Scaring 101",
        },
    ]

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="test")
        self.recommended_courses = [
            "MITx+6.00.1x",
            "IBM+PY0101EN",
            "HarvardX+CS50P",
            "UQx+IELTSx",
            "HarvardX+CS50x",
            "Harvard+CS50z",
            "BabsonX+EPS03x",
            "TUMx+QPLS2x",
            "NYUx+FCS.NET.1",
            "MichinX+101x",
        ]
        self.general_recommendation_courses = ["HogwartsX+6.00.1x", "MonstersX+SC101EN"]

    def _get_filtered_courses(self):
        """
        Returns the filtered course data
        """
        filtered_course = []
        for course_key in self.recommended_courses[:5]:
            filtered_course.append({
                "key": course_key,
                "title": f"Title for {course_key}",
                "logo_image_url": "https://www.logo_image_url.com",
                "marketing_url": "https://www.marketing_url.com",
            })
        return filtered_course

    @ddt.data(
        (True, GENERAL_RECOMMENDATIONS),
        (False, []),
    )
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_dashboard.api.v0.views.get_amplitude_course_recommendations"
    )
    @ddt.unpack
    def test_amplitude_user_profile_call_failed(
        self,
        show_fallback_recommendations,
        expected_course_list,
        get_amplitude_course_recommendations_mock,
    ):
        """
        Test that if the call to Amplitude user profile API fails, we return the
        fallback recommendations.

        If the fallback recommendations are not configured, an empty course list is returned.
        """
        get_amplitude_course_recommendations_mock.side_effect = Exception
        with override_waffle_flag(
            ENABLE_FALLBACK_RECOMMENDATIONS, active=show_fallback_recommendations
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, {"courses": expected_course_list, "is_control": None}
        )

    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch("lms.djangoapps.learner_dashboard.api.v0.views.segment.track")
    @mock.patch(
        "lms.djangoapps.learner_dashboard.api.v0.views.get_amplitude_course_recommendations"
    )
    def test_amplitude_recommended_no_courses(
        self,
        get_amplitude_course_recommendations_mock,
        segment_mock,
    ):
        """
        Verify API returns fallback recommendations if no courses are recommended by Amplitude.
        """
        get_amplitude_course_recommendations_mock.return_value = [False, True, []]

        with override_waffle_flag(ENABLE_FALLBACK_RECOMMENDATIONS, active=True):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"courses": self.GENERAL_RECOMMENDATIONS, "is_control": False},
        )

        # Verify that the segment event was fired
        assert segment_mock.call_args[0][1] == "edx.bi.user.recommendations.viewed"
        self.assertEqual(
            segment_mock.call_args[0][2],
            {
                "is_control": False,
                "amplitude_recommendations": False,
                "course_key_array": self.general_recommendation_courses,
                "page": "dashboard",
            },
        )

    @mock.patch("lms.djangoapps.learner_dashboard.api.v0.views.segment.track")
    @mock.patch(
        "lms.djangoapps.learner_dashboard.api.v0.views.get_amplitude_course_recommendations"
    )
    @mock.patch("lms.djangoapps.learner_dashboard.api.v0.views.filter_recommended_courses")
    def test_get_course_recommendations(
        self,
        filter_recommended_courses_mock,
        get_amplitude_course_recommendations_mock,
        segment_mock,
    ):
        """
        Verify API returns course recommendations for users that fall in non-control group.
        """
        filter_recommended_courses_mock.return_value = self._get_filtered_courses()
        get_amplitude_course_recommendations_mock.return_value = [
            False,
            True,
            self.recommended_courses,
        ]
        expected_recommendations = 5

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("is_control"), False)
        self.assertEqual(len(response.data.get("courses")), expected_recommendations)

        # Verify that the segment event was fired
        assert segment_mock.call_args[0][1] == "edx.bi.user.recommendations.viewed"
        self.assertEqual(
            segment_mock.call_args[0][2],
            {
                "is_control": False,
                "amplitude_recommendations": True,
                "course_key_array": [course.get("key") for course in
                                     self._get_filtered_courses()[:expected_recommendations]],
                "page": "dashboard",
            },
        )

    @ddt.data(
        (True, False, None),
        (False, True, False),
        (False, False, None),
        (True, True, True),
    )
    @mock.patch("lms.djangoapps.learner_dashboard.api.v0.views.segment.track")
    @mock.patch("lms.djangoapps.learner_dashboard.api.v0.views.filter_recommended_courses")
    @mock.patch(
        "lms.djangoapps.learner_dashboard.api.v0.views.get_amplitude_course_recommendations"
    )
    @ddt.unpack
    def test_recommendations_viewed_segment_event(
        self,
        is_control,
        has_is_control,
        expected_is_control,
        get_amplitude_course_recommendations_mock,
        filter_recommended_courses_mock,
        segment_mock,
    ):
        filter_recommended_courses_mock.return_value = self._get_filtered_courses()
        get_amplitude_course_recommendations_mock.return_value = [
            is_control,
            has_is_control,
            self.recommended_courses,
        ]
        self.client.get(self.url)

        assert segment_mock.call_count == 1
        assert segment_mock.call_args[0][1] == "edx.bi.user.recommendations.viewed"
        self.assertEqual(
            segment_mock.call_args[0][2]["is_control"], expected_is_control
        )

    @mock.patch(
        "lms.djangoapps.learner_dashboard.api.v0.views.is_user_enrolled_in_ut_austin_masters_program"
    )
    def test_no_recommendations_for_masters_program_learners(
        self, is_user_enrolled_in_ut_austin_masters_program_mock
    ):
        """
        Verify API returns no recommendations if a user is enrolled in UT Austin masters program.
        """
        is_user_enrolled_in_ut_austin_masters_program_mock.return_value = True

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("is_control"), None)
        self.assertEqual(len(response.data.get("courses")), 0)
