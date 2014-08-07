'''
django admin pages for courseware model
'''

from student.models import UserProfile, UserTestGroup, CourseEnrollmentAllowed
from student.models import CourseEnrollment, Registration, PendingNameChange, CourseAccessRole, CourseAccessRoleAdmin
from ratelimitbackend import admin

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'gender', 'allow_certificate')
admin.site.register(UserProfile, UserProfileAdmin)

admin.site.register(UserTestGroup)

admin.site.register(CourseEnrollment)

admin.site.register(CourseEnrollmentAllowed)

admin.site.register(Registration)

admin.site.register(PendingNameChange)

admin.site.register(CourseAccessRole, CourseAccessRoleAdmin)
