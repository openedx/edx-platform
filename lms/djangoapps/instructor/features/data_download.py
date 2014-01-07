"""
Define steps for instructor dashboard - data download tab
acceptance tests.
"""

# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_in, assert_regexp_matches  # pylint: disable=E0611
from terrain.steps import reload_the_page


@step(u'I see a table of student profiles')
def find_student_profile_table(step):  # pylint: disable=unused-argument
    # Find the grading configuration display
    world.wait_for_visible('#data-student-profiles-table')

    # Wait for the data table to be populated
    world.wait_for(lambda _: world.css_text('#data-student-profiles-table') not in [u'', u'Loading...'])

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
Listing grading context for course edx/999/Test_Course
graded sections:
[]
all descriptors:
length=0"""
    assert_in(expected_config, world.css_text('#data-grade-config-text'))


@step(u"I see a csv file in the grade reports table")
def find_grade_report_csv_link(step):  # pylint: disable=unused-argument
    # Need to reload the page to see the grades download table
    reload_the_page(step)
    world.wait_for_visible('#grade-downloads-table')
    # Find table and assert a .csv file is present
    expected_file_regexp = 'edx_999_Test_Course_grade_report_\d{4}-\d{2}-\d{2}-\d{4}\.csv'
    assert_regexp_matches(
        world.css_html('#grade-downloads-table'), expected_file_regexp,
        msg="Expected grade report filename was not found."
    )
