"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms schemamigration instructor_email_widget --auto description_of_your_change
3. Add the migration file created in edx-platform/lms/djangoapps/instructor_email_widget/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""
from django.contrib.auth.models import User
from django.db import models
from instructor.views.data_access_constants import Inclusion, QueryOrigin, QUERYORIGIN_MAP
from xmodule_django.models import CourseKeyField, LocationKeyField


class GroupedQuery(models.Model):
    """
    Email Distribution List: Individual queries are associated with a grouped query.
    A grouped query has a creation time, associated course and a name
    """
    title = models.CharField(max_length=255)
    course_id = CourseKeyField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)

    class Meta(object):
        app_label = 'instructor_email_widget'

    def __unicode__(self):
        return "[GroupedQuery] Query {} for Course {}, {}".format(
            self.id,  # pylint: disable=no-member
            self.course_id,
            self.title,
        )

INCLUSIONS = (
    ('A', Inclusion.AND),
    ('N', Inclusion.NOT),
    ('O', Inclusion.OR),
)


class SavedQuery(models.Model):
    """
    Email Distribution List: Individual queries are saved because they are associated with a grouped query
    """
    course_id = CourseKeyField(max_length=255, db_index=True)
    module_state_key = LocationKeyField(max_length=255, db_index=True, db_column='module_id')
    inclusion = models.CharField(max_length=1, choices=INCLUSIONS)
    #filter_on takes on values in instructor.views.data_access_constants.SectionFilters, ProblemFilters
    filter_on = models.CharField(max_length=255)
    entity_name = models.CharField(max_length=255)
    query_type = models.CharField(max_length=255)

    class Meta(object):
        app_label = 'instructor_email_widget'

    def __unicode__(self):
        return "[QueriesSaved] Query {} for {}/{}, {} {}".format(
            self.id,  # pylint: disable=no-member
            self.course_id,
            self.module_state_key,
            self.get_inclusion_display(),  # pylint: disable=no-member
            self.filter_on,
        )


class TemporaryQuery(models.Model):
    """
    Email Distribution List: Stores individual queries that are in progress. This table is purged periodically
    """
    course_id = CourseKeyField(max_length=255, db_index=True)
    module_state_key = LocationKeyField(max_length=255, db_index=True, db_column='module_id')
    inclusion = models.CharField(max_length=1, choices=INCLUSIONS)
    #filter_on takes on values in instructor.views.data_access_constants.SectionFilters, ProblemFilters
    filter_on = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    entity_name = models.CharField(max_length=255)
    query_type = models.CharField(max_length=255)
    ORIGIN = (
        ('E', QueryOrigin.EMAIL),
        ('W', QueryOrigin.WIDGET),
    )
    origin = models.CharField(default=QUERYORIGIN_MAP[QueryOrigin.WIDGET], max_length=1, choices=ORIGIN)
    done = models.NullBooleanField()

    class Meta(object):
        app_label = 'instructor_email_widget'

    def __unicode__(self):
        return "[QueriesSaved] Query {} for {}/{}, {} {}".format(
            self.id,  # pylint: disable=no-member
            self.course_id,
            self.module_state_key,
            self.get_inclusion_display(),  # pylint: disable=no-member
            self.filter_on,
        )


class StudentsForQuery(models.Model):
    """
    Email Distribution List: Students saved as part of a query. This will get purged periodically so do not query this
    directly (instead use one of functions that actively makes a query and then returns students). Associate these
    students with a query in QueriesTemporary
    """
    query = models.ForeignKey('TemporaryQuery')
    student = models.ForeignKey(User, db_index=True)
    inclusion = models.CharField(max_length=1, choices=INCLUSIONS)

    class Meta(object):
        app_label = 'instructor_email_widget'

    def __unicode__(self):
        return "[QueriesStudents] Query {} for {}, {}".format(
            self.query.id,  # pylint: disable=no-member
            self.student,
            self.get_inclusion_display(),  # pylint: disable=no-member
        )


class GroupedTempQueryForSubquery(models.Model):
    """
    Email Distribution List: Saved temporary queries associated with a group per course. Used when loading a
    saved query and then executing it.
    """
    grouped = models.ForeignKey('GroupedQuery')
    query = models.ForeignKey('TemporaryQuery')

    class Meta(object):
        app_label = 'instructor_email_widget'

    def __unicode__(self):
        return "[GroupedQueriesSubqueries] Group {} has Query {}".format(
            self.grouped.id,  # pylint: disable=no-member
            self.query.id,  # pylint: disable=no-member
        )


class SubqueryForGroupedQuery(models.Model):
    """
    Email Distribution List: Saved queries by instructors per course. Associates permanent queries in QueryiesSaved
    into GroupedQueries
    """
    grouped = models.ForeignKey('GroupedQuery')
    query = models.ForeignKey('SavedQuery')

    class Meta(object):
        app_label = 'instructor_email_widget'

    def __unicode__(self):
        return "[GroupedQueriesSubqueries] Group {} has Query {}".format(
            self.grouped.id,  # pylint: disable=no-member
            self.query.id,  # pylint: disable=no-member
        )
