"""
API v1 serializers.
"""

from rest_framework import serializers

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest


class ApiAccessRequestSerializer(serializers.ModelSerializer):
    """
    ApiAccessRequest serializer.
    """
    class Meta:
        model = ApiAccessRequest
        fields = (
            'id', 'created', 'modified', 'user', 'status', 'website',
            'reason', 'company_name', 'company_address', 'site', 'contacted'
        )
