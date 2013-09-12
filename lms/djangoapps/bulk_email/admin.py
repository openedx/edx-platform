"""
Django admin page for bulk email models
"""
from django.contrib import admin

from bulk_email.models import CourseEmail, Optout, CourseEmailTemplate
from bulk_email.forms import CourseEmailTemplateForm


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
            'fields': ('html_template', 'plain_template'),
            'description': '''
Enter template to be used by course staff when sending emails to enrolled students.

The HTML template is for HTML email, and may contain HTML markup.  The plain template is
for plaintext email.  Both templates should contain the string '{{message_body}}' (with
two curly braces on each side), to indicate where the email text is to be inserted.

Other tags that may be used (surrounded by one curly brace on each side):
{platform_name}        : the name of the platform
{course_title}         : the name of the course
{course_url}           : the course's full URL
{email}                : the user's email address
{account_settings_url} : URL at which users can change email preferences
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
        """Disables the ability to add new templates, as we want to maintain a Singleton."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disables the ability to remove existing templates, as we want to maintain a Singleton."""
        return False


admin.site.register(CourseEmail, CourseEmailAdmin)
admin.site.register(Optout, OptoutAdmin)
admin.site.register(CourseEmailTemplate, CourseEmailTemplateAdmin)
