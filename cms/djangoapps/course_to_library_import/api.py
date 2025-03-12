""""
API for course to library import.
"""

from .tasks import save_courses_to_staged_content_task

COURSE_TO_LIBRARY_IMPORT_PURPOSE = "course_to_library_import"


def save_courses_to_staged_content(
    course_ids: list[str],
    user_id: int,
    purpose: str = COURSE_TO_LIBRARY_IMPORT_PURPOSE,
    version_num: int | None = None,
) -> None:
    """
    Save courses to staged content.
    """
    save_courses_to_staged_content_task.delay(course_ids, user_id, purpose, version_num)
