""" Django REST Framework Serializers """

from django.core.urlresolvers import reverse
from rest_framework import serializers

from courseware.courses import course_image_url


class CourseSerializer(serializers.Serializer):
    """ Serializer for Courses """
    id = serializers.CharField()  # pylint: disable=invalid-name
    name = serializers.CharField(source='display_name')
    category = serializers.CharField()
    org = serializers.SerializerMethodField('get_org')
    run = serializers.SerializerMethodField('get_run')
    course = serializers.SerializerMethodField('get_course')
    uri = serializers.SerializerMethodField('get_uri')
    image_url = serializers.SerializerMethodField('get_image_url')
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
        # pylint: disable=no-member
        request = self.context['request']
        return request.build_absolute_uri(reverse('course_structure_api:v0:detail', kwargs={'course_id': course.id}))

    def get_image_url(self, course):
        """ Get the course image URL """
        return course_image_url(course)


class GradingPolicySerializer(serializers.Serializer):
    """ Serializer for course grading policy. """
    assignment_type = serializers.CharField(source='type')
    count = serializers.IntegerField(source='min_count')
    dropped = serializers.IntegerField(source='drop_count')
    weight = serializers.FloatField()


# pylint: disable=invalid-name
class BlockSerializer(serializers.Serializer):
    """ Serializer for course structure block. """
    id = serializers.CharField(source='usage_key')
    type = serializers.CharField(source='block_type')
    display_name = serializers.CharField()
    graded = serializers.BooleanField(default=False)
    format = serializers.CharField()
    children = serializers.CharField()


class CourseStructureSerializer(serializers.Serializer):
    """ Serializer for course structure. """
    root = serializers.CharField(source='root')
    blocks = serializers.SerializerMethodField('get_blocks')

    def get_blocks(self, structure):
        """ Serialize the individual blocks. """
        serialized = {}

        for key, block in structure['blocks'].iteritems():
            serialized[key] = BlockSerializer(block).data

        return serialized
