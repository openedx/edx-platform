"""
Test for forms helpers.
"""

from openedx.core.djangoapps.verified_track_content.forms import VerifiedTrackCourseForm
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


class TestVerifiedTrackCourseForm(SharedModuleStoreTestCase):
    """
    Test form validation.
    """

    FAKE_COURSE = 'edX/Test_Course/Run'
    BAD_COURSE_KEY = 'bad_course_key'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create()

    def test_form_validation_success(self):
        form_data = {
            'course_key': str(self.course.id), 'verified_cohort_name': 'Verified Learners', 'enabled': True
        }
        form = VerifiedTrackCourseForm(data=form_data)
        assert form.is_valid()

    def test_form_validation_failure(self):
        form_data = {'course_key': self.FAKE_COURSE, 'verified_cohort_name': 'Verified Learners', 'enabled': True}
        form = VerifiedTrackCourseForm(data=form_data)
        assert not form.is_valid()
        assert form.errors['course_key'] == ['COURSE NOT FOUND.  Please check that the course ID is valid.']

        form_data = {'course_key': self.BAD_COURSE_KEY, 'verified_cohort_name': 'Verified Learners', 'enabled': True}
        form = VerifiedTrackCourseForm(data=form_data)
        assert not form.is_valid()
        assert form.errors['course_key'] == ['COURSE NOT FOUND.  Please check that the course ID is valid.']
