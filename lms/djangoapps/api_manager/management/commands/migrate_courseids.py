"""
One-time data migration script -- shoulen't need to run it again
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.test import RequestFactory

from api_manager import models as api_models
from api_manager.courseware_access import get_course, get_course_child
from opaque_keys import InvalidKeyError
from projects import models as project_models


class Command(BaseCommand):
    """
    Migrates legacy course/content identifiers across several models to the new format
    """

    def handle(self, *args, **options):
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.user = User(email='migration@edx.org', username='migration', password='migration', is_active=True)

        projects = project_models.Project.objects.all()
        for project in projects:
            course_descriptor, course_key, course_content = get_course(request, request.user, project.course_id)
            project.course_id = unicode(course_key)
            try:
                project.content_id = course_key.make_usage_key_from_deprecated_string(project.content_id)
            except InvalidKeyError:
                pass  # If the key conversion fails it was either a new-style key or junk data
            project.save()

        workgroup_reviews = project_models.WorkgroupReview.objects.all()
        for wr in workgroup_reviews:
            course_id = wr.workgroup.project.course_id
            course_descriptor, course_key, course_content = get_course(request, request.user, course_id)
            try:
                wr.content_id = course_key.make_usage_key_from_deprecated_string(wr.content_id)
            except InvalidKeyError:
                pass  # If the key conversion fails it was either a new-style key or junk data
            wr.save()

        workgroup_submission_reviews = project_models.WorkgroupSubmissionReview.objects.all()
        for wsr in workgroup_submission_reviews:
            course_id = wsr.submission.workgroup.project.course_id
            course_descriptor, course_key, course_content = get_course(request, request.user, course_id)
            try:
                wsr.content_id = course_key.make_usage_key_from_deprecated_string(wsr.content_id)
            except InvalidKeyError:
                pass  # If the key conversion fails it was either a new-style key or junk data
            wsr.save()


        course_groups = api_models.CourseGroupRelationship.objects.all()
        for cg in course_groups:
            course_id = cg.course_id
            course_descriptor, course_key, course_content = get_course(request, request.user, course_id)
            cg.course_id = unicode(course_key)
            cg.save()

        course_content_groups = api_models.CourseContentGroupRelationship.objects.all()
        for ccg in course_content_groups:
            course_id = ccg.course_id
            course_descriptor, course_key, course_content = get_course(request, request.user, course_id)
            ccg.course_id = unicode(course_key)
            try:
                ccg.content_id = course_key.make_usage_key_from_deprecated_string(ccg.content_id)
            except InvalidKeyError:
                pass  # If the key conversion fails it was either a new-style key or junk data
            ccg.save()

        course_module_completions = api_models.CourseModuleCompletion.objects.all()
        for cmc in course_module_completions:
            course_id = cmc.course_id
            course_descriptor, course_key, course_content = get_course(request, request.user, course_id)
            cmc.course_id = unicode(course_key)
            try:
                cmc.content_id = course_key.make_usage_key_from_deprecated_string(cmc.content_id)
            except InvalidKeyError:
                pass  # If the key conversion fails it was either a new-style key or junk data
            cmc.save()
