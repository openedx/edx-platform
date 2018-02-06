from django.contrib.auth import get_user_model
from rest_framework import serializers

from entitlements.models import CourseEntitlement, CourseEntitlementSupportDetail
from openedx.core.lib.api.serializers import CourseKeyField


class CourseEntitlementSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=get_user_model().objects.all())
    enrollment_course_run = serializers.CharField(
        source='enrollment_course_run.course_id',
        read_only=True
    )

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
            'order_number'
        )

class CourseEntitlementSupportDetailSerializer(serializers.ModelSerializer):
    support_user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    unenrolled_run = CourseKeyField('unenrolled_run.id')
    reason = serializers.CharField(allow_null=True)

    class Meta:
        model = CourseEntitlementSupportDetail
        fields = (
            'support_user',
            'reason',
            'comments',
            'unenrolled_run'
        )

class SupportCourseEntitlementSerializer(CourseEntitlementSerializer):
    support_details = serializers.SerializerMethodField()

    def get_support_details(self, model):
        """
        Returns a serialized set of all support interactions with the course entitlement
        """
        qset = CourseEntitlementSupportDetail.objects.filter(entitlement=model)
        if qset:
            return CourseEntitlementSupportDetailSerializer(qset, many=True).data
        else:
            return []

    class Meta:
        model = CourseEntitlement
        fields = CourseEntitlementSerializer.Meta.fields + ('support_details', )
