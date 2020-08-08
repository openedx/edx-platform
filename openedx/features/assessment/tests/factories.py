""" Test Factories. """
import datetime
from uuid import uuid4

import factory
from factory.django import DjangoModelFactory
from submissions.models import StudentItem, Submission


class StudentItemFactory(DjangoModelFactory):
    """ A Factory for the StudentItem model. """
    class Meta:
        model = StudentItem

    student_id = factory.Faker('sha1')
    course_id = factory.Faker('sha1')
    item_id = factory.Faker('sha1')
    item_type = 'openassessment'


class SubmissionFactory(DjangoModelFactory):
    """ A factory for the Submission model. """
    class Meta:
        model = Submission

    uuid = factory.LazyFunction(uuid4)
    student_item = factory.SubFactory(StudentItemFactory)
    attempt_number = 1
    submitted_at = datetime.datetime.now()
    created_at = datetime.datetime.now()
    answer = {}
