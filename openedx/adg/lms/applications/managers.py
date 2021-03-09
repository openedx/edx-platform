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

    def get_courses(self, user, is_prereq=False):
        """
        Get courses from course groups.

        Args:
            is_prereq (bool):  List of MultilingualCourseGroups
            user (User): user for which we need to find courses

        Returns:
            list: List of courses which contains a course from each group
        """
        courses_list = []
        course_groups = self.prereq_course_groups() if is_prereq else self.get_queryset()

        for course_group in course_groups:
            open_multilingual_courses = course_group.multilingual_courses.open_multilingual_courses()
            multilingual_course = open_multilingual_courses.multilingual_course(user)
            if multilingual_course:
                courses_list.append(multilingual_course.course)

        return courses_list


class MultilingualCourseQuerySet(QuerySet):
    """
    QuerySet for MultilingualCourse
    """

    def enrolled_course(self, user):
        """
        Returns enrolled course for a authenticated user else None
        """
        if user.is_anonymous:
            return None

        return self.filter(
            course__courseenrollment__user=user,
            course__courseenrollment__is_active=True
        ).first()

    def preferred_lang_course(self):
        """
        Returns preferred language based course
        """
        user_preferred_lang = get_language()
        return self.filter(course__language=user_preferred_lang).first()

    def multilingual_course(self, user):
        """
        Returns a multilingual course

        Following are the preferences for the course.

        1. Enrollment
            Get User enrolled course.

        2. Language preferred
            If user has not enrolled then find a course with preferred language.

        3. First Course
            If user enrolled and preferred language courses are not found then
            return the first course of a group.
        Args:
            user (User): User for which we need to find the course

        Returns:
            MultilingualCourse: MultilingualCourse for a user
        """
        return self.enrolled_course(user) or self.preferred_lang_course() or self.first()


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
