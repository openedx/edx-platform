"""
Code related to the handling of Proctored Exams in Studio
"""

import logging

from django.conf import settings

from xmodule.modulestore.django import modulestore

from contentstore.views.helpers import is_item_in_course_tree

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


def register_proctored_exams(course_key):
    """
    This is typically called on a course published signal. The course is examined for sequences
    that are marked as timed exams. Then these are registered with the edx-proctoring
    subsystem. Likewise, if formerly registered exams are unmarked, then those
    registred exams are marked as inactive
    """

    if not settings.FEATURES.get('ENABLE_PROCTORED_EXAMS'):
        # if feature is not enabled then do a quick exit
        return

    course = modulestore().get_course(course_key)
    if not course.enable_proctored_exams:
        # likewise if course does not have this feature turned on
        return

    # get all sequences, since they can be marked as timed/proctored exams
    _timed_exams = modulestore().get_items(
        course_key,
        qualifiers={
            'category': 'sequential',
        },
        settings={
            'is_time_limited': True,
        }
    )

    # filter out any potential dangling sequences
    timed_exams = [
        timed_exam
        for timed_exam in _timed_exams
        if is_item_in_course_tree(timed_exam)
    ]

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
                time_limit_mins=timed_exam.default_time_limit_minutes,
                is_proctored=timed_exam.is_proctored_enabled,
                is_active=True
            )
            msg = 'Updated timed exam {exam_id}'.format(exam_id=exam['id'])
            log.info(msg)
        except ProctoredExamNotFoundException:
            exam_id = create_exam(
                course_id=unicode(course_key),
                content_id=unicode(timed_exam.location),
                exam_name=timed_exam.display_name,
                time_limit_mins=timed_exam.default_time_limit_minutes,
                is_proctored=timed_exam.is_proctored_enabled,
                is_active=True
            )
            msg = 'Created new timed exam {exam_id}'.format(exam_id=exam_id)
            log.info(msg)

    # then see which exams we have in edx-proctoring that are not in
    # our current list. That means the the user has disabled it
    exams = get_all_exams_for_course(course_key)

    for exam in exams:
        if exam['is_active']:
            # try to look up the content_id in the sequences location

            search = [
                timed_exam for timed_exam in timed_exams if
                unicode(timed_exam.location) == exam['content_id']
            ]
            if not search:
                # This means it was turned off in Studio, we need to mark
                # the exam as inactive (we don't delete!)
                msg = 'Disabling timed exam {exam_id}'.format(exam_id=exam['id'])
                log.info(msg)
                update_exam(
                    exam_id=exam['id'],
                    is_proctored=False,
                    is_active=False,
                )
