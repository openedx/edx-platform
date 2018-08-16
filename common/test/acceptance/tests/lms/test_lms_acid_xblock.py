# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS.
"""

import pytest

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.xblock.acid import AcidView
from common.test.acceptance.tests.helpers import UniqueCourseTest


class XBlockAcidBase(UniqueCourseTest):
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

        self.setup_fixtures()

        AutoAuthPage(self.browser, course_id=self.course_id).visit()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

    def validate_acid_block_view(self, acid_block):
        """
        Verify that the LMS view for the Acid Block is correct
        """
        self.assertTrue(acid_block.init_fn_passed)
        self.assertTrue(acid_block.resource_url_passed)
        self.assertTrue(acid_block.scope_passed('user_state'))
        self.assertTrue(acid_block.scope_passed('user_state_summary'))
        self.assertTrue(acid_block.scope_passed('preferences'))
        self.assertTrue(acid_block.scope_passed('user_info'))


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

    def test_acid_block(self):
        """
        Verify that all expected acid block tests pass in the lms.
        """
        self.courseware_page.visit()
        acid_block = AcidView(self.browser, '.xblock-student_view[data-block-type=acid]')
        self.validate_acid_block_view(acid_block)


class XBlockAcidChildTest(XBlockAcidBase):
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

    def validate_acid_parent_block_view(self, acid_parent_block):
        super(XBlockAcidChildTest, self).validate_acid_block_view(acid_parent_block)
        self.assertTrue(acid_parent_block.child_tests_passed)

    def test_acid_block(self):
        """
        Verify that all expected acid block tests pass in the lms.
        """
        self.courseware_page.visit()
        acid_parent_block = AcidView(self.browser, '.xblock-student_view[data-block-type=acid_parent]')
        self.validate_acid_parent_block_view(acid_parent_block)

        acid_block = AcidView(self.browser, '.xblock-student_view[data-block-type=acid]')
        self.validate_acid_block_view(acid_block)


@pytest.mark.xfail
class XBlockAcidAsideTest(XBlockAcidBase):
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
                        XBlockFixtureDesc('acid', 'Acid Block')
                    )
                )
            )
        ).install()

    def test_acid_block(self):
        """
        Verify that all expected acid block tests pass in the lms.
        """
        self.courseware_page.visit()
        acid_aside = AcidView(self.browser, '.xblock_asides-v1-student_view[data-block-type=acid_aside]')
        self.validate_acid_aside_view(acid_aside)

        acid_block = AcidView(self.browser, '.xblock-student_view[data-block-type=acid]')
        self.validate_acid_block_view(acid_block)

    def validate_acid_aside_view(self, acid_aside):
        self.validate_acid_block_view(acid_aside)
