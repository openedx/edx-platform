"""
Serializers for all Course Blocks related return objects.
"""
from rest_framework import serializers
from rest_framework.reverse import reverse

from transformers import SUPPORTED_FIELDS


class BlockSerializer(serializers.Serializer):
    """
    TODO
    """
    def _get_field(self, block_key, transformer, field_name):
        if transformer:
            return self.context['block_structure'].get_transformer_block_data(block_key, transformer, field_name)
        else:
            return self.context['block_structure'].get_xblock_field(block_key, field_name)

    def to_native(self, block_key):

        data = {
            'id': unicode(block_key),
            'lms_web_url': reverse(
                'jump_to',
                kwargs={'course_id': unicode(block_key.course_key), 'location': unicode(block_key)},
                request=self.context['request'],
            ),
            'student_view_url': reverse(
                'courseware.views.render_xblock',
                kwargs={'usage_key_string': unicode(block_key)},
                request=self.context['request'],
            ),
        }

        for supported_field in SUPPORTED_FIELDS:
            if supported_field.requested_field_name in self.context['requested_fields']:
                data[supported_field.requested_field_name] = self._get_field(
                    block_key,
                    supported_field.transformer,
                    supported_field.block_field_name,
                )

        return data
