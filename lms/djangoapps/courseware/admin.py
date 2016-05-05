'''
django admin pages for courseware model
'''

from ratelimitbackend import admin

from .models import StudentModule, OfflineComputedGrade, OfflineComputedGradeLog

admin.site.register(StudentModule)

admin.site.register(OfflineComputedGrade)

admin.site.register(OfflineComputedGradeLog)
