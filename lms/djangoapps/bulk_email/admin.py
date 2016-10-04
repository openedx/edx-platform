"""
Django admin page for bulk email models
"""
from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin

from bulk_email.models import CourseEmail, Optout, CourseEmailTemplate, CourseAuthorization, BulkEmailFlag
from bulk_email.forms import CourseEmailTemplateForm, CourseAuthorizationAdminForm


class CourseEmailAdmin(admin.ModelAdmin):
    """Admin for course email."""
    readonly_fields = ('sender',)


class OptoutAdmin(admin.ModelAdmin):
    """Admin for optouts."""
    list_display = ('user', 'course_id')


class CourseEmailTemplateAdmin(admin.ModelAdmin):
    """Admin for course email templates."""
    form = CourseEmailTemplateForm
    fieldsets = (
        (None, {
            # make the HTML template display above the plain template:
            'fields': ('html_template', 'plain_template', 'name'),
            'description': '''
Enter template to be used by course staff when sending emails to enrolled students.

The HTML template is for HTML email, and may contain HTML markup.  The plain template is
for plaintext email.  Both templates should contain the string '{{message_body}}' (with
two curly braces on each side), to indicate where the email text is to be inserted.

Other tags that may be used (surrounded by one curly brace on each side):
{platform_name}        : the name of the platform
{course_title}         : the name of the course
{course_root}          : the URL path to the root of the course
{course_url}           : the course's full URL
{email}                : the user's email address
{account_settings_url} : URL at which users can change account preferences
{email_settings_url}   : URL at which users can change course email preferences
{course_image_url}     : URL for the course's course image.
    Will return a broken link if course doesn't have a course image set.

Note that there is currently NO validation on tags, so be careful. Typos or use of
unsupported tags will cause email sending to fail.
'''
        }),
    )
    # Turn off the action bar (we have no bulk actions)
    actions = None

    def has_add_permission(self, request):
        """Enable the ability to add new templates, as we want to be able to define multiple templates."""
        return True

    def has_delete_permission(self, request, obj=None):
        """
        Disables the ability to remove existing templates, as we'd like to make sure we don't have dangling references.
        """
        return False


class CourseAuthorizationAdmin(admin.ModelAdmin):
    """Admin for enabling email on a course-by-course basis."""
    form = CourseAuthorizationAdminForm
    fieldsets = (
        (None, {
            'fields': ('course_id', 'email_enabled'),
            'description': '''
Enter a course id in the following form: Org/Course/CourseRun, eg MITx/6.002x/2012_Fall
Do not enter leading or trailing slashes. There is no need to surround the course ID with quotes.
Validation will be performed on the course name, and if it is invalid, an error message will display.

To enable email for the course, check the "Email enabled" box, then click "Save".
'''
        }),
    )

admin.site.register(CourseEmail, CourseEmailAdmin)
admin.site.register(Optout, OptoutAdmin)
admin.site.register(CourseEmailTemplate, CourseEmailTemplateAdmin)
admin.site.register(CourseAuthorization, CourseAuthorizationAdmin)
admin.site.register(BulkEmailFlag, ConfigurationModelAdmin)
