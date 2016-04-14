""" Django REST Framework Serializers """

from rest_framework import serializers

from api_manager.models import APIUser, GroupProfile
from organizations.serializers import BasicOrganizationSerializer
from student.models import UserProfile


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        fields = self.context['request'].QUERY_PARAMS.get('fields', None) if 'request' in self.context else None
        if fields:
            fields = fields.split(',')
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class GroupProfileSerializer(serializers.ModelSerializer):
    """ Serializer for GroupProfile model interactions """

    class Meta(object):
        """ Serializer/field specification """
        model = GroupProfile
        fields = ('id', 'name', )


class UserSerializer(DynamicFieldsModelSerializer):

    """ Serializer for User model interactions """
    organizations = BasicOrganizationSerializer(many=True, required=False)
    created = serializers.DateTimeField(source='date_joined', required=False)
    avatar_url = serializers.CharField(source='profile.avatar_url')
    city = serializers.CharField(source='profile.city')
    title = serializers.CharField(source='profile.title')
    country = serializers.CharField(source='profile.country')
    full_name = serializers.CharField(source='profile.name')
    courses_enrolled = serializers.SerializerMethodField('get_courses_enrolled')
    roles = serializers.SerializerMethodField('get_permission_group_type_roles')

    def get_courses_enrolled(self, user):
        """ Serialize user enrolled courses """
        if hasattr(user, 'courses_enrolled'):
            return user.courses_enrolled

        return user.courseenrollment_set.count

    def get_permission_group_type_roles(self, user):
        """ Serialize GroupProfile for permission group type """
        queryset = GroupProfile.objects.filter(group__user=user, group_type='permission')
        serializer = GroupProfileSerializer(queryset, many=True)

        return serializer.data

    class Meta(object):
        """ Serializer/field specification """
        model = APIUser
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "created",
            "is_active",
            "organizations",
            "avatar_url",
            "city",
            "title",
            "country",
            "full_name",
            "is_staff",
            "last_login",
            "courses_enrolled",
            "roles"
        )
        read_only_fields = ("id", "email", "username")


class SimpleUserSerializer(DynamicFieldsModelSerializer):
    created = serializers.DateTimeField(source='date_joined', required=False)

    class Meta:
        """ Serializer/field specification """
        model = APIUser
        fields = ("id", "email", "username", "first_name", "last_name", "created", "is_active")
        read_only_fields = ("id", "email", "username")


class UserCountByCitySerializer(serializers.Serializer):
    """ Serializer for user count by city """
    city = serializers.CharField(source='profile__city')
    count = serializers.IntegerField()


class UserRolesSerializer(serializers.Serializer):
    """ Serializer for user roles """
    course_id = serializers.CharField(source='course_id')
    role = serializers.CharField(source='role')
