"""
Test view handler for rerun (and eventually create)
"""
from django.test.client import RequestFactory
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.roles import CourseInstructorRole, CourseStaffRole
from student.tests.factories import UserFactory
from contentstore.tests.utils import AjaxEnabledTestClient, parse_json
from datetime import datetime
from xmodule.course_module import CourseFields


class TestCourseListing(ModuleStoreTestCase):
    """
    Unit tests for getting the list of courses for a logged in user
    """
    def setUp(self):
        """
        Add a user and a course
        """
        super(TestCourseListing, self).setUp()
        # create and log in a staff user.
        # create and log in a non-staff user
        self.user = UserFactory()
        self.factory = RequestFactory()
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.user.username, password='test')

        source_course = CourseFactory.create(
            org='origin',
            number='the_beginning',
            run='first',
            display_name='the one and only',
            start=datetime.utcnow()
        )
        self.source_course_key = source_course.id

        for role in [CourseInstructorRole, CourseStaffRole]:
            role(self.source_course_key).add_users(self.user)

    def tearDown(self):
        """
        Reverse the setup
        """
        self.client.logout()
        ModuleStoreTestCase.tearDown(self)

    def test_rerun(self):
        """
        Just testing the functionality the view handler adds over the tasks tested in test_clone_course
        """
        response = self.client.ajax_post('/course/', {
            'source_course_key': unicode(self.source_course_key),
            'org': self.source_course_key.org, 'course': self.source_course_key.course, 'run': 'copy',
            'display_name': 'not the same old name',
        })
        self.assertEqual(response.status_code, 200)
        data = parse_json(response)
        dest_course_key = CourseKey.from_string(data['destination_course_key'])

        self.assertEqual(dest_course_key.run, 'copy')
        dest_course = self.store.get_course(dest_course_key)
        self.assertEqual(dest_course.start, CourseFields.start.default)
