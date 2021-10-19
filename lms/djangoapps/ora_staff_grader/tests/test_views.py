"""
Tests for ESG views
"""
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from rest_framework.test import APITestCase
from unittest.mock import patch

from common.djangoapps.student.tests.factories import StaffFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.factories import ItemFactory


class TestInitializeView(SharedModuleStoreTestCase, APITestCase):
    """
    Tests for the /initialize view, creating setup data for ESG
    """
    view_name = 'ora-staff-grader:initialize'
    api_url = reverse(view_name)

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.course = CourseFactory.create()
        cls.course_key = cls.course.location.course_key

        cls.ora_block = ItemFactory.create(
            category='openassessment',
            parent_location=cls.course.location,
            display_name='test',
        )
        cls.ora_usage_key = str(cls.ora_block.location)

        cls.password = 'password'
        cls.staff = StaffFactory(course_key=cls.course_key, password=cls.password)

    def log_in(self):
        """ Log in as staff """
        self.client.login(username=self.staff.username, password=self.password)

    def test_missing_ora_location(self):
        """ Missing ora_location param should return 400 and error message """
        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url)

        assert response.status_code == 400
        assert response.content.decode() == "Query must contain an ora_location param."

    def test_bad_ora_location(self):
        """ Bad ORA location should return a 404 and error message """
        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, {'ora_location': 'not_a_real_location'})

        assert response.status_code == 404
        assert response.content.decode() == "Invalid ora_location."

    @patch('lms.djangoapps.ora_staff_grader.views.InitializeView.get_rubric_config')
    @patch('lms.djangoapps.ora_staff_grader.views.InitializeView.get_submissions')
    @patch('lms.djangoapps.ora_staff_grader.views.get_course_overview_or_none')
    def test_init(self, mock_get_course_overview, mock_get_submissions, mock_get_rubric_config):
        """ A successful call should return course, ORA, submissions, and rubric data """
        mock_course_overview = CourseOverviewFactory.create()
        mock_get_course_overview.return_value = mock_course_overview

        mock_get_submissions.return_value = {
            "a": {
                "submissionUuid": "a",
                "username": "foo",
                "teamName": "",
                "dateSubmitted": "1969-07-16 13:32:00",
                "dateGraded": "None",
                "gradedBy": "",
                "gradingStatus": "ungraded",
                "lockStatus": "unlocked",
                "score": {
                    "pointsEarned": 0,
                    "pointsPossible": 10
                }
            }
        }

        # Rubric data is passed through directly, so we can use a toy data payload
        mock_get_rubric_config.return_value = {"foo": "bar"}

        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, {'ora_location': self.ora_usage_key})

        expected_keys = set(['courseMetadata', 'oraMetadata', 'submissions', 'rubricConfig'])
        assert response.status_code == 200
        assert response.data.keys() == expected_keys
