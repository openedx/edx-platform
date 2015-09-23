"""
Serializers for Course Blocks related return objects.
"""
from rest_framework import serializers
from rest_framework.reverse import reverse

from transformers import SUPPORTED_FIELDS


# TODO support depth parameter (MA-1366)
class BlockSerializer(serializers.Serializer):
    """
    Serializer for single course block
    """
    def _get_field(self, block_key, transformer, field_name, default):
        if transformer:
            value = self.context['block_structure'].get_transformer_block_data(block_key, transformer, field_name)
        else:
            value = self.context['block_structure'].get_xblock_field(block_key, field_name)

        # TODO should we return falsey values in the response?
        # for example, if student_view_multi_device is false, just don't specify it?
        return value if (value is not None) else default

    def to_native(self, block_key):
        # create response data dict for basic fields
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

        # add additional requested fields that are supported by the various transformers
        for supported_field in SUPPORTED_FIELDS:
            if supported_field.requested_field_name in self.context['requested_fields']:
                field_value = self._get_field(
                    block_key,
                    supported_field.transformer,
                    supported_field.block_field_name,
                    supported_field.default_value,
                )
                if field_value is not None:
                    data[supported_field.requested_field_name] = field_value

        if 'children' in self.context['requested_fields']:
            children = self.context['block_structure'].get_children(block_key)
            if children:
                data['children'] = [unicode(child) for child in children]

        return data


class BlockDictSerializer(serializers.Serializer):
    """
    Serializer that formats to a dictionary, rather than a list, of blocks
    """
    root = serializers.CharField(source='root_block_key')
    blocks = serializers.SerializerMethodField('get_blocks')

    def get_blocks(self, structure):
        """
        Serialize to a dictionary of blocks keyed by the block's usage_key.
        """
        return {
            unicode(block_key): BlockSerializer(block_key, context=self.context).data
            for block_key in structure
        }
