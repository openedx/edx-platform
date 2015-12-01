""" Credit API Serializers """

from __future__ import unicode_literals
import datetime
import logging

from django.conf import settings
from opaque_keys import InvalidKeyError
import pytz
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from openedx.core.djangoapps.credit.models import CreditCourse, CreditProvider, CreditEligibility, CreditRequest
from openedx.core.djangoapps.credit.signature import get_shared_secret_key, signature
from openedx.core.lib.api.serializers import CourseKeyField
from util.date_utils import from_timestamp

log = logging.getLogger(__name__)


class CreditCourseSerializer(serializers.ModelSerializer):
    """ CreditCourse Serializer """

    course_key = CourseKeyField()

    class Meta(object):
        model = CreditCourse
        exclude = ('id',)


class CreditProviderSerializer(serializers.ModelSerializer):
    """ CreditProvider """
    id = serializers.CharField(source='provider_id')  # pylint:disable=invalid-name
    description = serializers.CharField(source='provider_description')
    status_url = serializers.URLField(source='provider_status_url')
    url = serializers.URLField(source='provider_url')

    class Meta(object):
        model = CreditProvider
        fields = ('id', 'display_name', 'url', 'status_url', 'description', 'enable_integration',
                  'fulfillment_instructions', 'thumbnail_url',)


class CreditEligibilitySerializer(serializers.ModelSerializer):
    """ CreditEligibility serializer. """
    course_key = serializers.SerializerMethodField()

    def get_course_key(self, obj):
        """ Returns the course key associated with the course. """
        return unicode(obj.course.course_key)

    class Meta(object):
        model = CreditEligibility
        fields = ('username', 'course_key', 'deadline',)


class CreditProviderCallbackSerializer(serializers.Serializer):  # pylint:disable=abstract-method
    """
    Serializer for input to the CreditProviderCallback view.

    This is used solely for validating the input.
    """
    request_uuid = serializers.CharField(required=True)
    status = serializers.ChoiceField(required=True, choices=CreditRequest.REQUEST_STATUS_CHOICES)
    timestamp = serializers.IntegerField(required=True)
    signature = serializers.CharField(required=True)

    def __init__(self, **kwargs):
        self.provider = kwargs.pop('provider', None)
        super(CreditProviderCallbackSerializer, self).__init__(**kwargs)

    def validate_timestamp(self, value):
        """ Ensure the request has been received in a timely manner. """
        date_time = from_timestamp(value)

        # Ensure we converted the timestamp to a datetime
        if not date_time:
            msg = '[{}] is not a valid timestamp'.format(value)
            log.warning(msg)
            raise serializers.ValidationError(msg)

        elapsed = (datetime.datetime.now(pytz.UTC) - date_time).total_seconds()
        if elapsed > settings.CREDIT_PROVIDER_TIMESTAMP_EXPIRATION:
            msg = '[{value}] is too far in the past (over [{elapsed}] seconds).'.format(value=value, elapsed=elapsed)
            log.warning(msg)
            raise serializers.ValidationError(msg)

        return value

    def validate_signature(self, value):
        """ Validate the signature and ensure the provider is setup properly. """
        provider_id = self.provider.provider_id
        secret_key = get_shared_secret_key(provider_id)
        if secret_key is None:
            msg = 'Could not retrieve secret key for credit provider [{}]. ' \
                  'Unable to validate requests from provider.'.format(provider_id)
            log.error(msg)
            raise PermissionDenied(msg)

        data = self.initial_data
        actual_signature = data["signature"]
        if signature(data, secret_key) != actual_signature:
            msg = 'Request from credit provider [{}] had an invalid signature.'.format(provider_id)
            raise PermissionDenied(msg)

        return value
