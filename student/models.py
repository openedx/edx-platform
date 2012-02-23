"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the mitx dir
2. ./manage.py schemamigration user --auto description_of_your_change
3. Add the migration file created in mitx/courseware/migrations/
"""
import uuid

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    class Meta:
        db_table = "auth_userprofile"

    ## CRITICAL TODO/SECURITY
    # Sanitize all fields. 
    # This is not visible to other users, but could introduce holes later
    user = models.ForeignKey(User, unique=True, db_index=True)
    name = models.CharField(blank=True, max_length=255, db_index=True)
    language = models.CharField(blank=True, max_length=255, db_index=True)
    location = models.CharField(blank=True, max_length=255, db_index=True)
    meta = models.CharField(blank=True, max_length=255) # JSON dictionary for future expansion
    courseware = models.CharField(blank=True, max_length=255, default='course.xml')

class UserTestGroup(models.Model):
    users = models.ManyToManyField(User, db_index=True)
    name = models.CharField(blank=False, max_length=32, db_index=True)
    description = models.TextField(blank=True)

class Registration(models.Model):
    ''' Allows us to wait for e-mail before user is registered. A
        registration profile is created when the user creates an 
        account, but that account is inactive. Once the user clicks
        on the activation key, it becomes active. '''
    class Meta:
        db_table = "auth_registration"

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
        #self.delete()

