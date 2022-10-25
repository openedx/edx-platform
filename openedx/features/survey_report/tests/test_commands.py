"""
Test for survey report commands.
"""

import logging

from datetime import datetime, timedelta
from unittest.mock import patch
from opaque_keys.edx.keys import CourseKey
from openedx.features.survey_report.queries import get_unique_courses_offered

from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


log = logging.getLogger(__name__)

class TestSurveyReportCommands(ModuleStoreTestCase):

    # def setUp(self):
    #     super().setUp()
        # self.user = UserFactory.create(username='test_user', email='test@example.com', password='password')
        # self.user1 = UserFactory.create(username='test_user1', email='test1@example.com', password='password')
        # self.user2 = UserFactory.create(username='test_user2', email='test2@example.com', password='password')
        # self.user3 = UserFactory.create(username='test_user3', email='test3@example.com', password='password')
        # self.user4 = UserFactory.create(username='test_user4', email='test4@example.com', password='password')

    def setUp(self):
        """
        We set up some content here, without publish signals enabled.
        """
        super().setUp()
        self.store = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)  # lint-amnesty, pylint: disable=protected-access
        self.first_course = CourseFactory.create(
            org="test", course="course1", display_name="run1", default_store=ModuleStoreEnum.Type.mongo
        )
        self.second_course = CourseFactory.create(
            org="test", course="course2", display_name="run2", default_store=ModuleStoreEnum.Type.mongo
        )

    def test_get_unique_courses_offered(self):
        """
        Test that get_unique_courses_offered returns the correct number of courses.
        """
        # course_overview = CourseOverviewFactory.create(id=self.course.id)
        # CourseEnrollmentFactory.create(user=self.user, course_id=course_overview.id)
        # with patch('openedx.features.survey_report.queries.datetime') as mock_datetime:
        #     mock_datetime.now.return_value = datetime.now()
        #     mock_datetime.now.return_value = mock_datetime.now.return_value - timedelta(days=1)
        log.critical(get_unique_courses_offered())
        #     assert get_unique_courses_offered() == 2
