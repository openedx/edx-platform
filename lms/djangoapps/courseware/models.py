"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py schemamigration courseware --auto description_of_your_change
3. Add the migration file created in edx-platform/lms/djangoapps/courseware/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from model_utils.models import TimeStampedModel

from xmodule_django.models import CourseKeyField, LocationKeyField, BlockTypeKeyField  # pylint: disable=import-error


class StudentModule(models.Model):
    """
    Keeps student state for a particular module in a particular course.
    """
    MODEL_TAGS = ['course_id', 'module_type']

    # For a homework problem, contains a JSON
    # object consisting of state
    MODULE_TYPES = (('problem', 'problem'),
                    ('video', 'video'),
                    ('html', 'html'),
                    ('course', 'course'),
                    ('chapter', 'Section'),
                    ('sequential', 'Subsection'),
                    ('library_content', 'Library Content'))
    ## These three are the key for the object
    module_type = models.CharField(max_length=32, choices=MODULE_TYPES, default='problem', db_index=True)

    # Key used to share state. This is the XBlock usage_id
    module_state_key = LocationKeyField(max_length=255, db_index=True, db_column='module_id')
    student = models.ForeignKey(User, db_index=True)

    course_id = CourseKeyField(max_length=255, db_index=True)

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = (('student', 'module_state_key', 'course_id'),)

    ## Internal state of the object
    state = models.TextField(null=True, blank=True)

    ## Grade, and are we done?
    grade = models.FloatField(null=True, blank=True, db_index=True)
    max_grade = models.FloatField(null=True, blank=True)
    DONE_TYPES = (
        ('na', 'NOT_APPLICABLE'),
        ('f', 'FINISHED'),
        ('i', 'INCOMPLETE'),
    )
    done = models.CharField(max_length=8, choices=DONE_TYPES, default='na', db_index=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    @classmethod
    def all_submitted_problems_read_only(cls, course_id):
        """
        Return all model instances that correspond to problems that have been
        submitted for a given course. So module_type='problem' and a non-null
        grade. Use a read replica if one exists for this environment.
        """
        queryset = cls.objects.filter(
            course_id=course_id,
            module_type='problem',
            grade__isnull=False
        )
        if "read_replica" in settings.DATABASES:
            return queryset.using("read_replica")
        else:
            return queryset

    def __repr__(self):
        return 'StudentModule<%r>' % ({
            'course_id': self.course_id,
            'module_type': self.module_type,
            'student': self.student.username,  # pylint: disable=no-member
            'module_state_key': self.module_state_key,
            'state': str(self.state)[:20],
        },)

    def __unicode__(self):
        return unicode(repr(self))


class StudentModuleHistory(models.Model):
    """Keeps a complete history of state changes for a given XModule for a given
    Student. Right now, we restrict this to problems so that the table doesn't
    explode in size."""

    HISTORY_SAVING_TYPES = {'problem'}

    class Meta(object):  # pylint: disable=missing-docstring
        get_latest_by = "created"

    student_module = models.ForeignKey(StudentModule, db_index=True)
    version = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    # This should be populated from the modified field in StudentModule
    created = models.DateTimeField(db_index=True)
    state = models.TextField(null=True, blank=True)
    grade = models.FloatField(null=True, blank=True)
    max_grade = models.FloatField(null=True, blank=True)

    @receiver(post_save, sender=StudentModule)
    def save_history(sender, instance, **kwargs):  # pylint: disable=no-self-argument, unused-argument
        """
        Checks the instance's module_type, and creates & saves a
        StudentModuleHistory entry if the module_type is one that
        we save.
        """
        if instance.module_type in StudentModuleHistory.HISTORY_SAVING_TYPES:
            history_entry = StudentModuleHistory(student_module=instance,
                                                 version=None,
                                                 created=instance.modified,
                                                 state=instance.state,
                                                 grade=instance.grade,
                                                 max_grade=instance.max_grade)
            history_entry.save()


class XBlockFieldBase(models.Model):
    """
    Base class for all XBlock field storage.
    """
    class Meta(object):  # pylint: disable=missing-docstring
        abstract = True

    # The name of the field
    field_name = models.CharField(max_length=64, db_index=True)

    # The value of the field. Defaults to None dumped as json
    value = models.TextField(default='null')

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __unicode__(self):
        return u'{}<{!r}'.format(
            self.__class__.__name__,
            {
                key: getattr(self, key)
                for key in self._meta.get_all_field_names()
                if key not in ('created', 'modified')
            }
        )


class XModuleUserStateSummaryField(XBlockFieldBase):
    """
    Stores data set in the Scope.user_state_summary scope by an xmodule field
    """

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = (('usage_id', 'field_name'),)

    # The definition id for the module
    usage_id = LocationKeyField(max_length=255, db_index=True)


class XModuleStudentPrefsField(XBlockFieldBase):
    """
    Stores data set in the Scope.preferences scope by an xmodule field
    """

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = (('student', 'module_type', 'field_name'),)

    # The type of the module for these preferences
    module_type = BlockTypeKeyField(max_length=64, db_index=True)

    student = models.ForeignKey(User, db_index=True)


class XModuleStudentInfoField(XBlockFieldBase):
    """
    Stores data set in the Scope.preferences scope by an xmodule field
    """

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = (('student', 'field_name'),)

    student = models.ForeignKey(User, db_index=True)


class OfflineComputedGrade(models.Model):
    """
    Table of grades computed offline for a given user and course.
    """
    user = models.ForeignKey(User, db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True)

    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)

    gradeset = models.TextField(null=True, blank=True)		# grades, stored as JSON

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = (('user', 'course_id'), )

    def __unicode__(self):
        return "[OfflineComputedGrade] %s: %s (%s) = %s" % (self.user, self.course_id, self.created, self.gradeset)


class OfflineComputedGradeLog(models.Model):
    """
    Log of when offline grades are computed.
    Use this to be able to show instructor when the last computed grades were done.
    """
    class Meta(object):  # pylint: disable=missing-docstring
        ordering = ["-created"]
        get_latest_by = "created"

    course_id = CourseKeyField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    seconds = models.IntegerField(default=0)  	# seconds elapsed for computation
    nstudents = models.IntegerField(default=0)

    def __unicode__(self):
        return "[OCGLog] %s: %s" % (self.course_id.to_deprecated_string(), self.created)  # pylint: disable=no-member


class StudentFieldOverride(TimeStampedModel):
    """
    Holds the value of a specific field overriden for a student.  This is used
    by the code in the `courseware.student_field_overrides` module to provide
    overrides of xblock fields on a per user basis.
    """
    course_id = CourseKeyField(max_length=255, db_index=True)
    location = LocationKeyField(max_length=255, db_index=True)
    student = models.ForeignKey(User, db_index=True)

    class Meta(object):   # pylint: disable=missing-docstring
        unique_together = (('course_id', 'field', 'location', 'student'),)

    field = models.CharField(max_length=255)
    value = models.TextField(default='null')
