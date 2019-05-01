"""
Factories for Program Enrollment tests.
"""
from uuid import uuid4

import factory
from factory.django import DjangoModelFactory

from lms.djangoapps.program_enrollments import models
from student.tests.factories import UserFactory


class ProgramEnrollmentFactory(DjangoModelFactory):
    """ A Factory for the ProgramEnrollment model. """
    class Meta(object):
        model = models.ProgramEnrollment

    user = factory.SubFactory(UserFactory)
    external_user_key = None
    program_uuid = uuid4()
    curriculum_uuid = uuid4()
    status = 'enrolled'
