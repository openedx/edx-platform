# pylint: disable=E1101
"""
Run these tests @ Devstack:
    paver test_system -s lms --test_id=lms/djangoapps/gradebook/tests.py
"""
from datetime import datetime
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.test.utils import override_settings
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, mixed_store_config

from util.signals import course_deleted
from projects import models

MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class ProjectsReceiversTests(ModuleStoreTestCase):
    """ Test suite for signal receivers """

    def setUp(self):
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
        project = models.Project.objects.create(
            course_id=unicode(self.course.id),
            content_id=unicode(self.chapter.location)
        )
        workgroup = models.Workgroup.objects.create(
            project=project,
            name='TEST WORKGROUP'
        )
        workgroup_user = models.WorkgroupUser.objects.create(
            workgroup=workgroup,
            user=self.user
        )
        workgroup_review = models.WorkgroupReview.objects.create(
            workgroup=workgroup,
            reviewer=self.user,
            question='test',
            answer='test',
            content_id=unicode(self.chapter.location),
        )
        workgroup_peer_review = models.WorkgroupPeerReview.objects.create(
            workgroup=workgroup,
            user=self.user,
            reviewer=self.user,
            question='test',
            answer='test',
            content_id=unicode(self.chapter.location),
        )
        workgroup_submission = models.WorkgroupSubmission.objects.create(
            workgroup=workgroup,
            user=self.user,
            document_id='test',
            document_url='test',
            document_mime_type='test',
        )
        workgroup_submission_review = models.WorkgroupSubmissionReview.objects.create(
            submission=workgroup_submission,
            reviewer=self.user,
            question='test',
            answer='test',
            content_id=unicode(self.chapter.location),
        )

        self.assertEqual(models.Project.objects.filter(id=project.id).count(), 1)
        self.assertEqual(models.Workgroup.objects.filter(id=workgroup.id).count(), 1)
        self.assertEqual(models.WorkgroupUser.objects.filter(id=workgroup_user.id).count(), 1)
        self.assertEqual(models.WorkgroupReview.objects.filter(id=workgroup_review.id).count(), 1)
        self.assertEqual(models.WorkgroupSubmission.objects.filter(id=workgroup_submission.id).count(), 1)
        self.assertEqual(models.WorkgroupSubmissionReview.objects.filter(id=workgroup_submission_review.id).count(), 1)
        self.assertEqual(models.WorkgroupPeerReview.objects.filter(id=workgroup_peer_review.id).count(), 1)

        # Run the data migration
        course_deleted.send(sender=None, course_key=self.course.id)

        # Validate that the course references were removed
        self.assertEqual(models.Project.objects.filter(id=project.id).count(), 0)
        self.assertEqual(models.Workgroup.objects.filter(id=workgroup.id).count(), 0)
        self.assertEqual(models.WorkgroupUser.objects.filter(id=workgroup_user.id).count(), 0)
        self.assertEqual(models.WorkgroupReview.objects.filter(id=workgroup_review.id).count(), 0)
        self.assertEqual(models.WorkgroupSubmission.objects.filter(id=workgroup_submission.id).count(), 0)
        self.assertEqual(models.WorkgroupSubmissionReview.objects.filter(id=workgroup_submission_review.id).count(), 0)
        self.assertEqual(models.WorkgroupPeerReview.objects.filter(id=workgroup_peer_review.id).count(), 0)
