""" Django REST Framework Serializers """
import json

from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

from api_manager.models import APIUser
from organizations.serializers import BasicOrganizationSerializer
from student.roles import CourseAccessRole
from gradebook.models import StudentGradebook


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if 'request' in self.context:
            fields = self.context['request'].QUERY_PARAMS.get('fields', None)
            if not fields and 'default_fields' in self.context:
                additional_fields = self.context['request'].QUERY_PARAMS.get('additional_fields', "")
                fields = ','.join([self.context['default_fields'], additional_fields])
            if fields:
                fields = fields.split(',')
                # Drop any fields that are not specified in the `fields` argument.
                allowed = set(fields)
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)


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
    roles = serializers.SerializerMethodField('get_user_roles')
    grades = serializers.SerializerMethodField('get_user_grades')

    def get_courses_enrolled(self, user):
        """ Serialize user enrolled courses """
        if hasattr(user, 'courses_enrolled'):
            return user.courses_enrolled

        return user.courseenrollment_set.count

    def get_user_roles(self, user):
        """ returns list of user roles """
        queryset = CourseAccessRole.objects.filter(user=user)
        if 'course_id' in self.context:
            course_id = self.context['course_id']
            queryset = queryset.filter(course_id=course_id)

        return queryset.values_list('role', flat=True).distinct()

    def get_user_grades(self, user):
        """ returns user proforma_grade, grade and grade_summary """
        grade, proforma_grade, section_breakdown = None, None, None
        if 'course_id' in self.context:
            course_id = self.context['course_id']
            try:
                gradebook = StudentGradebook.objects.get(user=user, course_id=course_id)
                grade = gradebook.grade
                proforma_grade = gradebook.proforma_grade
                section_breakdown = json.loads(gradebook.grade_summary)["section_breakdown"]
            except ObjectDoesNotExist:
                pass

        return {'grade': grade, 'proforma_grade': proforma_grade, 'section_breakdown': section_breakdown}

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
            "avatar_url",
            "city",
            "title",
            "country",
            "full_name",
            "is_staff",
            "last_login",
            "courses_enrolled",
            "organizations",
            "roles",
            "grades",
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
