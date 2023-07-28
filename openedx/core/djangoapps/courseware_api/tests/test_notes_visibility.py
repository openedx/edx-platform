from unittest.mock import Mock  # lint-amnesty, pylint: disable=wrong-import-order
from lms.djangoapps.courseware.tests.factories import StudentInfoFactory
from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


class NotesVisibilityTestCase(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Unit test for courseware notes visibility
    """

    def setUp(self):
        super().setUp()

        self.setup_user()
        self.request = Mock()
        self.request.user = self.user
        self.course = CourseFactory.create(metadata={'edxnotes': True})
        self.enroll(self.course)

    def test_notes_disabled_on_user_preferece(self):
        StudentInfoFactory.create(field_name='edxnotes_visibility', value=False, student=self.user)
        response = self.client.get(f'/api/courseware/course/{self.course.id}')

        assert response.status_code == 200
        assert response.json()["notes"]["enabled"]
        assert not response.json()["notes"]["visible"]

    def test_notes_enabled_on_user_preferece(self):
        StudentInfoFactory.create(field_name='edxnotes_visibility', value=True, student=self.user)
        response = self.client.get(f'/api/courseware/course/{self.course.id}')

        assert response.status_code == 200
        assert response.json()["notes"]["enabled"]
        assert response.json()["notes"]["visible"]
