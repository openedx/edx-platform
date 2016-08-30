"""
Grades Application Configuration

Signal handlers are connected here.
"""

from django.apps import AppConfig

from .signals import SCORE_CHANGED


class GradesConfig(AppConfig):
    """
    Application Configuration for Grades.
    """
    name = u'lms.djangoapps.grades'

    def ready(self):
        """
        Connect handlers to recalculate grades.

        Redispatch score_set and score_reset signals from submissions API
        to fire SCORE_CHANGED signal.
        """

        # Can't import models at module level in AppConfigs
        from . import receivers
        from submissions.models import score_set, score_reset

        # dispatch_uid prevents signals from getting registered multiple times
        score_set.connect(
            receivers.submissions_score_set_handler,
            dispatch_uid=u'grades.submissions_score_set_handler'
        )
        score_reset.connect(
            receivers.submissions_score_reset_handler,
            dispatch_uid=u'grades.submissions_score_reset_handler'
        )
        SCORE_CHANGED.connect(
            receivers.recalculate_subsection_grade_handler,
            dispatch_uid=u'grades.recalculate_subsection_grade_handler'
        )
