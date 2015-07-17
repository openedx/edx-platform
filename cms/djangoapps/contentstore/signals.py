""" receivers of course_published and library_updated events in order to trigger indexing task """
import logging

from datetime import datetime
from pytz import UTC

from django.dispatch import receiver

from xmodule.modulestore.django import SignalHandler, modulestore
from contentstore.courseware_index import CoursewareSearchIndexer, LibrarySearchIndexer

from edx_proctoring.api import (
    get_exam_by_content_id,
    update_exam,
    create_exam,
    get_all_exams_for_course,
)
from edx_proctoring.exceptions import (
    ProctoredExamNotFoundException
)

log = logging.getLogger(__name__)


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Receives signal and kicks off celery task to update search index
    """
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from .tasks import update_search_index
    if CoursewareSearchIndexer.indexing_is_enabled():
        update_search_index.delay(unicode(course_key), datetime.now(UTC).isoformat())


@receiver(SignalHandler.course_published)
def look_for_timed_exam_publishing(sender, course_key, **kwargs):
    """
    Receives a course published signal an examines the course for sequences
    that are marked as timed exams
    """

    if not settings.FEATURES.get('ENABLE_PROCTORED_EXAMS'):
        # if feature is not enabled then do a quick exit
        return

    course = modulestore().get_course(course_key)
    if not course.enable_proctored_exams:
        # likewise if course does not have this feature turned on
        return

    # get all sequences, since they can be marked as timed/proctored exams
    timed_exams = modulestore().get_items(
        course_key,
        qualifiers={
            'category': 'sequential',
        },
        settings={
            'is_time_limited': True,
        }
    )

    # enumerate over list of sequences which are time-limited and
    # add/update any exam entries in edx-proctoring
    for timed_exam in timed_exams:
        msg = (
            'Found {location} as a timed-exam in course structure. Inspecting...'.format(
                location=unicode(timed_exam.location)
            )
        )
        log.info(msg)

        try:
            exam = get_exam_by_content_id(unicode(course_key), unicode(timed_exam.location))
            # update case, make sure everything is synced
            update_exam(
                exam_id=exam['id'],
                exam_name=timed_exam.display_name,
                time_limit_mins=timed_exam.default_time_limit_mins,
                is_proctored=timed_exam.is_proctored_enabled,
                is_active=True
            )
            log.info('Updated timed exam {exam_id}'.format(exam_id=exam['id']))
        except ProctoredExamNotFoundException:
            exam_id = create_exam(
                course_id=unicode(course_key),
                content_id=unicode(timed_exam.location),
                exam_name=timed_exam.display_name,
                time_limit_mins=timed_exam.default_time_limit_mins,
                is_proctored=timed_exam.is_proctored_enabled,
                is_active=True
            )
            log.info('Created new timed exam {exam_id}'.format(exam_id=exam_id))

    # then see which exams we have in edx-proctoring that are not in
    # our current list. That means the the user has disabled it

    exams = get_all_exams_for_course(course_key)

    for exam in exams:
        if exam['is_active']:
            # try to look up the content_id in the sequences location

            if not filter(lambda t: unicode(t.location) == exam['content_id'], timed_exams):
                # This means it was turned off in Studio, we need to mark
                # the exam as inactive (we don't delete!)
                log.info('Disabling timed exam {exam_id}'.format(exam_id=exam['id']))
                update_exam(
                    exam_id=exam['id'],
                    is_active=False,
                )


@receiver(SignalHandler.library_updated)
def listen_for_library_update(sender, library_key, **kwargs):  # pylint: disable=unused-argument
    """
    Receives signal and kicks off celery task to update search index
    """
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from .tasks import update_library_index
    if LibrarySearchIndexer.indexing_is_enabled():
        update_library_index.delay(unicode(library_key), datetime.now(UTC).isoformat())
