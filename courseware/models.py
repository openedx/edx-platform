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
from django.core.cache import cache
from django.contrib.auth.models import User

from cache_toolbox import cache_model, cache_relation

CACHE_TIMEOUT = 60 * 60 * 4 # Set the cache timeout to be four hours

class StudentModule(models.Model):
    # For a homework problem, contains a JSON
    # object consisting of state
    MODULE_TYPES = (('problem','problem'),
                    ('video','video'),
                    ('html','html'),
                    )
    ## These three are the key for the object
    module_type = models.CharField(max_length=32, choices=MODULE_TYPES, default='problem', db_index=True)
    module_id = models.CharField(max_length=255, db_index=True) # Filename for homeworks, etc. 
    student = models.ForeignKey(User, db_index=True)
    class Meta:
        unique_together = (('student', 'module_id'),)

    ## Internal state of the object
    state = models.TextField(null=True, blank=True)

    ## Grade, and are we done? 
    grade = models.FloatField(null=True, blank=True, db_index=True)
    max_grade = models.FloatField(null=True, blank=True)
    DONE_TYPES = (('na','NOT_APPLICABLE'),
                    ('f','FINISHED'),
                    ('i','INCOMPLETE'),
                    )
    done = models.CharField(max_length=8, choices=DONE_TYPES, default='na', db_index=True)

    # DONE_TYPES = (('done','DONE'),          # Finished
    #               ('incomplete','NOTDONE'), # Not finished
    #               ('na','NA'))              # Not applicable (e.g. vertical)
    # done = models.CharField(max_length=16, choices=DONE_TYPES)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __unicode__(self):
        return self.module_type+'/'+self.student.username+"/"+self.module_id+'/'+str(self.state)[:20]

    @classmethod
    def get_from_cache(cls, student, module_ids):
        k = cls.key_for(student, module_ids)
        student_modules = k.get(k)
        if student_modules is None:
            student_modules = StudentModule.objects.filter(student=student, module_id__in=module_ids)
            # It's possible it really doesn't exist...
            if student_modules is not None:
                k.set(k, student_modules, CACHE_TIMEOUT)

        return student_modules


    @classmethod
    def clear_cache_for(cls, student, module_ids):
        k = cls.key_for(student_id, module_ids)
        cache.delete(k)

    @classmethod
    def key_for(cls, student, module_ids):
        module_ids_hash = md5(",".join(sorted(modules_ids))).hexdigest()
        return "StudentModule-student_id:{0};module_ids_hash:{1}".format(student.id, module_ids_hash)


cache_model(StudentModule)