'''
django admin pages for courseware model
'''

from student.models import *
from django.contrib import admin
from django.contrib.auth.models import User

admin.site.register(UserProfile)

admin.site.register(Registration)

admin.site.register(PendingNameChange)

