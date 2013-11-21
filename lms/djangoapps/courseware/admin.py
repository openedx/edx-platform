'''
django admin pages for courseware model
'''

from courseware.models import StudentModule, OfflineComputedGrade, OfflineComputedGradeLog, CoursePreference
from ratelimitbackend import admin
from django.contrib.auth.models import User

admin.site.register(StudentModule)

admin.site.register(OfflineComputedGrade)

admin.site.register(OfflineComputedGradeLog)

admin.site.register(CoursePreference)