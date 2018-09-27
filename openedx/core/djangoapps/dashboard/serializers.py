

import logging

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment

from rest_framework import serializers

class CourseOverviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseOverview
        fields = '__all__'


class CourseEnrollmentSerializer(serializers.ModelSerializer):

    course_overview = CourseOverviewSerializer()

    class Meta:
        model = CourseEnrollment
        fields = ('created', 'course_overview')

    # def to_representation(self, instance):
    #     representation = super(CourseEnrollmentSerializer, self).to_representation(instance)
    #     representation['course'] =  "Course: {}".format(representation['course'])
    #     # CourseOverview information
    #     representation['course_start'] = instance.course.start
    #     representation['course_end'] = instance.course.end
    #     representation['display_name'] = instance.course.display_name
    #     representation['course_image_url'] = instance.course.course_image_url
    #     representation['social_sharing_url'] = instance.course.social_sharing_url
    #     representation['certificates_display_behavior'] = instance.course.certificates_display_behavior
    #     representation['has_any_active_web_certificate'] = instance.course.has_any_active_web_certificate
    #     representation['cert_name_short'] = instance.course.cert_name_short
    #     representation['cert_name_long'] = instance.course.cert_name_long
    #     representation['certificate_available_date'] = instance.course.certificate_available_date
    #     representation['lowest_passing_grade'] = instance.course.lowest_passing_grade
    #     representation['mobile_available'] = instance.course.mobile_available
    #     representation['visible_to_staff_only'] = instance.course.visible_to_staff_only
    #     representation['invitation_only'] = instance.course.invitation_only
    #     representation['max_student_enrollments_allowed'] = instance.course.max_student_enrollments_allowed
    #     representation['catalog_visibility'] = instance.course.catalog_visibility
    #     representation['short_description'] = instance.course.short_description
    #     representation['course_video_url'] = instance.course.course_video_url
    #     representation['effort'] = instance.course.effort
    #     representation['self_paced'] = instance.course.self_paced
    #     representation['eligible_for_financial_aid'] = instance.course.eligible_for_financial_aid

    #     return representation
