"""
Admin registration for Course Teams.
"""


from django.contrib import admin

from .models import CourseTeam, CourseTeamMembership


@admin.register(CourseTeam)
class CourseTeamAdmin(admin.ModelAdmin):
    """
    Admin config for course teams.
    """
    list_display = ('course_id', 'topic_id', 'team_id', 'name', 'team_size', 'organization_protected')
    search_fields = ('course_id', 'topic_id', 'team_id', 'name', 'description')
    ordering = ('course_id', 'topic_id', 'team_id')
    readonly_fields = ('team_size',)


@admin.register(CourseTeamMembership)
class CourseTeamMembershipAdmin(admin.ModelAdmin):
    """
    Admin config for course team memberships.
    """
    list_display = ('team', 'user', 'date_joined', 'last_activity_at')
    search_fields = ('team__team_id', 'user__username', 'user__email')
