"""
Proctored Exams Transformer
"""

from django.conf import settings

from edx_proctoring.api import get_attempt_status_summary
from edx_proctoring.models import ProctoredExamStudentAttemptStatus
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class ProctoredExamTransformer(BlockStructureTransformer):
    """
    Proctored Exam Transformer Class
    """
    VERSION = 1
    BLOCK_HAS_PROCTORED_EXAM = 'has_proctored_exam'

    @classmethod
    def collect(cls, block_structure):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformer's transform method.

        Arguments:
            block_structure (BlockStructureXBlockData)
        """
        block_structure.request_xblock_fields('is_proctored_enabled')
        block_structure.request_xblock_fields('is_practice_exam')

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure based on the given user_info.
        """
        if not settings.FEATURES.get('ENABLE_PROCTORED_EXAMS', False):
            return

        def is_proctored_exam_for_user(block_key):
            if (
                block_key.block_type == 'sequential' and (
                    block_structure.get_xblock_field(block_key, 'is_proctored_enabled') or
                    block_structure.get_xblock_field(block_key, 'is_practice_exam')
                )
            ):
                # This section is an exam.  It should be excluded unless the
                # user is not a verified student or has declined taking the exam.
                user_exam_summary = get_attempt_status_summary(
                    user_info.user.id,
                    unicode(block_key.course_key),
                    unicode(block_key),
                )
                return user_exam_summary and user_exam_summary['status'] != ProctoredExamStudentAttemptStatus.declined

        block_structure.remove_block_if(is_proctored_exam_for_user)
