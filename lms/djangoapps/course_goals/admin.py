"""Django admin for course_goals"""

from django.contrib import admin

from lms.djangoapps.course_goals.models import CourseGoal, CourseGoalReminderStatus, UserActivity


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


@admin.register(CourseGoalReminderStatus)
class CourseGoalReminderStatusAdmin(admin.ModelAdmin):
    """Admin for CourseGoalReminderStatus"""
    list_display = ('id',
                    'goal_user',
                    'goal_course_key',
                    'email_reminder_sent')
    raw_id_fields = ('goal',)
    search_fields = ('goal__user__username', 'goal__course_key')

    def goal_user(self, obj):
        return obj.goal.user.username

    def goal_course_key(self, obj):
        return obj.goal.course_key


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin for UserActivity"""

    list_display = ('id',
                    'user',
                    'course_key',
                    'date')
    raw_id_fields = ('user',)
    search_fields = ('user__username', 'course_key')
