"""
Configuration for app to store information about whether or not Studio users have
course creation privileges.
"""


from django.apps import AppConfig


class CourseCreatorsConfig(AppConfig):
    name = 'cms.djangoapps.course_creators'
    verbose_name = 'Course Creators'
