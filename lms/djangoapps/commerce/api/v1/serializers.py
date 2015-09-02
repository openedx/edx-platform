""" API v1 serializers. """
from datetime import datetime

import pytz
from django.utils.translation import ugettext as _

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import serializers

from commerce.api.v1.models import Course
from course_modes.models import CourseMode

from xmodule.modulestore.django import modulestore


class CourseModeSerializer(serializers.ModelSerializer):
    """ CourseMode serializer. """
    name = serializers.CharField(source='mode_slug')
    price = serializers.IntegerField(source='min_price')
    expires = serializers.DateTimeField(source='expiration_datetime', required=False, blank=True)

    def get_identity(self, data):
        try:
            return data.get('name', None)
        except AttributeError:
            return None

    class Meta(object):  # pylint: disable=missing-docstring
        model = CourseMode
        fields = ('name', 'currency', 'price', 'sku', 'expires')


def validate_course_id(course_id):
    """
    Check that course id is valid and exists in modulestore.
    """
    try:
        course_key = CourseKey.from_string(unicode(course_id))
    except InvalidKeyError:
        raise serializers.ValidationError(
            _("{course_id} is not a valid course key.").format(
                course_id=course_id
            )
        )

    if not modulestore().has_course(course_key):
        raise serializers.ValidationError(
            _('Course {course_id} does not exist.').format(
                course_id=course_id
            )
        )


class CourseSerializer(serializers.Serializer):
    """ Course serializer. """
    id = serializers.CharField(validators=[validate_course_id])  # pylint: disable=invalid-name
    name = serializers.CharField(read_only=True)
    verification_deadline = serializers.DateTimeField(blank=True)
    modes = CourseModeSerializer(many=True, allow_add_remove=True)

    def validate(self, attrs):
        """ Ensure the verification deadline occurs AFTER the course mode enrollment deadlines. """
        verification_deadline = attrs.get('verification_deadline', None)

        if verification_deadline:
            upgrade_deadline = None

            # Find the earliest upgrade deadline
            for mode in attrs['modes']:
                expires = mode.expiration_datetime
                if expires:
                    # If we don't already have an upgrade_deadline value, use datetime.max so that we can actually
                    # complete the comparison.
                    upgrade_deadline = min(expires, upgrade_deadline or datetime.max.replace(tzinfo=pytz.utc))

            # In cases where upgrade_deadline is None (e.g. the verified professional mode), allow a verification
            # deadline to be set anyway.
            if upgrade_deadline is not None and verification_deadline < upgrade_deadline:
                raise serializers.ValidationError(
                    'Verification deadline must be after the course mode upgrade deadlines.')

        return attrs

    def restore_object(self, attrs, instance=None):
        if instance is None:
            return Course(attrs['id'], attrs['modes'], attrs['verification_deadline'])

        instance.update(attrs)
        return instance
