"""
Unit tests for Course card helpers
"""
from crum import set_current_request
from django.test.client import RequestFactory

from course_action_state.models import CourseRerunState
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory

from ..helpers import get_course_cards_list, get_future_courses, get_related_card, get_related_card_id, is_course_rereun
from .helpers import disable_course_card, set_course_dates
from .test_views import CourseCardBaseClass


class CourseCardHelperBaseClass(CourseCardBaseClass):
    """
    Base class for Course card helpers test cases
    """
    def setUp(self):
        super(CourseCardHelperBaseClass, self).setUp()

        self.rerun_parent_course = self.courses[0]
        org = self.rerun_parent_course.org
        course_number = self.rerun_parent_course.number
        course_run = '2015_Q2'
        display_name = self.rerun_parent_course.display_name + ' - re run'

        self.re_run_course = CourseFactory.create(org=org, number=course_number, run=course_run,
                                                  display_name=display_name, default_store=ModuleStoreEnum.Type.split)

        CourseRerunState.objects.initiated(self.rerun_parent_course.id, self.re_run_course.id, self.staff,
                                           display_name=display_name)

    def test_get_related_card_id(self):
        non_re_run_course_id = self.courses[1].id
        parent_course_id = self.rerun_parent_course.id
        re_run_course_id = self.re_run_course.id

        # Desired output is the parent's course id
        self.assertEqual(get_related_card_id(re_run_course_id), parent_course_id)

        # For courses without a rerun the passed course id is returned as it is
        self.assertEqual(get_related_card_id(non_re_run_course_id), non_re_run_course_id)

        # For parent course id as input, the same course id should be returned
        self.assertEqual(get_related_card_id(parent_course_id), parent_course_id)

    def test_get_related_card(self):
        non_re_run_course = self.courses[1]

        # Desired output is the parent course when course which is a rerun is passed as input
        self.assertEqual(get_related_card(self.re_run_course).id, self.rerun_parent_course.id)

        # For courses without a rerun the passed course is returned as it is
        self.assertEqual(get_related_card(non_re_run_course).id, non_re_run_course.id)

        # For parent course as input, the parent course should be returned as it is
        self.assertEqual(get_related_card(self.rerun_parent_course).id, self.rerun_parent_course.id)

    def test_get_future_courses(self):
        CourseRerunState.objects.succeeded(course_key=self.re_run_course.id)

        set_course_dates(self.re_run_course, -180, -152, -150, -120)
        set_course_dates(self.rerun_parent_course, -90, -76, -75, -60)

        self.assertIsNone(get_future_courses(self.rerun_parent_course.id))

        re_run_course_overview = set_course_dates(self.re_run_course, 5, 15, 16, 30)
        set_course_dates(self.rerun_parent_course, -90, -76, -75, -60)

        self.assertEqual(get_future_courses(self.rerun_parent_course.id), re_run_course_overview)

        re_run_course_overview = set_course_dates(self.re_run_course, 50, 150, 160, 300)
        set_course_dates(self.rerun_parent_course, 5, 15, 16, 30)

        self.assertEqual(get_future_courses(self.rerun_parent_course.id), re_run_course_overview)

    def test_is_course_rereun(self):
        non_re_run_course_id = self.courses[1].id
        parent_course_id = self.rerun_parent_course.id
        re_run_course_id = self.re_run_course.id

        # Desired output is the parent's course id
        self.assertEqual(is_course_rereun(re_run_course_id), parent_course_id)

        # For courses without a rerun the None is returned
        self.assertIsNone(is_course_rereun(non_re_run_course_id))

        # For parent course id as input, None should be returned
        self.assertIsNone(is_course_rereun(parent_course_id))

    def test_get_course_cards_list(self):
        # Disable a course's course card
        course = self.courses[-1]
        disable_course_card(course)

        request = RequestFactory().get('/dummy-url')
        request.user = self.user
        request.session = {}
        set_current_request(request)

        # For Normal User
        # Desired output is a list of course overview objects for which course card is enabled
        self.assertEqual({c.id for c in get_course_cards_list()}, {course.id for course in self.courses[:-1]})

        request.user = self.staff
        set_current_request(request)

        # For Staff User
        # Desired output is a list of all course overview objects
        self.assertEqual({c.id for c in get_course_cards_list()}, {course.id for course in self.courses})
