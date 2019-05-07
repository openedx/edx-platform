"""
This module contains utility functions for grading.
"""
import csv
from datetime import timedelta
from django.utils import timezone
from courseware.models import StudentModule
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .config.waffle import ENFORCE_FREEZE_GRADE_AFTER_COURSE_END, waffle_flags


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


def process_score_csv(block_id, thefile, max_points):
    processed = rownum = 0
    errors = 0
    data = {}
    reader = csv.DictReader(thefile)
    block_id_str = str(block_id)
    for rownum, row in enumerate(reader):
        if row['block_id'] != block_id_str:
            errors += 1
            data['message'] = 'bad file format'
            break
        elif 'points' in row:
            if not row['points']:
                continue
            try:
                new_points = float(row['points'])
            except ValueError:
                errors += 1
                data['message'] = 'points must be numbers'
            else:
                if new_points <= max_points:
                    set_score(block_id, row['user_id'], new_points, max_points)
                    processed += 1
                else:
                    errors += 1
                    data['message'] = 'points must not be greater than %s' % max_points
        else:
            errors += 1
            data['message'] = 'bad file format'
    data['errors'] = errors
    data['processed'] = rownum + 1 if rownum else 0
    data['graded'] = processed
    return data
