from django.contrib import admin

from .models import CourseEntitlement, CourseEntitlementPolicy


@admin.register(CourseEntitlement)
class CourseEntitlementAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'uuid',
                    'course_uuid',
                    'created',
                    'modified',
                    'expired_at',
                    'mode',
                    'enrollment_course_run',
                    'order_number')


@admin.register(CourseEntitlementPolicy)
class CourseEntitlementPolicyAdmin(admin.ModelAdmin):
    """
    Registration of CourseEntitlementPolicy for Django Admin
    """
    list_display = ('expiration_period_days',
                    'refund_period_days',
                    'regain_period_days',
                    'site')
