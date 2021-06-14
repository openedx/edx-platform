"""
Managers for the models of applications app
"""
from datetime import datetime

from django.db.models import Manager, Q, QuerySet
from django.utils.translation import get_language

from .helpers import get_courses_from_course_groups


class SubmittedApplicationsManager(Manager):
    """
    Manager which returns all written user applications which have been submitted successfully.
    """

    def get_queryset(self):
        return super().get_queryset().filter(
            user__application_hub__is_written_application_completed=True
        )


class MultilingualCourseGroupManager(Manager):
    """
    Manager for MultilingualCourseGroup
    """

    def program_prereq_and_all_non_prereq_course_groups(self):
        """
        All course groups which are not business line or common business line prerequisites course groups.
        """
        return self.get_queryset().filter(
            is_common_business_line_prerequisite=False, business_line_prerequisite__isnull=True
        )

    def program_prereq_course_groups(self):
        """
        Non-empty program prerequisite course groups.
        """
        return self.get_queryset().filter(is_program_prerequisite=True, multilingual_courses__isnull=False).distinct()

    def business_line_and_common_business_line_prereq_course_groups(self, user=None):
        """
        Returns prerequisite course groups for the selected business line and common prerequisite course groups
        for all business lines.

        Args:
            user (User): User for which prerequisite course groups will be returned

        Returns:
            list: List of business line prerequisite course groups for a user
        """
        prereq_course_filter = Q(is_common_business_line_prerequisite=True)
        if user:
            prereq_course_filter.add(Q(business_line_prerequisite=user.application.business_line), Q.OR)
        else:
            prereq_course_filter.add(Q(business_line_prerequisite__isnull=False), Q.OR)

        return self.get_queryset().filter(prereq_course_filter)

    def get_user_business_line_and_common_business_line_prereq_courses(self, user):
        """
        Returns prerequisite courses for the selected business line and common prerequisite courses
        for all business lines for a user.

        Args:
            user (User): User for which business line prerequisites will be returned

        Returns:
            list: List of prereq courses for a business line selected by user
            and common courses for all the business lines
        """
        return get_courses_from_course_groups(
            self.business_line_and_common_business_line_prereq_course_groups(user), user
        )

    def get_user_program_prereq_courses(self, user):
        """
        Returns program prerequisite courses for a user.

        Args:
            user (User): User for which program prerequisite courses will be returned

        Returns:
            list: List of program prerequisite courses for a user
        """
        return get_courses_from_course_groups(
            self.program_prereq_course_groups(), user
        )

    def get_user_program_prereq_courses_and_all_non_prereq_courses(self, user):
        """
        Returns program prerequisite courses and non prerequisite courses for a user.

        Args:
            user (User): User for which courses will be returned

        Returns:
            list: List of program prerequisite and non prerequisite courses
        """
        return get_courses_from_course_groups(
            self.program_prereq_and_all_non_prereq_course_groups(), user
        )


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

    def language_codes_with_course_ids(self):
        """
        Get a QuerySet containing tuples, each with a course_id and its corresponding language code

        Returns:
            QuerySet: A QuerySet containing one or more tuples in the form: (course_id, language_code)
        """
        return self.values_list('course__id', 'course__language')

    def multilingual_course_with_course_id(self, course_id):
        """
        Given a course_id, returns a MultilingualCourse associated with that course_id.

        Arguments:
            course_id (CourseKey): id of the specified course

        Returns:
            MultilingualCourse: MultilingualCourse object associated with the given course_id
        """
        return self.filter(course__id=course_id).first()


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
