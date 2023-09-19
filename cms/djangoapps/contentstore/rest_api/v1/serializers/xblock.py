"""
API Serializers for xblocks
"""

from rest_framework import serializers

# TODO: add all necessary fields and use this serializer in
# cms/djangoapps/contentstore/rest_api/v1/views/xblock.py
class XblockSerializer(serializers.Serializer):
    """Serializer for xblocks"""
    id=serializers.CharField(required=False)
    display_name=serializers.CharField(required=False)
    category=serializers.CharField(required=False)
    data=serializers.CharField(required=False)
    metadata=serializers.DictField(required=False)
