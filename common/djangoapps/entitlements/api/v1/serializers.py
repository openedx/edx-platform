from django.contrib.auth import get_user_model
from rest_framework import serializers

from entitlements.models import CourseEntitlement


class CourseEntitlementSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=get_user_model().objects.all())
    enrollment_course_run = serializers.CharField(
        source='enrollment_course_run.course_id',
        read_only=True
    )

    class Meta:
        model = CourseEntitlement
        fields = (
            'user',
            'uuid',
            'course_uuid',
            'enrollment_course_run',
            'expired_at',
            'created',
            'modified',
            'mode',
            'order_number'
        )
