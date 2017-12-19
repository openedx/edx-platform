from django.contrib.auth import get_user_model
from rest_framework import serializers

from entitlements.models import CourseEntitlement


class CourseEntitlementSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=get_user_model().objects.all())

    class Meta:
        model = CourseEntitlement
        fields = (
            'user',
            'uuid',
            'course_uuid',
            'expired_at',
            'created',
            'modified',
            'mode',
            'order_number'
        )
