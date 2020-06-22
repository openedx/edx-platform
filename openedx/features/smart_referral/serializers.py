from rest_framework import serializers

from .models import SmartReferral


class SmartReferralSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SmartReferral
        fields = '__all__'
