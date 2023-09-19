"""
API Serializers for xblocks
"""
from rest_framework import serializers

class XblockSerializer(serializers.Serializer):
    """Serializer for xblocks"""
    id=serializers.CharField(required=False)
    parent_locator=serializers.CharField(required=False)
    display_name=serializers.CharField(required=False)
    category=serializers.CharField(required=False)
    data=serializers.CharField(required=False)
    metadata=serializers.DictField(required=False)
    has_changes=serializers.BooleanField(required=False)
    publish=serializers.CharField(required=False)   # this takes one of several string values
    children=serializers.ListField(required=False)
    fields=serializers.DictField(required=False)

    def to_internal_value(self, data):
        """
        raise validation error if there are any unexpected fields.
        """
        # Transform and validate the expected fields
        ret = super().to_internal_value(data)

        # Check for unexpected fields
        extra_fields = set(data.keys()) - set(self.fields.keys())
        if extra_fields:
            raise serializers.ValidationError(
                {field: ["This field is not expected."] for field in extra_fields}
            )

        return ret
