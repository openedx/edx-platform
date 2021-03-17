"""
Extra Fields Transformer
"""
from django.conf import settings

from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer


class ExtraFieldsTransformer(BlockStructureTransformer):
    """
    A configurable transformer that adds additional XBlock fields to the course blocks API.

    Extra fields must be specified using the "COURSE_BLOCKS_API_EXTRA_FIELDS"
    LMS Django settings variable. Open edX instances can use this to make
    additional XBlock fields available via the course blocks API, that aren't
    otherwise included by default.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        return "blocks_api:extra_fields"

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this transformer's
        transform method.
        """
        requested_field_names = cls.get_requested_extra_fields()

        block_structure.request_xblock_fields('category', *requested_field_names)

    @classmethod
    def get_requested_extra_fields(cls):
        """
        Returns the names of the requested extra fields
        """
        try:
            return [field_name for block_type, field_name in settings.COURSE_BLOCKS_API_EXTRA_FIELDS]
        except AttributeError:
            return []

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure based on the given usage_info.
        """
        if len(self.get_requested_extra_fields()) == 0:
            return

        for block_key in block_structure.topological_traversal():
            for requested_block_type, requested_field_name in settings.COURSE_BLOCKS_API_EXTRA_FIELDS:
                block_type = block_structure.get_xblock_field(block_key, 'category')
                if (requested_block_type == '*' or
                        block_type in requested_block_type.split(',')):
                    requested_field_data = block_structure.get_xblock_field(
                        block_key,
                        requested_field_name,
                        None
                    )

                    if requested_field_data is not None:
                        block_structure.set_transformer_block_field(
                            block_key,
                            self,
                            requested_field_name,
                            requested_field_data
                        )
