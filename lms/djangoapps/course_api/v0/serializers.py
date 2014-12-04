""" Django REST Framework Serializers """

from django.core.urlresolvers import reverse

from rest_framework import serializers


# pylint: disable=invalid-name
class BaseSerializer(serializers.Serializer):
    """ Base serializer for module data. """
    id = serializers.CharField(source='location')
    name = serializers.CharField(source='display_name')


# pylint: disable=invalid-name
class CourseSerializer(serializers.Serializer):
    """ Serializer for Courses """
    id = serializers.CharField()
    name = serializers.CharField()
    category = serializers.CharField()
    course = serializers.CharField()
    org = serializers.CharField()
    run = serializers.CharField()
    uri = serializers.CharField()
    image_url = serializers.CharField()
    resources = serializers.CharField()
    due = serializers.DateTimeField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

    def get_uri(self, course):
        """
        Builds course detail uri
        """
        # pylint: disable=no-member
        request = self.context['request']
        return request.build_absolute_uri(reverse('course_api:detail', kwargs={'course_id': course.id}))


class GradedContentSerializer(BaseSerializer):
    """ Serializer for course graded content. """
    format = serializers.CharField()
    problems = BaseSerializer(many=True)


class GradingPolicySerializer(serializers.Serializer):
    """ Serializer for course grading policy. """
    assignment_type = serializers.CharField(source='type')
    count = serializers.IntegerField(source='min_count')
    dropped = serializers.IntegerField(source='drop_count')
    weight = serializers.FloatField()
