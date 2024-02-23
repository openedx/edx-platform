""" Django admins for support models """
from django.contrib import admin
from lms.djangoapps.support.models import CourseResetCourseOptIn, CourseResetAudit


class CourseResetCourseOptInAdmin(admin.ModelAdmin):
    """ Django admin for CourseResetCourseOptIn model """
    list_display = ['course_id', 'active']
    fields = ['course_id', 'active', 'created', 'modified']

    def get_readonly_fields(self, request, obj=None):
        """
        Ensure that 'course_id' cannot be edited after creation.
        """
        if obj:
            return ['course_id', 'created', 'modified']
        else:
            return ['created', 'modified']


class CourseResetAuditAdmin(admin.ModelAdmin):
    """ Django admin for CourseResetAudit model """

    list_display = ['course', 'user', 'status', 'created', 'completed_at', 'reset_by']
    fields = ['created', 'modified', 'status', 'completed_at', 'course', 'user', 'course_enrollment', 'reset_by']

    def get_readonly_fields(self, request, obj=None):
        """
        If we are editing an existing model, we should only be able to change the status, for potential debugging
        """
        if obj:
            return ['created', 'modified', 'completed_at', 'course', 'user', 'course_enrollment', 'reset_by']
        else:
            return ['created', 'modified', 'user']

    @admin.display(description="user")
    def user(self, obj):
        return obj.course_enrollment.user


admin.site.register(CourseResetCourseOptIn, CourseResetCourseOptInAdmin)
admin.site.register(CourseResetAudit, CourseResetAuditAdmin)
