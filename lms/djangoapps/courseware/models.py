"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py schemamigration courseware --auto description_of_your_change
3. Add the migration file created in edx-platform/lms/djangoapps/courseware/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""


import itertools
import logging

import six
from config_models.models import ConfigurationModel
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import BlockTypeKeyField, CourseKeyField, LearningContextKeyField, UsageKeyField
from lms.djangoapps.courseware.fields import UnsignedBigIntAutoField
from six import text_type
from six.moves import range

from openedx.core.djangolib.markup import HTML

log = logging.getLogger("edx.courseware")


def chunks(items, chunk_size):
    """
    Yields the values from items in chunks of size chunk_size
    """
    items = list(items)
    return (items[i:i + chunk_size] for i in range(0, len(items), chunk_size))


class ChunkingManager(models.Manager):
    """
    :class:`~Manager` that adds an additional method :meth:`chunked_filter` to provide
    the ability to make select queries with specific chunk sizes.
    """

    class Meta(object):
        app_label = "courseware"

    def chunked_filter(self, chunk_field, items, **kwargs):
        """
        Queries model_class with `chunk_field` set to chunks of size `chunk_size`,
        and all other parameters from `**kwargs`.

        This works around a limitation in sqlite3 on the number of parameters
        that can be put into a single query.

        Arguments:
            chunk_field (str): The name of the field to chunk the query on.
            items: The values for of chunk_field to select. This is chunked into ``chunk_size``
                chunks, and passed as the value for the ``chunk_field`` keyword argument to
                :meth:`~Manager.filter`. This implies that ``chunk_field`` should be an
                ``__in`` key.
            chunk_size (int): The size of chunks to pass. Defaults to 500.
        """
        chunk_size = kwargs.pop('chunk_size', 500)
        res = itertools.chain.from_iterable(
            self.filter(**dict([(chunk_field, chunk)] + list(kwargs.items())))
            for chunk in chunks(items, chunk_size)
        )
        return res


@python_2_unicode_compatible
class StudentModule(models.Model):
    """
    Keeps student state for a particular XBlock usage and particular student.

    Called Module since it was originally used for XModule state.

    .. no_pii:
    """
    objects = ChunkingManager()

    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name

    ## The XBlock/XModule type (e.g. "problem")
    module_type = models.CharField(max_length=32, db_index=True)

    # Key used to share state. This is the XBlock usage_id
    module_state_key = UsageKeyField(max_length=255, db_column='module_id')
    student = models.ForeignKey(User, db_index=True, db_constraint=False, on_delete=models.CASCADE)

    # The learning context of the usage_key (usually a course ID, but may be a library or something else)
    course_id = LearningContextKeyField(max_length=255, db_index=True)

    class Meta(object):
        app_label = "courseware"
        unique_together = (('student', 'module_state_key', 'course_id'),)

    # Internal state of the object
    state = models.TextField(null=True, blank=True)

    # Grade, and are we done?
    grade = models.FloatField(null=True, blank=True, db_index=True)
    max_grade = models.FloatField(null=True, blank=True)
    DONE_TYPES = (
        (u'na', u'NOT_APPLICABLE'),
        (u'f', u'FINISHED'),
        (u'i', u'INCOMPLETE'),
    )
    done = models.CharField(max_length=8, choices=DONE_TYPES, default='na')

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
        return 'StudentModule<%r>' % (
            {
                'course_id': self.course_id,
                'module_type': self.module_type,
                # We use the student_id instead of username to avoid a database hop.
                # This can actually matter in cases where we're logging many of
                # these (e.g. on a broken progress page).
                'student_id': self.student_id,
                'module_state_key': self.module_state_key,
                'state': str(self.state)[:20],
            },)

    def __str__(self):
        return six.text_type(repr(self))

    @classmethod
    def get_state_by_params(cls, course_id, module_state_keys, student_id=None):
        """
        Return all model instances that correspond to a course and module keys.

        Student ID is optional keyword argument, if provided it narrows down the instances.
        """
        module_states = cls.objects.filter(course_id=course_id, module_state_key__in=module_state_keys)
        if student_id:
            module_states = module_states.filter(student_id=student_id)
        return module_states

    @classmethod
    def save_state(cls, student, course_id, module_state_key, defaults):
        if not student.is_authenticated:
            return
        else:
            cls.objects.update_or_create(
                student=student,
                course_id=course_id,
                module_state_key=module_state_key,
                defaults=defaults,
            )


class BaseStudentModuleHistory(models.Model):
    """
    Abstract class containing most fields used by any class storing Student Module History

    .. no_pii:
    """
    objects = ChunkingManager()
    HISTORY_SAVING_TYPES = {'problem'}

    class Meta(object):
        abstract = True

    version = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    # This should be populated from the modified field in StudentModule
    created = models.DateTimeField(db_index=True)
    state = models.TextField(null=True, blank=True)
    grade = models.FloatField(null=True, blank=True)
    max_grade = models.FloatField(null=True, blank=True)

    @property
    def csm(self):
        """
        Finds the StudentModule object for this history record, even if our data is split
        across multiple data stores.  Django does not handle this correctly with the built-in
        student_module property.
        """
        return StudentModule.objects.get(pk=self.student_module_id)

    @staticmethod
    def get_history(student_modules):
        """
        Find history objects across multiple backend stores for a given StudentModule
        """

        history_entries = []

        if settings.FEATURES.get('ENABLE_CSMH_EXTENDED'):
            from lms.djangoapps.coursewarehistoryextended.models import StudentModuleHistoryExtended
            history_entries += StudentModuleHistoryExtended.objects.filter(
                # Django will sometimes try to join to courseware_studentmodule
                # so just do an in query
                student_module__in=[module.id for module in student_modules]
            ).order_by('-id')

        # If we turn off reading from multiple history tables, then we don't want to read from
        # StudentModuleHistory anymore, we believe that all history is in the Extended table.
        if settings.FEATURES.get('ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES'):
            # we want to save later SQL queries on the model which allows us to prefetch
            history_entries += StudentModuleHistory.objects.prefetch_related('student_module').filter(
                student_module__in=student_modules
            ).order_by('-id')

        return history_entries


@python_2_unicode_compatible
class StudentModuleHistory(BaseStudentModuleHistory):
    """Keeps a complete history of state changes for a given XModule for a given
    Student. Right now, we restrict this to problems so that the table doesn't
    explode in size."""

    class Meta(object):
        app_label = "courseware"
        get_latest_by = "created"

    student_module = models.ForeignKey(StudentModule, db_index=True, db_constraint=False, on_delete=models.CASCADE)

    def __str__(self):
        return six.text_type(repr(self))

    def save_history(sender, instance, **kwargs):  # pylint: disable=no-self-argument, unused-argument
        """
        Checks the instance's module_type, and creates & saves a
        StudentModuleHistoryExtended entry if the module_type is one that
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

    # When the extended studentmodulehistory table exists, don't save
    # duplicate history into courseware_studentmodulehistory, just retain
    # data for reading.
    if not settings.FEATURES.get('ENABLE_CSMH_EXTENDED'):
        post_save.connect(save_history, sender=StudentModule)


@python_2_unicode_compatible
class XBlockFieldBase(models.Model):
    """
    Base class for all XBlock field storage.

    .. no_pii:
    """
    objects = ChunkingManager()

    class Meta(object):
        app_label = "courseware"
        abstract = True

    # The name of the field
    field_name = models.CharField(max_length=64, db_index=True)

    # The value of the field. Defaults to None dumped as json
    value = models.TextField(default='null')

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        keys = [field.name for field in self._meta.get_fields() if field.name not in ('created', 'modified')]
        return HTML(u'{}<{!r}').format(
            HTML(self.__class__.__name__),
            {key: HTML(getattr(self, key)) for key in keys}
        )


class XModuleUserStateSummaryField(XBlockFieldBase):
    """
    Stores data set in the Scope.user_state_summary scope by an xmodule field
    """

    class Meta(object):
        app_label = "courseware"
        unique_together = (('usage_id', 'field_name'),)

    # The definition id for the module
    usage_id = UsageKeyField(max_length=255, db_index=True)


class XModuleStudentPrefsField(XBlockFieldBase):
    """
    Stores data set in the Scope.preferences scope by an xmodule field
    """

    class Meta(object):
        app_label = "courseware"
        unique_together = (('student', 'module_type', 'field_name'),)

    # The type of the module for these preferences
    module_type = BlockTypeKeyField(max_length=64, db_index=True)

    student = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)


class XModuleStudentInfoField(XBlockFieldBase):
    """
    Stores data set in the Scope.preferences scope by an xmodule field
    """

    class Meta(object):
        app_label = "courseware"
        unique_together = (('student', 'field_name'),)

    student = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)


@python_2_unicode_compatible
class OfflineComputedGrade(models.Model):
    """
    Table of grades computed offline for a given user and course.

    .. no_pii:
    """
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    course_id = CourseKeyField(max_length=255, db_index=True)

    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)

    gradeset = models.TextField(null=True, blank=True)  # grades, stored as JSON

    class Meta(object):
        app_label = "courseware"
        unique_together = (('user', 'course_id'),)

    def __str__(self):
        return "[OfflineComputedGrade] %s: %s (%s) = %s" % (self.user, self.course_id, self.created, self.gradeset)


@python_2_unicode_compatible
class OfflineComputedGradeLog(models.Model):
    """
    Log of when offline grades are computed.
    Use this to be able to show instructor when the last computed grades were done.

    .. no_pii:
    """

    class Meta(object):
        app_label = "courseware"
        ordering = ["-created"]
        get_latest_by = "created"

    course_id = CourseKeyField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    seconds = models.IntegerField(default=0)  # seconds elapsed for computation
    nstudents = models.IntegerField(default=0)

    def __str__(self):
        return "[OCGLog] %s: %s" % (text_type(self.course_id), self.created)


class StudentFieldOverride(TimeStampedModel):
    """
    Holds the value of a specific field overriden for a student.  This is used
    by the code in the `lms.djangoapps.courseware.student_field_overrides` module to provide
    overrides of xblock fields on a per user basis.

    .. no_pii:
    """
    course_id = CourseKeyField(max_length=255, db_index=True)
    location = UsageKeyField(max_length=255, db_index=True)
    student = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)

    class Meta(object):
        app_label = "courseware"
        unique_together = (('course_id', 'field', 'location', 'student'),)

    field = models.CharField(max_length=255)
    value = models.TextField(default='null')


class DynamicUpgradeDeadlineConfiguration(ConfigurationModel):
    """
    Dynamic upgrade deadline configuration.

    This model controls the behavior of the dynamic upgrade deadline for self-paced courses.

    .. no_pii:
    """
    class Meta(object):
        app_label = 'courseware'

    deadline_days = models.PositiveSmallIntegerField(
        default=21,
        help_text=_('Number of days a learner has to upgrade after content is made available')
    )


class OptOutDynamicUpgradeDeadlineMixin(object):
    """
    Provides convenience methods for interpreting the enabled and opt out status.
    """

    def opted_in(self):
        """Convenience function that returns True if this config model is both enabled and opt_out is False"""
        return self.enabled and not self.opt_out

    def opted_out(self):
        """Convenience function that returns True if this config model is both enabled and opt_out is True"""
        return self.enabled and self.opt_out


class CourseDynamicUpgradeDeadlineConfiguration(OptOutDynamicUpgradeDeadlineMixin, ConfigurationModel):
    """
    Per-course run configuration for dynamic upgrade deadlines.

    This model controls dynamic upgrade deadlines on a per-course run level, allowing course runs to
    have different deadlines or opt out of the functionality altogether.

    .. no_pii:
    """
    class Meta(object):
        app_label = "courseware"

    KEY_FIELDS = ('course_id',)

    course_id = CourseKeyField(max_length=255, db_index=True)

    deadline_days = models.PositiveSmallIntegerField(
        default=21,
        help_text=_('Number of days a learner has to upgrade after content is made available')
    )

    opt_out = models.BooleanField(
        default=False,
        help_text=_('Disable the dynamic upgrade deadline for this course run.')
    )


class OrgDynamicUpgradeDeadlineConfiguration(OptOutDynamicUpgradeDeadlineMixin, ConfigurationModel):
    """
    Per-org configuration for dynamic upgrade deadlines.

    This model controls dynamic upgrade deadlines on a per-org level, allowing organizations to
    have different deadlines or opt out of the functionality altogether.

    .. no_pii:
    """
    class Meta(object):
        app_label = "courseware"

    KEY_FIELDS = ('org_id',)

    org_id = models.CharField(max_length=255, db_index=True)

    deadline_days = models.PositiveSmallIntegerField(
        default=21,
        help_text=_('Number of days a learner has to upgrade after content is made available')
    )

    opt_out = models.BooleanField(
        default=False,
        help_text=_('Disable the dynamic upgrade deadline for this organization.')
    )
