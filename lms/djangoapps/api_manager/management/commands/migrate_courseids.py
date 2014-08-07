"""
One-time data migration script -- shoulen't need to run it again
"""
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.test import RequestFactory

from api_manager import models as api_models
from api_manager.courseware_access import get_course, get_course_child
from opaque_keys import InvalidKeyError

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Migrates legacy course/content identifiers across several models to the new format
    """

    def handle(self, *args, **options):
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.user = User(email='migration@edx.org', username='migration', password='migration', is_active=True)

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
                log.warning(
                    'Unable to convert content_id "{}"'.format(ccg.content_id),
                    exc_info=True
                )
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
                log.warning(
                    'Unable to convert content_id "{}"'.format(cmc.content_id),
                    exc_info=True
                )
                pass  # If the key conversion fails it was either a new-style key or junk data
            cmc.save()
