from django.db import models
from django.contrib.auth.models import User
import uuid

class UserProfile(models.Model):
    ## CRITICAL TODO/SECURITY
    # Sanitize all fields. 
    # This is not visible to other users, but could introduce holes later
    user = models.ForeignKey(User, unique=True, db_index=True)
    name = models.TextField(blank=True)
    language = models.TextField(blank=True)
    location = models.TextField(blank=True)
    meta = models.TextField(blank=True) # JSON dictionary for future expansion
    courseware = models.TextField(blank=True, default='courseware.xml')

class Registration(models.Model):
    ''' Allows us to wait for e-mail before user is registered. A
        registration profile is created when the user creates an 
        account, but that account is inactive. Once the user clicks
        on the activation key, it becomes active. '''
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

