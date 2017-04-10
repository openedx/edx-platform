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
    Adds special exams (timed, proctored, practice proctored) to the student view.
    May exclude special exams.
    Excludes all blocks with unfulfilled milestones from the student view.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        return "milestones"

    def __init__(self, include_special_exams=True):
        self.include_special_exams = include_special_exams

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

        course_key = block_structure.root_block_usage_key.course_key
        user_can_skip = EntranceExamConfiguration.user_can_skip_entrance_exam(usage_info.user, course_key)
        required_content = milestones_helpers.get_required_content(course_key, usage_info.user)

        def user_gated_from_block(block_key):
            """
            Checks whether the user is gated from accessing this block, first via special exams,
            then via a general milestones check.
            """
            if usage_info.has_staff_access:
                return False
            elif self.has_pending_milestones_for_user(block_key, usage_info):
                return True
            elif self.gated_by_required_content(block_key, block_structure, user_can_skip, required_content):
                return True
            elif (settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False) and
                  (self.is_special_exam(block_key, block_structure) and
                   not self.include_special_exams)):
                return True
            return False

        for block_key in block_structure.topological_traversal():
            if user_gated_from_block(block_key):
                block_structure.remove_block(block_key, False)
            else:
                self.add_special_exam_info(block_key, block_structure, usage_info)

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

    def add_special_exam_info(self, block_key, block_structure, usage_info):
        """
        Adds special exam information to course blocks.
        """
        if self.is_special_exam(block_key, block_structure):

            # call into edx_proctoring subsystem to get relevant special exam information
            #
            # This will return None, if (user, course_id, content_id) is not applicable
            special_exam_attempt_context = None
            try:
                special_exam_attempt_context = get_attempt_status_summary(
                    usage_info.user.id,
                    unicode(block_key.course_key),
                    unicode(block_key)
                )
            except ProctoredExamNotFoundException as ex:
                log.exception(ex)

            if special_exam_attempt_context:
                # yes, user has proctoring context about
                # this level of the courseware
                # so add to the accordion data context
                block_structure.set_transformer_block_field(
                    block_key,
                    self,
                    'special_exam_info',
                    special_exam_attempt_context,
                )

    @staticmethod
    def gated_by_required_content(block_key, block_structure, user_can_skip, required_content):
        """
        Returns True if the current block associated with the block_key should be gated by the given required_content.
        Returns False otherwise.
        """
        if not required_content:
            return False
        exam_id = block_structure.get_xblock_field(block_structure.root_block_usage_key, 'entrance_exam_id')
        if user_can_skip:
            required_content = [content for content in required_content if not content == exam_id]

        if block_key.block_type == 'chapter' and unicode(block_key) not in required_content:
            return True

        return False
