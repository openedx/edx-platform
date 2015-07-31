# pylint: disable=E1101
"""
Run these tests @ Devstack:
    paver test_system -s lms --test_id=lms/djangoapps/gradebook/tests.py
"""
from datetime import datetime
import uuid

from django.contrib.auth.models import Group, User
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from util.signals import course_deleted

from api_manager.models import GroupProfile, CourseGroupRelationship, CourseContentGroupRelationship


class ApiManagerReceiversTests(ModuleStoreTestCase):
    """ Test suite for signal receivers """

    def setUp(self):
        super(ApiManagerReceiversTests, self).setUp()
        # Create a course to work with
        self.course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2020, 1, 16)
        )
        test_data = '<html>{}</html>'.format(str(uuid.uuid4()))

        self.chapter = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        self.user = User.objects.create(email='testuser@edx.org', username='testuser', password='testpassword', is_active=True)

    def test_receiver_on_course_deleted(self):
        """
        Test the workflow
        """
        # Set up the data to be removed
        group = Group.objects.create(name='TestGroup')
        group_profile = GroupProfile.objects.create(group=group)

        CourseGroupRelationship.objects.create(
            course_id=unicode(self.course.id),
            group=group
        )
        CourseContentGroupRelationship.objects.create(
            course_id=unicode(self.course.id),
            content_id=unicode(self.chapter.location),
            group_profile=group_profile
        )

        self.assertEqual(CourseGroupRelationship.objects.filter(course_id=unicode(self.course.id)).count(), 1)
        self.assertEqual(CourseContentGroupRelationship.objects.filter(course_id=self.course.id, content_id=unicode(self.chapter.location)).count(), 1)

        # Emit the signal
        course_deleted.send(sender=None, course_key=self.course.id)

        # Validate that the course references were removed
        self.assertEqual(CourseGroupRelationship.objects.filter(course_id=unicode(self.course.id)).count(), 0)
        self.assertEqual(CourseContentGroupRelationship.objects.filter(course_id=self.course.id, content_id=unicode(self.chapter.location)).count(), 0)
