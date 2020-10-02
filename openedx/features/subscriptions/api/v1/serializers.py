from rest_framework import serializers

from openedx.features.subscriptions.models import UserSubscription
from enrollment.serializers import CourseEnrollmentSerializer


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for "UserSubscripion" model.
    """
    course_enrollments = CourseEnrollmentSerializer(many=True, required=False)

    class Meta:
        model = UserSubscription
        fields = ['subscription_id', 'subscription_type', 'expiration_date', 'course_enrollments', 'max_allowed_courses', 'user']
