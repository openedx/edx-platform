from rest_framework import serializers

from django.contrib.auth.models import User

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

    def to_internal_value(self, data):
        """
        Deserializer username to user object.
        """
        username = data.get('user')
        try:
            data['user'] = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with username {} does not exist'.format(username))

        return super(UserSubscriptionSerializer, self).to_internal_value(data)
