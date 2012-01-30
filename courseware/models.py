from django.db import models
from django.contrib.auth.models import User

class StudentModule(models.Model):
    # For a homework problem, contains a JSON
    # object consisting of state
    MODULE_TYPES = (('problem','problem'),
                    ('video','video'),
                    ('html','html'),
                    )
    ## These three are the key for the object
    module_type = models.CharField(max_length=32, choices=MODULE_TYPES, default='problem')
    module_id = models.CharField(max_length=255) # Filename for homeworks, etc. 
    student = models.ForeignKey(User)
    class Meta:
        unique_together = (('student', 'module_id'),)

    ## Internal state of the object
    state = models.TextField(null=True, blank=True)

    ## Grade, and are we done? 
    grade = models.FloatField(null=True, blank=True)
    #max_grade = models.FloatField(null=True, blank=True)
    
    # DONE_TYPES = (('done','DONE'),          # Finished
    #               ('incomplete','NOTDONE'), # Not finished
    #               ('na','NA'))              # Not applicable (e.g. vertical)
    # done = models.CharField(max_length=16, choices=DONE_TYPES)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.module_type+'/'+self.student.username+"/"+self.module_id+'/'+str(self.state)[:20]
