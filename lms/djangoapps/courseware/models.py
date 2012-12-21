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

# TODO (cpennington): Remove these once the LMS switches to using XModuleDescriptors


class StudentModuleCache(object):
    """
    A cache of StudentModules for a specific student
    """
    def __init__(self, course_id, user, descriptors, select_for_update=False):
        '''
        Find any StudentModule objects that are needed by any descriptor
        in descriptors. Avoids making multiple queries to the database.
        Note: Only modules that have store_state = True or have shared
        state will have a StudentModule.

        Arguments
        user: The user for which to fetch maching StudentModules
        descriptors: An array of XModuleDescriptors.
        select_for_update: Flag indicating whether the rows should be locked until end of transaction
        '''
        if user.is_authenticated():
            module_ids = self._get_module_state_keys(descriptors)

            # This works around a limitation in sqlite3 on the number of parameters
            # that can be put into a single query
            self.cache = []
            chunk_size = 500
            for id_chunk in [module_ids[i:i + chunk_size] for i in xrange(0, len(module_ids), chunk_size)]:
                if select_for_update:
                    self.cache.extend(StudentModule.objects.select_for_update().filter(
                        course_id=course_id,
                        student=user,
                        module_state_key__in=id_chunk)
                    )
                else:
                    self.cache.extend(StudentModule.objects.filter(
                        course_id=course_id,
                        student=user,
                        module_state_key__in=id_chunk)
                    )

        else:
            self.cache = []

    @classmethod
    def cache_for_descriptor_descendents(cls, course_id, user, descriptor, depth=None,
                                         descriptor_filter=lambda descriptor: True,
                                         select_for_update=False):
        """
        course_id: the course in the context of which we want StudentModules.
        user: the django user for whom to load modules.
        descriptor: An XModuleDescriptor
        depth is the number of levels of descendent modules to load StudentModules for, in addition to
            the supplied descriptor. If depth is None, load all descendent StudentModules
        descriptor_filter is a function that accepts a descriptor and return wether the StudentModule
            should be cached
        select_for_update: Flag indicating whether the rows should be locked until end of transaction
        """

        def get_child_descriptors(descriptor, depth, descriptor_filter):
            if descriptor_filter(descriptor):
                descriptors = [descriptor]
            else:
                descriptors = []

            if depth is None or depth > 0:
                new_depth = depth - 1 if depth is not None else depth

                for child in descriptor.get_children():
                    descriptors.extend(get_child_descriptors(child, new_depth, descriptor_filter))

            return descriptors

        descriptors = get_child_descriptors(descriptor, depth, descriptor_filter)

        return StudentModuleCache(course_id, user, descriptors, select_for_update)

    def _get_module_state_keys(self, descriptors):
        '''
        Get a list of the state_keys needed for StudentModules
        required for this module descriptor

        descriptor_filter is a function that accepts a descriptor and return wether the StudentModule
            should be cached
        '''
        return [descriptor.location.url() for descriptor in descriptors if descriptor.stores_state]

    def lookup(self, course_id, module_type, module_state_key):
        '''
        Look for a student module with the given course_id, type, and id in the cache.

        cache -- list of student modules

        returns first found object, or None
        '''
        for o in self.cache:
            if (o.course_id == course_id and
                o.module_type == module_type and
                o.module_state_key == module_state_key):
                return o
        return None

    def append(self, student_module):
        self.cache.append(student_module)
