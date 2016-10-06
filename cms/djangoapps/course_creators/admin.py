"""
django admin page for the course creators table
"""

import logging
from ratelimitbackend import admin
from smtplib import SMTPException

from django.conf import settings
from django.dispatch import receiver
from django.core.mail import send_mail

from course_creators.models import CourseCreator, update_creator_state, send_user_notification, send_admin_notification
from course_creators.views import update_course_creator_group
from openedx.core.djangoapps.edxmako.shortcuts import render_to_string

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
    list_display = ['username', get_email, 'state', 'state_changed', 'note']
    readonly_fields = ['username', 'state_changed']
    # Controls the order on the edit form (without this, read-only fields appear at the end).
    fieldsets = (
        (None, {
            'fields': ['username', 'state', 'state_changed', 'note']
        }),
    )
    # Fields that filtering support
    list_filter = ['state', 'state_changed']
    # Fields that search supports.
    search_fields = ['user__username', 'user__email', 'state', 'note']
    # Turn off the action bar (we have no bulk actions)
    actions = None

    def username(self, inst):
        """
        Returns the username for a given user.

        Implemented to make sorting by username instead of by user object.
        """
        return inst.user.username

    username.admin_order_field = 'user__username'

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


@receiver(send_user_notification, sender=CourseCreator)
def send_user_notification_callback(sender, **kwargs):
    """
    Callback for notifying user about course creator status change.
    """
    user = kwargs['user']
    updated_state = kwargs['state']

    studio_request_email = settings.FEATURES.get('STUDIO_REQUEST_EMAIL', '')
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


@receiver(send_admin_notification, sender=CourseCreator)
def send_admin_notification_callback(sender, **kwargs):
    """
    Callback for notifying admin of a user in the 'pending' state.
    """
    user = kwargs['user']

    studio_request_email = settings.FEATURES.get('STUDIO_REQUEST_EMAIL', '')
    context = {'user_name': user.username, 'user_email': user.email}

    subject = render_to_string('emails/course_creator_admin_subject.txt', context)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/course_creator_admin_user_pending.txt', context)

    try:
        send_mail(
            subject,
            message,
            studio_request_email,
            [studio_request_email],
            fail_silently=False
        )
    except SMTPException:
        log.warning("Failure sending 'pending state' e-mail for %s to %s", user.email, studio_request_email)
