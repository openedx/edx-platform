# -*- coding: utf-8 -*-
"""
Bok choy acceptance tests for Entrance exams in the LMS
"""
from textwrap import dedent

from common.test.acceptance.tests.helpers import UniqueCourseTest
from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.problem import ProblemPage
from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc


class EntranceExamTest(UniqueCourseTest):
    """
    Base class for tests of Entrance Exams in the LMS.
    """
    USERNAME = "joe_student"
    EMAIL = "joe@example.com"

    def setUp(self):
        super(EntranceExamTest, self).setUp()

        self.xqueue_grade_response = None

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with a hierarchy and problems
        course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name'],
            settings={
                'entrance_exam_enabled': 'true',
                'entrance_exam_minimum_score_pct': '50'
            }
        )

        problem = self.get_problem()
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(problem)
            )
        ).install()

        entrance_exam_subsection = None
        outline = course_fixture.course_outline
        for child in outline['child_info']['children']:
            if child.get('display_name') == "Entrance Exam":
                entrance_exam_subsection = child['child_info']['children'][0]

        if entrance_exam_subsection:
            course_fixture.create_xblock(entrance_exam_subsection['id'], problem)

        # Auto-auth register for the course.
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL,
                     course_id=self.course_id, staff=False).visit()

    def get_problem(self):
        """ Subclasses should override this to complete the fixture """
        raise NotImplementedError()


class EntranceExamPassTest(EntranceExamTest):
    """
    Tests the scenario when a student passes entrance exam.
    """

    def get_problem(self):
        """
        Create a multiple choice problem
        """
        xml = dedent("""
        <problem>
        <multiplechoiceresponse>
          <label>What is height of eiffel tower without the antenna?.</label>
          <choicegroup type="MultipleChoice">
            <choice correct="false">324 meters<choicehint>Antenna is 24 meters high</choicehint></choice>
            <choice correct="true">300 meters</choice>
            <choice correct="false">224 meters</choice>
            <choice correct="false">400 meters</choice>
          </choicegroup>
        </multiplechoiceresponse>
        </problem>
        """)
        return XBlockFixtureDesc('problem', 'HEIGHT OF EIFFEL TOWER', data=xml)

    def test_course_is_unblocked_as_soon_as_student_passes_entrance_exam(self):
        """
        Scenario: Ensure that entrance exam status message is updated and courseware is unblocked as soon as
        student passes entrance exam.
        Given I have a course with entrance exam as pre-requisite
        When I pass entrance exam
        Then I can see complete TOC of course
        And I can see message indicating my pass status
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.wait_for_page().problem_name, 'HEIGHT OF EIFFEL TOWER')
        self.assertTrue(self.courseware_page.has_entrance_exam_message())
        self.assertFalse(self.courseware_page.has_passed_message())
        problem_page.click_choice('choice_1')
        problem_page.click_submit()
        self.courseware_page.wait_for_page()
        self.assertTrue(self.courseware_page.has_passed_message())
        self.assertEqual(self.courseware_page.chapter_count_in_navigation, 2)
