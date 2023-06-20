"""
Serializers for all Course Entitlement related return objects.
"""


from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.djangoapps.entitlements.models import CourseEntitlement, CourseEntitlementSupportDetail
from openedx.core.lib.api.serializers import CourseKeyField


class CourseEntitlementSerializer(serializers.ModelSerializer):
    """ Serialize a learner's course entitlement and related information. """
    user = serializers.SlugRelatedField(slug_field='username', queryset=get_user_model().objects.all())
    enrollment_course_run = serializers.CharField(
        source='enrollment_course_run.course_id',
        read_only=True
    )
    support_details = serializers.SerializerMethodField()

    def get_support_details(self, model):
        """
        Returns a serialized set of all support interactions with the course entitlement
        """
        qset = CourseEntitlementSupportDetail.objects.filter(entitlement=model).order_by('-created')
        return CourseEntitlementSupportDetailSerializer(qset, many=True).data

    class Meta:
        model = CourseEntitlement
        fields = (
            'user',
            'uuid',
            'course_uuid',
            'enrollment_course_run',
            'expired_at',
            'created',
            'modified',
            'mode',
            'refund_locked',
            'order_number',
            'support_details'
        )


class CourseEntitlementSupportDetailSerializer(serializers.ModelSerializer):
    """ Serialize the details of a support team interaction with a learner's course entitlement. """
    support_user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    unenrolled_run = CourseKeyField('unenrolled_run.id')

    class Meta:
        model = CourseEntitlementSupportDetail
        fields = (
            'support_user',
            'action',
            'comments',
            'unenrolled_run',
            'created'
        )
