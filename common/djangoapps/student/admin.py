'''
django admin pages for courseware model
'''
from django import forms
from config_models.admin import ConfigurationModelAdmin
from django.contrib.auth.models import User

from student.models import UserProfile, UserTestGroup, CourseEnrollmentAllowed, DashboardConfiguration
from student.models import (
    CourseEnrollment, Registration, PendingNameChange, CourseAccessRole, LinkedInAddToProfileConfiguration
)
from ratelimitbackend import admin
from student.roles import REGISTERED_ACCESS_ROLES

from xmodule.modulestore.django import modulestore

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError


class CourseAccessRoleForm(forms.ModelForm):
    """Form for adding new Course Access Roles view the Django Admin Panel."""
    class Meta:
        model = CourseAccessRole

    email = forms.EmailField(required=True)
    COURSE_ACCESS_ROLES = [(role_name, role_name) for role_name in REGISTERED_ACCESS_ROLES.keys()]
    role = forms.ChoiceField(choices=COURSE_ACCESS_ROLES)

    def clean_course_id(self):
        """
        Checking course-id format and course exists in module store.
        This field can be null.
        """
        if self.cleaned_data['course_id']:
            course_id = self.cleaned_data['course_id']

            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
                raise forms.ValidationError(u"Invalid CourseID. Please check the format and re-try.")

            if not modulestore().has_course(course_key):
                raise forms.ValidationError(u"Cannot find course with id {} in the modulestore".format(course_id))

            return course_key

        return None

    def clean_org(self):
        """If org and course-id exists then Check organization name
        against the given course.
        """
        if self.cleaned_data.get('course_id') and self.cleaned_data['org']:
            org = self.cleaned_data['org']
            org_name = self.cleaned_data.get('course_id').org
            if org.lower() != org_name.lower():
                raise forms.ValidationError(
                    u"Org name {} is not valid. Valid name is {}.".format(
                        org, org_name
                    )
                )

        return self.cleaned_data['org']

    def clean_email(self):
        """
        Checking user object against given email id.
        """
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except Exception:
            raise forms.ValidationError(
                u"Email does not exist. Could not find {email}. Please re-enter email address".format(
                    email=email
                )
            )

        return user

    def clean(self):
        """
        Checking the course already exists in db.
        """
        cleaned_data = super(CourseAccessRoleForm, self).clean()
        if not self.errors:
            if CourseAccessRole.objects.filter(
                    user=cleaned_data.get("email"),
                    org=cleaned_data.get("org"),
                    course_id=cleaned_data.get("course_id"),
                    role=cleaned_data.get("role")
            ).exists():
                raise forms.ValidationError("Duplicate Record.")

        return cleaned_data


class CourseAccessRoleAdmin(admin.ModelAdmin):
    """Admin panel for the Course Access Role. """
    form = CourseAccessRoleForm
    raw_id_fields = ("user",)
    exclude = ("user",)

    fieldsets = (
        (None, {
            'fields': ('email', 'course_id', 'org', 'role',)
        }),
    )

    list_display = (
        'id', 'user', 'org', 'course_id', 'role',
    )
    search_fields = (
        'id', 'user__username', 'user__email', 'org', 'course_id', 'role',
    )

    def save_model(self, request, obj, form, change):
        obj.user = form.cleaned_data['email']
        super(CourseAccessRoleAdmin, self).save_model(request, obj, form, change)


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
