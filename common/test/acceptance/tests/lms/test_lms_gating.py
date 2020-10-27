# -*- coding: utf-8 -*-
"""
End-to-end tests for the gating feature.
"""
from textwrap import dedent

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.lms.course_home import CourseHomePage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.problem import ProblemPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage as StudioCourseOutlinePage
from common.test.acceptance.tests.helpers import UniqueCourseTest


class GatingTest(UniqueCourseTest):
    """
    Test gating feature in LMS.
    """
    STAFF_USERNAME = "STAFF_TESTER"
    STAFF_EMAIL = "staff101@example.com"

    STUDENT_USERNAME = "STUDENT_TESTER"
    STUDENT_EMAIL = "student101@example.com"

    def setUp(self):
        super(GatingTest, self).setUp()

        self.logout_page = LogoutPage(self.browser)
        self.course_home_page = CourseHomePage(self.browser, self.course_id)
        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.studio_course_outline = StudioCourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        xml = dedent("""
        <problem>
        <p>What is height of eiffel tower without the antenna?.</p>
        <multiplechoiceresponse>
          <choicegroup label="What is height of eiffel tower without the antenna?" type="MultipleChoice">
            <choice correct="false">324 meters<choicehint>Antenna is 24 meters high</choicehint></choice>
            <choice correct="true">300 meters</choice>
            <choice correct="false">224 meters</choice>
            <choice correct="false">400 meters</choice>
          </choicegroup>
        </multiplechoiceresponse>
        </problem>
        """)
        self.problem1 = XBlockFixtureDesc('problem', 'HEIGHT OF EIFFEL TOWER', data=xml)

        # Install a course with sections/problems
        course_fixture = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )
        course_fixture.add_advanced_settings({
            "enable_subsection_gating": {"value": "true"}, 'enable_proctored_exams': {"value": "true"}
        })

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1').add_children(
                    self.problem1
                ),
                XBlockFixtureDesc('sequential', 'Test Subsection 2').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 2')
                ),
                XBlockFixtureDesc('sequential', 'Test Subsection 3').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 3')
                ),

            )
        ).install()

    def _auto_auth(self, username, email, staff):
        """
        Logout and login with given credentials.
        """
        self.logout_page.visit()
        AutoAuthPage(self.browser, username=username, email=email,
                     course_id=self.course_id, staff=staff).visit()

    def _setup_prereq(self):
        """
        Make the first subsection a prerequisite
        """
        # Login as staff
        self._auto_auth(self.STAFF_USERNAME, self.STAFF_EMAIL, True)

        # Make the first subsection a prerequisite
        self.studio_course_outline.visit()
        self.studio_course_outline.open_subsection_settings_dialog(0)
        self.studio_course_outline.select_advanced_tab(desired_item='gated_content')
        self.studio_course_outline.make_gating_prerequisite()

    def _setup_gated_subsection(self, subsection_index=1):
        """
        Gate the given indexed subsection on the first subsection
        """
        # Login as staff
        self._auto_auth(self.STAFF_USERNAME, self.STAFF_EMAIL, True)

        # Gate the second subsection based on the score achieved in the first subsection
        self.studio_course_outline.visit()
        self.studio_course_outline.open_subsection_settings_dialog(subsection_index)
        self.studio_course_outline.select_advanced_tab(desired_item='gated_content')
        self.studio_course_outline.add_prerequisite_to_subsection("80", "")

    def _fulfill_prerequisite(self):
        """
        Fulfill the prerequisite needed to see gated content
        """
        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.wait_for_page().problem_name, 'HEIGHT OF EIFFEL TOWER')
        problem_page.click_choice('choice_1')
        problem_page.click_submit()

    def test_subsection_gating_in_studio(self):
        """
        Given that I am a staff member
        When I visit the course outline page in studio.
        And open the subsection edit dialog
        Then I can view all settings related to Gating
        And update those settings to gate a subsection
        """
        self._setup_prereq()

        # Assert settings are displayed correctly for a prerequisite subsection
        self.studio_course_outline.visit()
        self.studio_course_outline.open_subsection_settings_dialog(0)
        self.studio_course_outline.select_advanced_tab(desired_item='gated_content')
        self.assertTrue(self.studio_course_outline.gating_prerequisite_checkbox_is_visible())
        self.assertTrue(self.studio_course_outline.gating_prerequisite_checkbox_is_checked())
        self.assertFalse(self.studio_course_outline.gating_prerequisites_dropdown_is_visible())
        self.assertFalse(self.studio_course_outline.gating_prerequisite_min_score_is_visible())

        self._setup_gated_subsection()

        # Assert settings are displayed correctly for a gated subsection
        self.studio_course_outline.visit()
        self.studio_course_outline.open_subsection_settings_dialog(1)
        self.studio_course_outline.select_advanced_tab(desired_item='gated_content')
        self.assertTrue(self.studio_course_outline.gating_prerequisite_checkbox_is_visible())
        self.assertTrue(self.studio_course_outline.gating_prerequisites_dropdown_is_visible())
        self.assertTrue(self.studio_course_outline.gating_prerequisite_min_score_is_visible())

    def test_gated_subsection_in_lms_for_student(self):
        """
        Given that I am a student
        When I visit the LMS Courseware
        Then I can see a gated subsection
            The gated subsection should have a lock icon
            and be in the format: "<Subsection Title> (Prerequisite Required)"
        When I fulfill the gating Prerequisite
        Then I can see the gated subsection
            Now the gated subsection should have an unlock icon
            and screen readers should read the section as: "<Subsection Title> Unlocked"
        """
        self._setup_prereq()
        self._setup_gated_subsection()

        self._auto_auth(self.STUDENT_USERNAME, self.STUDENT_EMAIL, False)

        self.course_home_page.visit()
        self.assertEqual(self.course_home_page.outline.num_subsections, 3)

        # Fulfill prerequisite and verify that gated subsection is shown
        self.courseware_page.visit()
        self._fulfill_prerequisite()
        self.course_home_page.visit()
        self.assertEqual(self.course_home_page.outline.num_subsections, 3)

    def test_gated_subsection_in_lms_for_staff(self):
        """
        Given that I am a staff member
        When I visit the LMS Courseware
        Then I can see all gated subsections
        Displayed along with notification banners
        Then if I masquerade as a student
        Then I can see a gated subsection
            The gated subsection should have a lock icon
            and be in the format: "<Subsection Title> (Prerequisite Required)"
        """
        self._setup_prereq()
        self._setup_gated_subsection()

        self._auto_auth(self.STAFF_USERNAME, self.STAFF_EMAIL, True)

        self.course_home_page.visit()
        self.assertEqual(self.course_home_page.preview.staff_view_mode, 'Staff')
        self.assertEqual(self.course_home_page.outline.num_subsections, 3)

        # Click on gated section and check for banner
        self.course_home_page.outline.go_to_section('Test Section 1', 'Test Subsection 2')
        self.courseware_page.wait_for_page()
        self.assertTrue(self.courseware_page.has_banner())

        self.course_home_page.visit()
        self.course_home_page.outline.go_to_section('Test Section 1', 'Test Subsection 1')
        self.courseware_page.wait_for_page()

        self.course_home_page.visit()
        self.course_home_page.preview.set_staff_view_mode('Learner')
        self.course_home_page.wait_for_page()
        self.assertEqual(self.course_home_page.outline.num_subsections, 3)
        self.course_home_page.outline.go_to_section('Test Section 1', 'Test Subsection 1')
        self.courseware_page.wait_for_page()
        # banner displayed informing section is a prereq
        self.assertTrue(self.courseware_page.has_banner())

    def test_gated_banner_before_special_exam(self):
        """
        When a subsection with a prereq is a special
        exam, show the gating banner before starting
        the special exam.

            Setup the course with a subsection having pre-req
            Subsection with pre-req is a special exam
            Go the LMS course outline page
            Click the special exam subsection
                The gated banner asking for completing
                prereqs should be visible
            Go to the required subsection
            Fulfill the requirements
            Visit the special exam subsection again
                The gated banner is not visible anymore
                and user can start the special exam
        """

        self._setup_prereq()

        # Gating subsection 1 and making it a timed exam
        self._setup_gated_subsection()
        self.studio_course_outline.open_subsection_settings_dialog(1)
        self.studio_course_outline.select_advanced_tab()
        self.studio_course_outline.make_exam_timed()

        # Gating subsection 2 and making it a proctored exam
        self._setup_gated_subsection(2)
        self.studio_course_outline.open_subsection_settings_dialog(2)
        self.studio_course_outline.select_advanced_tab()
        self.studio_course_outline.make_exam_proctored()

        self._auto_auth(self.STUDENT_USERNAME, self.STUDENT_EMAIL, False)
        self.course_home_page.visit()

        # Test gating banner before starting timed exam
        self.course_home_page.outline.go_to_section('Test Section 1', 'Test Subsection 2')
        self.assertTrue(self.courseware_page.is_gating_banner_visible())

        # Test gating banner before proctored exams
        self.course_home_page.visit()
        self.course_home_page.outline.go_to_section('Test Section 1', 'Test Subsection 3')
        self.assertTrue(self.courseware_page.is_gating_banner_visible())

        # Fulfill requirements
        self.course_home_page.visit()
        self.course_home_page.outline.go_to_section('Test Section 1', 'Test Subsection 1')
        self._fulfill_prerequisite()

        # Banner is not visible anymore on timed exam sub-section
        self.course_home_page.visit()
        self.course_home_page.outline.go_to_section('Test Section 1', 'Test Subsection 2')
        self.assertFalse(self.courseware_page.is_gating_banner_visible())

        # Banner is not visible on proctored exam subsection
        self.course_home_page.visit()
        self.course_home_page.outline.go_to_section('Test Section 1', 'Test Subsection 3')
        self.assertFalse(self.courseware_page.is_gating_banner_visible())
