"""
Special Exams Transformer
"""
from django.conf import settings

from openedx.core.djangoapps.content.block_structure.transformer import (
    BlockStructureTransformer,
    FilteringTransformerMixin,
)
from edx_proctoring.api import get_attempt_status_summary


class SpecialExamsTransformer(FilteringTransformerMixin, BlockStructureTransformer):
    """
    Adds information about special exams to course blocks data.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        return "special_exams"

    @classmethod
    def collect(cls, block_structure):
        block_structure.request_xblock_fields('is_proctored_enabled')
        block_structure.request_xblock_fields('is_practice_exam')
        block_structure.request_xblock_fields('is_timed_exam')

    def transform_block_filters(self, usage_info, block_structure):

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
                timed_exam_attempt_context = get_attempt_status_summary(
                    usage_info.user.id,
                    unicode(block_key.course_key),
                    unicode(block_key)
                )

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
            return False

        return [block_structure.create_removal_filter(add_special_exam_info)]

    @staticmethod
    def is_special_exam(block_key, block_structure):
        """
        Test whether the block is a special exam. These exams are always excluded
        from the student view.
        """
        return settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False) and (
            block_structure.get_xblock_field(block_key, 'is_proctored_enabled') or
            block_structure.get_xblock_field(block_key, 'is_practice_exam') or
            block_structure.get_xblock_field(block_key, 'is_timed_exam')
        )
