"""
Managers for the models of applications app
"""
from datetime import datetime

from django.db.models import Manager


class SubmittedApplicationsManager(Manager):
    """
    Manager which returns all user applications which have been submitted successfully.
    """

    def get_queryset(self):
        return super().get_queryset().filter(
            user__application_hub__is_application_submitted=True
        )


class MultilingualCourseGroupManager(Manager):
    """
    Manager for MultilingualCourseGroup, It contains a method to return prerequisite course groups
    """

    def prereq_course_groups(self):
        return self.get_queryset().filter(is_prerequisite=True, multilingual_courses__isnull=False).distinct()


class OpenMultilingualCourseManager(Manager):
    """
    Manager which returns all open multilingual courses
    """

    def get_queryset(self):
        today = datetime.now()
        return super().get_queryset().filter(
            course__start_date__lte=today,
            course__end_date__gte=today
        )
