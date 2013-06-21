'''
django admin pages for courseware model
'''

from psychometrics.models import PsychometricData
from django.contrib import admin

admin.site.register(PsychometricData)
