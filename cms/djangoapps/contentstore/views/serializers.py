"""
Serializers for the contentstore.views module.

This module contains DRF serializers for various features such as certificates, blocks, and others.
Add new serializers here as needed for API endpoints in this module.
"""

from rest_framework import serializers


class CertificateActivationSerializer(serializers.Serializer):
    """
    Serializer for activating or deactivating course certificates.
    """
    # This field indicates whether the certificate should be activated or deactivated.
    is_active = serializers.BooleanField(required=False, default=False)
