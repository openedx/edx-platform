"""
Django REST Framework Serializers

FOR NON-BREAKING CHANGES:
 - Be sure to update the corresponding docstring information in views.py, which will technomagically
   find its way out to the Read The Docs platform API web site.

FOR BREAKING CHANGES:
 - Do you *really* have to do this?  Really???
 - Okay, then you can't modify this serializer, you must create a new version subfolder and files
 - Don't forget to support all unchanged views/logic as well, by either carrying references forward,
   pointing your own calls back to the previous logic, or some sort of clever generalization
 - And be sure to test everything!!!
"""


from django.core.urlresolvers import reverse
from rest_framework import serializers

from courseware.courses import course_image_url


class CourseSerializer(serializers.Serializer):
    """ Course Metadata Serializer """
    uri = serializers.SerializerMethodField('get_uri')
    course_id = serializers.CharField(source='id')
    org = serializers.SerializerMethodField('get_org')
    course = serializers.SerializerMethodField('get_course')
    run = serializers.SerializerMethodField('get_run')
    name = serializers.CharField(source='display_name')
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    short_description = serializers.SerializerMethodField('get_short_description')
    media = serializers.SerializerMethodFIeld('get_media')
    staff = serializers.SerializerMethodField('get_staff')


    def get_uri(self, course):
        """ Builds course detail uri """
        # pylint: disable=no-member
        request = self.context['request']
        return request.build_absolute_uri(
            reverse('course_metadata_api:v0:detail', kwargs={'course_id': course.id})
        )

    def get_org(self, course):
        """ Gets the course org """
        return course.id.org

    def get_course(self, course):
        """ Gets the course """
        return course.id.course

    def get_run(self, course):
        """ Gets the course run """
        return course.id.run

    def get_short_description(self, course):
        """ Gets the short description for this course """

    def get_media(self, course):
        """ Construct the media dictionary for this course """

    def get_staff(self, course):
        """ Construct the staff list for this course """

