"""
Instructor Task Factory
"""


import json

import factory
from celery.states import PENDING
from factory.django import DjangoModelFactory
from opaque_keys.edx.locator import CourseLocator

from lms.djangoapps.instructor_task.models import InstructorTask
from common.djangoapps.student.tests.factories import UserFactory as StudentUserFactory


class InstructorTaskFactory(DjangoModelFactory):
    class Meta(object):
        model = InstructorTask

    task_type = 'rescore_problem'
    course_id = CourseLocator("MITx", "999", "Robot_Super_Course")
    task_input = json.dumps({})
    task_key = None
    task_id = None
    task_state = PENDING
    task_output = None
    requester = factory.SubFactory(StudentUserFactory)
