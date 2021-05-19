"""
Tests related to the inlines used for ADG admin view
"""
import mock
import pytest
from django.forms import inlineformset_factory

from openedx.adg.lms.applications.admin import (
    ApplicationReviewInline,
    EducationInline,
    MultilingualCourseInlineFormset,
    WorkExperienceInline
)
from openedx.adg.lms.applications.models import MultilingualCourse, MultilingualCourseGroup
from openedx.adg.lms.applications.tests.factories import MultilingualCourseFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


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


@pytest.fixture(name='course_inline_formset')
def multilingual_course_inline_formset():
    return inlineformset_factory(
        MultilingualCourseGroup,
        MultilingualCourse,
        formset=MultilingualCourseInlineFormset,
        fields=['course', 'multilingual_course_group']
    )


@pytest.fixture(name='course_group_data')
def multilingual_course_group_data():
    return {
        'multilingual_courses-TOTAL_FORMS': '2',
        'multilingual_courses-INITIAL_FORMS': '0',
        'multilingual_courses-0-id': '',
        'multilingual_courses-0-multilingual_course_group': '',
        'multilingual_courses-0-course': '',
        'multilingual_courses-1-id': '',
        'multilingual_courses-1-multilingual_course_group': '',
        'multilingual_courses-1-course': '',
        'name': 'Test',
        'is_program_prerequisite': 'on',
    }


@mock.patch('openedx.adg.lms.applications.admin.modulestore')
def test_empty_multilingual_course_group(mock_module_store, course_inline_formset, course_group_data):
    """
    Test formset is valid when no courses are added.
    """
    mock_module_store.get_course.return_value = mock.Mock()
    formset = course_inline_formset(course_group_data, prefix='multilingual_courses')
    assert formset.is_valid()


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.admin.modulestore')
def test_multilingual_group_with_single_course(mock_module_store, course_inline_formset, course_group_data):
    """
    Test formset is valid for a single multilingual course.
    """
    mock_module_store.get_course.return_value = mock.Mock()

    course = CourseOverviewFactory()
    course_group_data['multilingual_courses-0-course'] = course.id

    formset = course_inline_formset(course_group_data, prefix='multilingual_courses')
    assert formset.is_valid()


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.admin.modulestore')
def test_multilingual_group_two_courses_of_same_language(mock_module_store, course_inline_formset, course_group_data):
    """
    Test formset is not valid for multiple courses with same language.
    """
    mock_module_store.get_course.return_value = mock.Mock()
    mock_module_store.get_course.language.return_value = 'en'

    course1 = CourseOverviewFactory()
    course2 = CourseOverviewFactory()

    course_group_data['multilingual_courses-0-course'] = course1.id
    course_group_data['multilingual_courses-1-course'] = course2.id

    formset = course_inline_formset(course_group_data, prefix='multilingual_courses')
    assert not formset.is_valid()


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.admin.modulestore')
def test_multilingual_group_course_already_exists(mock_module_store, course_inline_formset, course_group_data):
    """
    Test formset is not valid for an existing multilingual versioned course.
    """
    mock_module_store.get_course.return_value = mock.Mock()
    multilingual_course = MultilingualCourseFactory()
    course_group_data['multilingual_courses-0-course'] = multilingual_course.course.id

    formset = course_inline_formset(course_group_data, prefix='multilingual_courses')
    error = formset.errors[0]['course']
    assert not formset.is_valid()
    assert error == ['Multilingual course with this Multilingual version of a course already exists.']
