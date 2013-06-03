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
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class StudentModule(models.Model):
    """
    Keeps student state for a particular module in a particular course.
    """
    # For a homework problem, contains a JSON
    # object consisting of state
    MODULE_TYPES = (('problem', 'problem'),
                    ('video', 'video'),
                    ('html', 'html'),
                    ('timelimit', 'timelimit'),
                    )
    ## These three are the key for the object
    module_type = models.CharField(max_length=32, choices=MODULE_TYPES, default='problem', db_index=True)

    # Key used to share state. By default, this is the module_id,
    # but for abtests and the like, this can be set to a shared value
    # for many instances of the module.
    # Filename for homeworks, etc.
    module_state_key = models.CharField(max_length=255, db_index=True, db_column='module_id')
    student = models.ForeignKey(User, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)

    class Meta:
        unique_together = (('student', 'module_state_key', 'course_id'),)

    ## Internal state of the object
    state = models.TextField(null=True, blank=True)

    ## Grade, and are we done?
    grade = models.FloatField(null=True, blank=True, db_index=True)
    max_grade = models.FloatField(null=True, blank=True)
    DONE_TYPES = (('na', 'NOT_APPLICABLE'),
                    ('f', 'FINISHED'),
                    ('i', 'INCOMPLETE'),
                    )
    done = models.CharField(max_length=8, choices=DONE_TYPES, default='na', db_index=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __repr__(self):
        return 'StudentModule<%r>' % ({
            'course_id': self.course_id,
            'module_type': self.module_type,
            'student': self.student.username,
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

    class Meta:
        get_latest_by = "created"

    student_module = models.ForeignKey(StudentModule, db_index=True)
    version = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    # This should be populated from the modified field in StudentModule
    created = models.DateTimeField(db_index=True)
    state = models.TextField(null=True, blank=True)
    grade = models.FloatField(null=True, blank=True)
    max_grade = models.FloatField(null=True, blank=True)

    @receiver(post_save, sender=StudentModule)
    def save_history(sender, instance, **kwargs):
        if instance.module_type in StudentModuleHistory.HISTORY_SAVING_TYPES:
            history_entry = StudentModuleHistory(student_module=instance,
                                                 version=None,
                                                 created=instance.modified,
                                                 state=instance.state,
                                                 grade=instance.grade,
                                                 max_grade=instance.max_grade)
            history_entry.save()


class XModuleContentField(models.Model):
    """
    Stores data set in the Scope.content scope by an xmodule field
    """

    class Meta:
        unique_together = (('definition_id', 'field_name'),)

    # The name of the field
    field_name = models.CharField(max_length=64, db_index=True)

    # The definition id for the module
    definition_id = models.CharField(max_length=255, db_index=True)

    # The value of the field. Defaults to None dumped as json
    value = models.TextField(default='null')

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __repr__(self):
        return 'XModuleContentField<%r>' % ({
            'field_name': self.field_name,
            'definition_id': self.definition_id,
            'value': self.value,
        },)

    def __unicode__(self):
        return unicode(repr(self))


class XModuleSettingsField(models.Model):
    """
    Stores data set in the Scope.settings scope by an xmodule field
    """

    class Meta:
        unique_together = (('usage_id', 'field_name'),)

    # The name of the field
    field_name = models.CharField(max_length=64, db_index=True)

    # The usage id for the module
    usage_id = models.CharField(max_length=255, db_index=True)

    # The value of the field. Defaults to None, dumped as json
    value = models.TextField(default='null')

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __repr__(self):
        return 'XModuleSettingsField<%r>' % ({
            'field_name': self.field_name,
            'usage_id': self.usage_id,
            'value': self.value,
        },)

    def __unicode__(self):
        return unicode(repr(self))


class XModuleStudentPrefsField(models.Model):
    """
    Stores data set in the Scope.preferences scope by an xmodule field
    """

    class Meta:
        unique_together = (('student', 'module_type', 'field_name'),)

    # The name of the field
    field_name = models.CharField(max_length=64, db_index=True)

    # The type of the module for these preferences
    module_type = models.CharField(max_length=64, db_index=True)

    # The value of the field. Defaults to None dumped as json
    value = models.TextField(default='null')

    student = models.ForeignKey(User, db_index=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __repr__(self):
        return 'XModuleStudentPrefsField<%r>' % ({
            'field_name': self.field_name,
            'module_type': self.module_type,
            'student': self.student.username,
            'value': self.value,
        },)

    def __unicode__(self):
        return unicode(repr(self))


class XModuleStudentInfoField(models.Model):
    """
    Stores data set in the Scope.preferences scope by an xmodule field
    """

    class Meta:
        unique_together = (('student', 'field_name'),)

    # The name of the field
    field_name = models.CharField(max_length=64, db_index=True)

    # The value of the field. Defaults to None dumped as json
    value = models.TextField(default='null')

    student = models.ForeignKey(User, db_index=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __repr__(self):
        return 'XModuleStudentInfoField<%r>' % ({
            'field_name': self.field_name,
            'student': self.student.username,
            'value': self.value,
        },)

    def __unicode__(self):
        return unicode(repr(self))


class OfflineComputedGrade(models.Model):
    """
    Table of grades computed offline for a given user and course.
    """
    user = models.ForeignKey(User, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)

    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)

    gradeset = models.TextField(null=True, blank=True)		# grades, stored as JSON

    class Meta:
        unique_together = (('user', 'course_id'), )

    def __unicode__(self):
        return "[OfflineComputedGrade] %s: %s (%s) = %s" % (self.user, self.course_id, self.created, self.gradeset)


class OfflineComputedGradeLog(models.Model):
    """
    Log of when offline grades are computed.
    Use this to be able to show instructor when the last computed grades were done.
    """
    class Meta:
        ordering = ["-created"]
        get_latest_by = "created"

    course_id = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    seconds = models.IntegerField(default=0)  	# seconds elapsed for computation
    nstudents = models.IntegerField(default=0)

    def __unicode__(self):
        return "[OCGLog] %s: %s" % (self.course_id, self.created)


class CourseTask(models.Model):
    """
    Stores information about background tasks that have been submitted to
    perform course-specific work.
    Examples include grading and rescoring.

    `task_type` identifies the kind of task being performed, e.g. rescoring.
    `course_id` uses the course run's unique id to identify the course.
    `task_input` stores input arguments as JSON-serialized dict, for reporting purposes.
        Examples include url of problem being rescored, id of student if only one student being rescored.
    `task_key` stores relevant input arguments encoded into key value for testing to see
           if the task is already running (together with task_type and course_id).

    `task_id` stores the id used by celery for the background task.
    `task_state` stores the last known state of the celery task
    `task_output` stores the output of the celery task.
        Format is a JSON-serialized dict.  Content varies by task_type and task_state.

    `requester` stores id of user who submitted the task
    `created` stores date that entry was first created
    `updated` stores date that entry was last modified
    """
    task_type = models.CharField(max_length=50, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)
    task_key = models.CharField(max_length=255, db_index=True)
    task_input = models.CharField(max_length=255)
    task_id = models.CharField(max_length=255, db_index=True)  # max_length from celery_taskmeta
    task_state = models.CharField(max_length=50, null=True, db_index=True)  # max_length from celery_taskmeta
    task_output = models.CharField(max_length=1024, null=True)
    requester = models.ForeignKey(User, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return 'CourseTask<%r>' % ({
            'task_type': self.task_type,
            'course_id': self.course_id,
            'task_input': self.task_input,
            'task_id': self.task_id,
            'task_state': self.task_state,
            'task_output': self.task_output,
        },)

    def __unicode__(self):
        return unicode(repr(self))
