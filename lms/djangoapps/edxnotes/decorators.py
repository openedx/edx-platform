"""
Decorators related to edXNotes.
"""

import json
from uuid import uuid4

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
        is_feature_enabled = self.runtime.service(self, 'edxnotes').is_feature_enabled(course)

        # Must be disabled:
        # - in Studio;
        # - when Harvard Annotation Tool is enabled for the course;
        # - when the feature flag or `edxnotes` setting of the course is set to False.
        if is_studio or not is_feature_enabled:
            return original_get_html(self, *args, **kwargs)
        else:
            return render_to_string("edxnotes_wrapper.html", {
                "content": original_get_html(self, *args, **kwargs),
                "uid": uuid4().int,
                "usage_id": unicode(self.scope_ids.usage_id).encode("utf-8"),
            })

    cls.get_html = get_html
    return cls
