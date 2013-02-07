'''
django admin pages for courseware model
'''

from courseware.models import *
from django.contrib import admin
from django.contrib.auth.models import User

admin.site.register(StudentModule)

admin.site.register(OfflineComputedGrade)

admin.site.register(OfflineComputedGradeLog)
