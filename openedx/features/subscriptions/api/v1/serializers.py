from rest_framework import serializers

from django.contrib.auth.models import User

from lms.djangoapps.support.serializers import CourseEnrollmentSerializer
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.features.subscriptions.models import UserSubscription


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for "UserSubscripion" model.
    """
    course_enrollments = CourseEnrollmentSerializer(many=True, required=False)

    class Meta:
        model = UserSubscription
        fields = [
            'subscription_id',
            'subscription_type',
            'description',
            'expiration_date',
            'course_enrollments',
            'max_allowed_courses',
            'user',
        ]

    def to_internal_value(self, data):
        """
        Deserializer username to user object.
        """
        data['site'] = get_current_site()
        username = data.get('user')
        try:
            data['user'] = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with username {} does not exist'.format(username))

        return data

    def to_representation(self, instance):
        """
        Serialize username instead of user id for compatibility with ecommerce.
        """
        data = super(UserSubscriptionSerializer, self).to_representation(instance)
        data['user'] = instance.user.username
        return data
