"""Django admin for course_goals"""

from django.contrib import admin

from lms.djangoapps.course_goals.models import CourseGoal, UserActivity


@admin.register(CourseGoal)
class CourseGoalAdmin(admin.ModelAdmin):
    """Admin for CourseGoal"""
    list_display = ('id',
                    'user',
                    'course_key',
                    'days_per_week',
                    'subscribed_to_reminders')
    raw_id_fields = ('user',)
    search_fields = ('user__username', 'course_key')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin for UserActivity"""

    list_display = ('id',
                    'user',
                    'course_key',
                    'date')
    raw_id_fields = ('user',)
    search_fields = ('user__username', 'course_key')
