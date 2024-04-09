"""
Signal/event handlers for content search
"""
from django.db.models.signals import post_delete
from django.dispatch import receiver
from openedx_events.content_authoring.data import ContentLibraryData
from openedx_events.content_authoring.signals import CONTENT_LIBRARY_DELETED

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.search.models import SearchAccess


# Using post_delete here because there is no COURSE_DELETED event defined.
@receiver(post_delete, sender=CourseOverview)
def delete_course_search_access(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Deletes the SearchAccess instance for deleted CourseOverview"""
    SearchAccess.objects.filter(context_key=instance.id).delete()


@receiver(CONTENT_LIBRARY_DELETED)
def delete_library_search_access(content_library: ContentLibraryData, **kwargs):
    """Deletes the SearchAccess instance for deleted content libraries"""
    SearchAccess.objects.filter(context_key=content_library.library_key).delete()
