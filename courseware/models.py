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
        unique_together = (('student', 'module_id', 'module_type'),)

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


class UserProfile(models.Model):
    class Meta:
        db_table = "auth_userprofile"

    ## CRITICAL TODO/SECURITY
    # Sanitize all fields. 
    # This is not visible to other users, but could introduce holes later
    user = models.ForeignKey(User, unique=True, db_index=True)
    name = models.TextField(blank=True)
    language = models.TextField(blank=True)
    location = models.TextField(blank=True)
    meta = models.TextField(blank=True) # JSON dictionary for future expansion
    courseware = models.TextField(blank=True, default='course.xml')


class Registration(models.Model):
    ''' Allows us to wait for e-mail before user is registered. A
        registration profile is created when the user creates an 
        account, but that account is inactive. Once the user clicks
        on the activation key, it becomes active. '''

    class Meta:
        db_table = "auth_userprofile"

    user = models.ForeignKey(User, unique=True)
    activation_key = models.CharField(('activation key'), max_length=32, unique=True, db_index=True)

    def register(self, user):
        # MINOR TODO: Switch to crypto-secure key
        self.activation_key=uuid.uuid4().hex
        self.user=user
        self.save()

    def activate(self):
        self.user.is_active = True
        self.user.save()
        self.delete()

