"""
Managers for the models of applications app
"""
from datetime import datetime

from django.db.models import Manager, QuerySet
from django.utils.translation import get_language


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
    Manager for MultilingualCourseGroup
    """

    def prereq_course_groups(self):
        """
        Get non-empty prerequisite course groups
        """
        return self.get_queryset().filter(is_prerequisite=True, multilingual_courses__isnull=False).distinct()


class MultilingualCourseQuerySet(QuerySet):
    """
    QuerySet for MultilingualCourse
    """

    def get_enrolled_course(self, user):
        """
        Returns enrolled course for a user
        """
        return self.filter(
            course__courseenrollment__user=user,
            course__courseenrollment__is_active=True
        ).first()

    def get_preferred_lang_course(self):
        """
        Returns preferred language based course
        """
        user_preferred_lang = get_language()
        return self.filter(course__language=user_preferred_lang).first()


class MultilingualCourseManager(Manager):
    """
    Manager which returns all open multilingual courses
    """

    def get_queryset(self):
        """
        Over-ridden to use custom QuerySet
        """
        return MultilingualCourseQuerySet(self.model, using=self._db)

    def open_multilingual_courses(self):
        """
        Returns Open MultilingualCourse queryset
        """
        today = datetime.now()
        return self.get_queryset().filter(
            course__start_date__lte=today,
            course__end_date__gte=today
        )
