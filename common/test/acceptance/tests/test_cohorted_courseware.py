"""
End-to-end test for cohorted courseware. This uses both Studio and LMS.
"""

from bok_choy.page_object import XSS_INJECTION

from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.common.utils import add_enrollment_course_modes, enroll_user_track
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.instructor_dashboard import InstructorDashboardPage
from common.test.acceptance.pages.studio.settings_group_configurations import GroupConfigurationsPage
from common.test.acceptance.pages.studio.xblock_editor import XBlockVisibilityEditorView
from common.test.acceptance.tests.discussion.helpers import CohortTestMixin
from common.test.acceptance.tests.lms.test_lms_user_preview import verify_expected_problem_visibility
from studio.base_studio_test import ContainerBase

AUDIT_TRACK = "Audit"
VERIFIED_TRACK = "Verified"


class EndToEndCohortedCoursewareTest(ContainerBase, CohortTestMixin):
    """
    End-to-end of cohorted courseware.
    """
    shard = 5

    def setUp(self, is_staff=True):

        super(EndToEndCohortedCoursewareTest, self).setUp(is_staff=is_staff)
        self.staff_user = self.user

        self.content_group_a = "Content Group A" + XSS_INJECTION
        self.content_group_b = "Content Group B" + XSS_INJECTION

        # Creates the Course modes needed to test enrollment tracks
        add_enrollment_course_modes(self.browser, self.course_id, ["audit", "verified"])

        # Create a student who will be in "Cohort A"
        self.cohort_a_student_username = "cohort_a_student"
        self.cohort_a_student_email = "cohort_a_student@example.com"
        AutoAuthPage(
            self.browser, username=self.cohort_a_student_username, email=self.cohort_a_student_email, no_login=True
        ).visit()

        # Create a student who will be in "Cohort B"
        self.cohort_b_student_username = "cohort_b_student"
        self.cohort_b_student_email = "cohort_b_student@example.com"
        AutoAuthPage(
            self.browser, username=self.cohort_b_student_username, email=self.cohort_b_student_email, no_login=True
        ).visit()

        # Create a Verified Student
        self.cohort_verified_student_username = "cohort_verified_student"
        self.cohort_verified_student_email = "cohort_verified_student@example.com"
        AutoAuthPage(
            self.browser,
            username=self.cohort_verified_student_username,
            email=self.cohort_verified_student_email,
            no_login=True
        ).visit()

        # Create audit student
        self.cohort_audit_student_username = "cohort_audit_student"
        self.cohort_audit_student_email = "cohort_audit_student@example.com"
        AutoAuthPage(
            self.browser,
            username=self.cohort_audit_student_username,
            email=self.cohort_audit_student_email,
            no_login=True
        ).visit()

        # Create a student who will end up in the default cohort group
        self.cohort_default_student_username = "cohort_default_student"
        self.cohort_default_student_email = "cohort_default_student@example.com"
        AutoAuthPage(
            self.browser, username=self.cohort_default_student_username,
            email=self.cohort_default_student_email, no_login=True
        ).visit()

        # Start logged in as the staff user.
        AutoAuthPage(
            self.browser, username=self.staff_user["username"], email=self.staff_user["email"]
        ).visit()

    def populate_course_fixture(self, course_fixture):
        """
        Populate the children of the test course fixture.
        """
        self.group_a_problem = 'GROUP A CONTENT'
        self.group_b_problem = 'GROUP B CONTENT'
        self.group_verified_problem = 'GROUP VERIFIED CONTENT'
        self.group_audit_problem = 'GROUP AUDIT CONTENT'

        self.group_a_and_b_problem = 'GROUP A AND B CONTENT'

        self.visible_to_all_problem = 'VISIBLE TO ALL CONTENT'
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('problem', self.group_a_problem, data='<problem></problem>'),
                        XBlockFixtureDesc('problem', self.group_b_problem, data='<problem></problem>'),
                        XBlockFixtureDesc('problem', self.group_verified_problem, data='<problem></problem>'),
                        XBlockFixtureDesc('problem', self.group_audit_problem, data='<problem></problem>'),
                        XBlockFixtureDesc('problem', self.group_a_and_b_problem, data='<problem></problem>'),
                        XBlockFixtureDesc('problem', self.visible_to_all_problem, data='<problem></problem>')
                    )
                )
            )
        )

    def create_content_groups(self):
        """
        Creates two content groups in Studio Group Configurations Settings.
        """
        group_configurations_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        group_configurations_page.visit()

        group_configurations_page.create_first_content_group()
        config = group_configurations_page.content_groups[0]
        config.name = self.content_group_a
        config.save()

        group_configurations_page.add_content_group()
        config = group_configurations_page.content_groups[1]
        config.name = self.content_group_b
        config.save()

    def link_problems_to_content_groups_and_publish(self):
        """
        Updates 5 of the 6 existing problems to limit their visibility by content group.
        Publishes the modified units.
        """
        container_page = self.go_to_unit_page()
        enrollment_group = 'enrollment_track_group'

        def set_visibility(problem_index, groups, group_partition='content_group'):
            problem = container_page.xblocks[problem_index]
            problem.edit_visibility()
            visibility_dialog = XBlockVisibilityEditorView(self.browser, problem.locator)
            partition_name = (visibility_dialog.ENROLLMENT_TRACK_PARTITION
                              if group_partition == enrollment_group
                              else visibility_dialog.CONTENT_GROUP_PARTITION)
            visibility_dialog.select_groups_in_partition_scheme(partition_name, groups)

        set_visibility(1, [self.content_group_a])
        set_visibility(2, [self.content_group_b])
        set_visibility(3, [VERIFIED_TRACK], enrollment_group)
        set_visibility(4, [AUDIT_TRACK], enrollment_group)
        set_visibility(5, [self.content_group_a, self.content_group_b])

        container_page.publish_action.click()

    def create_cohorts_and_assign_students(self):
        """
        Adds 2 manual cohorts, linked to content groups, to the course.
        Each cohort is assigned one student.
        """
        instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        instructor_dashboard_page.visit()
        cohort_management_page = instructor_dashboard_page.select_cohort_management()

        def add_cohort_with_student(cohort_name, content_group, student):
            cohort_management_page.add_cohort(cohort_name, content_group=content_group)
            cohort_management_page.add_students_to_selected_cohort([student])

        add_cohort_with_student("Cohort A", self.content_group_a, self.cohort_a_student_username)
        add_cohort_with_student("Cohort B", self.content_group_b, self.cohort_b_student_username)

    def view_cohorted_content_as_different_users(self):
        """
        View content as staff, student in Cohort A, student in Cohort B, Verified Student, Audit student,
        and student in Default Cohort.
        """
        courseware_page = CoursewarePage(self.browser, self.course_id)

        def login_and_verify_visible_problems(username, email, expected_problems, track=None):
            AutoAuthPage(
                self.browser, username=username, email=email, course_id=self.course_id
            ).visit()
            if track is not None:
                enroll_user_track(self.browser, self.course_id, track)
            courseware_page.visit()
            verify_expected_problem_visibility(self, courseware_page, expected_problems)

        login_and_verify_visible_problems(
            self.staff_user["username"], self.staff_user["email"],
            [self.group_a_problem,
             self.group_b_problem,
             self.group_verified_problem,
             self.group_audit_problem,
             self.group_a_and_b_problem,
             self.visible_to_all_problem
             ],
        )

        login_and_verify_visible_problems(
            self.cohort_a_student_username, self.cohort_a_student_email,
            [self.group_a_problem, self.group_audit_problem, self.group_a_and_b_problem, self.visible_to_all_problem]
        )

        login_and_verify_visible_problems(
            self.cohort_b_student_username, self.cohort_b_student_email,
            [self.group_b_problem, self.group_audit_problem, self.group_a_and_b_problem, self.visible_to_all_problem]
        )

        login_and_verify_visible_problems(
            self.cohort_verified_student_username, self.cohort_verified_student_email,
            [self.group_verified_problem, self.visible_to_all_problem],
            'verified'
        )

        login_and_verify_visible_problems(
            self.cohort_audit_student_username, self.cohort_audit_student_email,
            [self.group_audit_problem, self.visible_to_all_problem],
            'audit'
        )

        login_and_verify_visible_problems(
            self.cohort_default_student_username, self.cohort_default_student_email,
            [self.group_audit_problem, self.visible_to_all_problem],
        )

    def test_cohorted_courseware(self):
        """
        Scenario: Can create content that is only visible to students in particular cohorts
          Given that I have course with 6 problems, 1 staff member, and 6 students
          When I enable cohorts in the course
          And I add the Course Modes for Verified and Audit
          And I create two content groups, Content Group A, and Content Group B, in the course
          And I link one problem to Content Group A
          And I link one problem to Content Group B
          And I link one problem to the Verified Group
          And I link one problem to the Audit Group
          And I link one problem to both Content Group A and Content Group B
          And one problem remains unlinked to any Content Group
          And I create two manual cohorts, Cohort A and Cohort B,
            linked to Content Group A and Content Group B, respectively
          And I assign one student to each manual cohort
          And I assign one student to each enrollment track
          And one student remains in the default cohort
          Then the staff member can see all 6 problems
          And the student in Cohort A can see all the problems linked to A
          And the student in Cohort B can see all the problems linked to B
          And the student in Verified can see the problems linked to Verified and those not linked to a Group
          And the student in Audit can see the problems linked to Audit and those not linked to a Group
          And the student in the default cohort can ony see the problem that is unlinked to any Content Group
        """
        self.enable_cohorting(self.course_fixture)
        self.create_content_groups()
        self.link_problems_to_content_groups_and_publish()
        self.create_cohorts_and_assign_students()
        self.view_cohorted_content_as_different_users()
