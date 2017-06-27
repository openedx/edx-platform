'''
django admin pages for courseware model
'''

from ratelimitbackend import admin

from courseware.models import OfflineComputedGrade, OfflineComputedGradeLog, StudentModule

admin.site.register(StudentModule)

admin.site.register(OfflineComputedGrade)

admin.site.register(OfflineComputedGradeLog)
