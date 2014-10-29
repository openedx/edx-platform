"""
Decorators related to edXNotes.
"""
from edxnotes.api import (
    get_prefix,
    get_token_url,
    get_user_id,
    generate_uid,
    generate_token,
    get_usage_id,
    get_course_id,
)
from edxmako.shortcuts import render_to_string


def edxnotes(cls):
    """
    Decorator that makes components annotatable.
    """
    original_get_html = cls.get_html

    def get_html(self, *args, **kargs):
        # edXNotes should be enabled in Studio, that's why just return
        # original method.
        if getattr(self.system, 'is_author_mode', False):
            return original_get_html(self, *args, **kargs)
        else:
            return render_to_string('edxnotes_wrapper.html', {
                'content': original_get_html(self, *args, **kargs),
                'uid': generate_uid(),
                'params': {
                    # Use camelCase to name keys.
                    'usageId': get_usage_id(),
                    'courseId': get_course_id(),
                    'token': generate_token(),
                    'prefix': get_prefix(),
                    'tokenUrl': get_token_url(),
                    'user': get_user_id(),
                },
            })

    cls.get_html = get_html
    return cls
