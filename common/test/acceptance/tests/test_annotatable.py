# -*- coding: utf-8 -*-
"""
E2E tests for the LMS.
"""
import time

from unittest import skip

from .helpers import UniqueCourseTest
from ..pages.studio.auto_auth import AutoAuthPage
from ..pages.lms.courseware import CoursewarePage
from ..pages.lms.annotation_component import AnnotationComponentPage
from ..fixtures.course import CourseFixture, XBlockFixtureDesc
from ..fixtures.xqueue import XQueueResponseFixture
from textwrap import dedent


def _correctness(choice, target):
    if choice == target:
        return "correct"
    elif abs(choice - target) == 1:
        return "partially-correct"
    else:
        return "incorrect"


class AnnotatableProblemTest(UniqueCourseTest):
    """
    Tests for annotation components.
    """
    USERNAME = "STAFF_TESTER"
    EMAIL = "johndoe@example.com"

    DATA_TEMPLATE = dedent("""\
        <annotatable>
            <instructions>Instruction text</instructions>
            <p>{}</p>
        </annotatable>
    """)

    ANNOTATION_TEMPLATE = dedent("""\
        Before {0}.
        <annotation title="region {0}" body="Comment {0}" highlight="yellow" problem="{0}">
            Region Contents {0}
        </annotation>
        After {0}.
    """)

    PROBLEM_TEMPLATE = dedent("""\
    <problem max_attempts="1" weight="">
      <annotationresponse>
        <annotationinput>
          <title>Question {number}</title>
          <text>Region Contents {number}</text>
          <comment>What number is this region?</comment>
          <comment_prompt>Type your response below:</comment_prompt>
          <tag_prompt>What number is this region?</tag_prompt>
          <options>
          {options}
          </options>
        </annotationinput>
      </annotationresponse>
      <solution>
        This problem is checking region {number}
      </solution>
    </problem>
    """)

    OPTION_TEMPLATE = """<option choice="{correctness}">{number}</option>"""

    def setUp(self):
        super(AnnotatableProblemTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with two annotations and two annotations problems.
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.annotation_count = 2
        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Annotation Vertical').add_children(
                        XBlockFixtureDesc('annotatable', 'Test Annotation Module',
                                          data=self.DATA_TEMPLATE.format("\n".join(
                                              self.ANNOTATION_TEMPLATE.format(i) for i in xrange(self.annotation_count)
                                          ))),
                        XBlockFixtureDesc('problem', 'Test Annotation Problem 0',
                                          data=self.PROBLEM_TEMPLATE.format(number=0, options="\n".join(
                                              self.OPTION_TEMPLATE.format(
                                                  number=k,
                                                  correctness=_correctness(k, 0))
                                              for k in xrange(self.annotation_count)
                                          ))),
                        XBlockFixtureDesc('problem', 'Test Annotation Problem 1',
                                          data=self.PROBLEM_TEMPLATE.format(number=1, options="\n".join(
                                              self.OPTION_TEMPLATE.format(
                                                  number=k,
                                                  correctness=_correctness(k, 1))
                                              for k in xrange(self.annotation_count)
                                          )))
                    )
                )
            )
        ).install()

        # Auto-auth register for the course.
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL,
                     course_id=self.course_id, staff=False).visit()

    def _goto_annotation_component_page(self):
        """
        Open annotation component page with assertion.
        """
        self.courseware_page.visit()
        annotation_component_page = AnnotationComponentPage(self.browser)
        self.assertEqual(
            annotation_component_page.component_name, 'TEST ANNOTATION MODULE'.format()
        )
        return annotation_component_page

    @skip  # TODO fix TNL-1590
    def test_annotation_component(self):
        """
        Test annotation components links to annotation problems.
        """

        annotation_component_page = self._goto_annotation_component_page()

        for i in xrange(self.annotation_count):
            annotation_component_page.click_reply_annotation(i)
            self.assertTrue(annotation_component_page.check_scroll_to_problem())

            annotation_component_page.answer_problem()
            self.assertTrue(annotation_component_page.check_feedback())

            annotation_component_page.click_return_to_annotation()
            self.assertTrue(annotation_component_page.check_scroll_to_annotation())
