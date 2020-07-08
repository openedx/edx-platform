# -*- coding: utf-8 -*-
"""
Bok choy acceptance tests for problems in the LMS
"""


from textwrap import dedent

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.problem import ProblemPage
from common.test.acceptance.tests.helpers import UniqueCourseTest
from openedx.core.lib.tests import attr


class ProblemsTest(UniqueCourseTest):
    """
    Base class for tests of problems in the LMS.
    """

    def setUp(self):
        super(ProblemsTest, self).setUp()

        self.username = "test_student_{uuid}".format(uuid=self.unique_id[0:8])
        self.email = "{username}@example.com".format(username=self.username)
        self.password = "keep it secret; keep it safe."

        self.xqueue_grade_response = None

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with a hierarchy and problems
        course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        problem = self.get_problem()
        sequential = self.get_sequential()
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                sequential.add_children(problem)
            )
        ).install()

        # Auto-auth register for the course.
        AutoAuthPage(
            self.browser,
            username=self.username,
            email=self.email,
            password=self.password,
            course_id=self.course_id,
            staff=True
        ).visit()

    def get_problem(self):
        """ Subclasses should override this to complete the fixture """
        raise NotImplementedError()

    def get_sequential(self):
        """ Subclasses can override this to add a sequential with metadata """
        return XBlockFixtureDesc('sequential', 'Test Subsection')


class CAPAProblemA11yBaseTestMixin(object):
    """Base TestCase Class to verify CAPA problem accessibility."""

    def test_a11y(self):
        """
        Verifies that there are no accessibility issues for a particular problem type
        """
        self.courseware_page.visit()
        problem_page = ProblemPage(self.browser)

        # Set the scope to the problem question
        problem_page.a11y_audit.config.set_scope(
            include=['.wrapper-problem-response']
        )

        # Run the accessibility audit.
        problem_page.a11y_audit.check_for_accessibility_errors()


@attr('a11y')
class CAPAProblemChoiceA11yTest(CAPAProblemA11yBaseTestMixin, ProblemsTest):
    """TestCase Class to verify accessibility for checkboxes and multiplechoice CAPA problems."""

    def get_problem(self):
        """
        Problem structure.
        """
        xml = dedent("""
        <problem>
            <choiceresponse>
                <label>question 1 text here</label>
                <description>description 2 text 1</description>
                <description>description 2 text 2</description>
                <checkboxgroup>
                    <choice correct="true">True</choice>
                    <choice correct="false">False</choice>
                </checkboxgroup>
            </choiceresponse>
            <multiplechoiceresponse>
                <label>question 2 text here</label>
                <description>description 2 text 1</description>
                <description>description 2 text 2</description>
                <choicegroup type="MultipleChoice">
                    <choice correct="false">Alpha <choicehint>A hint</choicehint></choice>
                    <choice correct="true">Beta</choice>
                </choicegroup>
            </multiplechoiceresponse>
         </problem>
        """)
        return XBlockFixtureDesc('problem', 'Problem A11Y TEST', data=xml)


@attr('a11y')
class ProblemTextInputA11yTest(CAPAProblemA11yBaseTestMixin, ProblemsTest):
    """TestCase Class to verify TextInput problem accessibility."""

    def get_problem(self):
        """
        TextInput problem XML.
        """
        xml = dedent("""
        <problem>
            <stringresponse answer="fight" type="ci">
                <label>who wishes to _____ must first count the cost.</label>
                <description>Appear weak when you are strong, and strong when you are weak.</description>
                <description>In the midst of chaos, there is also opportunity.</description>
                <textline size="40"/>
            </stringresponse>
            <stringresponse answer="force" type="ci">
                <label>A leader leads by example not by _____.</label>
                <description>The supreme art of war is to subdue the enemy without fighting.</description>
                <description>Great results, can be achieved with small forces.</description>
                <textline size="40"/>
            </stringresponse>
        </problem>""")
        return XBlockFixtureDesc('problem', 'TEXTINPUT PROBLEM', data=xml)


@attr('a11y')
class CAPAProblemDropDownA11yTest(CAPAProblemA11yBaseTestMixin, ProblemsTest):
    """TestCase Class to verify accessibility for dropdowns(optioninput) CAPA problems."""

    def get_problem(self):
        """
        Problem structure.
        """
        xml = dedent("""
        <problem>
            <optionresponse>
                <p>You can use this template as a guide to the simple editor markdown and OLX markup to use for
                 dropdown problems. Edit this component to replace this template with your own assessment.</p>
                <label>Which of the following is a fruit</label>
                <description>Choose wisely</description>
                <optioninput>
                    <option correct="False">radish</option>
                    <option correct="True">appple</option>
                    <option correct="False">carrot</option>
                </optioninput>
            </optionresponse>
        </problem>
        """)
        return XBlockFixtureDesc('problem', 'Problem A11Y TEST', data=xml)


@attr('a11y')
class ProblemNumericalInputA11yTest(CAPAProblemA11yBaseTestMixin, ProblemsTest):
    """Tests NumericalInput accessibility."""

    def get_problem(self):
        """NumericalInput problem XML."""
        xml = dedent("""
        <problem>
            <numericalresponse answer="10*i">
                <label>The square of what number is -100?</label>
                <description>Use scientific notation to answer.</description>
                <formulaequationinput/>
            </numericalresponse>
        </problem>""")
        return XBlockFixtureDesc('problem', 'NUMERICALINPUT PROBLEM', data=xml)


@attr('a11y')
class ProblemMathExpressionInputA11yTest(CAPAProblemA11yBaseTestMixin, ProblemsTest):
    """Tests MathExpressionInput accessibility."""

    def get_problem(self):
        """MathExpressionInput problem XML."""
        xml = dedent(r"""
        <problem>
            <script type="loncapa/python">
        derivative = "n*x^(n-1)"
            </script>

            <formularesponse type="ci" samples="x,n@1,2:3,4#10" answer="$derivative">
                <label>Let \( x\) be a variable, and let \( n\) be an arbitrary constant. What is the derivative of \( x^n\)?</label>
                <description>Enter the equation</description>
                <responseparam type="tolerance" default="0.00001"/>
                <formulaequationinput size="40"/>
            </formularesponse>
        </problem>""")
        return XBlockFixtureDesc('problem', 'MATHEXPRESSIONINPUT PROBLEM', data=xml)
