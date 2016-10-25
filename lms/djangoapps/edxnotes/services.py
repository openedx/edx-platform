"""
edxnotes service.
"""
from importlib import import_module
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from request_cache.middleware import RequestCache

# from helpers import (
#     get_edxnotes_id_token,
#     get_public_endpoint,
#     get_token_url,
#     is_feature_enabled
# )

log = logging.getLogger(__name__)

CACHE_KEY_TEMPLATE = u"edxnotes.params.{}.{}"


class EdxNotesService(object):
    """
    A service that provides access to the edxnotes utils methods.
    """

    def __init__(self, **kwargs):
        super(EdxNotesService, self).__init__(**kwargs)
        self.helpers = import_module('lms.djangoapps.edxnotes.helpers')

    def is_feature_enabled(self, course):
        return self.helpers.is_feature_enabled(course)

    def params(self, runtime):
        course = runtime.modulestore.get_course(runtime.course_id)
        if self.is_feature_enabled(course):
            return {
                "isVisible": course.edxnotes_visibility,
                "courseId": unicode(runtime.course_id).encode("utf-8"),
                'user': runtime.anonymous_student_id,
                "token": self.helpers.get_edxnotes_id_token(runtime.get_real_user(runtime.anonymous_student_id)),
                "tokenUrl": self.helpers.get_token_url(runtime.course_id),
                "endpoint": self.helpers.get_public_endpoint(),
                "debug": settings.DEBUG,
                "eventStringLimit": settings.TRACK_MAX_EVENT / 6,
            }
        else:
            return {}
