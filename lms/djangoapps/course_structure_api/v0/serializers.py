""" Django REST Framework Serializers """

from django.core.urlresolvers import reverse
from rest_framework import serializers

from openedx.core.lib.courses import course_image_url


class CourseSerializer(serializers.Serializer):
    """ Serializer for Courses """
    id = serializers.CharField()  # pylint: disable=invalid-name
    name = serializers.CharField(source='display_name')
    category = serializers.CharField()
    org = serializers.SerializerMethodField()
    run = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    uri = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

    def get_org(self, course):
        """ Gets the course org """
        return course.id.org

    def get_run(self, course):
        """ Gets the course run """
        return course.id.run

    def get_course(self, course):
        """ Gets the course """
        return course.id.course

    def get_uri(self, course):
        """ Builds course detail uri """
        request = self.context['request']
        return request.build_absolute_uri(reverse('course_structure_api:v0:detail', kwargs={'course_id': course.id}))

    def get_image_url(self, course):
        """ Get the course image URL """
        return course_image_url(course)
