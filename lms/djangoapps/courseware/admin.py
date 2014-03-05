'''
django admin pages for courseware model
'''

from courseware.models import StudentModule, OfflineComputedGrade, OfflineComputedGradeLog, CoursePreference
from ratelimitbackend import admin

admin.site.register(StudentModule)

admin.site.register(OfflineComputedGrade)

admin.site.register(OfflineComputedGradeLog)

admin.site.register(CoursePreference)
