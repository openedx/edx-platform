'''
django admin pages for courseware model
'''
from django import forms
from config_models.admin import ConfigurationModelAdmin

from student.models import UserProfile, UserTestGroup, CourseEnrollmentAllowed, DashboardConfiguration
from student.models import (
    CourseEnrollment, Registration, PendingNameChange, CourseAccessRole, LinkedInAddToProfileConfiguration
)
from ratelimitbackend import admin
from student.roles import REGISTERED_ACCESS_ROLES


class CourseAccessRoleForm(forms.ModelForm):
    """Form for adding new Course Access Roles view the Django Admin Panel."""
    class Meta:
        model = CourseAccessRole

    COURSE_ACCESS_ROLES = [(role_name, role_name) for role_name in REGISTERED_ACCESS_ROLES.keys()]
    role = forms.ChoiceField(choices=COURSE_ACCESS_ROLES)


class CourseAccessRoleAdmin(admin.ModelAdmin):
    """Admin panel for the Course Access Role. """
    form = CourseAccessRoleForm
    raw_id_fields = ("user",)
    list_display = (
        'id', 'user', 'org', 'course_id', 'role'
    )


class LinkedInAddToProfileConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for the LinkedIn Add to Profile configuration. """

    class Meta:
        model = LinkedInAddToProfileConfiguration

    # Exclude deprecated fields
    exclude = ('dashboard_tracking_code',)


admin.site.register(UserProfile)

admin.site.register(UserTestGroup)

admin.site.register(CourseEnrollment)

admin.site.register(CourseEnrollmentAllowed)

admin.site.register(Registration)

admin.site.register(PendingNameChange)

admin.site.register(CourseAccessRole, CourseAccessRoleAdmin)

admin.site.register(DashboardConfiguration, ConfigurationModelAdmin)

admin.site.register(LinkedInAddToProfileConfiguration, LinkedInAddToProfileConfigurationAdmin)
