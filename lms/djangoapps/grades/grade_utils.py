"""
This module contains utility functions for grading.
"""
from __future__ import absolute_import, unicode_literals

import logging

from datetime import timedelta
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from courseware.models import StudentModule
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from util.csv_processor import CSVProcessor, ChecksumMixin
from .config.waffle import ENFORCE_FREEZE_GRADE_AFTER_COURSE_END, waffle_flags

log = logging.getLogger(__name__)


class ScoreCSVProcessor(ChecksumMixin, CSVProcessor):
    columns = ['user_id', 'username', 'full_name', 'email', 'student_uid',
               'enrolled', 'track', 'block_id', 'title', 'date_last_graded',
               'who_last_graded', 'csum', 'last_points', 'points']
    required_columns = ['user_id', 'points', 'csum', 'block_id', 'last_points']
    checksum_columns = ['user_id', 'block_id', 'last_points']

    handle_undo = False

    def __init__(self, **kwargs):
        super(ScoreCSVProcessor, self).__init__(**kwargs)
        self.users_seen = set()

    def validate_row(self, row):
        validated = super(ScoreCSVProcessor, self).validate_row(row)
        if validated:
            validated = row['block_id'] == self.block_id_str
            if validated:
                points = row['points']
                if points:
                    try:
                        validated = float(row['points']) <= self.max_points
                        if not validated:
                            self.add_error(_('Points must be less than {}.').format(self.max_points))
                    except ValueError:
                        self.add_error(_('Points must be numbers.'))
                        validated = False
                else:
                    validated = True
            else:
                self.add_error(_('The CSV does not match this problem. Check that you uploaded the right CSV.'))
        return validated

    def preprocess_row(self, row):
        if row['points']:
            to_save = {
                'user_id': row['user_id'],
                'block_id': self.block_id,
                'new_points': float(row['points']),
                'max_points': self.max_points
            }
            return to_save

    def process_row(self, row):
        if row['user_id'] not in self.users_seen:
            if self.handle_undo:
                # get the current score, for undo. expensive
                undo = get_score(row['block_id'], row['user_id'])
                undo['new_points'] = undo['score']
                undo['max_points'] = row['max_points']
            else:
                undo = None
            set_score(row['block_id'], row['user_id'], row['new_points'], row['max_points'])
            self.users_seen.add(row['user_id'])
            return True, undo
        else:
            return False, None


def are_grades_frozen(course_key):
    """ Returns whether grades are frozen for the given course. """
    if waffle_flags()[ENFORCE_FREEZE_GRADE_AFTER_COURSE_END].is_enabled(course_key):
        course = CourseOverview.get_from_id(course_key)
        if course.end:
            freeze_grade_date = course.end + timedelta(30)
            now = timezone.now()
            return now > freeze_grade_date
    return False


def set_score(usage_key, student_id, score, max_points, **defaults):
    """
    Set a score.
    """
    defaults['module_type'] = 'problem'
    defaults['grade'] = score / max_points
    defaults['max_grade'] = max_points
    StudentModule.objects.update_or_create(
        student_id=student_id,
        course_id=usage_key.course_key,
        module_state_key=usage_key,
        defaults=defaults)


def get_score(usage_key, user_id):
    """
    Return score for user_id and usage_key.
    """
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

    return {row.student_id: {'grade': row.grade,
                             'score': row.grade * (row.max_grade or 1),
                             'max_grade': row.max_grade,
                             'created': row.created,
                             'modified': row.modified,
                             'state': row.state} for row in scores_qset}
