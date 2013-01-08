"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the mitx dir
2. ./manage.py schemamigration courseware --auto description_of_your_change
3. Add the migration file created in mitx/courseware/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""
from django.db import models
#from django.core.cache import cache
from django.contrib.auth.models import User

#from cache_toolbox import cache_model, cache_relation

#CACHE_TIMEOUT = 60 * 60 * 4 # Set the cache timeout to be four hours


class StudentModule(models.Model):
    """
    Keeps student state for a particular module in a particular course.
    """
    # For a homework problem, contains a JSON
    # object consisting of state
    MODULE_TYPES = (('problem', 'problem'),
                    ('video', 'video'),
                    ('html', 'html'),
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
    Stores data set in the Scope.student_preferences scope by an xmodule field
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
    Stores data set in the Scope.student_preferences scope by an xmodule field
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

