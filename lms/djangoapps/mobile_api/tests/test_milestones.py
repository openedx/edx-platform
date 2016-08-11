"""
Milestone related tests for the mobile_api
"""
from django.conf import settings
from mock import patch

from courseware.access_response import MilestoneError
from courseware.tests.helpers import get_request_for_user
from courseware.tests.test_entrance_exam import answer_entrance_exam_problem, add_entrance_exam_milestone
from util.milestones_helpers import (
    add_prerequisite_course,
    fulfill_course_milestone,
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class MobileAPIMilestonesMixin(object):
    """
    Tests the Mobile API decorators for milestones.

    The two milestones currently supported in these tests are entrance exams and
    pre-requisite courses. If either of these milestones are unfulfilled,
    the mobile api will appropriately block content until the milestone is
    fulfilled.
    """

    ALLOW_ACCESS_TO_MILESTONE_COURSE = False  # pylint: disable=invalid-name

    @patch.dict(settings.FEATURES, {
        'ENABLE_PREREQUISITE_COURSES': True,
        'ENABLE_MKTG_SITE': True,
    })
    def test_unfulfilled_prerequisite_course(self):
        """ Tests the case for an unfulfilled pre-requisite course """
        self._add_prerequisite_course()
        self.init_course_access()
        self._verify_unfulfilled_milestone_response()

    @patch.dict(settings.FEATURES, {'ENABLE_PREREQUISITE_COURSES': True, 'ENABLE_MKTG_SITE': True})
    def test_unfulfilled_prerequisite_course_for_staff(self):
        self._add_prerequisite_course()
        self.user.is_staff = True
        self.user.save()
        self.init_course_access()
        self.api_response()

    @patch.dict(settings.FEATURES, {'ENABLE_PREREQUISITE_COURSES': True, 'ENABLE_MKTG_SITE': True})
    def test_fulfilled_prerequisite_course(self):
        """
        Tests the case when a user fulfills existing pre-requisite course
        """
        self._add_prerequisite_course()
        add_prerequisite_course(self.course.id, self.prereq_course.id)
        fulfill_course_milestone(self.prereq_course.id, self.user)
        self.init_course_access()
        self.api_response()

    @patch.dict(settings.FEATURES, {'ENTRANCE_EXAMS': True, 'ENABLE_MKTG_SITE': True})
    def test_unpassed_entrance_exam(self):
        """
        Tests the case where the user has not passed the entrance exam
        """
        self._add_entrance_exam()
        self.init_course_access()
        self._verify_unfulfilled_milestone_response()

    @patch.dict(settings.FEATURES, {'ENTRANCE_EXAMS': True, 'ENABLE_MKTG_SITE': True})
    def test_unpassed_entrance_exam_for_staff(self):
        self._add_entrance_exam()
        self.user.is_staff = True
        self.user.save()
        self.init_course_access()
        self.api_response()

    @patch.dict(settings.FEATURES, {'ENTRANCE_EXAMS': True, 'ENABLE_MKTG_SITE': True})
    def test_passed_entrance_exam(self):
        """
        Tests access when user has passed the entrance exam
        """
        self._add_entrance_exam()
        self._pass_entrance_exam()
        self.init_course_access()
        self.api_response()

    def _add_entrance_exam(self):
        """ Sets up entrance exam """
        self.course.entrance_exam_enabled = True

        self.entrance_exam = ItemFactory.create(  # pylint: disable=attribute-defined-outside-init
            parent=self.course,
            category="chapter",
            display_name="Entrance Exam Chapter",
            is_entrance_exam=True,
            in_entrance_exam=True
        )
        self.problem_1 = ItemFactory.create(  # pylint: disable=attribute-defined-outside-init
            parent=self.entrance_exam,
            category='problem',
            display_name="The Only Exam Problem",
            graded=True,
            in_entrance_exam=True
        )

        add_entrance_exam_milestone(self.course, self.entrance_exam)

        self.course.entrance_exam_minimum_score_pct = 0.50
        self.course.entrance_exam_id = unicode(self.entrance_exam.location)
        modulestore().update_item(self.course, self.user.id)

    def _add_prerequisite_course(self):
        """ Helper method to set up the prerequisite course """
        self.prereq_course = CourseFactory.create()  # pylint: disable=attribute-defined-outside-init
        add_prerequisite_course(self.course.id, self.prereq_course.id)

    def _pass_entrance_exam(self):
        """ Helper function to pass the entrance exam """
        request = get_request_for_user(self.user)
        answer_entrance_exam_problem(self.course, request, self.problem_1)

    def _verify_unfulfilled_milestone_response(self):
        """
        Verifies the response depending on ALLOW_ACCESS_TO_MILESTONE_COURSE

        Since different endpoints will have different behaviours towards milestones,
        setting ALLOW_ACCESS_TO_MILESTONE_COURSE (default is False) to True, will
        not return a 404. For example, when getting a list of courses a user is
        enrolled in, although a user may have unfulfilled milestones, the course
        should still show up in the course enrollments list.
        """
        if self.ALLOW_ACCESS_TO_MILESTONE_COURSE:
            self.api_response()
        else:
            response = self.api_response(expected_response_code=404)
            self.assertEqual(response.data, MilestoneError().to_json())
