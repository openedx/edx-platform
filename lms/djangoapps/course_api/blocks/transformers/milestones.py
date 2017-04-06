"""
Milestones Transformer
"""

import logging
from django.conf import settings

from openedx.core.djangoapps.content.block_structure.transformer import (
    BlockStructureTransformer,
    FilteringTransformerMixin,
)
from edx_proctoring.exceptions import ProctoredExamNotFoundException
from edx_proctoring.api import get_attempt_status_summary
from student.models import EntranceExamConfiguration
from util import milestones_helpers

log = logging.getLogger(__name__)


class MilestonesTransformer(BlockStructureTransformer):
    """
    Excludes all special exams (timed, proctored, practice proctored) from the student view.
    Excludes all blocks with unfulfilled milestones from the student view.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        return "milestones"

    def __init__(self, can_view_special_exams=True):
        self.can_view_special_exams = can_view_special_exams

    @classmethod
    def collect(cls, block_structure):
        """
        Computes any information for each XBlock that's necessary to execute
        this transformer's transform method.

        Arguments:
            block_structure (BlockStructureCollectedData)
        """
        block_structure.request_xblock_fields('is_proctored_enabled')
        block_structure.request_xblock_fields('is_practice_exam')
        block_structure.request_xblock_fields('is_timed_exam')
        block_structure.request_xblock_fields('entrance_exam_id')

    def transform(self, usage_info, block_structure):
        """
        Modify block structure according to the behavior of milestones and special exams.
        """

        def add_special_exam_info(block_key):
            """
            Adds special exam information to course blocks.
            """
            if self.is_special_exam(block_key, block_structure):

                #
                # call into edx_proctoring subsystem
                # to get relevant proctoring information regarding this
                # level of the courseware
                #
                # This will return None, if (user, course_id, content_id)
                # is not applicable
                #
                timed_exam_attempt_context = None
                try:
                    timed_exam_attempt_context = get_attempt_status_summary(
                        usage_info.user.id,
                        unicode(block_key.course_key),
                        unicode(block_key)
                    )
                except ProctoredExamNotFoundException as ex:
                    log.exception(ex)

                if timed_exam_attempt_context:
                    # yes, user has proctoring context about
                    # this level of the courseware
                    # so add to the accordion data context
                    block_structure.set_transformer_block_field(
                        block_key,
                        self,
                        'special_exam',
                        timed_exam_attempt_context,
                    )

        course_key = block_structure.root_block_usage_key.course_key
        user_can_skip = EntranceExamConfiguration.user_can_skip_entrance_exam(usage_info.user, course_key)
        exam_id = block_structure.get_xblock_field(course_key, 'entrance_exam_id')

        def user_gated_from_block(block_key):
            """
            Checks whether the user is gated from accessing this block, first via special exams,
            then via a general milestones check.
            """
            if usage_info.has_staff_access:
                return False
            elif user_can_skip and block_key == exam_id:
                return False
            elif self.has_pending_milestones_for_user(block_key, usage_info):
                return True
            elif (settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False) and
                  (self.is_special_exam(block_key, block_structure) and
                   not self.can_view_special_exams)):
                return True
            return False

        for block_key in block_structure.topological_traversal():
            if user_gated_from_block(block_key):
                block_structure.remove_block(block_key, False)
            else:
                add_special_exam_info(block_key)

    @staticmethod
    def is_special_exam(block_key, block_structure):
        """
        Test whether the block is a special exam. These exams are always excluded
        from the student view.
        """
        return (
            block_structure.get_xblock_field(block_key, 'is_proctored_enabled') or
            block_structure.get_xblock_field(block_key, 'is_practice_exam') or
            block_structure.get_xblock_field(block_key, 'is_timed_exam')
        )

    @staticmethod
    def has_pending_milestones_for_user(block_key, usage_info):
        """
        Test whether the current user has any unfulfilled milestones preventing
        them from accessing this block.
        """
        return bool(milestones_helpers.get_course_content_milestones(
            unicode(block_key.course_key),
            unicode(block_key),
            'requires',
            usage_info.user.id
        ))
