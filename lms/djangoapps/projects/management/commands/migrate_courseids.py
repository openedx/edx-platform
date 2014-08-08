"""
One-time data migration script -- shoulen't need to run it again
"""
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.test import RequestFactory

from api_manager.courseware_access import get_course, get_course_child
from opaque_keys import InvalidKeyError
from project.models import Project, WorkgroupReview, WorkgroupSubmissionReview

log = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Migrates legacy course/content identifiers across several models to the new format
    """

    def handle(self, *args, **options):
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.user = User(email='migration@edx.org', username='migration', password='migration', is_active=True)

        projects = Project.objects.all()
        for project in projects:
            course_descriptor, course_key, course_content = get_course(request, request.user, project.course_id)
            project.course_id = unicode(course_key)
            try:
                project.content_id = course_key.make_usage_key_from_deprecated_string(project.content_id)
            except InvalidKeyError:
                log.warning(
                    'Unable to convert content_id "{}"'.format(project.content_id),
                    exc_info=True
                )
                pass  # If the key conversion fails it was either a new-style key or junk data
            project.save()

        workgroup_reviews = WorkgroupReview.objects.all()
        for wr in workgroup_reviews:
            course_id = wr.workgroup.project.course_id
            course_descriptor, course_key, course_content = get_course(request, request.user, course_id)
            try:
                wr.content_id = course_key.make_usage_key_from_deprecated_string(wr.content_id)
            except InvalidKeyError:
                log.warning(
                    'Unable to convert content_id "{}"'.format(wr.content_id),
                    exc_info=True
                )
                pass  # If the key conversion fails it was either a new-style key or junk data
            wr.save()

        workgroup_submission_reviews = WorkgroupSubmissionReview.objects.all()
        for wsr in workgroup_submission_reviews:
            course_id = wsr.submission.workgroup.project.course_id
            course_descriptor, course_key, course_content = get_course(request, request.user, course_id)
            try:
                wsr.content_id = course_key.make_usage_key_from_deprecated_string(wsr.content_id)
            except InvalidKeyError:
                log.warning(
                    'Unable to convert content_id "{}"'.format(wsr.content_id),
                    exc_info=True
                )
                pass  # If the key conversion fails it was either a new-style key or junk data
            wsr.save()
