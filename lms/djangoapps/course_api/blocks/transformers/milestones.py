"""
Milestones Transformer
"""

from django.conf import settings

from openedx.core.lib.block_structure.transformer import BlockStructureTransformer, FilteringTransformerMixin
from util import milestones_helpers


class MilestonesTransformer(FilteringTransformerMixin, BlockStructureTransformer):
    """
    Excludes all special exams (timed, proctored, practice proctored) from the student view.
    Excludes all blocks with unfulfilled milestones from the student view.
    """
    VERSION = 1

    @classmethod
    def name(cls):
        return "milestones"

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

    def transform_block_filters(self, usage_info, block_structure):
        if usage_info.has_staff_access:
            return [block_structure.create_universal_filter()]

        def user_gated_from_block(block_key):
            """
            Checks whether the user is gated from accessing this block, first via special exams,
            then via a general milestones check.
            """
            return (
                settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False) and
                self.is_special_exam(block_key, block_structure)
            ) or self.has_pending_milestones_for_user(block_key, usage_info)

        return [block_structure.create_removal_filter(user_gated_from_block)]

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
