
from django.contrib.auth import get_user_model

from rest_framework import serializers

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from openedx.core.djangoapps.appsembler.api.helpers import as_course_key


class StringListField(serializers.ListField):
    child = serializers.CharField()


class CourseOverviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseOverview
        fields = (
            'id', 'display_name', 'org',
        )


class BulkEnrollmentSerializer(serializers.Serializer):
    identifiers = StringListField(allow_empty=False)
    courses = StringListField(allow_empty=False)
    action = serializers.ChoiceField(
        choices=(
            ('enroll', 'enroll'),
            ('unenroll', 'unenroll')
        ),
        required=True
    )
    auto_enroll = serializers.BooleanField(default=False)
    email_learners = serializers.BooleanField(default=False)

    def validate_courses(self, value):
        """
        Check that each course key in list is valid.

        Will raise `serializers.ValidationError` if any exceptions found in
        converting to a `CourseKey` instance
        """
        course_keys = value
        for course in course_keys:
            try:
                as_course_key(course)
            except:
                raise serializers.ValidationError("Course key not valid: {}".format(course))
        return value

    def validate_identifiers(self, value):

        if not isinstance(value, (list, tuple)):
            raise serializers.ValidationError(
                'identifiers must be a list, not a {}'.format(type(value)))
        # TODO: Do we want to enforce identifier type (like email, username)
        return value


class UserIndexSerializer(serializers.ModelSerializer):
    """Provides a limited set of user information for summary display
    """
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    fullname = serializers.CharField(
        source='profile.name', default=None, read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'fullname', 'email', 'date_joined',
        )
