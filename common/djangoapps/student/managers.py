from collections import defaultdict

from django.contrib.auth.models import User
from django.db import connections, models
from django.db.models import Count
from django.db.models.query import QuerySet

from util.query import use_read_replica_if_available


class NoCountQuerySet(QuerySet):
    def count(self):
        """
        Override entire table count queries only. Any WHERE or other altering
        statements will default back to an actual COUNT query.
        """
        if self._result_cache is not None and not self._iter:
            return len(self._result_cache)

        is_mysql = 'mysql' in connections[self.db].client.executable_name.lower()

        query = self.query
        if (is_mysql and not query.where and
                    query.high_mark is None and
                    query.low_mark == 0 and
                not query.select and
                not query.group_by and
                not query.having and
                not query.distinct):
            # If query has no constraints, we would be simply doing
            # "SELECT COUNT(*) FROM foo". Monkey patch so the we get an approximation instead.
            cursor = connections[self.db].cursor()
            cursor.execute("SHOW TABLE STATUS LIKE %s", (self.model._meta.db_table,))
            return cursor.fetchall()[0][4]
        else:
            return self.query.get_count(using=self.db)


class NoCountManager(models.Manager):
    """
    Manager that uses an approximated count.

    This manager should only be used by models where calls to determine the number of rows in the ENTIRE table
    do NOT need to be completely accurate. This is intended to help decrease load times for admin pages, which
    attempt to count the number of rows in an the table.

    Adapted from http://craiglabenz.me/2013/06/12/how-i-made-django-admin-scale/.
    """

    def get_query_set(self):
        return NoCountQuerySet(self.model, using=self._db)


class CourseEnrollmentManager(NoCountManager):
    """
    Custom manager for CourseEnrollment with Table-level filter methods.
    """

    def num_enrolled_in(self, course_id):
        """
        Returns the count of active enrollments in a course.

        'course_id' is the course_id to return enrollments
        """

        enrollment_number = super(CourseEnrollmentManager, self).get_query_set().filter(
            course_id=course_id,
            is_active=1
        ).count()

        return enrollment_number

    def is_course_full(self, course):
        """
        Returns a boolean value regarding whether a course has already reached it's max enrollment
        capacity
        """
        is_course_full = False
        if course.max_student_enrollments_allowed is not None:
            is_course_full = self.num_enrolled_in(course.id) >= course.max_student_enrollments_allowed
        return is_course_full

    def users_enrolled_in(self, course_id):
        """Return a queryset of User for every user enrolled in the course."""
        return User.objects.filter(
            courseenrollment__course_id=course_id,
            courseenrollment__is_active=True
        )

    def enrollment_counts(self, course_id):
        """
        Returns a dictionary that stores the total enrollment count for a course, as well as the
        enrollment count for each individual mode.
        """
        # Unfortunately, Django's "group by"-style queries look super-awkward
        query = use_read_replica_if_available(
            super(CourseEnrollmentManager, self).get_query_set().filter(course_id=course_id, is_active=True).values(
                'mode').order_by().annotate(Count('mode')))
        total = 0
        enroll_dict = defaultdict(int)
        for item in query:
            enroll_dict[item['mode']] = item['mode__count']
            total += item['mode__count']
        enroll_dict['total'] = total
        return enroll_dict

    def enrolled_and_dropped_out_users(self, course_id):
        """Return a queryset of Users in the course."""
        return User.objects.filter(
            courseenrollment__course_id=course_id
        )
