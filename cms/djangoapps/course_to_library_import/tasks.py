"""
Tasks for course to library import.
"""

from celery import shared_task
from django.db import transaction
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content_staging import api as content_staging_api
from xmodule.modulestore.django import modulestore

from .data import CourseToLibraryImportStatus
from .models import CourseToLibraryImport


@shared_task
@set_code_owner_attribute
def save_courses_to_staged_content_task(
    course_ids: list[str], user_id: int, purpose: str, version_num: int | None
) -> None:
    """
    Save courses to staged content task.
    """
    course_to_library_import = CourseToLibraryImport.objects.create(
        course_ids=' '.join(course_ids),
        user_id=user_id,
    )

    with transaction.atomic():
        for course_id in course_ids:
            course_key = CourseKey.from_string(course_id)
            sections = modulestore().get_items(course_key, qualifiers={"category": "chapter"})

            for section in sections:
                content_staging_api.stage_xblock_temporarily(
                    section,
                    user_id,
                    purpose=purpose,
                    version_num=version_num,
                )

        course_to_library_import.status = CourseToLibraryImportStatus.READY
        course_to_library_import.save()
