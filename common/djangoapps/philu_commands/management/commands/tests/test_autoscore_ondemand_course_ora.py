"""
Tests for autoscore ondemand course ora command.
"""
import factory
import mock
import pytest
from django.core.management import call_command

from openassessment.workflow import api as workflow_api
from openassessment.workflow.models import AssessmentWorkflow
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.features.assessment.tests.factories import SubmissionFactory
from student.tests.factories import CourseEnrollmentFactory


@pytest.fixture(
    params=['on_demand_active_enrollments', 'on_demand_inactive_enrollments', 'instructor_paced_enrollments']
)
def expected_enrollments(request, mute_signals):  # pylint: disable=unused-argument
    """
    A fixture for testing autoscore ORA command. It creates test data regarding courses and user enrollment.
    """
    if request.param == 'on_demand_active_enrollments':

        on_demand_courses = CourseOverviewFactory.create_batch(2, self_paced=True,
            org=factory.Sequence('active-{0}'.format))
        enrollments = CourseEnrollmentFactory.create_batch(2, course_id=on_demand_courses[0].id)
        enrollments += CourseEnrollmentFactory.create_batch(3, course_id=on_demand_courses[1].id)
        return enrollments

    elif request.param == 'on_demand_inactive_enrollments':

        on_demand_courses = CourseOverviewFactory.create_batch(2, self_paced=True,
            org=factory.Sequence('inactive-{0}'.format))
        enrollments = CourseEnrollmentFactory.create_batch(2, course_id=on_demand_courses[0].id, is_active=False)
        enrollments += CourseEnrollmentFactory.create_batch(2, course_id=on_demand_courses[1].id, is_active=False)
        return enrollments

    elif request.param == 'instructor_paced_enrollments':

        instructor_paced_course = CourseOverviewFactory(self_paced=False, org='instructor')
        enrollments = CourseEnrollmentFactory.create_batch(5, course_id=instructor_paced_course.id)
        return enrollments


@pytest.mark.django_db
@mock.patch('philu_commands.management.commands.autoscore_ondemand_course_ora.find_and_autoscore_submissions')
@mock.patch('philu_commands.management.commands.autoscore_ondemand_course_ora.log.info')
# pylint: disable=redefined-outer-name
def test_autoscore_ondemand_course_ora_successfully(mock_log_info, mock_autoscore_submissions, expected_enrollments):
    """
    Verify that command is auto scoring ORA for only self-paced courses, in which user enrollment is active.
    """
    submission_uuids = []
    enrollments = []

    for enrollment in expected_enrollments:
        submission = SubmissionFactory(
            student_item__student_id=enrollment.user.id,
            student_item__course_id=enrollment.course_id,
            student_item__item_id='test_item_id'
        )
        workflow_api.create_workflow(submission.uuid, ['training', 'peer', 'self'])

        if enrollment.course_overview.self_paced:
            submission_uuids.insert(0, unicode(submission.uuid))
        if enrollment.is_active:
            enrollments.append(enrollment)

    call_command('autoscore_ondemand_course_ora')

    if not submission_uuids:
        assert mock_log_info.called
        assert not mock_autoscore_submissions.called
    else:
        assert not mock_log_info.called
        mock_autoscore_submissions.assert_called_once_with(enrollments, submission_uuids)


@pytest.mark.django_db
@pytest.mark.usefixtures('mute_signals')
@mock.patch('philu_commands.management.commands.autoscore_ondemand_course_ora.find_and_autoscore_submissions')
@mock.patch('philu_commands.management.commands.autoscore_ondemand_course_ora.log.info')
def test_autoscore_ondemand_course_ora_for_done_and_cancelled_workflow(mock_log_info, mock_autoscore_submissions):
    """
    Verify that ORA submissions which are already scored or cancelled are not auto scored.
    """
    on_demand_courses = CourseOverviewFactory.create_batch(2, self_paced=True,
        org=factory.Sequence('org-{0}'.format))

    # Create workflow and mark it done
    submission_1 = SubmissionFactory(
        student_item__student_id='student_id',
        student_item__course_id=on_demand_courses[0].id,
        student_item__item_id='test_item_id'
    )
    workflow_api.create_workflow(submission_1.uuid, ['done', ])  # status will be set to waiting instead of done
    AssessmentWorkflow.objects.filter(submission_uuid=submission_1.uuid).update(status='done')

    # Create workflow and mark it cancelled
    submission_2 = SubmissionFactory(
        student_item__student_id='test_student_id',
        student_item__course_id=on_demand_courses[1].id,
        student_item__item_id='test_item_id'
    )
    workflow_api.create_workflow(submission_2.uuid, ['done', ])
    workflow_api.cancel_workflow(submission_2.uuid, "Test Cancel", "student_id", {})

    call_command('autoscore_ondemand_course_ora')

    assert mock_log_info.called
    assert not mock_autoscore_submissions.called


@pytest.mark.django_db
@pytest.mark.usefixtures('mute_signals')
@mock.patch('philu_commands.management.commands.autoscore_ondemand_course_ora.find_and_autoscore_submissions')
@mock.patch('philu_commands.management.commands.autoscore_ondemand_course_ora.log.info')
def test_autoscore_ondemand_course_ora_no_ora_submission(mock_log_info, mock_autoscore_submissions):
    """
    Verify that command executes without auto scoring any ORA, if there is no pending ORA submission.
    """
    CourseOverviewFactory(self_paced=True)

    call_command('autoscore_ondemand_course_ora')

    assert mock_log_info.called
    assert not mock_autoscore_submissions.called
