#!/usr/bin/python
#
# django management command: dump grades to csv files
# for use by batch processes

from instructor.offline_gradecalc import offline_grade_calculation
from courseware.courses import get_course_by_id
from xmodule.modulestore.django import modulestore
from courseware.models import StudentModule
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module, get_module_for_descriptor
from django.contrib.auth.models import User
from ...utils import create_module, get_descriptor, DummyRequest

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Usage: openended_stats course_id location \n"

    def handle(self, *args, **options):

        print "args = ", args

        if len(args) > 0:
            course_id = args[0]
            location = args[1]
        else:
            print self.help
            return

        request = DummyRequest()
        course = get_course_by_id(course_id)
        descriptor = get_descriptor(course, location)
        if descriptor is None:
            print "Location not found in course"
            return

        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_id,
            courseenrollment__is_active=1
        ).prefetch_related("groups").order_by('username')

        for student in enrolled_students:
            request.user = student
            request.session = {}
            module = create_module(descriptor, course, student, request)
            tasks = len(module.task_states)
            # if tasks>0:
            print tasks

            try:
                student_module = StudentModule.objects.get(
                    student=student,
                    course_id=course_id,
                    module_state_key=descriptor.id
                )
                # print student_module

            except StudentModule.DoesNotExist:
                student_module = None
