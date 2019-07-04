from rest_framework import serializers

from lms.djangoapps.onboarding.models import PartnerNetwork


class PartnerNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerNetwork
        fields = ('label', 'code', 'affiliated_name', 'program_name')
