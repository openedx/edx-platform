from django.contrib import admin

from .models import CourseEntitlement


@admin.register(CourseEntitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'uuid',
                    'course_uuid',
                    'created',
                    'modified',
                    'expired_at',
                    'mode',
                    'enrollment_course_run',
                    'order_number')
