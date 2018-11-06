# -*- coding: utf-8 -*-
"""
Bok choy acceptance tests for Entrance exams in the LMS
"""
from textwrap import dedent

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.tests.helpers import UniqueCourseTest


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
        outline = course_fixture.studio_course_outline_as_json
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
