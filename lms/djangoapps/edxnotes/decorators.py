"""
Decorators related to edXNotes.
"""


import json

import six
from django.conf import settings

from common.djangoapps.edxmako.shortcuts import render_to_string


def edxnotes(cls):
    """
    Decorator that makes components annotatable.
    """
    original_get_html = cls.get_html

    def get_html(self, *args, **kwargs):
        """
        Returns raw html for the component.
        """
        # Import is placed here to avoid model import at project startup.
        from .helpers import (
            generate_uid, get_edxnotes_id_token, get_public_endpoint, get_token_url, is_feature_enabled
        )

        runtime = getattr(self, 'descriptor', self).runtime
        if not hasattr(runtime, 'modulestore'):
            return original_get_html(self, *args, **kwargs)

        is_studio = getattr(self.system, "is_author_mode", False)
        course = getattr(self, 'descriptor', self).runtime.modulestore.get_course(self.runtime.course_id)

        # Must be disabled when:
        # - in Studio
        # - Harvard Annotation Tool is enabled for the course
        # - the feature flag or `edxnotes` setting of the course is set to False
        # - the user is not authenticated
        user = self.runtime.get_real_user(self.runtime.anonymous_student_id)

        if is_studio or not is_feature_enabled(course, user):
            return original_get_html(self, *args, **kwargs)
        else:
            return render_to_string("edxnotes_wrapper.html", {
                "content": original_get_html(self, *args, **kwargs),
                "uid": generate_uid(),
                "edxnotes_visibility": json.dumps(
                    getattr(self, 'edxnotes_visibility', course.edxnotes_visibility)
                ),
                "params": {
                    # Use camelCase to name keys.
                    "usageId": six.text_type(self.scope_ids.usage_id),
                    "courseId": six.text_type(self.runtime.course_id),
                    "token": get_edxnotes_id_token(user),
                    "tokenUrl": get_token_url(self.runtime.course_id),
                    "endpoint": get_public_endpoint(),
                    "debug": settings.DEBUG,
                    "eventStringLimit": settings.TRACK_MAX_EVENT / 6,
                },
            })

    cls.get_html = get_html
    return cls
