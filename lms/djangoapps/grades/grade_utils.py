"""
This module contains utility functions for grading.
"""
from __future__ import absolute_import, unicode_literals

import logging
import time
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import ugettext as _
from opaque_keys.edx.keys import UsageKey

from courseware.models import StudentModule
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment
from super_csv.csv_processor import ChecksumMixin, CSVProcessor, DeferrableMixin

from .models import ScoreOverrider
from .config.waffle import ENFORCE_FREEZE_GRADE_AFTER_COURSE_END, waffle_flags

log = logging.getLogger(__name__)


class ScoreCSVProcessor(ChecksumMixin, DeferrableMixin, CSVProcessor):
    """
    CSV Processor for file format defined for Staff Graded Points
    """
    columns = ['user_id', 'username', 'full_name', 'student_uid',
               'enrolled', 'track', 'block_id', 'title', 'date_last_graded',
               'who_last_graded', 'csum', 'last_points', 'points']
    required_columns = ['user_id', 'points', 'csum', 'block_id', 'last_points']
    checksum_columns = ['user_id', 'block_id', 'last_points']
    # files larger than 100 rows will be processed asynchronously
    size_to_defer = 100
    max_file_size = 4 * 1024 * 1024
    handle_undo = False

    def __init__(self, **kwargs):
        self.max_points = 1
        self.user_id = None
        self.display_name = ''
        super(ScoreCSVProcessor, self).__init__(**kwargs)
        self.users_seen = {}

    def get_unique_path(self):
        return 'sgp/{}'.format(self.block_id)

    def validate_row(self, row):
        if not super(ScoreCSVProcessor, self).validate_row(row):
            return False
        if row['block_id'] != self.block_id:
            self.add_error(_('The CSV does not match this problem. Check that you uploaded the right CSV.'))
            return False
        if row['points']:
            try:
                if float(row['points']) > self.max_points:
                    self.add_error(_('Points must not be greater than {}.').format(self.max_points))
                    return False
            except ValueError:
                self.add_error(_('Points must be numbers.'))
                return False
        return True

    def preprocess_row(self, row):
        if row['points'] and row['user_id'] not in self.users_seen:
            to_save = {
                'user_id': row['user_id'],
                'block_id': self.block_id,
                'new_points': float(row['points']),
                'max_points': self.max_points,
                'override_user_id': self.user_id,
            }
            self.users_seen[row['user_id']] = 1
            return to_save

    def process_row(self, row):
        """
        Set the score for the given row, returning (status, undo)
        undo is a dict of an operation which would undo the set_score. In this case,
        that means we would have to call get_score, which could be expensive to do for the entire file.
        """
        if self.handle_undo:
            # get the current score, for undo. expensive
            undo = get_score(row['block_id'], row['user_id'])
            undo['new_points'] = undo['score']
            undo['max_points'] = row['max_points']
        else:
            undo = None
        set_score(row['block_id'], row['user_id'], row['new_points'], row['max_points'], row['override_user_id'])
        return True, undo

    def _get_enrollments(self, course_id, **kwargs):  # pylint: disable=unused-argument
        """
        Return iterator of enrollments, as dicts.
        """
        enrollments = CourseEnrollment.objects.filter(
            course_id=course_id).select_related('programcourseenrollment')
        for enrollment in enrollments:
            enrollment_dict = {
                'user_id': enrollment.user.id,
                'username': enrollment.user.username,
                'full_name': enrollment.user.profile.name,
                'enrolled': enrollment.is_active,
                'track': enrollment.mode,
            }
            try:
                pce = enrollment.programcourseenrollment.program_enrollment
                enrollment_dict['student_uid'] = pce.external_user_key
            except ObjectDoesNotExist:
                enrollment_dict['student_uid'] = None
            yield enrollment_dict

    def get_rows_to_export(self):
        """
        Return iterator of rows for file export.
        """
        location = UsageKey.from_string(self.block_id)
        my_name = self.display_name

        students = get_scores(location)

        enrollments = self._get_enrollments(location.course_key)
        for enrollment in enrollments:
            row = {
                'block_id': location,
                'title': my_name,
                'points': None,
                'last_points': None,
                'date_last_graded': None,
                'who_last_graded': None,
            }
            row.update(enrollment)
            score = students.get(enrollment['user_id'], None)

            if score:
                row['last_points'] = int(score['grade'] * self.max_points)
                row['date_last_graded'] = score['modified']
                row['who_last_graded'] = score.get('who_last_graded', None)
            yield row


def are_grades_frozen(course_key):
    """ Returns whether grades are frozen for the given course. """
    if waffle_flags()[ENFORCE_FREEZE_GRADE_AFTER_COURSE_END].is_enabled(course_key):
        course = CourseOverview.get_from_id(course_key)
        if course.end:
            freeze_grade_date = course.end + timedelta(30)
            now = timezone.now()
            return now > freeze_grade_date
    return False


def set_score(usage_key, student_id, score, max_points, override_user_id=None, **defaults):
    """
    Set a score.
    """
    if not isinstance(usage_key, UsageKey):
        usage_key = UsageKey.from_string(usage_key)
    defaults['module_type'] = 'problem'
    defaults['grade'] = score / (max_points or 1.0)
    defaults['max_grade'] = max_points
    module = StudentModule.objects.update_or_create(
        student_id=student_id,
        course_id=usage_key.course_key,
        module_state_key=usage_key,
        defaults=defaults)[0]
    if override_user_id:
        ScoreOverrider.objects.create(
            module=module,
            user_id=override_user_id)


def get_score(usage_key, user_id):
    """
    Return score for user_id and usage_key.
    """
    if not isinstance(usage_key, UsageKey):
        usage_key = UsageKey.from_string(usage_key)
    try:
        score = StudentModule.objects.get(
            course_id=usage_key.course_key,
            module_state_key=usage_key,
            student_id=user_id
        )
    except StudentModule.DoesNotExist:
        return None
    else:
        return {
            'grade': score.grade,
            'score': score.grade * (score.max_grade or 1),
            'max_grade': score.max_grade,
            'created': score.created,
            'modified': score.modified
        }


def get_scores(usage_key, user_ids=None):
    """
    Return dictionary of student_id: scores.
    """
    scores_qset = StudentModule.objects.filter(
        course_id=usage_key.course_key,
        module_state_key=usage_key,
    )
    if user_ids:
        scores_qset = scores_qset.filter(student_id__in=user_ids)

    scores = {}
    for row in scores_qset:
        scores[row.student_id] = {
            'grade': row.grade,
            'score': row.grade * (row.max_grade or 1),
            'max_grade': row.max_grade,
            'created': row.created,
            'modified': row.modified,
            'state': row.state,
        }
        last_override = row.scoreoverrider_set.latest('created')
        if last_override:
            scores[row.student_id]['who_last_graded'] = last_override.user_id
    return scores
