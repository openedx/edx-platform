"""
API for course to library import.
"""

from .constants import COURSE_TO_LIBRARY_IMPORT_PURPOSE
from .models import CourseToLibraryImport
from .tasks import (
    import_library_from_staged_content_task,
    save_courses_to_staged_content_task,
)
from .types import CompositionLevel


def import_library_from_staged_content(
    library_key: str,
    user_id: int,
    usage_ids: list[str],
    course_id: str,
    import_id: str,
    composition_level: CompositionLevel,
    override: bool
) -> None:
    """
    Import staged content to a library.
    """
    import_library_from_staged_content_task.delay(
        user_id,
        usage_ids,
        library_key,
        COURSE_TO_LIBRARY_IMPORT_PURPOSE,
        course_id,
        import_id,
        composition_level,
        override,
    )


def create_import(
    course_ids: list[str], user_id: int, library_key: str
) -> None:
    """
    Create a new import task to import a course to a library.
    """
    import_task = CourseToLibraryImport(
        course_ids=" ".join(course_ids),
        library_key=library_key,
        user_id=user_id,
    )
    import_task.save()

    save_courses_to_staged_content_task.delay(
        course_ids, user_id, import_task.id, COURSE_TO_LIBRARY_IMPORT_PURPOSE
    )
    return import_task
