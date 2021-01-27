"""
Tests related to the inlines used for ADG admin view
"""
import mock
import pytest

from openedx.adg.lms.applications.admin import ApplicationReviewInline, EducationInline, WorkExperienceInline


def test_has_delete_permission_application_review_inline():
    """
    Test that ADG admin is not allowed to delete ApplicationReviewInline
    """
    assert ApplicationReviewInline.has_delete_permission('self', 'request') is False


def test_has_add_permission_application_review_inline():
    """
    Test that ADG admin is not allowed to add ApplicationReviewInline
    """
    assert ApplicationReviewInline.has_add_permission('self', 'request') is False


@pytest.mark.parametrize(
    'is_current', [True, False]
)
@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.admin.get_duration')
def test_dates_education_inline(mock_get_duration, is_current, education):
    """
    Test that the field method `dates()` in EducationInline successfully calls `get_duration()` with correct parameters.
    """
    education.is_in_progress = is_current
    EducationInline.dates('self', education)

    mock_get_duration.assert_called_with(education, is_current)


@pytest.mark.parametrize(
    'is_current', [True, False]
)
@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.admin.get_duration')
def test_dates_work_experience_inline(mock_get_duration, work_experience, is_current):
    """
    Test that the field method `dates()` in WorkExperienceInline successfully calls `get_duration()` with correct
    parameters.
    """
    work_experience.is_current_position = is_current
    WorkExperienceInline.dates('self', work_experience)

    mock_get_duration.assert_called_with(work_experience, is_current)


@pytest.mark.django_db
def test_responsibilities_work_experience_inline(work_experience):
    """
    Test that field method `responsibilities()` returns the job responsibilities associated with a work experience.
    """
    expected_responsibilities = work_experience.job_responsibilities
    actual_responsibilities = WorkExperienceInline.responsibilities('self', work_experience)

    assert expected_responsibilities == actual_responsibilities
