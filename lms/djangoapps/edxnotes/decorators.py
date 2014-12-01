"""
Decorators related to edXNotes.
"""
from django.conf import settings
from edxnotes.helpers import (
    get_endpoint,
    get_id_token,
    get_token_url,
    generate_uid,
    is_feature_enabled,
)
from edxmako.shortcuts import render_to_string


def edxnotes(cls):
    """
    Decorator that makes components annotatable.
    """
    original_get_html = cls.get_html

    def get_html(self, *args, **kwargs):
        """
        Returns raw html for the component.
        """
        is_studio = getattr(self.system, "is_author_mode", False)
        course = self.descriptor.runtime.modulestore.get_course(self.runtime.course_id)

        # Must be disabled in Studio or depends on the feature flag/advanced
        # settings of the course.
        if is_studio or not is_feature_enabled(course):
            return original_get_html(self, *args, **kwargs)
        else:
            return render_to_string("edxnotes_wrapper.html", {
                "content": original_get_html(self, *args, **kwargs),
                "uid": generate_uid(),
                "params": {
                    # Use camelCase to name keys.
                    "usageId": unicode(self.scope_ids.usage_id).encode("utf-8"),
                    "courseId": unicode(self.runtime.course_id).encode("utf-8"),
                    "token": get_id_token(self.runtime.get_real_user(self.runtime.anonymous_student_id)),
                    "tokenUrl": get_token_url(self.runtime.course_id),
                    "endpoint": get_endpoint(),
                    "debug": settings.DEBUG,
                },
            })

    cls.get_html = get_html
    return cls
