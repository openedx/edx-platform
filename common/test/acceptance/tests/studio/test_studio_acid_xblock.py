"""
Acceptance tests for Studio related to the acid xblock.
"""
from unittest import skip
from bok_choy.web_app_test import WebAppTest

from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.xblock.acid import AcidView
from ...fixtures.course import CourseFixture, XBlockFixtureDesc


class XBlockAcidBase(WebAppTest):
    """
    Base class for tests that verify that XBlock integration is working correctly
    """
    __test__ = False

    def setUp(self):
        """
        Create a unique identifier for the course used in this test.
        """
        # Ensure that the superclass sets up
        super(XBlockAcidBase, self).setUp()

        # Define a unique course identifier
        self.course_info = {
            'org': 'test_org',
            'number': 'course_' + self.unique_id[:5],
            'run': 'test_' + self.unique_id,
            'display_name': 'Test Course ' + self.unique_id
        }

        self.outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.course_id = '{org}.{number}.{run}'.format(**self.course_info)

        self.setup_fixtures()

        self.auth_page = AutoAuthPage(
            self.browser,
            staff=False,
            username=self.user.get('username'),
            email=self.user.get('email'),
            password=self.user.get('password')
        )
        self.auth_page.visit()

    def validate_acid_block_preview(self, acid_block):
        """
        Validate the Acid Block's preview
        """
        self.assertTrue(acid_block.init_fn_passed)
        self.assertTrue(acid_block.resource_url_passed)
        self.assertTrue(acid_block.scope_passed('user_state'))
        self.assertTrue(acid_block.scope_passed('user_state_summary'))
        self.assertTrue(acid_block.scope_passed('preferences'))
        self.assertTrue(acid_block.scope_passed('user_info'))

    def test_acid_block_preview(self):
        """
        Verify that all expected acid block tests pass in studio preview
        """

        self.outline.visit()
        subsection = self.outline.section('Test Section').subsection('Test Subsection')
        unit = subsection.toggle_expand().unit('Test Unit').go_to()

        acid_block = AcidView(self.browser, unit.xblocks[0].preview_selector)
        self.validate_acid_block_preview(acid_block)

    def test_acid_block_editor(self):
        """
        Verify that all expected acid block tests pass in studio editor
        """

        self.outline.visit()
        subsection = self.outline.section('Test Section').subsection('Test Subsection')
        unit = subsection.toggle_expand().unit('Test Unit').go_to()

        acid_block = AcidView(self.browser, unit.xblocks[0].edit().editor_selector)
        self.assertTrue(acid_block.init_fn_passed)
        self.assertTrue(acid_block.resource_url_passed)
        self.assertTrue(acid_block.scope_passed('content'))
        self.assertTrue(acid_block.scope_passed('settings'))


class XBlockAcidNoChildTest(XBlockAcidBase):
    """
    Tests of an AcidBlock with no children
    """
    __test__ = True

    def setup_fixtures(self):

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('acid', 'Acid Block')
                    )
                )
            )
        ).install()

        self.user = course_fix.user


class XBlockAcidParentBase(XBlockAcidBase):
    """
    Base class for tests that verify that parent XBlock integration is working correctly
    """
    __test__ = False

    def validate_acid_block_preview(self, acid_block):
        super(XBlockAcidParentBase, self).validate_acid_block_preview(acid_block)
        self.assertTrue(acid_block.child_tests_passed)

    def test_acid_block_preview(self):
        """
        Verify that all expected acid block tests pass in studio preview
        """

        self.outline.visit()
        subsection = self.outline.section('Test Section').subsection('Test Subsection')
        unit = subsection.toggle_expand().unit('Test Unit').go_to()
        container = unit.xblocks[0].go_to_container()

        acid_block = AcidView(self.browser, container.xblocks[0].preview_selector)
        self.validate_acid_block_preview(acid_block)


class XBlockAcidEmptyParentTest(XBlockAcidParentBase):
    """
    Tests of an AcidBlock with children
    """
    __test__ = True

    def setup_fixtures(self):

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('acid_parent', 'Acid Parent Block').add_children(
                        )
                    )
                )
            )
        ).install()

        self.user = course_fix.user


class XBlockAcidChildTest(XBlockAcidParentBase):
    """
    Tests of an AcidBlock with children
    """
    __test__ = True

    def setup_fixtures(self):

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('acid_parent', 'Acid Parent Block').add_children(
                            XBlockFixtureDesc('acid', 'First Acid Child', metadata={'name': 'first'}),
                            XBlockFixtureDesc('acid', 'Second Acid Child', metadata={'name': 'second'}),
                            XBlockFixtureDesc('html', 'Html Child', data="<html>Contents</html>"),
                        )
                    )
                )
            )
        ).install()

        self.user = course_fix.user

    @skip('This will fail until we fix support of children in pure XBlocks')
    def test_acid_block_preview(self):
        super(XBlockAcidChildTest, self).test_acid_block_preview()

    @skip('This will fail until we fix support of children in pure XBlocks')
    def test_acid_block_editor(self):
        super(XBlockAcidChildTest, self).test_acid_block_editor()
