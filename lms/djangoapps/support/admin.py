""" Django admins for support models """
from django.contrib import admin
from lms.djangoapps.support.models import CourseResetCourseOptIn, CourseResetAudit


class CourseResetCourseOptInAdmin(admin.ModelAdmin):
    """ Django admin for CourseResetCourseOptIn model """
    list_display = ['course_id', 'active']
    fields = ['course_id', 'active', 'created', 'modified']
    readonly_fields = ['course_id', 'created', 'modified']


class CourseResetAuditAdmin(admin.ModelAdmin):
    """ Django admin for CourseResetAudit model """

    list_display = ['course', 'user', 'status', 'created', 'completed_at', 'reset_by']
    fields = ['created', 'modified', 'status', 'completed_at', 'course', 'user', 'course_enrollment', 'reset_by']
    readonly_fields = fields

    @admin.display(description="user")
    def user(self, obj):
        return obj.course_enrollment.user


admin.site.register(CourseResetCourseOptIn, CourseResetCourseOptInAdmin)
admin.site.register(CourseResetAudit, CourseResetAuditAdmin)
