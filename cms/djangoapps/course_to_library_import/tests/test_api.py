"""
Test cases for course_to_library_import.api module.
"""

from unittest.mock import patch

import pytest

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.course_to_library_import.api import (
    create_import,
    import_library_from_staged_content,
)
from cms.djangoapps.course_to_library_import.constants import COURSE_TO_LIBRARY_IMPORT_PURPOSE
from cms.djangoapps.course_to_library_import.models import CourseToLibraryImport


@pytest.mark.django_db
def test_create_import():
    """
    Test create_import function.
    """
    course_ids = [
        "course-v1:edX+DemoX+Demo_Course",
        "course-v1:edX+DemoX+Demo_Course_2",
    ]
    user = UserFactory()
    library_key = "lib:edX:DemoLib"
    with patch(
        "cms.djangoapps.course_to_library_import.api.save_courses_to_staged_content_task"
    ) as save_courses_to_staged_content_task_mock:
        create_import(course_ids, user.id, library_key)

    import_task = CourseToLibraryImport.objects.get()
    assert import_task.course_ids == " ".join(course_ids)
    assert import_task.library_key == library_key
    assert import_task.user_id == user.id
    save_courses_to_staged_content_task_mock.delay.assert_called_once_with(
        course_ids, user.id, import_task.id, COURSE_TO_LIBRARY_IMPORT_PURPOSE
    )


@pytest.mark.django_db
@pytest.mark.parametrize("override", [True, False])
def test_import_library_from_staged_content(override):
    """
    Test import_library_from_staged_content function with different override values.
    """
    library_key = "lib:edX:DemoLib"
    user = UserFactory()
    usage_ids = [
        "block-v1:edX+DemoX+Demo_Course+type@html+block@123",
        "block-v1:edX+DemoX+Demo_Course+type@html+block@456",
    ]
    course_id = "course-v1:edX+DemoX+Demo_Course"

    with patch(
        "cms.djangoapps.course_to_library_import.api.import_library_from_staged_content_task"
    ) as import_library_from_staged_content_task_mock:
        import_library_from_staged_content(library_key, user.id, usage_ids, course_id, 'xblock', override)

    import_library_from_staged_content_task_mock.delay.assert_called_once_with(
        user.id, usage_ids, library_key, COURSE_TO_LIBRARY_IMPORT_PURPOSE, course_id, 'xblock', override
    )
