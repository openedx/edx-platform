""" Course run serializers. """
import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from opaque_keys import InvalidKeyError
from rest_framework import serializers
from rest_framework.fields import empty

from cms.djangoapps.contentstore.views.assets import update_course_run_asset
from cms.djangoapps.contentstore.views.course import create_new_course, get_course_and_check_access, rerun_course
from common.djangoapps.student.models import CourseAccessRole
from openedx.core.lib.courses import course_image_url
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

IMAGE_TYPES = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
}
User = get_user_model()
log = logging.getLogger(__name__)


class CourseAccessRoleSerializer(serializers.ModelSerializer):  # lint-amnesty, pylint: disable=missing-class-docstring
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = CourseAccessRole
        fields = ('user', 'role',)


class CourseRunScheduleSerializer(serializers.Serializer):  # lint-amnesty, pylint: disable=abstract-method
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    enrollment_start = serializers.DateTimeField(allow_null=True, required=False)
    enrollment_end = serializers.DateTimeField(allow_null=True, required=False)


class CourseRunTeamSerializer(serializers.Serializer):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    def to_internal_value(self, data):
        """Overriding this to support deserialization, for write operations."""
        for member in data:
            try:
                User.objects.get(username=member['user'])
            except User.DoesNotExist:
                raise serializers.ValidationError(  # lint-amnesty, pylint: disable=raise-missing-from
                    _('Course team user does not exist')
                )

        return CourseAccessRoleSerializer(data=data, many=True).to_internal_value(data)

    def to_representation(self, instance):
        roles = CourseAccessRole.objects.filter(course_id=instance.id)
        return CourseAccessRoleSerializer(roles, many=True).data

    def get_attribute(self, instance):
        # Course instances have no "team" attribute. Return the course, and the consuming serializer will
        # handle the rest.
        return instance


class CourseRunTeamSerializerMixin(serializers.Serializer):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    team = CourseRunTeamSerializer(required=False)

    def update_team(self, instance, team):  # lint-amnesty, pylint: disable=missing-function-docstring
        # Existing data should remain intact when performing a partial update.
        if not self.partial:
            CourseAccessRole.objects.filter(course_id=instance.id).delete()

        # We iterate here, instead of using a bulk operation, to avoid uniqueness errors that arise
        # when using `bulk_create` with existing data. Given the relatively small number of team members
        # in a course, this is not worth optimizing at this time.
        for member in team:
            CourseAccessRole.objects.get_or_create(
                course_id=instance.id,
                org=instance.id.org,
                user=User.objects.get(username=member['user']),
                role=member['role']
            )


def image_is_jpeg_or_png(value):
    content_type = value.content_type
    if content_type not in list(IMAGE_TYPES.keys()):  # lint-amnesty, pylint: disable=consider-iterating-dictionary
        raise serializers.ValidationError(
            f'Only JPEG and PNG image types are supported. {content_type} is not valid')


class CourseRunImageField(serializers.ImageField):  # lint-amnesty, pylint: disable=missing-class-docstring
    default_validators = [image_is_jpeg_or_png]

    def get_attribute(self, instance):
        return course_image_url(instance)

    def to_representation(self, value):
        # Value will always be the URL path of the image.
        request = self.context['request']
        return request.build_absolute_uri(value)


class CourseRunPacingTypeField(serializers.ChoiceField):  # lint-amnesty, pylint: disable=missing-class-docstring
    def to_representation(self, value):
        return 'self_paced' if value else 'instructor_paced'

    def to_internal_value(self, data):
        return data == 'self_paced'


class CourseRunImageSerializer(serializers.Serializer):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    # We set an empty default to prevent the parent serializer from attempting
    # to save this value to the Course object.
    card_image = CourseRunImageField(source='course_image', default=empty)

    def update(self, instance, validated_data):
        course_image = validated_data['course_image']
        course_image.name = 'course_image.' + IMAGE_TYPES[course_image.content_type]
        update_course_run_asset(instance.id, course_image)

        instance.course_image = course_image.name
        modulestore().update_item(instance, self.context['request'].user.id)
        return instance


class CourseRunSerializerCommonFieldsMixin(serializers.Serializer):  # lint-amnesty, pylint: disable=abstract-method
    schedule = CourseRunScheduleSerializer(source='*', required=False)
    pacing_type = CourseRunPacingTypeField(source='self_paced', required=False,
                                           choices=((False, 'instructor_paced'), (True, 'self_paced'),))


class CourseRunSerializer(CourseRunSerializerCommonFieldsMixin, CourseRunTeamSerializerMixin, serializers.Serializer):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(source='display_name')
    images = CourseRunImageSerializer(source='*', required=False)

    def update(self, instance, validated_data):
        team = validated_data.pop('team', [])

        with transaction.atomic():
            self.update_team(instance, team)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            modulestore().update_item(instance, self.context['request'].user.id)
            return instance


class CourseRunCreateSerializer(CourseRunSerializer):  # lint-amnesty, pylint: disable=missing-class-docstring
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


class CourseRunRerunSerializer(CourseRunSerializerCommonFieldsMixin, CourseRunTeamSerializerMixin,  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
                               serializers.Serializer):
    title = serializers.CharField(source='display_name', required=False)
    number = serializers.CharField(source='id.course', required=False)
    run = serializers.CharField(source='id.run')

    def validate(self, attrs):
        course_run_key = self.instance.id
        _id = attrs.get('id')
        number = _id.get('course', course_run_key.course)
        run = _id['run']
        store = modulestore()
        try:
            with store.default_store('split'):
                new_course_run_key = store.make_course_key(course_run_key.org, number, run)
        except InvalidKeyError:
            raise serializers.ValidationError(  # lint-amnesty, pylint: disable=raise-missing-from
                'Invalid key supplied. Ensure there are no special characters in the Course Number.'
            )
        if store.has_course(new_course_run_key, ignore_case=True):
            raise serializers.ValidationError(
                {'run': f'Course run {new_course_run_key} already exists'}
            )
        return attrs

    def update(self, instance, validated_data):
        course_run_key = instance.id
        _id = validated_data.pop('id')
        number = _id.get('course', course_run_key.course)
        run = _id['run']
        team = validated_data.pop('team', [])
        user = self.context['request'].user
        fields = {
            'display_name': instance.display_name
        }
        fields.update(validated_data)
        new_course_run_key = rerun_course(user, course_run_key, course_run_key.org, number, run, fields, False)

        course_run = get_course_and_check_access(new_course_run_key, user)
        self.update_team(course_run, team)
        return course_run
