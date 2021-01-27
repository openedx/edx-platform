"""
Tests for Course_Meta models
"""
import pytest

from openedx.adg.common.course_meta.models import CourseMeta

from .factories import CourseMetaFactory


@pytest.mark.django_db
def test_pre_requisite_course_manager():
    """
    Test that the PreRequisiteCourseManager returns course_ids of only those courses that are marked as prerequisite.
    """
    prereq_course_1 = _create_and_get_prereq_course()
    prereq_course_2 = _create_and_get_prereq_course()

    CourseMetaFactory()

    expected_prereq_course_ids = (prereq_course_1.id, prereq_course_2.id)
    actual_prereq_course_ids = tuple(CourseMeta.prereq_course_ids.all())

    assert expected_prereq_course_ids == actual_prereq_course_ids


def _create_and_get_prereq_course():
    """
    Create a course meta instance, mark it as prerequisite, save it in DB and return the corresponding course.
    """
    course_meta = CourseMetaFactory()
    course_meta.is_prereq = True
    course_meta.save()

    return course_meta.course
