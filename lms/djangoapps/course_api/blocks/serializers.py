"""
Serializers for Course Blocks related return objects.
"""


import six
from django.conf import settings
from rest_framework import serializers
from rest_framework.reverse import reverse

from .transformers import SUPPORTED_FIELDS

# This lists the names of all fields that are allowed
# to be show to users who do not have access to a particular piece
# of content
FIELDS_ALLOWED_IN_AUTH_DENIED_CONTENT = [
    "display_name",
    "block_id",
    "student_view_url",
    "student_view_multi_device",
    "lms_web_url",
    "type",
    "id",
    "block_counts",
    "graded",
    "descendants",
    "authorization_denial_reason",
    "authorization_denial_message",
]


class BlockSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for single course block
    """
    def _get_field(self, block_key, transformer, field_name, default):
        """
        Get the field value requested.  The field may be an XBlock field, a
        transformer block field, or an entire tranformer block data dict.
        """
        value = None
        if transformer is None:
            value = self.context['block_structure'].get_xblock_field(block_key, field_name)
        elif field_name is None:
            try:
                value = self.context['block_structure'].get_transformer_block_data(block_key, transformer).fields
            except KeyError:
                pass
        else:
            value = self.context['block_structure'].get_transformer_block_field(block_key, transformer, field_name)

        return value if (value is not None) else default

    def to_representation(self, block_key):
        """
        Return a serializable representation of the requested block
        """
        # create response data dict for basic fields

        block_structure = self.context['block_structure']
        authorization_denial_reason = block_structure.get_xblock_field(block_key, 'authorization_denial_reason')
        authorization_denial_message = block_structure.get_xblock_field(block_key, 'authorization_denial_message')

        data = {
            'id': six.text_type(block_key),
            'block_id': six.text_type(block_key.block_id),
            'lms_web_url': reverse(
                'jump_to',
                kwargs={'course_id': six.text_type(block_key.course_key), 'location': six.text_type(block_key)},
                request=self.context['request'],
            ),
            'student_view_url': reverse(
                'render_xblock',
                kwargs={'usage_key_string': six.text_type(block_key)},
                request=self.context['request'],
            ),
        }

        if settings.FEATURES.get("ENABLE_LTI_PROVIDER") and 'lti_url' in self.context['requested_fields']:
            data['lti_url'] = reverse(
                'lti_provider_launch',
                kwargs={'course_id': six.text_type(block_key.course_key), 'usage_id': six.text_type(block_key)},
                request=self.context['request'],
            )

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
                    # only return fields that have data
                    data[supported_field.serializer_field_name] = field_value

        if 'children' in self.context['requested_fields']:
            children = block_structure.get_children(block_key)
            if children:
                data['children'] = [six.text_type(child) for child in children]

        if authorization_denial_reason and authorization_denial_message:
            data['authorization_denial_reason'] = authorization_denial_reason
            data['authorization_denial_message'] = authorization_denial_message
            cleaned_data = data.copy()
            for field in data.keys():  # pylint: disable=consider-iterating-dictionary
                if field not in FIELDS_ALLOWED_IN_AUTH_DENIED_CONTENT:
                    del cleaned_data[field]
            data = cleaned_data

        return data


class BlockDictSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer that formats a BlockStructure object to a dictionary, rather
    than a list, of blocks
    """
    root = serializers.CharField(source='root_block_usage_key')
    blocks = serializers.SerializerMethodField()

    def get_blocks(self, structure):
        """
        Serialize to a dictionary of blocks keyed by the block's usage_key.
        """
        return {
            six.text_type(block_key): BlockSerializer(block_key, context=self.context).data
            for block_key in structure
        }
