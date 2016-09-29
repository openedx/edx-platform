"""
Bok choy acceptance tests for conditionals in the LMS
"""
from capa.tests.response_xml_factory import StringResponseXMLFactory
from common.test.acceptance.tests.helpers import UniqueCourseTest
from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.conditional import ConditionalPage, POLL_ANSWER
from common.test.acceptance.pages.lms.problem import ProblemPage
from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage


class ConditionalTest(UniqueCourseTest):
    """
    Test the conditional module in the lms.
    """

    def setUp(self):
        super(ConditionalTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        AutoAuthPage(
            self.browser,
            course_id=self.course_id,
            staff=False
        ).visit()

    def install_course_fixture(self, block_type='problem'):
        """
        Install a course fixture
        """
        course_fixture = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name'],
        )
        vertical = XBlockFixtureDesc('vertical', 'Test Unit')
        # populate the course fixture with the right conditional modules
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    vertical
                )
            )
        )
        course_fixture.install()

        # Construct conditional block
        source_block = None
        conditional_attr = None
        conditional_value = None
        if block_type == 'problem':
            problem_factory = StringResponseXMLFactory()
            problem_xml = problem_factory.build_xml(
                question_text='The answer is "correct string"',
                case_sensitive=False,
                answer='correct string',
            ),
            problem = XBlockFixtureDesc('problem', 'Test Problem', data=problem_xml[0])
            source_block = problem
            conditional_attr = 'attempted'
            conditional_value = 'True'
        elif block_type == 'poll':
            poll = XBlockFixtureDesc(
                'poll_question',
                'Conditional Poll',
                question='Is this a good poll?',
                answers=[
                    {'id': 'yes', 'text': POLL_ANSWER},
                    {'id': 'no', 'text': 'Of course not!'}
                ],
            )
            conditional_attr = 'poll_answer'
            conditional_value = 'yes'
            source_block = poll
        else:
            raise NotImplementedError()

        course_fixture.create_xblock(vertical.locator, source_block)
        # create conditional
        conditional = XBlockFixtureDesc(
            'conditional',
            'Test Conditional',
            sources_list=[source_block.locator],
            conditional_attr=conditional_attr,
            conditional_value=conditional_value
        )
        result_block = XBlockFixtureDesc(
            'html', 'Conditional Contents',
            data='<html><div class="hidden-contents">Hidden Contents</p></html>'
        )
        course_fixture.create_xblock(vertical.locator, conditional)
        course_fixture.create_xblock(conditional.locator, result_block)

    def test_conditional_hides_content(self):
        self.install_course_fixture()
        self.courseware_page.visit()
        conditional_page = ConditionalPage(self.browser)
        self.assertFalse(conditional_page.is_content_visible())

    def test_conditional_displays_content(self):
        self.install_course_fixture()
        self.courseware_page.visit()
        # Answer the problem
        problem_page = ProblemPage(self.browser)
        problem_page.fill_answer('correct string')
        problem_page.click_check()
        # The conditional does not update on its own, so we need to reload the page.
        self.courseware_page.visit()
        # Verify that we can see the content.
        conditional_page = ConditionalPage(self.browser)
        self.assertTrue(conditional_page.is_content_visible())

    def test_conditional_handles_polls(self):
        self.install_course_fixture(block_type='poll')
        self.courseware_page.visit()
        # Fill in the conditional page poll
        conditional_page = ConditionalPage(self.browser)
        conditional_page.fill_in_poll()
        # The conditional does not update on its own, so we need to reload the page.
        self.courseware_page.visit()
        self.assertTrue(conditional_page.is_content_visible())
