"""
Unit tests for course card admin
"""
from course_action_state.models import CourseRerunState
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory

from ..admin import get_parent_courses
from .helpers import set_course_dates
from .test_views import CourseCardBaseClass


class CourseCardAdminBaseClass(CourseCardBaseClass):
    """
    This class contains test cases for course card admin
    """
    def setUp(self):
        super(CourseCardAdminBaseClass, self).setUp()

        self.rerun_parent_course = self.courses[0]
        org = self.rerun_parent_course.org
        course_number = self.rerun_parent_course.number
        course_run = '2015_Q2'
        display_name = self.rerun_parent_course.display_name + ' - re run'

        self.re_run_course = CourseFactory.create(org=org, number=course_number, run=course_run,
                                                  display_name=display_name, default_store=ModuleStoreEnum.Type.split)

        CourseRerunState.objects.initiated(self.rerun_parent_course.id, self.re_run_course.id, self.staff,
                                           display_name=display_name)

    def test_get_parent_courses(self):
        parent_course = self.courses[-1]
        set_course_dates(self.re_run_course, 5, 10, 15, 20)
        set_course_dates(parent_course, 5, 10, 15, 20)

        # Desired ouput is a list of tuple containing
        # only 1 parent course in the following format: (course_id, 'name -- id')
        self.assertEquals(
            set(get_parent_courses()),
            {(parent_course.id, '{} -- {}'.format(parent_course.display_name, parent_course.id))}
        )
