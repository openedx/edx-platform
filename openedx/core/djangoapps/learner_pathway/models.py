"""
Models for learner_pathway App.
"""

import json
import logging
from uuid import uuid4

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext as _
from jsonfield.fields import JSONField
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.grades.models import PersistentCourseGrade
from openedx.core.djangoapps.programs.utils import ProgramProgressMeter

from .constants import PathwayCourseStatus, PathwayProgramStatus

log = logging.getLogger(__name__)


class LearnerPathwayProgress(TimeStampedModel):
    """
    Learner pathway progress model.

    .. no_pii:
    """
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    learner_pathway_uuid = models.UUIDField(
        default=uuid4, editable=False, verbose_name=_('LEARNER_PATHWAY_UUID')
    )
    learner_pathway_progress = JSONField(
        blank=True,
        default={},
        help_text=_("The pathway snapshot with progress annotations."),
    )
    history = HistoricalRecords()

    class Meta:
        """
        Learner pathway progress metadata.
        """
        unique_together = ('user', 'learner_pathway_uuid')

    def __str__(self):
        return f"{self.user.id} - {self.learner_pathway_uuid}"

    @staticmethod
    def get_learner_course_status(user, course):
        """
        Get the progress of the learner in the course.
        """
        course_runs = course['course_runs'] or []
        learner_enrollments = []
        for course_run in course_runs:
            learner_course_grade = PersistentCourseGrade.objects.filter(
                user_id=user.id,
                course_id=course_run['key']
            ).first()
            if learner_course_grade and learner_course_grade.passed_timestamp:
                return PathwayCourseStatus.complete
            else:
                course_enrollment = CourseEnrollment.get_enrollment(user, course_run['key'])
                if course_enrollment:
                    learner_enrollments.append(course_enrollment)
        if learner_enrollments:
            return PathwayCourseStatus.in_progress
        return PathwayCourseStatus.not_started

    @staticmethod
    def get_learner_program_status(user, program):
        """
        Get the progress of the learner in the program.
        """
        site = Site.objects.get_current()
        meter = ProgramProgressMeter(site=site, user=user, include_course_entitlements=False)
        programs_progress = meter.progress()
        for program_progress in programs_progress:
            if (
                program_progress['uuid'] == program['uuid'] and
                program_progress['complete'] and
                not program_progress['in_progress'] and
                not program_progress['not_started']
            ):
                return PathwayProgramStatus.complete
            elif program_progress['uuid'] == program['uuid'] and program_progress['in_progress']:
                return PathwayProgramStatus.in_progress
        return PathwayProgramStatus.not_started

    def update_pathway_progress(self):
        """
        Update the progress for the learner in the pathway.
        """
        pathway_snapshot = json.loads(self.learner_pathway_progress)
        pathway_steps = pathway_snapshot['steps'] or []
        for step in pathway_steps:
            step_courses = step['courses'] or []
            step_programs = step['programs'] or []
            step_completion_requirement = step['min_requirement'] or 1
            completion_count = 0
            for course in step_courses:
                learner_course_status = self.get_learner_course_status(self.user, course)
                course["status"] = learner_course_status
                if learner_course_status == PathwayCourseStatus.complete:
                    completion_count += 1
            for program in step_programs:
                learner_program_status = self.get_learner_program_status(self.user, program)
                program["status"] = learner_program_status
                if learner_program_status == PathwayProgramStatus.complete:
                    completion_count += 1
            step['status'] = completion_count / step_completion_requirement * 100
        self.learner_pathway_progress = json.dumps(pathway_snapshot)
        self.save()
