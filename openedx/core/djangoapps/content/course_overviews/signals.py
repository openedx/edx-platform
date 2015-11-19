"""
Signal handler for invalidating cached course overviews
"""
from django.dispatch.dispatcher import receiver

from .models import CourseOverview
from xmodule.modulestore.django import SignalHandler


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    updates the corresponding CourseOverview cache entry.
    """
    CourseOverview.objects.filter(id=course_key).delete()
    CourseOverview.load_from_module_store(course_key)


@receiver(SignalHandler.course_deleted)
def _listen_for_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from Studio and
    invalidates the corresponding CourseOverview cache entry if one exists.
    """
    CourseOverview.objects.filter(id=course_key).delete()
    # import CourseAboutSearchIndexer inline due to cyclic import
    from cms.djangoapps.contentstore.courseware_index import CourseAboutSearchIndexer
    # Delete course entry from Course About Search_index
    CourseAboutSearchIndexer.remove_deleted_items(course_key)
