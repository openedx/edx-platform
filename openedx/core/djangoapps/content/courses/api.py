"""
Low Level Courses and Course Runs API

🛑 UNSTABLE: All APIs related to courses in Learning Core are unstable until
they have parity with modulestore courses.
"""
from __future__ import annotations

from datetime import datetime
from logging import getLogger
from typing import Any

from django.db.transaction import atomic

from ..outline_roots import api as outline_roots
from .models import CatalogCourse, Course

# The public API that will be re-exported by openedx_learning.apps.authoring.api
# is listed in the __all__ entries below. Internal helper functions that are
# private to this module should start with an underscore. If a function does not
# start with an underscore AND it is not in __all__, that function is considered
# to be callable only by other apps in the authoring package.
__all__ = [
    "create_course_and_run",
    "create_run",
]


log = getLogger()


def create_course_and_run(
    org_id: str,
    course_id: str,
    run: str,
    *,
    learning_package_id: int,
    title: str,
    created: datetime,
    created_by: int | None,
    initial_blank_version: bool = True,
) -> Course:
    """
    Create a new course (CatalogCourse and Course / run).

    If initial_blank_version is True (default), the course outline will have an
    existing empty version 1, which can be used for building a course from
    scratch. For other use cases like importing a course, it could be better to
    avoid creating an empty version and jump right to creating an initial
    version with the imported content, or even importing the entire version
    history. In that case, set initial_blank_version to False. Note that the
    provided "title" is ignored in that case.
    """
    outline_root_args: dict[str, Any] = {
        "learning_package_id": learning_package_id,
        "key": f'course-root-v1:{org_id}+{course_id}+{run}',  # See docstring of create_outline_root_and_version()
        "created": created,
        "created_by": created_by,
    }
    with atomic(savepoint=False):
        if initial_blank_version:
            outline_root, _version = outline_roots.create_outline_root_and_version(**outline_root_args, title=title)
        else:
            outline_root = outline_roots.create_outline_root(**outline_root_args)
        catalog_course = CatalogCourse.objects.create(
            org_id=org_id,
            course_id=course_id,
        )
        # Create the course run
        course = Course.objects.create(
            catalog_course=catalog_course,
            learning_package_id=learning_package_id,
            run=run,
            outline_root=outline_root,
            source_course=None,
        )
    return course


def create_run(
    source_course: Course,
    new_run: str,
    *,
    created: datetime,
) -> Course:
    """
    Create a new run of the given course, with the same content.
    """
    raise NotImplementedError
