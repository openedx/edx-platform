"""
Define steps for instructor dashboard - data download tab
acceptance tests.
"""

# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from nose.tools import assert_in, assert_regexp_matches  # pylint: disable=no-name-in-module
from terrain.steps import reload_the_page
from django.utils import http


@step(u'I see a table of student profiles')
def find_student_profile_table(step):  # pylint: disable=unused-argument
    # Find the grading configuration display
    world.wait_for_visible('#data-student-profiles-table')

    # Wait for the data table to be populated
    world.wait_for(lambda _: world.css_text('#data-student-profiles-table') not in [u'', u'Loading'])

    if world.role == 'instructor':
        expected_data = [
            world.instructor.username,
            world.instructor.email,
            world.instructor.profile.name,
            world.instructor.profile.gender,
            world.instructor.profile.goals
        ]
    elif world.role == 'staff':
        expected_data = [
            world.staff.username,
            world.staff.email,
            world.staff.profile.name,
            world.staff.profile.gender,
            world.staff.profile.goals
        ]
    for datum in expected_data:
        assert_in(datum, world.css_text('#data-student-profiles-table'))


@step(u"I do not see a button to 'List enrolled students' profile information'")
def no_student_profile_table(step):  # pylint: disable=unused-argument
    world.is_css_not_present('input[name="list-profiles"]')


@step(u"I see the grading configuration for the course")
def find_grading_config(step):  # pylint: disable=unused-argument
    # Find the grading configuration display
    world.wait_for_visible('#data-grade-config-text')
    # expected config is the default grading configuration from common/lib/xmodule/xmodule/course_module.py
    expected_config = u"""-----------------------------------------------------------------------------
Course grader:
<class 'xmodule.graders.WeightedSubsectionsGrader'>

Graded sections:
  subgrader=<class 'xmodule.graders.AssignmentFormatGrader'>, type=Homework, category=Homework, weight=0.15
  subgrader=<class 'xmodule.graders.AssignmentFormatGrader'>, type=Lab, category=Lab, weight=0.15
  subgrader=<class 'xmodule.graders.AssignmentFormatGrader'>, type=Midterm Exam, category=Midterm Exam, weight=0.3
  subgrader=<class 'xmodule.graders.AssignmentFormatGrader'>, type=Final Exam, category=Final Exam, weight=0.4
-----------------------------------------------------------------------------
Listing grading context for course {}
graded sections:
[]
all descriptors:
length=0""".format(world.course_key)
    assert_in(expected_config, world.css_text('#data-grade-config-text'))


def verify_report_is_generated(report_name_substring):
    # Need to reload the page to see the reports table updated
    reload_the_page(step)
    world.wait_for_visible('#report-downloads-table')
    # Find table and assert a .csv file is present
    quoted_id = http.urlquote(world.course_key).replace('/', '_')
    expected_file_regexp = quoted_id + '_' + report_name_substring + '_\d{4}-\d{2}-\d{2}-\d{4}\.csv'
    assert_regexp_matches(
        world.css_html('#report-downloads-table'), expected_file_regexp,
        msg="Expected report filename was not found."
    )


@step(u"I see a grade report csv file in the reports table")
def find_grade_report_csv_link(step):  # pylint: disable=unused-argument
    verify_report_is_generated('grade_report')


@step(u"I see a student profile csv file in the reports table")
def find_student_profile_report_csv_link(step):  # pylint: disable=unused-argument
    verify_report_is_generated('student_profile_info')
