"""
Tests for the course completion helper functions.
"""
from datetime import datetime
from uuid import uuid4

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.badges.events import course_complete
from lms.djangoapps.certificates.models import GeneratedCertificate
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


class CourseCompleteTestCase(ModuleStoreTestCase):
    """
    Tests for the course completion helper functions.
    """

    def setUp(self):
        super().setUp()
        # Need key to be deterministic to test slugs.
        self.course = CourseFactory.create(
            org='edX', course='course_test', run='test_run', display_name='Badged',
            start=datetime(year=2015, month=5, day=19),
            end=datetime(year=2015, month=5, day=20)
        )
        self.course_key = self.course.location.course_key

    def test_slug(self):
        """
        Verify slug generation is working as expected. If this test fails, the algorithm has changed, and it will cause
        the handler to lose track of all badges it made in the past.
        """
        assert course_complete.course_slug(self.course_key, 'honor') ==\
               'course-v1edxcourse_testtest_run_honor_2055051'
        assert course_complete.course_slug(self.course_key, 'verified') ==\
               'course-v1edxcourse_testtest_run_verified_d550ad7'

    def test_dated_description(self):
        """
        Verify that a course with start/end dates contains a description with them.
        """
        assert course_complete.badge_description(self.course, 'honor') ==\
               'Completed the course "Badged" (honor, 2015-05-19 - 2015-05-20)'

    def test_self_paced_description(self):
        """
        Verify that a badge created for a course with no end date gets a different description.
        """
        self.course.end = None
        assert course_complete.badge_description(self.course, 'honor') == 'Completed the course "Badged" (honor)'

    def test_evidence_url(self):
        """
        Make sure the evidence URL points to the right place.
        """
        user = UserFactory.create()
        cert = GeneratedCertificate.eligible_certificates.create(
            user=user,
            course_id=self.course_key,
            download_uuid=uuid4(),
            grade="0.95",
            key='the_key',
            distinction=True,
            status='downloadable',
            mode='honor',
            name=user.profile.name,
            verify_uuid=uuid4().hex
        )
        assert f'https://edx.org/certificates/{cert.verify_uuid}?evidence_visit=1' ==\
               course_complete.evidence_url(user.id, self.course_key)
