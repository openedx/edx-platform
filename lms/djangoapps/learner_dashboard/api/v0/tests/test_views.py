"""
Unit tests for Learner Dashboard REST APIs and Views
"""

from unittest import mock
from uuid import uuid4

from django.core.cache import cache
from django.urls import reverse_lazy
from enterprise.models import EnterpriseCourseEnrollment
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory as ModuleStoreCourseFactory

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.program_enrollments.rest_api.v1.tests.test_views import ProgramCacheMixin
from lms.djangoapps.program_enrollments.tests.factories import ProgramEnrollmentFactory
from openedx.core.djangoapps.catalog.cache import SITE_PROGRAM_UUIDS_CACHE_KEY_TPL
from openedx.core.djangoapps.catalog.constants import PathwayType
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    PathwayFactory,
    ProgramFactory
)
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.tests.factories import (
    EnterpriseCourseEnrollmentFactory,
    EnterpriseCustomerFactory,
    EnterpriseCustomerUserFactory
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


class TestCourseRecommendationApiView(SharedModuleStoreTestCase):
    """Unit tests for the course recommendations on dashboard page."""

    password = 'test'
    url = reverse_lazy('learner_dashboard:v0:courses')

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=self.password)
        self.recommended_courses = ['MITx+6.00.1x', 'IBM+PY0101EN', 'HarvardX+CS50P', 'UQx+IELTSx', 'HarvardX+CS50x',
                                    'Harvard+CS50z', 'BabsonX+EPS03x', 'TUMx+QPLS2x', 'NYUx+FCS.NET.1', 'MichinX+101x']
        self.course_data = {
            'course_key': 'MITx+6.00.1x',
            'title': 'Introduction to Computer Science and Programming Using Python',
            'owners': [{'logo_image_url': 'https://prod-discovery.edx-cdn.org/organization/logos/2a73d2ce-c34a-4e08'
                                          '-822383bca9d2f01d-2cc8854c6fee.png'}],
            'marketing_url': 'https://www.edx.org/course/introduction-to-computer-science-and-programming-7'
        }

    @mock.patch('lms.djangoapps.learner_dashboard.api.v0.views.get_personalized_course_recommendations')
    @mock.patch('lms.djangoapps.learner_dashboard.api.v0.views.get_course_data')
    def test_no_recommendations_from_amplitude(self, mocked_get_course_data,
                                               mocked_get_personalized_course_recommendations):
        """
        Verify API returns 400 if no course recommendations from amplitude.
        """
        mocked_get_personalized_course_recommendations.return_value = [False, []]
        mocked_get_course_data.return_value = self.course_data

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, None)

    @mock.patch('lms.djangoapps.learner_dashboard.api.v0.views.get_personalized_course_recommendations')
    @mock.patch('lms.djangoapps.learner_dashboard.api.v0.views.get_course_data')
    def test_get_course_recommendations(self, mocked_get_course_data,
                                        mocked_get_personalized_course_recommendations):
        """
        Verify API returns course recommendations.
        """
        mocked_get_personalized_course_recommendations.return_value = [False, self.recommended_courses]
        mocked_get_course_data.return_value = self.course_data
        expected_recommendations = 5

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('is_personalized_recommendation'), True)
        self.assertEqual(len(response.data.get('courses')), expected_recommendations)

    @mock.patch('lms.djangoapps.learner_dashboard.api.v0.views.get_personalized_course_recommendations')
    @mock.patch('lms.djangoapps.learner_dashboard.api.v0.views.get_course_data')
    def test_get_enrollable_course_recommendations(self, mocked_get_course_data,
                                                   mocked_get_personalized_course_recommendations):
        """
        Verify API returns course recommendations for courses in which user is not enrolled.
        """
        mocked_get_personalized_course_recommendations.return_value = [False, self.recommended_courses]
        mocked_get_course_data.return_value = self.course_data
        course_keys = ['course-v1:IBM+PY0101EN+Run_0', 'course-v1:UQx+IELTSx+Run_0', 'course-v1:MITx+6.00.1x+Run_0',
                       'course-v1:HarvardX+CS50P+Run_0', 'course-v1:Harvard+CS50z+Run_0', 'course-v1:TUMx+QPLS2x+Run_0']
        expected_recommendations = 4
        # enrolling in 6 courses
        for course_key in course_keys:
            CourseEnrollmentFactory(course_id=course_key, user=self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('is_personalized_recommendation'), True)
        self.assertEqual(len(response.data.get('courses')), expected_recommendations)
