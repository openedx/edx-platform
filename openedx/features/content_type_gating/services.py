"""
Content Type Gating service.
"""

from lms.djangoapps.courseware.access import has_access
from openedx.features.content_type_gating.models import ContentTypeGatingConfig


class ContentTypeGatingService(object):
    """
    Content Type Gating uses Block Transformers to gate sections of the course outline
    and field overrides to gate course content.
    This service was created as a helper class for handling timed exams that contain content type gated problems.
    """
    def enabled_for_enrollment(self, **kwargs):
        """
        Returns whether content type gating is enabled for a given user/course pair
        """
        return ContentTypeGatingConfig.enabled_for_enrollment(**kwargs)

    def content_type_gate_for_block(self, user, block, course_id):
        """
        Returns a Fragment of the content type gate (if any) that would appear for a given block
        """
        problem_eligible_for_content_gating = (getattr(block, 'graded', False) and
                                               block.has_score and
                                               getattr(block, 'weight', 0) != 0)
        if problem_eligible_for_content_gating:
            access = has_access(user, 'load', block, course_id)
            if (not access and access.error_code == 'incorrect_user_group'):
                return access.user_fragment
            return None
