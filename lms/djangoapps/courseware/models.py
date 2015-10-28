"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py schemamigration courseware --auto description_of_your_change
3. Add the migration file created in edx-platform/lms/djangoapps/courseware/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""
import logging
import itertools

from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

from model_utils.models import TimeStampedModel
from student.models import user_by_anonymous_id
from submissions.models import score_set, score_reset

from openedx.core.djangoapps.call_stack_manager import CallStackManager, CallStackMixin
from xmodule_django.models import CourseKeyField, LocationKeyField, BlockTypeKeyField  # pylint: disable=import-error
log = logging.getLogger(__name__)

log = logging.getLogger("edx.courseware")


def chunks(items, chunk_size):
    """
    Yields the values from items in chunks of size chunk_size
    """
    items = list(items)
    return (items[i:i + chunk_size] for i in xrange(0, len(items), chunk_size))


class ChunkingManager(models.Manager):
    """
    :class:`~Manager` that adds an additional method :meth:`chunked_filter` to provide
    the ability to make select queries with specific chunk sizes.
    """
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
            self.filter(**dict([(chunk_field, chunk)] + kwargs.items()))
            for chunk in chunks(items, chunk_size)
        )
        return res


class ChunkingCallStackManager(CallStackManager, ChunkingManager):
    """
    A derived class of ChunkingManager, and CallStackManager

    Class is currently unused but remains as part of the CallStackManger work. To re-enable see comment in StudentModule
    """
    pass


class StudentModule(CallStackMixin, models.Model):
    """
    Keeps student state for a particular module in a particular course.
    """
    # Changed back to ChunkingManager from ChunkingCallStackManger. To re-enable CallStack Management change the line
    # back to: objects = ChunkingCallStackManager() Ticket: PLAT-881
    objects = ChunkingManager()
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

    class Meta(object):
        unique_together = (('student', 'module_state_key', 'course_id'),)

    # Internal state of the object
    state = models.TextField(null=True, blank=True)

    # Grade, and are we done?
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
            # We use the student_id instead of username to avoid a database hop.
            # This can actually matter in cases where we're logging many of
            # these (e.g. on a broken progress page).
            'student_id': self.student_id,  # pylint: disable=no-member
            'module_state_key': self.module_state_key,
            'state': str(self.state)[:20],
        },)

    def __unicode__(self):
        return unicode(repr(self))


class StudentModuleHistory(CallStackMixin, models.Model):
    """Keeps a complete history of state changes for a given XModule for a given
    Student. Right now, we restrict this to problems so that the table doesn't
    explode in size."""
    objects = CallStackManager()
    HISTORY_SAVING_TYPES = {'problem'}

    class Meta(object):
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
    objects = ChunkingManager()

    class Meta(object):
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
    class Meta(object):
        unique_together = (('usage_id', 'field_name'),)

    # The definition id for the module
    usage_id = LocationKeyField(max_length=255, db_index=True)


class XModuleStudentPrefsField(XBlockFieldBase):
    """
    Stores data set in the Scope.preferences scope by an xmodule field
    """
    class Meta(object):
        unique_together = (('student', 'module_type', 'field_name'),)

    # The type of the module for these preferences
    module_type = BlockTypeKeyField(max_length=64, db_index=True)

    student = models.ForeignKey(User, db_index=True)


class XModuleStudentInfoField(XBlockFieldBase):
    """
    Stores data set in the Scope.preferences scope by an xmodule field
    """
    class Meta(object):
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

    class Meta(object):
        unique_together = (('user', 'course_id'), )

    def __unicode__(self):
        return "[OfflineComputedGrade] %s: %s (%s) = %s" % (self.user, self.course_id, self.created, self.gradeset)


class OfflineComputedGradeLog(models.Model):
    """
    Log of when offline grades are computed.
    Use this to be able to show instructor when the last computed grades were done.
    """
    class Meta(object):
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

    class Meta(object):
        unique_together = (('course_id', 'field', 'location', 'student'),)

    field = models.CharField(max_length=255)
    value = models.TextField(default='null')


# Signal that indicates that a user's score for a problem has been updated.
# This signal is generated when a scoring event occurs either within the core
# platform or in the Submissions module. Note that this signal will be triggered
# regardless of the new and previous values of the score (i.e. it may be the
# case that this signal is generated when a user re-attempts a problem but
# receives the same score).
SCORE_CHANGED = Signal(
    providing_args=[
        'points_possible',  # Maximum score available for the exercise
        'points_earned',   # Score obtained by the user
        'user_id',  # Integer User ID
        'course_id',  # Unicode string representing the course
        'usage_id'  # Unicode string indicating the courseware instance
    ]
)


@receiver(score_set)
def submissions_score_set_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_set signal defined in the Submissions API, and convert it
    to a SCORE_CHANGED signal defined in this module. Converts the unicode keys
    for user, course and item into the standard representation for the
    SCORE_CHANGED signal.

    This method expects that the kwargs dictionary will contain the following
    entries (See the definition of score_set):
      - 'points_possible': integer,
      - 'points_earned': integer,
      - 'anonymous_user_id': unicode,
      - 'course_id': unicode,
      - 'item_id': unicode
    """
    points_possible = kwargs.get('points_possible', None)
    points_earned = kwargs.get('points_earned', None)
    course_id = kwargs.get('course_id', None)
    usage_id = kwargs.get('item_id', None)
    user = None
    if 'anonymous_user_id' in kwargs:
        user = user_by_anonymous_id(kwargs.get('anonymous_user_id'))

    # If any of the kwargs were missing, at least one of the following values
    # will be None.
    if all((user, points_possible, points_earned, course_id, usage_id)):
        SCORE_CHANGED.send(
            sender=None,
            points_possible=points_possible,
            points_earned=points_earned,
            user_id=user.id,
            course_id=course_id,
            usage_id=usage_id
        )
    else:
        log.exception(
            u"Failed to process score_set signal from Submissions API. "
            "points_possible: %s, points_earned: %s, user: %s, course_id: %s, "
            "usage_id: %s", points_possible, points_earned, user, course_id, usage_id
        )


@receiver(score_reset)
def submissions_score_reset_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_reset signal defined in the Submissions API, and convert
    it to a SCORE_CHANGED signal indicating that the score has been set to 0/0.
    Converts the unicode keys for user, course and item into the standard
    representation for the SCORE_CHANGED signal.

    This method expects that the kwargs dictionary will contain the following
    entries (See the definition of score_reset):
      - 'anonymous_user_id': unicode,
      - 'course_id': unicode,
      - 'item_id': unicode
    """
    course_id = kwargs.get('course_id', None)
    usage_id = kwargs.get('item_id', None)
    user = None
    if 'anonymous_user_id' in kwargs:
        user = user_by_anonymous_id(kwargs.get('anonymous_user_id'))

    # If any of the kwargs were missing, at least one of the following values
    # will be None.
    if all((user, course_id, usage_id)):
        SCORE_CHANGED.send(
            sender=None,
            points_possible=0,
            points_earned=0,
            user_id=user.id,
            course_id=course_id,
            usage_id=usage_id
        )
    else:
        log.exception(
            u"Failed to process score_reset signal from Submissions API. "
            "user: %s, course_id: %s, usage_id: %s", user, course_id, usage_id
        )
