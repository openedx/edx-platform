"""
Factories for Program Enrollment tests.
"""
from __future__ import absolute_import

from uuid import uuid4

import factory
from factory.django import DjangoModelFactory
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.program_enrollments import models
from student.tests.factories import CourseEnrollmentFactory, UserFactory


class ProgramEnrollmentFactory(DjangoModelFactory):
    """ A Factory for the ProgramEnrollment model. """
    class Meta(object):
        model = models.ProgramEnrollment

    user = factory.SubFactory(UserFactory)
    external_user_key = None
    program_uuid = uuid4()
    curriculum_uuid = uuid4()
    status = 'enrolled'


class ProgramCourseEnrollmentFactory(DjangoModelFactory):
    """ A factory for the ProgramCourseEnrollment model. """
    class Meta(object):
        model = models.ProgramCourseEnrollment

    program_enrollment = factory.SubFactory(ProgramEnrollmentFactory)
    course_enrollment = factory.SubFactory(CourseEnrollmentFactory)
    course_key = CourseKey.from_string("course-v1:edX+DemoX+Demo_Course")
    status = 'active'
