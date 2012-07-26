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

    class Meta:
        unique_together = (('student', 'module_state_key'),)

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

    def __unicode__(self):
        return '/'.join([self.module_type, self.student.username, self.module_state_key, str(self.state)[:20]])


# TODO (cpennington): Remove these once the LMS switches to using XModuleDescriptors


class StudentModuleCache(object):
    """
    A cache of StudentModules for a specific student
    """
    def __init__(self, user, descriptor, depth=None):
        '''
        Find any StudentModule objects that are needed by any child modules of the
        supplied descriptor. Avoids making multiple queries to the database

        descriptor: An XModuleDescriptor
        depth is the number of levels of descendent modules to load StudentModules for, in addition to
            the supplied descriptor. If depth is None, load all descendent StudentModules
        '''
        if user.is_authenticated():
            module_ids = self._get_module_state_keys(descriptor, depth)

            # This works around a limitation in sqlite3 on the number of parameters
            # that can be put into a single query
            self.cache = []
            chunk_size = 500
            for id_chunk in [module_ids[i:i + chunk_size] for i in xrange(0, len(module_ids), chunk_size)]:
                self.cache.extend(StudentModule.objects.filter(
                    student=user,
                    module_state_key__in=id_chunk)
                )

        else:
            self.cache = []

    def _get_module_state_keys(self, descriptor, depth):
        '''
        Get a list of the state_keys needed for StudentModules
        required for this module descriptor

        descriptor: An XModuleDescriptor
        depth is the number of levels of descendent modules to load StudentModules for, in addition to
            the supplied descriptor. If depth is None, load all descendent StudentModules
        '''
        keys = [descriptor.location.url()]

        shared_state_key = getattr(descriptor, 'shared_state_key', None)
        if shared_state_key is not None:
            keys.append(shared_state_key)

        if depth is None or depth > 0:
            new_depth = depth - 1 if depth is not None else depth

            for child in descriptor.get_children():
                keys.extend(self._get_module_state_keys(child, new_depth))

        return keys

    def lookup(self, module_type, module_state_key):
        '''
        Look for a student module with the given type and id in the cache.

        cache -- list of student modules

        returns first found object, or None
        '''
        for o in self.cache:
            if o.module_type == module_type and o.module_state_key == module_state_key:
                return o
        return None

    def append(self, student_module):
        self.cache.append(student_module)
