"""
Unit tests for Learner Dashboard REST APIs and Views
"""

from unittest import mock
from uuid import uuid4

from django.urls import reverse_lazy
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory as ModuleStoreCourseFactory

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.catalog.constants import PathwayType
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    PathwayFactory,
    ProgramFactory
)
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangolib.testing.utils import skip_unless_lms

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
