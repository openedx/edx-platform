import six
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import get_attribute

from cms.djangoapps.contentstore.views.course import create_new_course, get_course_and_check_access, rerun_course
from student.models import CourseAccessRole
from xmodule.modulestore.django import modulestore

User = get_user_model()


class CourseAccessRoleSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = CourseAccessRole
        fields = ('user', 'role',)


class CourseRunScheduleSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    enrollment_start = serializers.DateTimeField()
    enrollment_end = serializers.DateTimeField(allow_null=True)


class CourseRunTeamSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        return CourseAccessRoleSerializer(data=data, many=True).to_internal_value(data)

    def to_representation(self, instance):
        roles = CourseAccessRole.objects.filter(course_id=instance.id)
        return CourseAccessRoleSerializer(roles, many=True).data

    def get_attribute(self, instance):
        # Course instances have no "team" attribute. Return the course, and the consuming serializer will
        # handle the rest.
        return instance


class CourseRunTeamSerializerMixin(serializers.Serializer):
    team = CourseRunTeamSerializer(required=False)

    def update_team(self, instance, team):
        CourseAccessRole.objects.filter(course_id=instance.id).delete()

        # TODO In the future we can optimize by getting users in a single query.
        CourseAccessRole.objects.bulk_create([
            CourseAccessRole(course_id=instance.id, role=member['role'], user=User.objects.get(username=member['user']))
            for member in team
        ])


class CourseRunSerializer(CourseRunTeamSerializerMixin, serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(source='display_name')
    schedule = CourseRunScheduleSerializer(source='*', required=False)

    def update(self, instance, validated_data):
        team = validated_data.pop('team', [])

        with transaction.atomic():
            self.update_team(instance, team)

            for attr, value in six.iteritems(validated_data):
                setattr(instance, attr, value)

            modulestore().update_item(instance, self.context['request'].user.id)
            return instance

    def update_team(self, instance, team):
        CourseAccessRole.objects.filter(course_id=instance.id).delete()

        # TODO In the future we can optimize by getting users in a single query.
        CourseAccessRole.objects.bulk_create([
            CourseAccessRole(course_id=instance.id, role=member['role'], user=User.objects.get(username=member['user']))
            for member in team
        ])


class CourseRunCreateSerializer(CourseRunSerializer):
    org = serializers.CharField(source='id.org')
    number = serializers.CharField(source='id.course')
    run = serializers.CharField(source='id.run')

    def create(self, validated_data):
        _id = validated_data.pop('id')
        team = validated_data.pop('team', [])
        user = self.context['request'].user

        with transaction.atomic():
            instance = create_new_course(user, _id['org'], _id['course'], _id['run'], validated_data)
            self.update_team(instance, team)
            return instance


class CourseRunRerunSerializer(CourseRunTeamSerializerMixin, serializers.Serializer):
    title = serializers.CharField(source='display_name', required=False)
    run = serializers.CharField(source='id.run')
    schedule = CourseRunScheduleSerializer(source='*', required=False)

    def validate_run(self, value):
        course_run_key = self.instance.id
        store = modulestore()
        with store.default_store('split'):
            new_course_run_key = store.make_course_key(course_run_key.org, course_run_key.course, value)
        if store.has_course(new_course_run_key, ignore_case=True):
            raise serializers.ValidationError('Course run {key} already exists'.format(key=new_course_run_key))
        return value

    def update(self, instance, validated_data):
        course_run_key = instance.id
        _id = validated_data.pop('id')
        team = validated_data.pop('team', [])
        user = self.context['request'].user
        fields = {
            'display_name': instance.display_name
        }
        fields.update(validated_data)
        new_course_run_key = rerun_course(user, course_run_key, course_run_key.org, course_run_key.course, _id['run'],
                                          fields, async=False)

        course_run = get_course_and_check_access(new_course_run_key, user)
        self.update_team(course_run, team)
        return course_run
