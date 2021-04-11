# -*- coding: utf-8 -*-
"""
Tests the "preview" selector in the LMS that allows changing between Staff, Learner, and Content Groups.
"""


from textwrap import dedent

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.staff_view import StaffCoursewarePage
from common.test.acceptance.tests.helpers import UniqueCourseTest, create_user_partition_json
from openedx.core.lib.tests import attr
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID, MINIMUM_STATIC_PARTITION_ID, Group


@attr(shard=20)
class StaffViewTest(UniqueCourseTest):
    """
    Tests that verify the staff view.
    """
    USERNAME = "STAFF_TESTER"
    EMAIL = "johndoe@example.com"

    def setUp(self):
        super(StaffViewTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with sections/problems, tabs, updates, and handouts
        self.course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.populate_course_fixture(self.course_fixture)

        self.course_fixture.install()

        # Auto-auth register for the course.
        # Do this as global staff so that you will see the Staff View
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL,
                     course_id=self.course_id, staff=True).visit()

    def _goto_staff_page(self):
        """
        Open staff page with assertion
        """
        self.courseware_page.visit()
        staff_page = StaffCoursewarePage(self.browser, self.course_id)
        self.assertEqual(staff_page.staff_view_mode, 'Staff')
        return staff_page


@attr(shard=20)
class CourseWithContentGroupsTest(StaffViewTest):
    """
    Verifies that changing the "View this course as" selector works properly for content groups.
    """

    def setUp(self):
        super(CourseWithContentGroupsTest, self).setUp()
        # pylint: disable=protected-access
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        MINIMUM_STATIC_PARTITION_ID,
                        'Configuration alpha,beta',
                        'Content Group Partition',
                        [
                            Group(MINIMUM_STATIC_PARTITION_ID + 1, 'alpha'),
                            Group(MINIMUM_STATIC_PARTITION_ID + 2, 'beta')
                        ],
                        scheme="cohort"
                    )
                ],
            },
        })

    def populate_course_fixture(self, course_fixture):
        """
        Populates test course with chapter, sequential, and 3 problems.
        One problem is visible to all, one problem is visible only to Group "alpha", and
        one problem is visible only to Group "beta".
        """
        problem_data = dedent("""
            <problem markdown="Simple Problem" max_attempts="" weight="">
              <choiceresponse>
              <label>Choose Yes.</label>
                <checkboxgroup>
                  <choice correct="true">Yes</choice>
                </checkboxgroup>
              </choiceresponse>
            </problem>
        """)

        self.alpha_text = "VISIBLE TO ALPHA"
        self.beta_text = "VISIBLE TO BETA"
        self.audit_text = "VISIBLE TO AUDIT"
        self.everyone_text = "VISIBLE TO EVERYONE"

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc(
                            'problem',
                            self.alpha_text,
                            data=problem_data,
                            metadata={"group_access": {MINIMUM_STATIC_PARTITION_ID: [MINIMUM_STATIC_PARTITION_ID + 1]}}
                        ),
                        XBlockFixtureDesc(
                            'problem',
                            self.beta_text,
                            data=problem_data,
                            metadata={"group_access": {MINIMUM_STATIC_PARTITION_ID: [MINIMUM_STATIC_PARTITION_ID + 2]}}
                        ),
                        XBlockFixtureDesc(
                            'problem',
                            self.audit_text,
                            data=problem_data,
                            # Below 1 is the hardcoded group ID for "Audit"
                            metadata={"group_access": {ENROLLMENT_TRACK_PARTITION_ID: [1]}}
                        ),
                        XBlockFixtureDesc(
                            'problem',
                            self.everyone_text,
                            data=problem_data
                        )
                    )
                )
            )
        )

    @attr('a11y')
    def test_course_page(self):
        """
        Run accessibility audit for course staff pages.
        """
        course_page = self._goto_staff_page()
        course_page.a11y_audit.config.set_rules({
            'ignore': [
                'aria-allowed-attr',  # TODO: AC-559
                'aria-roles',  # TODO: AC-559,
                'aria-valid-attr',  # TODO: AC-559
                'color-contrast',  # TODO: AC-559
                'link-href',  # TODO: AC-559
                'section',  # TODO: AC-559
                'region',  # TODO: AC-932
            ]
        })
        course_page.a11y_audit.check_for_accessibility_errors()
