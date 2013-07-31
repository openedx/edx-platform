"""
django admin page for the course creators table
"""

from course_creators.models import CourseCreator, update_creator_state
from course_creators.views import update_course_creator_group

from ratelimitbackend import admin
from django.conf import settings
from django.dispatch import receiver
from mitxmako.shortcuts import render_to_string

import logging

log = logging.getLogger("studio.coursecreatoradmin")


def get_email(obj):
    """ Returns the email address for a user """
    return obj.user.email

get_email.short_description = 'email'


class CourseCreatorAdmin(admin.ModelAdmin):
    """
    Admin for the course creator table.
    """

    # Fields to display on the overview page.
    list_display = ['user', get_email, 'state', 'state_changed', 'note']
    readonly_fields = ['user', 'state_changed']
    # Controls the order on the edit form (without this, read-only fields appear at the end).
    fieldsets = (
        (None, {
            'fields': ['user', 'state', 'state_changed', 'note']
        }),
    )
    # Fields that filtering support
    list_filter = ['state', 'state_changed']
    # Fields that search supports.
    search_fields = ['user__username', 'user__email', 'state', 'note']
    # Turn off the action bar (we have no bulk actions)
    actions = None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def save_model(self, request, obj, form, change):
        # Store who is making the request.
        obj.admin = request.user
        obj.save()


admin.site.register(CourseCreator, CourseCreatorAdmin)


@receiver(update_creator_state, sender=CourseCreator)
def update_creator_group_callback(sender, **kwargs):
    """
    Callback for when the model's creator status has changed.
    """
    user = kwargs['user']
    updated_state = kwargs['state']
    update_course_creator_group(kwargs['caller'], user, updated_state == CourseCreator.GRANTED)

    studio_request_email = settings.MITX_FEATURES.get('STUDIO_REQUEST_EMAIL','')
    context = {'studio_request_email': studio_request_email}

    subject = render_to_string('emails/course_creator_subject.txt', context)
    subject = ''.join(subject.splitlines())
    if updated_state == CourseCreator.GRANTED:
        message_template = 'emails/course_creator_granted.txt'
    elif updated_state == CourseCreator.DENIED:
        message_template = 'emails/course_creator_denied.txt'
    else:
        # changed to unrequested or pending
        message_template = 'emails/course_creator_revoked.txt'
    message = render_to_string(message_template, context)

    try:
        user.email_user(subject, message, studio_request_email)
    except:
        log.warning("Unable to send course creator status e-mail to %s", user.email)
