""" Django REST Framework Serializers """

from django.core.urlresolvers import reverse
from rest_framework import serializers


class CourseSerializer(serializers.Serializer):
    """ Serializer for Courses """
    id = serializers.SerializerMethodField()  # pylint: disable=invalid-name
    name = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    org = serializers.SerializerMethodField()
    run = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    uri = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()

    def get_id(self, course):
        """ Gets course ID """
        return unicode(course.id)

    def get_org(self, course):
        """ Gets the course org """
        return course.id.org

    def get_category(self, _course):
        """ Gets course category (always a course) """
        return 'course'

    def get_run(self, course):
        """ Gets the course run """
        return course.id.run

    def get_name(self, course):
        """ Gets display name """
        return course.display_name

    def get_start(self, course):
        """ Gets course start """
        return course.start

    def get_end(self, course):
        """ Gets course end """
        return course.end

    def get_course(self, course):
        """ Gets the course """
        return course.id.course

    def get_uri(self, course):
        """ Builds course detail uri """
        request = self.context['request']
        return request.build_absolute_uri(reverse('course_structure_api:v0:detail', kwargs={'course_id': course.id}))

    def get_image_url(self, course):
        """ Get the course image URL """
        return course.course_image_url
