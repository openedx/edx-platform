"""
All tests for course meta helper functions
"""
import pytest
from django.db.utils import OperationalError

from openedx.adg.common.course_meta.helpers import next_course_short_id
from openedx.adg.common.course_meta.tests.factories import CourseMetaFactory


@pytest.mark.django_db
def test_next_course_short_id():
    """
    Assert that course short ids are generating in a sequence starting from 100
    """
    assert next_course_short_id() == 100
    CourseMetaFactory()
    assert next_course_short_id() == 101
    CourseMetaFactory()
    course_meta_list = CourseMetaFactory.create_batch(10)
    assert course_meta_list[-1].short_id == 111


@pytest.mark.django_db
def test_next_course_short_id_operational_error(mocker):
    """
    Assert that course short id returned is 100, when function throws operational error (For example, when
    `course_meta` table do not have `short_id` field during migration)
    """
    course_meta_last = mocker.patch('openedx.adg.common.course_meta.tests.factories.CourseMeta.objects.last')
    course_meta_last.side_effect = OperationalError
    assert next_course_short_id() == 100
